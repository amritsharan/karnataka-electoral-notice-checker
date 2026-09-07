import hashlib
import logging
import httpx
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Document, NoticeRecord, CrawlLog, SystemStatus
from ..pdf_processor.processor import process_pdf_bytes

logger = logging.getLogger(__name__)

# Standard headers to bypass basic user-agent blocks
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def crawl_and_index_source(db: Session, source_url: str = None) -> Dict[str, Any]:
    """
    Main background crawler entrypoint:
    1. Crawls configured source URL
    2. Discovers PDF links & subpages
    3. Queues & downloads PDFs
    4. Computes SHA-256 hash to avoid duplicate processing
    5. Extracts text & OCR -> saves notice records to DB
    """
    target_url = source_url or settings.SOURCE_URL
    
    # Create crawl log entry
    crawl_log = CrawlLog(
        started_at=datetime.utcnow(),
        status="RUNNING",
        message=f"Started crawl of {target_url}"
    )
    db.add(crawl_log)
    db.commit()
    db.refresh(crawl_log)

    discovered_links = []
    discovered_count = 0
    processed_count = 0
    failed_count = 0
    records_added = 0

    try:
        # Step 1: Fetch source page HTML
        logger.info(f"Fetching source page: {target_url}")
        with httpx.Client(timeout=settings.CRAWLER_TIMEOUT, follow_redirects=True, headers=HTTP_HEADERS) as client:
            resp = client.get(target_url)
            resp.raise_for_status()

            # Step 2: Parse HTML & extract PDF & sub-links
            discovered_links = parse_links_from_html(resp.text, base_url=target_url)
            discovered_count = len(discovered_links)
            crawl_log.discovered_count = discovered_count
            db.commit()

            # Step 3: Process discovered PDF URLs
            for link_info in discovered_links:
                url = link_info["url"]
                doc_name = link_info["name"]

                # Check if document URL already exists in DB
                existing_doc = db.query(Document).filter(Document.source_url == url).first()
                if existing_doc and existing_doc.processing_status == "INDEXED":
                    logger.info(f"Document already indexed: {url}")
                    continue

                # Download PDF bytes
                try:
                    pdf_resp = client.get(url, timeout=45)
                    pdf_resp.raise_for_status()
                    pdf_bytes = pdf_resp.content

                    # Compute SHA-256 Hash
                    file_hash = hashlib.sha256(pdf_bytes).hexdigest()

                    # Deduplication check by hash
                    hash_doc = db.query(Document).filter(Document.document_hash == file_hash).first()
                    if hash_doc and hash_doc.processing_status == "INDEXED":
                        logger.info(f"PDF hash already processed: {file_hash}")
                        continue

                    # Create or update Document record
                    if not existing_doc:
                        existing_doc = Document(
                            source_url=url,
                            document_name=doc_name,
                            document_hash=file_hash,
                            download_status="DOWNLOADED",
                            processing_status="PROCESSING",
                            discovered_at=datetime.utcnow()
                        )
                        db.add(existing_doc)
                        db.commit()
                        db.refresh(existing_doc)
                    else:
                        existing_doc.document_hash = file_hash
                        existing_doc.download_status = "DOWNLOADED"
                        existing_doc.processing_status = "PROCESSING"
                        db.commit()

                    # Step 4: Extract records from PDF
                    extracted_records, total_pages, ocr_used = process_pdf_bytes(pdf_bytes, document_name=doc_name)
                    
                    existing_doc.page_count = total_pages
                    existing_doc.ocr_used = ocr_used

                    # Delete previous records if re-indexing
                    db.query(NoticeRecord).filter(NoticeRecord.document_id == existing_doc.id).delete()

                    # Insert notice records
                    for rec in extracted_records:
                        notice_rec = NoticeRecord(
                            document_id=existing_doc.id,
                            page_number=rec["page_number"],
                            epic_normalized=rec["epic_normalized"],
                            epic_raw=rec["epic_raw"],
                            epic_match_confidence=rec["epic_match_confidence"],
                            name=rec.get("name"),
                            district=rec.get("district") or link_info.get("district"),
                            constituency=rec.get("constituency"),
                            part_number=rec.get("part_number"),
                            serial_number=rec.get("serial_number"),
                            notice_reason=rec.get("notice_reason"),
                            extracted_text=rec.get("extracted_text")
                        )
                        db.add(notice_rec)
                        records_added += 1

                    existing_doc.processing_status = "INDEXED"
                    existing_doc.indexed_at = datetime.utcnow()
                    processed_count += 1
                    db.commit()

                except Exception as doc_err:
                    logger.error(f"Failed to process document {url}: {doc_err}")
                    failed_count += 1
                    if existing_doc:
                        existing_doc.processing_status = "FAILED"
                        existing_doc.error_message = str(doc_err)
                        db.commit()

        # Update crawl log status
        crawl_log.status = "SUCCESS"
        crawl_log.completed_at = datetime.utcnow()
        crawl_log.processed_count = processed_count
        crawl_log.failed_count = failed_count
        crawl_log.records_count = records_added
        crawl_log.message = f"Crawl completed. {processed_count} indexed, {failed_count} failed."
        db.commit()

        # Update system status last crawl
        update_system_status(db, "LAST_CRAWL", datetime.utcnow().isoformat())
        update_system_status(db, "LAST_SUCCESSFUL_CRAWL", datetime.utcnow().isoformat())
        update_system_status(db, "SOURCE_URL", target_url)

    except Exception as crawl_err:
        logger.error(f"Crawl failed: {crawl_err}")
        crawl_log.status = "FAILED"
        crawl_log.completed_at = datetime.utcnow()
        crawl_log.message = f"Crawl failed: {str(crawl_err)}"
        db.commit()

    return {
        "discovered": discovered_count,
        "processed": processed_count,
        "failed": failed_count,
        "records_added": records_added
    }

def parse_links_from_html(html_text: str, base_url: str) -> List[Dict[str, str]]:
    """
    Parses HTML anchor tags to find PDF links, Drive links, or notice tables.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    links = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text().strip()
        
        # Absolute URL resolution
        full_url = urljoin(base_url, href)
        
        # Filter PDF or document links, strictly excluding non-PDF media files
        url_lower = full_url.lower()
        non_pdf_extensions = (".mp4", ".mp3", ".avi", ".mov", ".mkv", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".rar")
        if any(url_lower.endswith(ext) for ext in non_pdf_extensions):
            continue

        if url_lower.endswith(".pdf") or ("uploads" in url_lower and not any(url_lower.endswith(ext) for ext in non_pdf_extensions)) or "drive.google.com" in url_lower:
            links.append({
                "url": full_url,
                "name": text or href.split("/")[-1],
                "district": extract_district_from_link_text(text)
            })

            
    return links

def extract_district_from_link_text(text: str) -> str:
    districts = [
        "BAGALKOT", "BALLARI", "BELAGAVI", "BENGALURU URBAN", "BENGALURU RURAL",
        "BIDAR", "CHAMARAJANAGAR", "CHIKKABALLAPUR", "CHIKKAMAGALURU", "CHITRADURGA",
        "DAKSHINA KANNADA", "DAVANAGERE", "DHARWAD", "GADAG", "HASSAN", "HAVERI",
        "KALABURAGI", "KODAGU", "KOLAR", "KOPPAL", "MANDYA", "MYSURU", "RAICHUR",
        "RAMANAGARA", "SHIVAMOGGA", "TUMAKURU", "UDUPI", "UTTARA KANNADA", "VIJAYANAGARA", "YADGIR"
    ]
    text_upper = text.upper()
    for d in districts:
        if d in text_upper:
            return d.title()
    return "Karnataka"

def update_system_status(db: Session, key: str, value: str):
    item = db.query(SystemStatus).filter(SystemStatus.key == key).first()
    if not item:
        item = SystemStatus(key=key, value=value, updated_at=datetime.utcnow())
        db.add(item)
    else:
        item.value = value
        item.updated_at = datetime.utcnow()
    db.commit()


def live_crawl_epic_search(db: Session, epic_normalized: str, source_url: str = None) -> List[Tuple[NoticeRecord, Document]]:
    """
    On-Demand Live Crawl and PDF Search for an EPIC Number:
    1. Checks unindexed Documents / Crawl Queue in DB or fetches CEO Karnataka live pages.
    2. Downloads & scans candidate PDFs on-the-fly for `epic_normalized`.
    3. If matches found, extracts records, persists them to DB, and returns matching (NoticeRecord, Document) tuples.
    """
    target_url = source_url or settings.SOURCE_URL
    logger.info(f"Triggering live PDF crawl search for EPIC '{epic_normalized}' from {target_url}...")
    
    found_matches: List[Tuple[NoticeRecord, Document]] = []
    
    # 1. First check unindexed or pending Documents already in DB
    pending_docs = db.query(Document).filter(Document.processing_status != "INDEXED").limit(20).all()
    
    candidate_urls = []
    for d in pending_docs:
        candidate_urls.append({"url": d.source_url, "name": d.document_name, "district": d.district, "doc_obj": d})

    import time
    start_time = time.time()
    MAX_SEARCH_TIME = 4.0  # seconds

    # 2. Fetch live links from source URL if candidate list is small
    if len(candidate_urls) < 5 and (time.time() - start_time) < MAX_SEARCH_TIME:
        try:
            with httpx.Client(timeout=2.0, follow_redirects=True, headers=HTTP_HEADERS) as client:
                resp = client.get(target_url)
                if resp.status_code == 200:
                    links = parse_links_from_html(resp.text, base_url=target_url)
                    for l in links:
                        if not any(c["url"] == l["url"] for c in candidate_urls):
                            candidate_urls.append({"url": l["url"], "name": l["name"], "district": l.get("district"), "doc_obj": None})
        except Exception as err:
            logger.warning(f"Live HTML fetch note during search: {err}")

    # 3. Process candidates live
    with httpx.Client(timeout=3.0, follow_redirects=True, headers=HTTP_HEADERS) as client:
        for item in candidate_urls[:5]:
            if (time.time() - start_time) > MAX_SEARCH_TIME:
                logger.info(f"Live crawl search time limit reached ({MAX_SEARCH_TIME}s). Returning current results.")
                break
            url = item["url"]
            url_lower = url.lower()
            if any(url_lower.endswith(ext) for ext in (".mp4", ".mp3", ".avi", ".mov", ".mkv", ".png", ".jpg", ".jpeg", ".gif", ".zip")):
                continue
            doc_name = item["name"]
            doc_obj = item.get("doc_obj")


            try:
                pdf_resp = client.get(url)
                if pdf_resp.status_code != 200:
                    continue
                pdf_bytes = pdf_resp.content

                import fitz
                try:
                    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    epic_in_pdf = False
                    for page in pdf_doc:
                        if epic_normalized.lower() in page.get_text("text").lower():
                            epic_in_pdf = True
                            break
                    pdf_doc.close()
                except Exception:
                    epic_in_pdf = True

                if not epic_in_pdf:
                    continue

                file_hash = hashlib.sha256(pdf_bytes).hexdigest()
                if not doc_obj:
                    doc_obj = db.query(Document).filter(Document.source_url == url).first()
                
                if not doc_obj:
                    doc_obj = Document(
                        source_url=url,
                        document_name=doc_name,
                        document_hash=file_hash,
                        download_status="DOWNLOADED",
                        processing_status="PROCESSING",
                        discovered_at=datetime.utcnow()
                    )
                    db.add(doc_obj)
                    db.commit()
                    db.refresh(doc_obj)

                extracted_records, total_pages, ocr_used = process_pdf_bytes(pdf_bytes, document_name=doc_name)
                doc_obj.page_count = total_pages
                doc_obj.ocr_used = ocr_used

                db.query(NoticeRecord).filter(NoticeRecord.document_id == doc_obj.id).delete()

                for rec in extracted_records:
                    notice_rec = NoticeRecord(
                        document_id=doc_obj.id,
                        page_number=rec["page_number"],
                        epic_normalized=rec["epic_normalized"],
                        epic_raw=rec["epic_raw"],
                        epic_match_confidence=rec["epic_match_confidence"],
                        name=rec.get("name"),
                        district=rec.get("district") or item.get("district"),
                        constituency=rec.get("constituency"),
                        part_number=rec.get("part_number"),
                        serial_number=rec.get("serial_number"),
                        notice_reason=rec.get("notice_reason"),
                        extracted_text=rec.get("extracted_text")
                    )
                    db.add(notice_rec)
                    if rec["epic_normalized"] == epic_normalized:
                        found_matches.append((notice_rec, doc_obj))

                doc_obj.processing_status = "INDEXED"
                doc_obj.indexed_at = datetime.utcnow()
                db.commit()

                if found_matches:
                    logger.info(f"Live PDF scan discovered {len(found_matches)} match(es) for EPIC '{epic_normalized}'!")
                    break

            except Exception as scan_err:
                logger.error(f"Error live scanning PDF {url}: {scan_err}")
                continue

    return found_matches

