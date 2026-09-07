"""
Discovery tasks for crawling and discovering PDFs.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
import importlib
try:
    _celery_mod = importlib.import_module("celery")
    shared_task = _celery_mod.shared_task
except Exception:
    class DummyTask:
        def __init__(self, fn):
            self.fn = fn
            self.id = "mock-task-id"
        def __call__(self, *args, **kwargs):
            import inspect
            sig = inspect.signature(self.fn)
            params = list(sig.parameters.keys())
            if params and params[0] in ("self", "task"):
                return self.fn(self, *args, **kwargs)
            return self.fn(*args, **kwargs)
        def delay(self, *args, **kwargs):
            return self(*args, **kwargs)
        def retry(self, exc=None, countdown=None, max_retries=None):
            if exc:
                raise exc
            return None

    def shared_task(func=None, **kwargs):
        if func is None:
            return lambda f: DummyTask(f)
        return DummyTask(func)
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models import CrawlLog, CrawlQueue, Document, SystemStatus
from ..services.discovery_service import (
    claim_next_crawl_queue_item,
    fetch_html,
    parse_ceo_district_links,
    parse_drive_listing,
    record_crawl_log,
    upsert_crawl_queue,
    upsert_document,
    update_system_status,
)

logger = logging.getLogger(__name__)

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


@shared_task(bind=True, max_retries=5)
def process_crawl_queue_item(self, crawl_queue_id: int) -> dict:
    """
    Process a single item from the crawl_queue.
    
    This task:
    1. Claims the next PENDING crawl queue item
    2. Fetches and parses the URL based on its type
    3. Discovers new URLs and adds them to the queue
    4. Updates the queue item status
    5. Implements exponential backoff on failure
    """
    db = SessionLocal()
    try:
        queue_item = db.query(CrawlQueue).filter(CrawlQueue.id == crawl_queue_id).first()
        if not queue_item:
            logger.warning(f"Crawl queue item {crawl_queue_id} not found")
            return {"status": "NOT_FOUND", "item_id": crawl_queue_id}

        queue_item.status = "PROCESSING"
        queue_item.last_attempt = datetime.utcnow()
        db.commit()

        logger.info(f"Processing crawl queue item: {queue_item.url} (type: {queue_item.url_type})")

        try:
            html = fetch_html(queue_item.url)
            discovered = 0

            # Parse based on URL type
            if queue_item.url_type == "SOURCE":
                # Main CEO Karnataka page - extract district links
                district_links = parse_ceo_district_links(html, queue_item.url)

                # Filter by targeted district if single-district mode is active
                if queue_item.district and queue_item.district.upper() != "ALL":
                    target_dist_lower = queue_item.district.lower()
                    district_links = [
                        link for link in district_links
                        if target_dist_lower in link["district"].lower() or link["district"].lower() in target_dist_lower
                    ]
                    logger.info(f"Targeting single district: '{queue_item.district}'. Matched {len(district_links)} district link(s).")

                for link in district_links:
                    new_queue_item, created = upsert_crawl_queue(
                        db,
                        url=link["url"],
                        url_type="DISTRICT",
                        parent_url=queue_item.url,
                        district=link["district"],
                        priority=50,
                    )
                    if created:
                        discovered += 1
                logger.info(f"Discovered {discovered} district links from SOURCE")

            elif queue_item.url_type in ("DISTRICT", "SUBDISTRICT", "FOLDER"):
                # Drive folder page - extract subfolders and PDFs recursively
                items = parse_drive_listing(html, queue_item.url)
                for item in items:
                    if item["type"] == "folder":
                        child_subdistrict = item.get("subdistrict") or queue_item.subdistrict
                        new_queue_item, created = upsert_crawl_queue(
                            db,
                            url=item["url"],
                            url_type="FOLDER",
                            parent_url=queue_item.url,
                            district=queue_item.district,
                            subdistrict=child_subdistrict,
                            priority=40,
                        )
                        if created:
                            discovered += 1
                    elif item["type"] == "pdf":
                        # Found a PDF - create Document and enqueue for processing
                        doc, created = upsert_document(
                            db,
                            url=item["url"],
                            parent_url=queue_item.url,
                            district=queue_item.district,
                            subdistrict=queue_item.subdistrict,
                            document_name=item["name"],
                        )
                        if created:
                            discovered += 1
                logger.info(f"Discovered {discovered} items (folders/PDFs) from {queue_item.url_type}: {queue_item.url}")

            db.commit()

            # Mark queue item as completed
            queue_item.status = "COMPLETED"
            queue_item.attempt_count = (queue_item.attempt_count or 0) + 1
            db.commit()

            return {
                "status": "SUCCESS",
                "item_id": crawl_queue_id,
                "url": queue_item.url,
                "discovered": discovered,
            }

        except Exception as fetch_error:
            logger.error(f"Error processing crawl queue item {crawl_queue_id}: {str(fetch_error)}")
            
            # Implement exponential backoff
            retry_count = queue_item.attempt_count or 0
            if retry_count < settings.MAX_RETRY_ATTEMPTS:
                backoff_delay = settings.INITIAL_RETRY_DELAY * (2 ** retry_count)
                next_attempt = datetime.utcnow() + timedelta(seconds=backoff_delay)
                
                queue_item.status = "RETRY"
                queue_item.error = str(fetch_error)
                queue_item.next_attempt = next_attempt
                queue_item.attempt_count = retry_count + 1
                db.commit()

                logger.info(f"Retrying crawl queue item {crawl_queue_id} in {backoff_delay} seconds (attempt {queue_item.attempt_count}/{settings.MAX_RETRY_ATTEMPTS})")
                
                # Re-raise to trigger Celery retry with exponential backoff
                raise self.retry(
                    exc=fetch_error,
                    countdown=backoff_delay,
                    max_retries=settings.MAX_RETRY_ATTEMPTS - retry_count,
                )
            else:
                # Max retries exceeded
                queue_item.status = "FAILED"
                queue_item.error = f"Max retries exceeded: {str(fetch_error)}"
                queue_item.attempt_count = retry_count + 1
                db.commit()
                logger.error(f"Crawl queue item {crawl_queue_id} failed permanently after {retry_count} attempts")
                
                return {
                    "status": "FAILED",
                    "item_id": crawl_queue_id,
                    "error": str(fetch_error),
                }

    finally:
        db.close()


@shared_task
def start_discovery_background(
    source_url: Optional[str] = None,
    district: Optional[str] = None,
) -> dict:
    """
    Start the discovery process by queuing the initial URL.
    
    This task initializes the discovery by:
    1. Setting system status to RUNNING
    2. Adding the source URL to the crawl queue
    3. Triggering the processing of the queue
    """
    db = SessionLocal()
    try:
        target_url = source_url or settings.SOURCE_URL
        target_district = district or settings.DISCOVERY_DISTRICT

        logger.info(f"Starting discovery from {target_url} for district {target_district}")

        # Record crawl log
        crawl_log = record_crawl_log(
            db=db,
            status="RUNNING",
            stage="DISCOVERY",
            district=target_district,
            message=f"Started discovery for {target_district} from {target_url}",
        )

        # Update system status
        update_system_status(db, "DISCOVERY_STATE", "RUNNING")
        update_system_status(db, "SOURCE_URL", target_url)
        update_system_status(db, "DISCOVERY_DISTRICT", target_district)
        db.commit()

        # Add the source URL to the crawl queue if not already present
        queue_item, created = upsert_crawl_queue(
            db,
            url=target_url,
            url_type="SOURCE",
            parent_url=None,
            district=target_district,
            priority=100,
        )
        db.commit()

        logger.info(f"Discovery initialized with crawl log ID {crawl_log.id}")

        return {
            "status": "INITIALIZED",
            "crawl_log_id": crawl_log.id,
            "source_url": target_url,
            "district": target_district,
        }

    finally:
        db.close()


@shared_task
def process_next_crawl_items(batch_size: int = 1) -> dict:
    """
    Process the next batch of crawl queue items.
    
    This task:
    1. Claims the next available crawl queue items
    2. Queues process_crawl_queue_item tasks for each
    3. Returns summary of items queued
    """
    db = SessionLocal()
    try:
        items_queued = 0
        pending_items = db.query(CrawlQueue).filter(
            CrawlQueue.status.in_(["PENDING", "RETRY"])
        ).limit(batch_size).all()

        logger.info(f"Found {len(pending_items)} items to process")

        for item in pending_items:
            # Queue the processing task
            process_crawl_queue_item.delay(item.id)
            items_queued += 1

        logger.info(f"Queued {items_queued} crawl tasks for processing")

        return {
            "status": "QUEUED",
            "items_queued": items_queued,
        }

    finally:
        db.close()
