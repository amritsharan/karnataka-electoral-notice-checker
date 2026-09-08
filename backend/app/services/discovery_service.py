import logging
import re
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
import gdown

import httpx
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models import CrawlLog, CrawlQueue, Document, PdfProcessingQueue, SystemStatus

logger = logging.getLogger(__name__)

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def extract_folder_id_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    match = re.search(r'drive\.google\.com/(?:drive/(?:u/\d+/)?folders/|uc\?id=|file/d/)([a-zA-Z0-9_-]{20,60})', url)
    return match.group(1) if match else None


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_subdistrict_name(label: str) -> Optional[str]:
    if not label:
        return None

    cleaned = normalize_name(label)
    cleaned = re.sub(r"^\d+\s*[-.]\s*", "", cleaned)
    cleaned = re.sub(r"\s+Discrepancies and No Mapping.*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+Shared folder.*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+Folder.*$", "", cleaned, flags=re.I)
    cleaned = cleaned.strip()
    return cleaned or None


def is_probable_pdf(name: str) -> bool:
    lowered = (name or "").lower()
    return lowered.endswith(".pdf") or ".pdf" in lowered


def is_probable_folder(name: str) -> bool:
    lowered = (name or "").lower()
    return "shared folder" in lowered or "folder" in lowered or "discrepancies and no mapping" in lowered or "lac" in lowered or "constituency" in lowered


def build_drive_url(item_id: str, item_type: str) -> str:
    if item_type == "folder":
        return f"https://drive.google.com/drive/folders/{item_id}"
    return f"https://drive.google.com/uc?id={item_id}&export=download"


def fetch_html(url: str, client: Optional[httpx.Client] = None) -> str:
    if client is not None:
        response = client.get(url)
        response.raise_for_status()
        return response.text

    with httpx.Client(timeout=settings.CRAWLER_TIMEOUT, follow_redirects=True, headers=HTTP_HEADERS) as local_client:
        response = local_client.get(url)
        response.raise_for_status()
        return response.text


def parse_ceo_district_links(html_text: str, base_url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html_text, "html.parser")
    district_links: List[Dict[str, str]] = []
    seen_urls = set()
    ignored_keywords = ["facebook", "twitter", "contact-us", "sitemap", "gallery", "rtistats", "feedback", "events", "faq", "media", "organisation-hierarchy", "ceo's-desk", "training_material", "acts-and-rules"]

    # Method 1: Table rows on CEO Karnataka page
    for row in soup.select("table tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        district_name = ""
        if len(cells) >= 2:
            district_name = normalize_name(cells[1].get_text(" ", strip=True))
        if not district_name:
            district_name = normalize_name(row.get_text(" ", strip=True))

        link = row.find("a", href=True)
        if not link:
            continue

        href = urljoin(base_url, link["href"].strip())
        if href.lower().startswith("javascript:") or href in seen_urls:
            continue

        if any(ign in href.lower() for ign in ignored_keywords):
            continue

        seen_urls.add(href)
        district_links.append({"district": district_name or "Karnataka District", "url": href})

    # Method 2: Fallback scan for anchor tags with drive links or notice links
    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link["href"].strip())
        if href.lower().startswith("javascript:") or href in seen_urls:
            continue

        if any(ign in href.lower() for ign in ignored_keywords):
            continue

        text = normalize_name(link.get_text(" ", strip=True))
        if "drive.google.com" in href.lower() or "notices" in href.lower() or ("district" in text.lower() and len(text) > 3):
            seen_urls.add(href)
            district_links.append({"district": text or "Karnataka District", "url": href})

    return district_links


def parse_drive_listing(html_text: str, folder_url: Optional[str] = None) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen_ids = set()

    # Method 0: Use gdown folder parsing if folder_url or folder ID is present
    target_folder_id = extract_folder_id_from_url(folder_url) if folder_url else None
    if not target_folder_id:
        # Search for folder ID in html_text
        match = re.search(r'drive\.google\.com/(?:drive/(?:u/\d+/)?folders/|uc\?id=|file/d/)([a-zA-Z0-9_-]{20,60})', html_text)
        if match:
            target_folder_id = match.group(1)

    if target_folder_id:
        try:
            gdown_items = gdown.download_folder(id=target_folder_id, skip_download=True, quiet=True)
            if gdown_items:
                for git in gdown_items:
                    item_id = git.id
                    if item_id and item_id not in seen_ids:
                        seen_ids.add(item_id)
                        path_parts = git.path.replace("\\", "/").split("/")
                        file_name = path_parts[-1]
                        subdist = path_parts[0] if len(path_parts) > 1 else None

                        items.append({
                            "id": item_id,
                            "name": normalize_name(file_name),
                            "type": "pdf",
                            "url": build_drive_url(item_id, "pdf"),
                            "subdistrict": normalize_subdistrict_name(subdist) if subdist else None,
                        })
                if items:
                    return items
        except Exception as exc:
            logger.warning("gdown parsing fallback for folder %s: %s", target_folder_id, exc)

    # Method 1: AF_initDataCallback payload JSON parsing (Modern Google Drive web format)
    callbacks = re.findall(r'AF_initDataCallback\((\{.*?\})\);', html_text, re.DOTALL)
    for cb in callbacks:
        data_match = re.search(r'data:(.*?), sideChannel:', cb, re.DOTALL)
        if not data_match:
            continue
        raw_data = data_match.group(1).strip()
        try:
            parsed = json.loads(raw_data)

            def extract_item_from_array(obj):
                if isinstance(obj, list) and len(obj) >= 5:
                    first = obj[0]
                    if isinstance(first, list) and len(first) >= 2 and first[0] is None and isinstance(first[1], str) and 20 <= len(first[1]) <= 60:
                        item_id = first[1]
                        if item_id in seen_ids:
                            return

                        mime_type = obj[4] if len(obj) > 4 and isinstance(obj[4], str) else ""

                        # Extract strings to find exact folder/file title
                        strings = []
                        def get_strings(o):
                            if isinstance(o, str):
                                strings.append(o)
                            elif isinstance(o, list):
                                for child in o:
                                    get_strings(child)

                        get_strings(obj)

                        ignored_strs = {
                            item_id,
                            mime_type,
                            "Shared folder",
                            "Download",
                            "More actions",
                            "Modified",
                            "Size not available",
                            "application/vnd.google-apps.folder",
                            "application/pdf",
                        }
                        name = ""
                        for s in strings:
                            if s in ignored_strs or s.startswith("http") or s.startswith("driveweb") or len(s) < 2:
                                continue
                            name = s
                            break

                        seen_ids.add(item_id)
                        clean_name = normalize_name(name) or f"Document_{item_id[:8]}"

                        is_folder = (mime_type == "application/vnd.google-apps.folder") or ("folder" in mime_type.lower()) or (is_probable_folder(clean_name) and not is_probable_pdf(clean_name))
                        item_type = "folder" if is_folder else "pdf"

                        items.append({
                            "id": item_id,
                            "name": clean_name,
                            "type": item_type,
                            "url": build_drive_url(item_id, item_type),
                            "subdistrict": normalize_subdistrict_name(clean_name) if item_type == "folder" else None,
                        })
                        return

                if isinstance(obj, list):
                    for elem in obj:
                        extract_item_from_array(elem)
                elif isinstance(obj, dict):
                    for v in obj.values():
                        extract_item_from_array(v)

            extract_item_from_array(parsed)
        except Exception:
            pass

    # Method 2: HTML table rows (if present)
    soup = BeautifulSoup(html_text, "html.parser")
    for row in soup.select("tr[data-id]"):
        item_id = row.get("data-id")
        if not item_id or item_id in seen_ids:
            continue

        raw_name = normalize_name(row.get_text(" ", strip=True))
        if not raw_name:
            continue

        seen_ids.add(item_id)
        item_type = "folder" if is_probable_folder(raw_name) and not is_probable_pdf(raw_name) else "pdf"
        items.append({
            "id": item_id,
            "name": raw_name,
            "type": item_type,
            "url": build_drive_url(item_id, item_type),
            "subdistrict": normalize_subdistrict_name(raw_name) if item_type == "folder" else None,
        })

    # Method 3: Regex extraction from legacy JS arrays ["FILE_ID", ["FILENAME.pdf", ...]]
    pdf_matches = re.findall(r'\["([a-zA-Z0-9_-]{20,60})",\s*\["([^"]+\.pdf)"', html_text, re.IGNORECASE)
    for item_id, file_name in pdf_matches:
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            clean_name = normalize_name(file_name)
            items.append({
                "id": item_id,
                "name": clean_name,
                "type": "pdf",
                "url": build_drive_url(item_id, "pdf"),
                "subdistrict": normalize_subdistrict_name(clean_name),
            })

    folder_matches = re.findall(r'\["([a-zA-Z0-9_-]{20,60})",\s*\["([^"]+)"', html_text)
    for item_id, folder_name in folder_matches:
        clean_name = normalize_name(folder_name)
        if item_id not in seen_ids and is_probable_folder(clean_name) and not is_probable_pdf(clean_name):
            seen_ids.add(item_id)
            items.append({
                "id": item_id,
                "name": clean_name,
                "type": "folder",
                "url": build_drive_url(item_id, "folder"),
                "subdistrict": normalize_subdistrict_name(clean_name),
            })

    # Method 4: Direct Google Drive URL patterns in HTML
    drive_file_urls = re.findall(r'https://drive\.google\.com/(?:file/d/|uc\?id=)([a-zA-Z0-9_-]{20,60})', html_text)
    for item_id in drive_file_urls:
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            items.append({
                "id": item_id,
                "name": f"Document_{item_id[:8]}.pdf",
                "type": "pdf",
                "url": build_drive_url(item_id, "pdf"),
                "subdistrict": None,
            })

    return items


def upsert_crawl_queue(
    db: Session,
    url: str,
    url_type: str,
    parent_url: Optional[str] = None,
    district: Optional[str] = None,
    subdistrict: Optional[str] = None,
    priority: int = 0,
    reset_status: bool = True,
) -> Tuple[CrawlQueue, bool]:
    existing = db.query(CrawlQueue).filter(CrawlQueue.url == url).first()
    if existing:
        existing.parent_url = parent_url or existing.parent_url
        existing.district = district or existing.district
        existing.subdistrict = subdistrict or existing.subdistrict
        existing.url_type = url_type or existing.url_type
        if reset_status:
            existing.status = "PENDING"
            existing.next_attempt = datetime.utcnow()
        return existing, False


    item = CrawlQueue(
        url=url,
        url_type=url_type,
        parent_url=parent_url,
        district=district,
        subdistrict=subdistrict,
        status="PENDING",
        priority=priority,
        attempt_count=0,
        next_attempt=datetime.utcnow(),
    )
    db.add(item)
    db.flush()
    return item, True


def upsert_document(
    db: Session,
    url: str,
    parent_url: Optional[str],
    district: Optional[str],
    subdistrict: Optional[str],
    document_name: str,
) -> Tuple[Document, bool]:
    existing = db.query(Document).filter(Document.url == url).first()
    if existing:
        existing.parent_url = parent_url or existing.parent_url
        existing.district = district or existing.district
        existing.subdistrict = subdistrict or existing.subdistrict
        existing.document_name = document_name or existing.document_name
        existing.status = "DISCOVERED"
        existing.processing_status = existing.processing_status or "PENDING"
        return existing, False

    document = Document(
        url=url,
        parent_url=parent_url,
        district=district,
        subdistrict=subdistrict,
        document_name=document_name,
        discovered_at=datetime.utcnow(),
        status="DISCOVERED",
        download_status="DISCOVERED",
        processing_status="PENDING",
        attempt_count=0,
    )
    db.add(document)
    db.flush()
    return document, True


def enqueue_pdf_processing(db: Session, document: Document, priority: int = 0) -> Tuple[PdfProcessingQueue, bool]:
    existing = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.document_id == document.id).first()
    if existing:
        existing.url = document.url
        existing.priority = priority if priority is not None else existing.priority
        return existing, False

    item = PdfProcessingQueue(
        document_id=document.id,
        url=document.url,
        priority=priority,
        status="PENDING",
        attempt_count=0,
        next_attempt=datetime.utcnow(),
    )
    db.add(item)
    db.flush()
    return item, True


def update_system_status(db: Session, key: str, value: str) -> None:
    item = db.query(SystemStatus).filter(SystemStatus.key == key).first()
    if not item:
        item = SystemStatus(key=key, value=value, updated_at=datetime.utcnow())
        db.add(item)
    else:
        item.value = value
        item.updated_at = datetime.utcnow()


def record_crawl_log(db: Session, status: str, stage: str, district: Optional[str], message: str) -> CrawlLog:
    log = CrawlLog(
        started_at=datetime.utcnow(),
        status=status,
        stage=stage,
        district=district,
        message=message,
    )
    db.add(log)
    db.flush()
    return log


def claim_next_crawl_queue_item(
    db: Session,
    district_name: Optional[str] = None,
    source_url: Optional[str] = None,
) -> Optional[CrawlQueue]:
    now = datetime.utcnow()
    query = db.query(CrawlQueue).filter(CrawlQueue.status.in_(["PENDING", "RETRY"]))
    query = query.filter(or_(CrawlQueue.next_attempt.is_(None), CrawlQueue.next_attempt <= now))

    if district_name is not None and source_url is not None:
        query = query.filter(or_(CrawlQueue.district == district_name, CrawlQueue.url == source_url))
    elif district_name is not None:
        query = query.filter(CrawlQueue.district == district_name)
    elif source_url is not None:
        query = query.filter(CrawlQueue.url == source_url)

    item = query.order_by(CrawlQueue.priority.desc(), CrawlQueue.id.asc()).first()

    if not item:
        return None

    item.status = "PROCESSING"
    item.last_attempt = now
    item.attempt_count = (item.attempt_count or 0) + 1
    db.commit()
    db.refresh(item)
    return item


def run_discovery_for_all_districts(
    db: Session,
    source_url: Optional[str] = None,
    target_district: Optional[str] = "ALL",
    batch_size: Optional[int] = None,
) -> Dict[str, Any]:
    target_url = source_url or settings.SOURCE_URL
    batch_limit = batch_size if batch_size is not None and batch_size > 0 else None
    district_filter = target_district or settings.DISCOVERY_DISTRICT

    crawl_log = record_crawl_log(
        db=db,
        status="RUNNING",
        stage="DISCOVERY",
        district=district_filter,
        message=f"Started discovery run for district '{district_filter}' from {target_url}",
    )

    update_system_status(db, "DISCOVERY_STATE", "RUNNING")
    update_system_status(db, "SOURCE_URL", target_url)
    update_system_status(db, "DISCOVERY_DISTRICT", district_filter)
    db.commit()

    queue_items_added = 0
    pages_discovered = 0
    subdistricts = set()
    pdfs_discovered = 0

    _, created = upsert_crawl_queue(db, target_url, "SOURCE", parent_url=None, district=district_filter, subdistrict=None, priority=100)
    queue_items_added += 1 if created else 0
    db.commit()

    with httpx.Client(timeout=settings.CRAWLER_TIMEOUT, follow_redirects=True, headers=HTTP_HEADERS) as client:
        while True:
            queue_item = claim_next_crawl_queue_item(db)
            if queue_item is None:
                break

            if batch_limit is not None and pages_discovered >= batch_limit:
                break

            try:
                if queue_item.url_type == "SOURCE":
                    root_html = fetch_html(queue_item.url, client)
                    root_links = parse_ceo_district_links(root_html, queue_item.url)

                    if not root_links:
                        raise RuntimeError("No district links discovered on the CEO Karnataka source page.")

                    if district_filter and district_filter.upper() != "ALL":
                        dist_lower = district_filter.lower()
                        root_links = [
                            l for l in root_links
                            if dist_lower in l["district"].lower() or l["district"].lower() in dist_lower
                        ]

                    for index, selected_link in enumerate(root_links):
                        district_url = selected_link["url"]
                        district_label = normalize_name(selected_link["district"])
                        _, created = upsert_crawl_queue(
                            db,
                            district_url,
                            "DISTRICT",
                            parent_url=target_url,
                            district=district_label,
                            priority=max(90 - index, 50),
                        )
                        queue_items_added += 1 if created else 0
                    pages_discovered += 1
                    queue_item.status = "COMPLETED"
                    queue_item.error = None
                    queue_item.next_attempt = None
                    db.commit()
                    crawl_log.message = f"Discovered {len(root_links)} district landing pages from the source page."
                    db.commit()
                    continue

                page_html = fetch_html(queue_item.url, client)
                page_items = parse_drive_listing(page_html, queue_item.url)
                pages_discovered += 1
                queue_item.status = "COMPLETED"
                queue_item.error = None
                queue_item.next_attempt = None
                district_label = queue_item.district or "Unassigned"

                for entry in page_items:
                    if entry["type"] == "folder":
                        child_subdistrict = entry.get("subdistrict") or normalize_subdistrict_name(entry["name"])
                        if child_subdistrict:
                            subdistricts.add(child_subdistrict)
                        child_queue, created = upsert_crawl_queue(
                            db,
                            entry["url"],
                            "FOLDER",
                            parent_url=queue_item.url,
                            district=district_label,
                            subdistrict=child_subdistrict,
                            priority=max(0, 75 - queue_item.attempt_count),
                        )
                        queue_items_added += 1 if created else 0
                    elif entry["type"] == "pdf":
                        pdf_name = entry["name"]
                        pdf_url = entry["url"]
                        pdf_subdistrict = queue_item.subdistrict or normalize_subdistrict_name(pdf_name)
                        document, created = upsert_document(
                            db,
                            url=pdf_url,
                            parent_url=queue_item.url,
                            district=district_label,
                            subdistrict=pdf_subdistrict,
                            document_name=pdf_name,
                        )
                        _, pdf_created = enqueue_pdf_processing(db, document, priority=max(0, 50 - queue_item.attempt_count))
                        queue_items_added += 1 if pdf_created else 0
                        pdfs_discovered += 1 if created else 0
                        logger.info("Discovered PDF URL: %s", pdf_url)

                crawl_log.discovered_count = db.query(Document).count()
                crawl_log.message = f"Discovered {len(subdistricts)} subdistricts and {pdfs_discovered} PDFs so far across all districts."
                db.commit()

            except Exception as exc:
                queue_item.status = "FAILED"
                queue_item.error = str(exc)
                queue_item.next_attempt = datetime.utcnow() + timedelta(minutes=min(60, 2 ** max(1, queue_item.attempt_count)))
                crawl_log.failed_count += 1
                db.commit()
                logger.exception("Discovery failed for %s", queue_item.url)
                continue

    update_system_status(db, "DISCOVERY_STATE", "PAUSED")
    update_system_status(db, "LAST_CRAWL", datetime.utcnow().isoformat())
    update_system_status(db, "LAST_SUCCESSFUL_CRAWL", datetime.utcnow().isoformat())
    db.commit()

    crawl_log.status = "SUCCESS"
    crawl_log.completed_at = datetime.utcnow()
    crawl_log.discovered_count = db.query(Document).count()
    crawl_log.message = f"Discovery completed for all districts: {len(subdistricts)} subdistricts, {pdfs_discovered} PDFs discovered."
    db.commit()

    return {
        "success": True,
        "district": "ALL",
        "source_url": target_url,
        "queue_items_added": queue_items_added,
        "pages_discovered": pages_discovered,
        "subdistricts_discovered": len(subdistricts),
        "pdfs_discovered": pdfs_discovered,
        "crawl_log_id": crawl_log.id,
    }


def start_discovery_job(
    source_url: Optional[str] = None,
    batch_size: Optional[int] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        return run_discovery_for_all_districts(
            db=db,
            source_url=source_url,
            batch_size=batch_size,
        )
    finally:
        db.close()


def run_discovery_for_one_district(
    db: Session,
    source_url: Optional[str] = None,
    district_name: Optional[str] = None,
    batch_size: Optional[int] = None,
) -> Dict[str, Any]:
    return run_discovery_for_all_districts(
        db=db,
        source_url=source_url,
        batch_size=batch_size,
    )


def get_recent_crawl_events(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for log in db.query(CrawlLog).order_by(CrawlLog.started_at.desc()).limit(limit).all():
        timestamp = log.completed_at or log.started_at
        events.append(
            {
                "timestamp": timestamp.isoformat() if timestamp else None,
                "stage": log.stage,
                "status": log.status,
                "district": log.district,
                "message": log.message,
                "discovered_count": log.discovered_count,
                "processed_count": log.processed_count,
                "failed_count": log.failed_count,
                "records_count": log.records_count,
            }
        )
    return events


def get_district_progress(db: Session) -> List[Dict[str, Any]]:
    try:
        from sqlalchemy import func
        rows = db.query(
            func.coalesce(Document.district, "Unassigned"),
            Document.processing_status,
            func.count(Document.id)
        ).group_by(Document.district, Document.processing_status).all()

        progress: Dict[str, Dict[str, Any]] = {}
        for district_name, processing_status, cnt in rows:
            bucket = progress.setdefault(
                district_name,
                {"district": district_name, "pdfs": 0, "processed": 0, "pending": 0, "failed": 0},
            )
            bucket["pdfs"] += cnt
            if processing_status == "INDEXED":
                bucket["processed"] += cnt
            elif processing_status == "FAILED":
                bucket["failed"] += cnt
            else:
                bucket["pending"] += cnt
        return sorted(progress.values(), key=lambda item: item["district"])
    except Exception as err:
        logger.warning(f"Error building district progress: {err}")
        return []


def get_subdistrict_progress(db: Session, district_name: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        from sqlalchemy import func
        query = db.query(
            func.coalesce(Document.district, "Unassigned"),
            func.coalesce(Document.subdistrict, "Unassigned"),
            Document.processing_status,
            func.count(Document.id)
        )
        if district_name:
            query = query.filter(Document.district == district_name)

        rows = query.group_by(Document.district, Document.subdistrict, Document.processing_status).all()
        progress: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for district_bucket, subdistrict_bucket, processing_status, cnt in rows:
            key = (district_bucket, subdistrict_bucket)
            bucket = progress.setdefault(
                key,
                {
                    "district": district_bucket,
                    "subdistrict": subdistrict_bucket,
                    "pdfs": 0,
                    "processed": 0,
                    "pending": 0,
                    "failed": 0,
                },
            )
            bucket["pdfs"] += cnt
            if processing_status == "INDEXED":
                bucket["processed"] += cnt
            elif processing_status == "FAILED":
                bucket["failed"] += cnt
            else:
                bucket["pending"] += cnt
        return sorted(progress.values(), key=lambda item: (item["district"], item["subdistrict"]))
    except Exception as err:
        logger.warning(f"Error building subdistrict progress: {err}")
        return []