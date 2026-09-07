import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Document, NoticeRecord, SystemStatus

MOCK_DOCUMENTS = [
    {
        "source_url": "https://ceo.karnataka.gov.in/uploads/Notice_List_Tumakuru_SIR2026.pdf",
        "document_name": "Notice_List_Tumakuru_SIR2026.pdf",
        "published_date": "2026-08-20",
        "district": "Tumakuru",
        "constituency": "132 - Tumakuru City",
        "category": "Special Intensive Revision - 2026",
        "page_count": 45,
        "ocr_used": True,
        "records": [
            {
                "epic_normalized": "ABC1234567",
                "epic_raw": "ABC1234567",
                "epic_match_confidence": "HIGH",
                "page_number": 27,
                "name": "Ramesh Gowda",
                "district": "Tumakuru",
                "constituency": "132 - Tumakuru City",
                "taluk": "Tumakuru",
                "part_number": "42",
                "serial_number": "115",
                "notice_reference": "CEO/KN/TMK/2026/N-8842",
                "notice_date": "2026-08-15",
                "notice_reason": "Multiple registration / Demographic Similar Entry (DSE) detected under SIR-2026",
                "extracted_text": "SL: 115 | EPIC: ABC1234567 | NAME: Ramesh Gowda | PART: 42 | REASON: Multiple registration / Demographic Similar Entry (DSE) detected under SIR-2026 | NOTICE REF: CEO/KN/TMK/2026/N-8842"
            },
            {
                "epic_normalized": "KLM9876543",
                "epic_raw": "KLM9876543",
                "epic_match_confidence": "HIGH",
                "page_number": 14,
                "name": "Sunita Patil",
                "district": "Tumakuru",
                "constituency": "132 - Tumakuru City",
                "taluk": "Tumakuru",
                "part_number": "18",
                "serial_number": "204",
                "notice_reference": "CEO/KN/TMK/2026/N-8814",
                "notice_date": "2026-08-14",
                "notice_reason": "Shifted residence / Elector absent during BLO door-to-door verification",
                "extracted_text": "SL: 204 | EPIC: KLM9876543 | NAME: Sunita Patil | PART: 18 | REASON: Shifted residence / Elector absent during BLO door-to-door verification"
            }
        ]
    },
    {
        "source_url": "https://ceo.karnataka.gov.in/uploads/Notice_List_Bengaluru_Urban_2026.pdf",
        "document_name": "Notice_List_Bengaluru_Urban_2026.pdf",
        "published_date": "2026-09-01",
        "district": "Bengaluru Urban",
        "constituency": "160 - Sarvagnanagar",
        "category": "Special Intensive Revision - 2026",
        "page_count": 82,
        "ocr_used": False,
        "records": [
            {
                "epic_normalized": "XYZ5551234",
                "epic_raw": "XYZ5551234",
                "epic_match_confidence": "HIGH",
                "page_number": 6,
                "name": "Anil Kumar Rao",
                "district": "Bengaluru Urban",
                "constituency": "160 - Sarvagnanagar",
                "taluk": "Bengaluru East",
                "part_number": "105",
                "serial_number": "312",
                "notice_reference": "CEO/KN/BLR/2026/N-10902",
                "notice_date": "2026-08-28",
                "notice_reason": "Photo Mismatch / Image Blur notice for EPIC photo update",
                "extracted_text": "SL: 312 | EPIC: XYZ5551234 | NAME: Anil Kumar Rao | PART: 105 | REASON: Photo Mismatch / Image Blur notice for EPIC photo update"
            },
            {
                "epic_normalized": "ABC1234567", # Multiple match test!
                "epic_raw": "ABC1234567",
                "epic_match_confidence": "HIGH",
                "page_number": 19,
                "name": "Ramesh Gowda",
                "district": "Bengaluru Urban",
                "constituency": "160 - Sarvagnanagar",
                "taluk": "Bengaluru East",
                "part_number": "88",
                "serial_number": "410",
                "notice_reference": "CEO/KN/BLR/2026/N-11005",
                "notice_date": "2026-08-30",
                "notice_reason": "Uncollected EPIC card / Undelivered notice notice",
                "extracted_text": "SL: 410 | EPIC: ABC1234567 | NAME: Ramesh Gowda | PART: 88 | REASON: Uncollected EPIC card / Undelivered notice notice"
            }
        ]
    },
    {
        "source_url": "https://ceo.karnataka.gov.in/uploads/Notice_List_Mysuru_SIR2026.pdf",
        "document_name": "Notice_List_Mysuru_SIR2026.pdf",
        "published_date": "2026-08-25",
        "district": "Mysuru",
        "constituency": "216 - Krishnaraja",
        "category": "Special Intensive Revision - 2026",
        "page_count": 30,
        "ocr_used": True,
        "records": [
            {
                "epic_normalized": "LOW9998887",
                "epic_raw": "LOW9998887",
                "epic_match_confidence": "LOW", # Low confidence OCR match test
                "page_number": 12,
                "name": "Lakshmi Narayana",
                "district": "Mysuru",
                "constituency": "216 - Krishnaraja",
                "taluk": "Mysuru",
                "part_number": "14",
                "serial_number": "89",
                "notice_reference": "CEO/KN/MYS/2026/N-4012",
                "notice_date": "2026-08-22",
                "notice_reason": "Low confidence OCR match: Possible EPIC match extracted from scanned document image",
                "extracted_text": "SL: 89 | EPIC: LOW9998887 (OCR confidence: 65%) | NAME: Lakshmi Narayana"
            }
        ]
    }
]

def seed_sample_data(db: Session) -> dict:
    """
    Seeds mock test data into database if empty or explicitly triggered by Admin.
    Returns summary dict.
    """
    docs_created = 0
    records_created = 0

    for doc_data in MOCK_DOCUMENTS:
        # Check if doc exists
        file_hash = hashlib.sha256(doc_data["source_url"].encode()).hexdigest()
        existing = db.query(Document).filter(Document.source_url == doc_data["source_url"]).first()
        
        if not existing:
            doc = Document(
                source_url=doc_data["source_url"],
                document_name=doc_data["document_name"],
                document_hash=file_hash,
                published_date=doc_data["published_date"],
                district=doc_data["district"],
                constituency=doc_data["constituency"],
                category=doc_data["category"],
                page_count=doc_data["page_count"],
                download_status="DOWNLOADED",
                processing_status="INDEXED",
                ocr_used=doc_data["ocr_used"],
                discovered_at=datetime.utcnow(),
                indexed_at=datetime.utcnow()
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            docs_created += 1
        else:
            doc = existing

        # Add records
        for rec in doc_data["records"]:
            rec_existing = db.query(NoticeRecord).filter(
                NoticeRecord.document_id == doc.id,
                NoticeRecord.epic_normalized == rec["epic_normalized"],
                NoticeRecord.page_number == rec["page_number"]
            ).first()

            if not rec_existing:
                n_rec = NoticeRecord(
                    document_id=doc.id,
                    page_number=rec["page_number"],
                    epic_normalized=rec["epic_normalized"],
                    epic_raw=rec["epic_raw"],
                    epic_match_confidence=rec["epic_match_confidence"],
                    name=rec["name"],
                    district=rec["district"],
                    constituency=rec["constituency"],
                    taluk=rec["taluk"],
                    part_number=rec["part_number"],
                    serial_number=rec["serial_number"],
                    notice_reference=rec["notice_reference"],
                    notice_date=rec["notice_date"],
                    notice_reason=rec["notice_reason"],
                    extracted_text=rec["extracted_text"]
                )
                db.add(n_rec)
                records_created += 1

    db.commit()

    # Set system status
    update_system_setting(db, "LAST_CRAWL", datetime.utcnow().isoformat())
    update_system_setting(db, "LAST_SUCCESSFUL_CRAWL", datetime.utcnow().isoformat())
    update_system_setting(db, "SOURCE_URL", "https://ceo.karnataka.gov.in/notices_issued.html")

    return {
        "docs_created": docs_created,
        "records_created": records_created,
        "total_docs": db.query(Document).count(),
        "total_records": db.query(NoticeRecord).count()
    }

def update_system_setting(db: Session, key: str, value: str):
    item = db.query(SystemStatus).filter(SystemStatus.key == key).first()
    if not item:
        item = SystemStatus(key=key, value=value, updated_at=datetime.utcnow())
        db.add(item)
    else:
        item.value = value
        item.updated_at = datetime.utcnow()
    db.commit()
