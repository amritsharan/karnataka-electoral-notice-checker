"""
PDF processing tasks for downloading, extracting, OCR, and parsing PDFs.
"""
import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx
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
from ..models import Document, PdfProcessingQueue, NoticeRecord
from ..pdf_processor.processor import process_pdf_bytes
from ..pdf_processor.epic_extractor import normalize_epic

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def process_pdf(self, pdf_queue_id: int) -> dict:
    """
    Process a single PDF from the pdf_processing_queue.
    
    Pipeline:
    1. Download PDF
    2. Calculate SHA-256 checksum
    3. Check for duplicates
    4. Extract text and EPICs (with OCR fallback)
    5. Store in notice_records table
    6. Implement exponential backoff on failure
    """
    db = SessionLocal()
    try:
        pdf_queue = db.query(PdfProcessingQueue).filter(
            PdfProcessingQueue.id == pdf_queue_id
        ).first()
        if not pdf_queue:
            logger.warning(f"PDF queue item {pdf_queue_id} not found")
            return {"status": "NOT_FOUND", "item_id": pdf_queue_id}

        document = db.query(Document).filter(
            Document.id == pdf_queue.document_id
        ).first()
        if not document:
            logger.warning(f"Document {pdf_queue.document_id} not found")
            return {"status": "DOCUMENT_NOT_FOUND", "item_id": pdf_queue_id}

        pdf_queue.status = "PROCESSING"
        pdf_queue.last_attempt = datetime.utcnow()
        db.commit()

        logger.info(f"Processing PDF: {document.document_name} (URL: {document.url})")

        try:
            # Step 1: Obtain PDF bytes (local file or remote URL)
            logger.info(f"Retrieving PDF content for {document.document_name} from {document.url}")
            pdf_content = None
            
            if document.url.startswith("local://"):
                local_path = document.url.replace("local://", "")
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        pdf_content = f.read()
                else:
                    raise FileNotFoundError(f"Local PDF file not found: {local_path}")
            elif "drive.google.com" in document.url:
                import re, tempfile
                fid = None
                match = re.search(r'(?:id=|/d/)([a-zA-Z0-9_-]{20,60})', document.url)
                if match:
                    fid = match.group(1)
                
                if fid:
                    try:
                        drive_url = f"https://drive.google.com/uc?export=download&id={fid}"
                        with httpx.Client(timeout=20.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
                            resp = client.get(drive_url)
                            if resp.status_code == 200 and len(resp.content) > 1000 and resp.content[:4] == b'%PDF':
                                pdf_content = resp.content
                    except Exception as drive_err:
                        logger.warning(f"Direct Google Drive download attempt failed: {drive_err}")

                    if pdf_content is None:
                        try:
                            import gdown
                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                                tmp_path = tmp.name
                            try:
                                gdown.download(id=fid, output=tmp_path, quiet=True)
                                with open(tmp_path, "rb") as f:
                                    pdf_content = f.read()
                            finally:
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                        except Exception as gdown_err:
                            logger.warning(f"gdown fallback failed for {fid}: {gdown_err}")
            
            if pdf_content is None:
                with httpx.Client(timeout=settings.CRAWLER_TIMEOUT, follow_redirects=True) as client:
                    response = client.get(document.url)
                    response.raise_for_status()
                    pdf_content = response.content

            # Check file size
            file_size_mb = len(pdf_content) / (1024 * 1024)
            if file_size_mb > settings.MAX_PDF_SIZE_MB:
                raise ValueError(f"PDF size {file_size_mb}MB exceeds max {settings.MAX_PDF_SIZE_MB}MB")

            # Step 2: Calculate checksum
            pdf_hash = hashlib.sha256(pdf_content).hexdigest()
            logger.info(f"PDF hash: {pdf_hash}")

            # Step 3: Check for duplicates
            existing_doc = db.query(Document).filter(
                Document.document_hash == pdf_hash,
                Document.id != document.id
            ).first()
            if existing_doc:
                logger.info(f"Duplicate PDF detected: matches document {existing_doc.id}")
                document.processing_status = "DUPLICATE"
                document.indexed_at = datetime.utcnow()
                pdf_queue.status = "COMPLETED"
                db.commit()
                return {
                    "status": "DUPLICATE",
                    "item_id": pdf_queue_id,
                    "document_id": document.id,
                    "hash": pdf_hash,
                }

            # Step 4: Extract records using pipeline
            logger.info("Extracting text and EPICs from PDF")
            records, total_pages, ocr_used = process_pdf_bytes(
                pdf_content,
                document_name=document.document_name
            )

            document.document_hash = pdf_hash
            document.ocr_used = ocr_used
            document.page_count = total_pages
            document.processing_status = "PROCESSED"
            document.download_status = "DOWNLOADED"

            # Step 5: Store records in database
            for record_data in records:
                notice_record = NoticeRecord(
                    document_id=document.id,
                    page_number=record_data.get("page_number", 1),
                    epic_normalized=record_data.get("epic_normalized", normalize_epic(record_data["epic_raw"])),
                    epic_raw=record_data["epic_raw"],
                    epic_match_confidence=record_data.get("epic_match_confidence", "HIGH"),
                    name=record_data.get("name"),
                    district=record_data.get("district") or document.district,
                    taluk=record_data.get("taluk"),
                    constituency=record_data.get("constituency"),
                    part_number=record_data.get("part_number"),
                    serial_number=record_data.get("serial_number"),
                    notice_reason=record_data.get("notice_reason"),
                    extracted_text=record_data.get("extracted_text", "")[:1000],  # Store first 1000 chars
                )
                db.add(notice_record)

            document.processing_status = "INDEXED"
            document.indexed_at = datetime.utcnow()
            pdf_queue.status = "COMPLETED"
            pdf_queue.attempt_count = (pdf_queue.attempt_count or 0) + 1
            db.commit()

            logger.info(f"PDF processed successfully: {len(records)} records extracted, OCR used: {ocr_used}")

            return {
                "status": "SUCCESS",
                "item_id": pdf_queue_id,
                "document_id": document.id,
                "records_extracted": len(records),
                "ocr_used": ocr_used,
                "pages": total_pages,
            }

        except Exception as process_error:
            logger.error(f"Error processing PDF {pdf_queue_id}: {str(process_error)}")

            # Implement exponential backoff
            retry_count = pdf_queue.attempt_count or 0
            if retry_count < settings.MAX_RETRY_ATTEMPTS:
                backoff_delay = settings.INITIAL_RETRY_DELAY * (2 ** retry_count)
                next_attempt = datetime.utcnow() + timedelta(seconds=backoff_delay)

                pdf_queue.status = "RETRY"
                pdf_queue.error = str(process_error)
                pdf_queue.next_attempt = next_attempt
                pdf_queue.attempt_count = retry_count + 1
                document.processing_status = "FAILED"
                document.error_message = str(process_error)
                db.commit()

                logger.info(
                    f"Retrying PDF {pdf_queue_id} in {backoff_delay} seconds "
                    f"(attempt {pdf_queue.attempt_count}/{settings.MAX_RETRY_ATTEMPTS})"
                )

                raise self.retry(
                    exc=process_error,
                    countdown=backoff_delay,
                    max_retries=settings.MAX_RETRY_ATTEMPTS - retry_count,
                )
            else:
                # Max retries exceeded
                pdf_queue.status = "FAILED"
                pdf_queue.error = f"Max retries exceeded: {str(process_error)}"
                pdf_queue.attempt_count = retry_count + 1
                document.processing_status = "FAILED"
                document.error_message = str(process_error)
                document.last_error = str(process_error)
                db.commit()

                logger.error(
                    f"PDF {pdf_queue_id} failed permanently after {retry_count} attempts"
                )

                return {
                    "status": "FAILED",
                    "item_id": pdf_queue_id,
                    "document_id": document.id,
                    "error": str(process_error),
                }

    finally:
        db.close()


@shared_task
def process_next_pdf_items(batch_size: int = 1) -> dict:
    """
    Process the next batch of PDF queue items.
    
    This task:
    1. Finds the next available PDF queue items
    2. Queues process_pdf tasks for each
    3. Returns summary of items queued
    """
    db = SessionLocal()
    try:
        items_queued = 0
        pending_items = db.query(PdfProcessingQueue).filter(
            PdfProcessingQueue.status.in_(["PENDING", "RETRY"])
        ).order_by(
            PdfProcessingQueue.priority.desc(),
            PdfProcessingQueue.id.asc()
        ).limit(batch_size).all()

        logger.info(f"Found {len(pending_items)} PDF items to process")

        for item in pending_items:
            # Queue the processing task
            process_pdf.delay(item.id)
            items_queued += 1

        logger.info(f"Queued {items_queued} PDF processing tasks")

        return {
            "status": "QUEUED",
            "items_queued": items_queued,
        }

    finally:
        db.close()
