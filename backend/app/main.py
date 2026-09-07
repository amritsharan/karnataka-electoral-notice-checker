import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from .config import settings
from .database import get_db, engine, Base
from .models import Document, NoticeRecord, SystemStatus, CrawlLog, CrawlQueue, PdfProcessingQueue
from .schemas import (
    EpicCheckRequest, EpicCheckResponse, NoticeRecordResponse, SourceInfo,
    SystemStatusResponse, AdminActionResponse, NameCheckRequest, SearchResponse,
    StartDiscoveryRequest, StartProcessingRequest
)
from .pdf_processor.epic_extractor import normalize_epic, is_valid_epic
from .pdf_processor.reasons import get_reason_explanation
from .services.seed_service import seed_sample_data
from .services.discovery_service import (
    start_discovery_job,
    get_district_progress,
    get_subdistrict_progress,
    get_recent_crawl_events,
    update_system_status,
)
from .tasks.discovery_tasks import (
    start_discovery_background,
    process_next_crawl_items,
    process_crawl_queue_item,
)
from .tasks.pdf_tasks import (
    process_next_pdf_items,
    process_pdf,
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="EPIC Notice Checker API for Chief Electoral Officer, Karnataka notices",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != settings.ADMIN_USERNAME or credentials.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

import threading
import time
from .database import get_db, engine, Base, SessionLocal

def background_worker_loop():
    logger.info("Automatic background document queue processing loop active.")
    while True:
        try:
            db = SessionLocal()
            pending_crawl = db.query(CrawlQueue).filter(CrawlQueue.status.in_(["PENDING", "RETRY"])).count()
            if pending_crawl > 0:
                update_system_status(db, "DISCOVERY_STATE", "RUNNING")
                db.commit()
                process_next_crawl_items(batch_size=5)
            else:
                update_system_status(db, "DISCOVERY_STATE", "COMPLETED")
                db.commit()

            pending_pdfs = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status.in_(["PENDING", "RETRY"])).count()
            if pending_pdfs > 0:
                update_system_status(db, "PROCESSING_STATE", "RUNNING")
                db.commit()
                process_next_pdf_items(batch_size=5)
            else:
                update_system_status(db, "PROCESSING_STATE", "COMPLETED")
                db.commit()

            db.close()
        except Exception as err:
            logger.error(f"Error in background worker loop: {err}")
        time.sleep(3)


@app.on_event("startup")
def startup_event():
    logger.info("Application startup complete. Automatic background document loading active.")
    try:
        db = SessionLocal()
        total_docs = db.query(Document).count()
        total_crawl_queue = db.query(CrawlQueue).count()
        if total_docs == 0 and total_crawl_queue == 0:
            logger.info("No documents enqueued yet. Auto-triggering background document discovery...")
            start_discovery_background.delay(
                source_url=settings.SOURCE_URL,
                district="ALL",
            )
        db.close()
    except Exception as exc:
        logger.warning(f"Automatic startup discovery trigger note: {exc}")

    # Start background processing thread for automatic continuous queue execution
    worker_thread = threading.Thread(target=background_worker_loop, daemon=True)
    worker_thread.start()


def build_status_payload(db: Session) -> SystemStatusResponse:
    total_docs = db.query(Document).count()
    indexed_docs = db.query(Document).filter(Document.processing_status == "INDEXED").count()
    pending_docs = db.query(Document).filter(Document.processing_status == "PENDING").count()
    failed_docs = db.query(Document).filter(Document.processing_status == "FAILED").count()
    ocr_docs = db.query(Document).filter(Document.ocr_used == True).count()  # noqa: E712
    total_records = db.query(NoticeRecord).count()

    last_crawl = db.query(SystemStatus).filter(SystemStatus.key == "LAST_CRAWL").first()
    last_success = db.query(SystemStatus).filter(SystemStatus.key == "LAST_SUCCESSFUL_CRAWL").first()
    source_item = db.query(SystemStatus).filter(SystemStatus.key == "SOURCE_URL").first()
    discovery_state = db.query(SystemStatus).filter(SystemStatus.key == "DISCOVERY_STATE").first()
    discovery_district = db.query(SystemStatus).filter(SystemStatus.key == "DISCOVERY_DISTRICT").first()
    processing_state = db.query(SystemStatus).filter(SystemStatus.key == "PROCESSING_STATE").first()

    crawl_queue_total = db.query(CrawlQueue).count()
    crawl_queue_pending = db.query(CrawlQueue).filter(CrawlQueue.status == "PENDING").count()
    crawl_queue_processing = db.query(CrawlQueue).filter(CrawlQueue.status == "PROCESSING").count()
    crawl_queue_completed = db.query(CrawlQueue).filter(CrawlQueue.status == "COMPLETED").count()
    crawl_queue_failed = db.query(CrawlQueue).filter(CrawlQueue.status == "FAILED").count()

    pdf_queue_total = db.query(PdfProcessingQueue).count()
    pdf_queue_pending = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status == "PENDING").count()
    pdf_queue_processing = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status == "PROCESSING").count()
    pdf_queue_completed = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status == "COMPLETED").count()
    pdf_queue_failed = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status == "FAILED").count()

    active_crawl = db.query(CrawlLog).filter(CrawlLog.status == "RUNNING").first()
    indexing_in_progress = bool(
        pending_docs > 0
        or crawl_queue_pending > 0
        or pdf_queue_pending > 0
        or active_crawl is not None
    )
    if total_docs > 0 and indexed_docs >= total_docs and pending_docs == 0:
        indexing_in_progress = False

    indexing_complete = bool(
        total_docs > 0 and indexed_docs >= total_docs and pending_docs == 0 and not indexing_in_progress
    )


    subdistrict_scope = None if not discovery_district or discovery_district.value == "ALL" else discovery_district.value

    return SystemStatusResponse(
        source_url=source_item.value if source_item else settings.SOURCE_URL,
        last_updated=last_success.value if last_success else datetime.utcnow().isoformat(),
        last_crawl=last_crawl.value if last_crawl else None,
        last_successful_crawl=last_success.value if last_success else None,
        documents_discovered=total_docs,
        documents_processed=indexed_docs,
        documents_pending=pending_docs,
        documents_failed=failed_docs,
        ocr_documents_count=ocr_docs,
        total_records_indexed=total_records,
        indexing_in_progress=indexing_in_progress,
        indexing_complete=indexing_complete,
        crawl_queue_total=crawl_queue_total,
        crawl_queue_pending=crawl_queue_pending,
        crawl_queue_processing=crawl_queue_processing,
        crawl_queue_completed=crawl_queue_completed,
        crawl_queue_failed=crawl_queue_failed,
        pdf_queue_total=pdf_queue_total,
        pdf_queue_pending=pdf_queue_pending,
        pdf_queue_processing=pdf_queue_processing,
        pdf_queue_completed=pdf_queue_completed,
        pdf_queue_failed=pdf_queue_failed,
        discovery_district=discovery_district.value if discovery_district else None,
        district_progress=get_district_progress(db),
        subdistrict_progress=get_subdistrict_progress(db, subdistrict_scope),
        recent_events=get_recent_crawl_events(db),
    )

@app.get("/")
def read_root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "documentation": "/docs"
    }

def parse_record_details(record, doc):
    import re
    name = record.name
    relative_name = None
    age = None
    gender = None
    serial_number = record.serial_number
    part_number = record.part_number
    constituency = record.constituency
    district = record.district
    reason = record.notice_reason

    # Fix generic constituency if it's set to filename or missing
    if not constituency or constituency == "N/A" or constituency.endswith(".pdf"):
        if doc and doc.document_name:
            s10_m = re.search(r'S10[_\-](\d{1,3})[_\-](\d{1,4})', doc.document_name, re.IGNORECASE)
            if s10_m:
                constituency = f"AC {s10_m.group(1)}"
                part_number = s10_m.group(2)
            elif "ac176" in doc.document_name.lower():
                constituency = "176 Bengaluru South"
                part_m = re.search(r'part(\d+)', doc.document_name, re.IGNORECASE)
                if part_m: part_number = part_m.group(1)
                district = "Bengaluru Urban"

    # Fix district if Previous or missing
    if not district or district == "Previous":
        district = doc.district if (doc and doc.district and doc.district != "Previous") else "Karnataka"

    # Parse extracted_text for Name, Relative Name, Age, Gender, Serial Number, Reason
    text = record.extracted_text
    parsed_reason_from_text = None
    if text:
        parts = [p.strip() for p in text.split("|") if p.strip()]
        if "Name:" in text or "S.No:" in text or "EPIC:" in text or "Reason:" in text:
            for p in parts:
                if ":" in p:
                    k, v = p.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if ("name" in k or "elector" in k) and (name == "Record Holder" or not name):
                        name = v
                    elif "relative" in k or "parent" in k:
                        relative_name = v
                    elif "age" in k:
                        age = v
                    elif "gender" in k:
                        gender = v
                    elif "s.no" in k or "serial" in k:
                        if not serial_number or serial_number == "N/A": serial_number = v
                    elif "part" in k:
                        if not part_number or part_number == "N/A": part_number = v
                    elif "reason" in k or "category" in k or "remarks" in k:
                        if v and len(v) > 2: parsed_reason_from_text = v
        else:
            # Piped format: "1 | 6 | ZLW5716501 | SHAKILA BANU | ZEENATH (Mother)"
            epic_idx = -1
            for idx, p in enumerate(parts):
                if re.match(r'^[A-Z]{3}\d{7}$', p.upper()):
                    epic_idx = idx
                    break
            if epic_idx != -1:
                before_nums = [p for p in parts[:epic_idx] if p.isdigit()]
                if len(before_nums) >= 2:
                    if not serial_number or serial_number == "N/A": serial_number = before_nums[1]
                elif len(before_nums) == 1:
                    if not serial_number or serial_number == "N/A": serial_number = before_nums[0]
                if epic_idx + 1 < len(parts):
                    cand_name = parts[epic_idx + 1]
                    if not cand_name.isdigit() and len(cand_name) > 1:
                        if name == "Record Holder" or not name:
                            name = cand_name
                if epic_idx + 2 < len(parts):
                    cand_rel = parts[epic_idx + 2]
                    if cand_rel.isdigit() and not age:
                        age = cand_rel
                    elif not cand_rel.isdigit():
                        relative_name = cand_rel
                if epic_idx + 3 < len(parts) and parts[epic_idx + 3].isdigit() and not age:
                    age = parts[epic_idx + 3]

    # Refine reason if generic or missing
    doc_name = (doc.document_name if doc else "") or ""
    doc_name_lower = doc_name.lower()

    if parsed_reason_from_text and parsed_reason_from_text.lower() not in ["listed", "n/a", "none"]:
        reason = parsed_reason_from_text
    elif not reason or "listed" in reason.lower() or reason == "N/A":
        if "form_39" in doc_name_lower or "form 39" in doc_name_lower:
            reason = "Form 39 - Discrepancy Elector Report (SIR-2026)"
        elif "form_60" in doc_name_lower or "form 60" in doc_name_lower:
            reason = "Form 60 - Discrepancy Elector Report (SIR-2026)"
        elif "form_154" in doc_name_lower or "form 154" in doc_name_lower:
            reason = "Form 154 - Discrepancy Elector Report (SIR-2026)"
        elif "form_6" in doc_name_lower or "form 6" in doc_name_lower:
            reason = "Form 6 - Inclusion & Duplicate Verification Notice"
        elif "form_7" in doc_name_lower or "form 7" in doc_name_lower:
            reason = "Form 7 - Deletion & Objection Notice"
        elif "form_8" in doc_name_lower or "form 8" in doc_name_lower:
            reason = "Form 8 - Correction & Shifting Notice"
        elif "no mapping" in doc_name_lower or "nomapping" in doc_name_lower or "unmapped" in doc_name_lower:
            reason = "Polling Station Unmapped / Mapping Discrepancy"
        elif "logical" in doc_name_lower or "error" in doc_name_lower:
            reason = "Logical Error in Roll Data Verification"
        elif "dse" in doc_name_lower or "demographic" in doc_name_lower:
            reason = "Demographic Similar Entry (DSE) Verification"
        elif "shifted" in doc_name_lower or "absent" in doc_name_lower:
            reason = "Shifted Residence / Absent Elector Verification"
        elif "uncollected" in doc_name_lower or "undelivered" in doc_name_lower:
            reason = "Uncollected EPIC Card / Undelivered Notice"
        elif "discrepency" in doc_name_lower or "discrepancy" in doc_name_lower:
            ac_m = re.search(r'ac(\d{1,3})', doc_name_lower)
            if ac_m:
                reason = f"Discrepancy Elector Report (AC {ac_m.group(1)})"
            else:
                reason = "Elector Data Discrepancy List (SIR-2026)"
        else:
            reason = "Special Intensive Revision (SIR-2026) Notice Verification"

    return {
        "name": name or "Elector",
        "relative_name": relative_name,
        "age": age,
        "gender": gender,
        "serial_number": serial_number or "N/A",
        "part_number": part_number or "N/A",
        "constituency": constituency or "N/A",
        "district": district or "Karnataka",
        "reason": reason or "Listed in CEO Karnataka notice document"
    }


def format_notice_records(matches: List[Any]) -> List[NoticeRecordResponse]:
    formatted_records: List[NoticeRecordResponse] = []
    seen_keys = set()
    for record, doc in matches:
        enriched = parse_record_details(record, doc)
        official_reason = enriched["reason"]
        clean_reason, explanation = get_reason_explanation(official_reason)

        page_num = record.page_number or 1
        source_pdf_url = doc.url
        if not source_pdf_url.startswith("http"):
            source_pdf_url = settings.SOURCE_URL

        doc_url_with_page = f"{source_pdf_url}#page={page_num}"

        rec = NoticeRecordResponse(
            epic=record.epic_normalized,
            name=enriched["name"],
            relative_name=enriched["relative_name"],
            age=enriched["age"],
            gender=enriched["gender"],
            district=enriched["district"],
            constituency=enriched["constituency"],
            taluk=record.taluk or "N/A",
            part_number=enriched["part_number"],
            serial_number=enriched["serial_number"],
            notice_reference=record.notice_reference or f"NOTICE-{record.id}",
            notice_date=record.notice_date or doc.published_date or "N/A",
            reason=clean_reason,
            reason_explanation=explanation,
            confidence=record.epic_match_confidence or "HIGH",
            source=SourceInfo(
                document_name=doc.document_name,
                page=page_num,
                url=doc_url_with_page,
                published_date=doc.published_date,
                district=doc.district
            )
        )

        dedup_key = (
            str(rec.epic or "").strip().upper(),
            str(rec.name or "").strip().upper(),
            str(rec.constituency or "").strip().upper(),
            str(rec.part_number or "").strip(),
            str(rec.serial_number or "").strip(),
            str(rec.reason or "").strip().upper(),
            str(doc.document_name or "").strip().lower(),
        )

        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        formatted_records.append(rec)

    return formatted_records


# ==========================================
# CITIZEN SEARCH ENDPOINTS (SYSTEM B)
# ==========================================

@app.post("/api/check-epic", response_model=EpicCheckResponse)
def check_epic(payload: EpicCheckRequest, db: Session = Depends(get_db)):
    """
    Citizen EPIC Status Check Endpoint. Fast indexed lookup (< 1s).
    """
    raw_epic = payload.epic
    normalized = normalize_epic(raw_epic)

    if not normalized or len(normalized) < 5:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid EPIC number (e.g. ABC1234567)."
        )

    matches = (
        db.query(NoticeRecord, Document)
        .join(Document, NoticeRecord.document_id == Document.id)
        .filter(NoticeRecord.epic_normalized == normalized)
        .all()
    )

    total_docs_indexed = db.query(Document).filter(Document.processing_status == "INDEXED").count()
    total_docs_discovered = db.query(Document).count()
    last_crawl_item = db.query(SystemStatus).filter(SystemStatus.key == "LAST_SUCCESSFUL_CRAWL").first()
    last_updated = last_crawl_item.value if last_crawl_item else datetime.utcnow().isoformat()
    
    active_crawl = db.query(CrawlLog).filter(CrawlLog.status == "RUNNING").first()
    pending_docs = db.query(Document).filter(Document.processing_status == "PENDING").count()
    crawl_queue_pending = db.query(CrawlQueue).filter(CrawlQueue.status == "PENDING").count()
    pdf_queue_pending = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status == "PENDING").count()

    indexing_in_progress = bool(
        active_crawl is not None
        or pending_docs > 0
        or crawl_queue_pending > 0
        or pdf_queue_pending > 0
    )
    indexing_complete = bool(total_docs_discovered > 0 and pending_docs == 0 and not indexing_in_progress)

    if not matches:
        return EpicCheckResponse(
            query=normalized,
            query_type="EPIC",
            epic=normalized,
            found=False,
            records_count=0,
            records=[],
            indexed_at=datetime.utcnow().isoformat(),
            total_documents_indexed=total_docs_indexed,
            total_documents_discovered=total_docs_discovered,
            last_updated=last_updated,
            indexing_in_progress=indexing_in_progress,
            indexing_complete=indexing_complete,
        )

    formatted_records = format_notice_records(matches)

    return EpicCheckResponse(
        query=normalized,
        query_type="EPIC",
        epic=normalized,
        found=True,
        records_count=len(formatted_records),
        records=formatted_records,
        indexed_at=datetime.utcnow().isoformat(),
        total_documents_indexed=total_docs_indexed,
        total_documents_discovered=total_docs_discovered,
        last_updated=last_updated,
        indexing_in_progress=indexing_in_progress,
        indexing_complete=indexing_complete,
    )


@app.post("/api/check-name", response_model=SearchResponse)
def check_name(payload: NameCheckRequest, db: Session = Depends(get_db)):
    """
    Citizen Name Search Endpoint.
    Searches notice records with an explicit non-unique identity warning.
    """
    raw_name = payload.name.strip()
    if not raw_name or len(raw_name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid name (at least 2 characters)."
        )

    matches = (
        db.query(NoticeRecord, Document)
        .join(Document, NoticeRecord.document_id == Document.id)
        .filter(NoticeRecord.name.ilike(f"%{raw_name}%"))
        .all()
    )

    total_docs_indexed = db.query(Document).filter(Document.processing_status == "INDEXED").count()
    total_docs_discovered = db.query(Document).count()
    last_crawl_item = db.query(SystemStatus).filter(SystemStatus.key == "LAST_SUCCESSFUL_CRAWL").first()
    last_updated = last_crawl_item.value if last_crawl_item else datetime.utcnow().isoformat()
    
    active_crawl = db.query(CrawlLog).filter(CrawlLog.status == "RUNNING").first()
    pending_docs = db.query(Document).filter(Document.processing_status == "PENDING").count()
    crawl_queue_pending = db.query(CrawlQueue).filter(CrawlQueue.status == "PENDING").count()
    pdf_queue_pending = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status == "PENDING").count()

    indexing_in_progress = bool(
        active_crawl is not None
        or pending_docs > 0
        or crawl_queue_pending > 0
        or pdf_queue_pending > 0
    )
    indexing_complete = bool(total_docs_discovered > 0 and pending_docs == 0 and not indexing_in_progress)
    warning_text = "Names may not uniquely identify a person. EPIC number is recommended for accurate verification."

    if not matches:
        return SearchResponse(
            query=raw_name,
            query_type="NAME",
            found=False,
            records_count=0,
            records=[],
            warning=warning_text,
            indexed_at=datetime.utcnow().isoformat(),
            total_documents_indexed=total_docs_indexed,
            total_documents_discovered=total_docs_discovered,
            last_updated=last_updated,
            indexing_in_progress=indexing_in_progress,
            indexing_complete=indexing_complete,
        )

    formatted_records = format_notice_records(matches)

    return SearchResponse(
        query=raw_name,
        query_type="NAME",
        found=True,
        records_count=len(formatted_records),
        records=formatted_records,
        warning=warning_text,
        indexed_at=datetime.utcnow().isoformat(),
        total_documents_indexed=total_docs_indexed,
        total_documents_discovered=total_docs_discovered,
        last_updated=last_updated,
        indexing_in_progress=indexing_in_progress,
        indexing_complete=indexing_complete,
    )

# ==========================================
# PUBLIC SYSTEM STATUS ENDPOINT
# ==========================================

@app.get("/api/status", response_model=SystemStatusResponse)
def get_public_status(db: Session = Depends(get_db)):
    """
    Public Status & Metadata endpoint for citizen UI footer.
    """
    return build_status_payload(db)

# ==========================================
# ADMIN DASHBOARD ENDPOINTS
# ==========================================

@app.get("/api/admin/metrics", response_model=SystemStatusResponse)
def get_admin_metrics(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    return build_status_payload(db)

def get_task_id(task_obj: Any) -> str:
    if hasattr(task_obj, "id"):
        return str(task_obj.id)
    if isinstance(task_obj, dict):
        return str(task_obj.get("task_id") or task_obj.get("crawl_log_id") or "job-1")
    return "job-1"

@app.post("/api/admin/start-discovery", response_model=AdminActionResponse)
@app.post("/api/admin/trigger-crawl", response_model=AdminActionResponse)
def start_discovery(
    payload: Optional[StartDiscoveryRequest] = None,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Starts resumable discovery for target district (or ALL) via background Celery tasks.
    """
    target_district = payload.district if payload and payload.district else settings.DISCOVERY_DISTRICT
    batch_size = payload.batch_size if payload and payload.batch_size else settings.DISCOVERY_BATCH_SIZE

    active = db.query(SystemStatus).filter(
        SystemStatus.key == "DISCOVERY_STATE",
        SystemStatus.value == "RUNNING"
    ).first()
    if active:
        return AdminActionResponse(
            success=False,
            message="Discovery is already running."
        )

    task = start_discovery_background.delay(
        source_url=settings.SOURCE_URL,
        district=target_district,
    )
    tid = get_task_id(task)

    return AdminActionResponse(
        success=True,
        message=f"Discovery initiated for district '{target_district}' (Batch size: {batch_size}). Task ID: {tid}",
        task_id=tid,
        details={"task_id": tid, "district": target_district, "batch_size": batch_size}
    )

@app.post("/api/admin/pause-discovery", response_model=AdminActionResponse)
def pause_discovery(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    update_system_status(db, "DISCOVERY_STATE", "PAUSED")
    db.commit()
    return AdminActionResponse(success=True, message="Discovery paused.")


@app.post("/api/admin/resume-discovery", response_model=AdminActionResponse)
def resume_discovery(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    update_system_status(db, "DISCOVERY_STATE", "RUNNING")
    db.commit()
    
    # Queue the next batch of crawl items
    task = process_next_crawl_items.delay(
        batch_size=settings.DISCOVERY_BATCH_SIZE
    )
    tid = get_task_id(task)
    
    return AdminActionResponse(
        success=True,
        message=f"Discovery resumed. Queuing next batch of crawl items. Task ID: {tid}",
        task_id=tid,
        details={"task_id": tid}
    )


@app.post("/api/admin/start-processing", response_model=AdminActionResponse)
def start_processing(
    payload: Optional[StartProcessingRequest] = None,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    batch_size = payload.batch_size if payload and payload.batch_size else settings.PDF_BATCH_SIZE
    update_system_status(db, "PROCESSING_STATE", "RUNNING")
    db.commit()
    
    # Queue the next batch of PDF items for processing
    task = process_next_pdf_items.delay(
        batch_size=batch_size
    )
    tid = get_task_id(task)
    
    return AdminActionResponse(
        success=True,
        message=f"PDF processing started with batch size {batch_size}. Task ID: {tid}",
        task_id=tid,
        details={"task_id": tid, "batch_size": batch_size}
    )


@app.post("/api/admin/pause-processing", response_model=AdminActionResponse)
def pause_processing(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    update_system_status(db, "PROCESSING_STATE", "PAUSED")
    db.commit()
    return AdminActionResponse(success=True, message="PDF processing paused.")


@app.post("/api/admin/resume-processing", response_model=AdminActionResponse)
def resume_processing(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    update_system_status(db, "PROCESSING_STATE", "RUNNING")
    db.commit()
    return AdminActionResponse(success=True, message="PDF processing resumed.")


@app.post("/api/admin/retry-failed", response_model=AdminActionResponse)
def retry_failed(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    failed_crawl_items = db.query(CrawlQueue).filter(CrawlQueue.status == "FAILED").all()
    failed_pdf_items = db.query(PdfProcessingQueue).filter(PdfProcessingQueue.status == "FAILED").all()

    for item in failed_crawl_items:
        item.status = "RETRY"
        item.next_attempt = datetime.utcnow()
        item.error = None

    for item in failed_pdf_items:
        item.status = "RETRY"
        item.next_attempt = datetime.utcnow()
        item.error = None

    db.commit()

    return AdminActionResponse(
        success=True,
        message=f"Queued {len(failed_crawl_items)} crawl items and {len(failed_pdf_items)} PDF jobs for retry.",
    )


@app.post("/api/admin/reindex", response_model=AdminActionResponse)
def reindex(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    update_system_status(db, "PROCESSING_STATE", "RUNNING")
    for doc in db.query(Document).filter(Document.processing_status == "INDEXED").all():
        doc.processing_status = "PENDING"
    db.commit()
    return AdminActionResponse(success=True, message="Reindex requested. Existing documents were reset to pending for the processing queue.")

@app.post("/api/admin/seed-test-data", response_model=AdminActionResponse)
def seed_test_data(username: str = Depends(verify_admin), db: Session = Depends(get_db)):
    """
    Seeds mock development test data for immediate testing.
    """
    res = seed_sample_data(db)
    return AdminActionResponse(
        success=True,
        message=f"Seeded mock test data. {res['docs_created']} documents created, {res['records_created']} records added.",
        details=res
    )
