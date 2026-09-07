from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship, synonym
from datetime import datetime
from .database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String(1024), nullable=False)
    url = synonym("source_url")
    parent_url = Column(String(1024), nullable=True)
    document_name = Column(String(512), nullable=False)
    document_hash = Column(String(64), unique=True, index=True, nullable=True)
    checksum = synonym("document_hash")
    published_date = Column(String(100), nullable=True)
    district = Column(String(200), nullable=True)
    subdistrict = Column(String(200), nullable=True)
    constituency = Column(String(200), nullable=True)
    category = Column(String(200), nullable=True)
    page_count = Column(Integer, default=0)
    status = Column(String(50), default="DISCOVERED")
    
    # Statuses: DISCOVERED, QUEUED, DOWNLOADING, DOWNLOADED, PROCESSING, INDEXED, FAILED
    download_status = Column(String(50), default="DISCOVERED")
    processing_status = Column(String(50), default="PENDING")
    attempt_count = Column(Integer, default=0)
    
    ocr_used = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    
    discovered_at = Column(DateTime, default=datetime.utcnow)
    indexed_at = Column(DateTime, nullable=True)

    records = relationship("NoticeRecord", back_populates="document", cascade="all, delete-orphan")


class CrawlQueue(Base):
    __tablename__ = "crawl_queue"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1024), unique=True, index=True, nullable=False)
    url_type = Column(String(50), nullable=False)
    parent_url = Column(String(1024), nullable=True)
    district = Column(String(200), nullable=True)
    subdistrict = Column(String(200), nullable=True)
    status = Column(String(50), default="PENDING")
    priority = Column(Integer, default=0)
    attempt_count = Column(Integer, default=0)
    last_attempt = Column(DateTime, nullable=True)
    next_attempt = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PdfProcessingQueue(Base):
    __tablename__ = "pdf_processing_queue"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    url = Column(String(1024), nullable=False)
    priority = Column(Integer, default=0)
    status = Column(String(50), default="PENDING")
    attempt_count = Column(Integer, default=0)
    last_attempt = Column(DateTime, nullable=True)
    next_attempt = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document")

class NoticeRecord(Base):
    __tablename__ = "notice_records"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, default=1)
    
    epic_normalized = Column(String(20), index=True, nullable=False)
    epic_raw = Column(String(50), nullable=True)
    epic_match_confidence = Column(String(20), default="HIGH") # HIGH, MEDIUM, LOW
    
    name = Column(String(255), nullable=True, index=True)
    district = Column(String(255), nullable=True)
    constituency = Column(String(255), nullable=True)
    taluk = Column(String(255), nullable=True)
    part_number = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    notice_reference = Column(String(255), nullable=True)
    notice_date = Column(String(100), nullable=True)
    notice_reason = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    verification_status = Column(String(50), default="VERIFIED")

    document = relationship("Document", back_populates="records")

Index("idx_epic_normalized", NoticeRecord.epic_normalized)
Index("idx_notice_record_name", NoticeRecord.name)

class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="RUNNING") # RUNNING, SUCCESS, FAILED
    stage = Column(String(50), default="DISCOVERY")
    district = Column(String(200), nullable=True)
    discovered_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    records_count = Column(Integer, default=0)
    message = Column(Text, nullable=True)

class SystemStatus(Base):
    __tablename__ = "system_status"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
