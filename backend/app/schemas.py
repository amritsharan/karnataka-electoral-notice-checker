from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class EpicCheckRequest(BaseModel):
    epic: str = Field(..., example="ABC1234567", description="Citizen's EPIC/Voter ID number")

class NameCheckRequest(BaseModel):
    name: str = Field(..., example="Ramesh Kumar", description="Citizen's Name to search notice records")

class SourceInfo(BaseModel):
    document_name: str
    page: int
    url: str
    published_date: Optional[str] = None
    district: Optional[str] = None

class NoticeRecordResponse(BaseModel):
    epic: str
    name: Optional[str] = None
    relative_name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    taluk: Optional[str] = None
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    notice_reference: Optional[str] = None
    notice_date: Optional[str] = None
    reason: str
    reason_explanation: str
    confidence: str
    source: SourceInfo

class SearchResponse(BaseModel):
    query: str
    query_type: str  # "EPIC" or "NAME"
    found: bool
    records_count: int
    records: List[NoticeRecordResponse]
    warning: Optional[str] = None
    indexed_at: Optional[str] = None
    total_documents_indexed: Optional[int] = 0
    total_documents_discovered: Optional[int] = 0
    last_updated: Optional[str] = None
    indexing_in_progress: Optional[bool] = False
    indexing_complete: Optional[bool] = True

class EpicCheckResponse(SearchResponse):
    epic: str

class StartDiscoveryRequest(BaseModel):
    district: Optional[str] = Field("ALL", description="Target district name or 'ALL'")
    batch_size: Optional[int] = Field(10, description="Batch size for initial page discovery")

class StartProcessingRequest(BaseModel):
    batch_size: Optional[int] = Field(10, description="Number of PDFs to process in this queue run")

class SystemStatusResponse(BaseModel):
    source_url: str
    last_updated: Optional[str] = None
    last_crawl: Optional[str] = None
    last_successful_crawl: Optional[str] = None
    documents_discovered: int
    documents_processed: int
    documents_pending: int
    documents_failed: int
    ocr_documents_count: int
    total_records_indexed: int
    indexing_in_progress: bool
    indexing_complete: bool = True
    crawl_queue_total: int = 0
    crawl_queue_pending: int = 0
    crawl_queue_processing: int = 0
    crawl_queue_completed: int = 0
    crawl_queue_failed: int = 0
    pdf_queue_total: int = 0
    pdf_queue_pending: int = 0
    pdf_queue_processing: int = 0
    pdf_queue_completed: int = 0
    pdf_queue_failed: int = 0
    discovery_district: Optional[str] = None
    district_progress: List[dict] = Field(default_factory=list)
    subdistrict_progress: List[dict] = Field(default_factory=list)
    recent_events: List[dict] = Field(default_factory=list)

class AdminActionResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    details: Optional[dict] = None


class DiscoverySummaryResponse(BaseModel):
    success: bool
    district: str
    source_url: str
    queue_items_added: int
    pages_discovered: int
    subdistricts_discovered: int
    pdfs_discovered: int
    crawl_log_id: Optional[int] = None

