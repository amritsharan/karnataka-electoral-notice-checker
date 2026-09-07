from backend.app.database import SessionLocal
from backend.app.models import CrawlQueue, Document, PdfProcessingQueue
from backend.app.services import discovery_service


ROOT_HTML = """
<html><body>
<table>
  <tr><th>Sl. No.</th><th>District Names</th><th>Drive Link</th></tr>
  <tr><td>4</td><td>Bagalkot</td><td><a href="https://drive.google.com/drive/folders/root-district-id">Click here</a></td></tr>
</table>
</body></html>
"""


DISTRICT_HTML = """
<html><body>
<table>
  <tr data-id="folder-001"><td>19-Mudhol Discrepancies and No Mapping Shared folder</td></tr>
</table>
</body></html>
"""


FOLDER_HTML = """
<html><body>
<table>
  <tr data-id="pdf-001"><td>notice_001.pdf</td></tr>
</table>
</body></html>
"""


MULTI_ROOT_HTML = """
<html><body>
<table>
    <tr><th>Sl. No.</th><th>District Names</th><th>Drive Link</th></tr>
    <tr><td>4</td><td>Bagalkot</td><td><a href="https://drive.google.com/drive/folders/root-district-id">Click here</a></td></tr>
    <tr><td>5</td><td>Belagavi</td><td><a href="https://drive.google.com/drive/folders/root-belagavi-id">Click here</a></td></tr>
</table>
</body></html>
"""


BELAGAVI_DISTRICT_HTML = """
<html><body>
<table>
    <tr data-id="folder-002"><td>01-Chikodi Discrepancies and No Mapping Shared folder</td></tr>
</table>
</body></html>
"""


BELAGAVI_FOLDER_HTML = """
<html><body>
<table>
    <tr data-id="pdf-002"><td>notice_002.pdf</td></tr>
</table>
</body></html>
"""


def test_run_discovery_persists_queue_and_documents(monkeypatch):
    db = SessionLocal()
    try:
        db.query(PdfProcessingQueue).delete()
        db.query(Document).delete()
        db.query(CrawlQueue).delete()
        db.commit()

        def fake_fetch_html(url, client=None):
            if url.endswith("notices_issued.html"):
                return ROOT_HTML
            if url == "https://drive.google.com/drive/folders/root-district-id":
                return DISTRICT_HTML
            if url == "https://drive.google.com/drive/folders/folder-001":
                return FOLDER_HTML
            raise AssertionError(f"Unexpected URL: {url}")

        monkeypatch.setattr(discovery_service, "fetch_html", fake_fetch_html)

        result = discovery_service.run_discovery_for_one_district(
            db,
            source_url="https://ceo.karnataka.gov.in/notices_issued.html",
            district_name="Bagalkot",
            batch_size=10,
        )

        assert result["district"] == "ALL"
        assert result["subdistricts_discovered"] == 1
        assert result["pdfs_discovered"] == 1

        assert db.query(CrawlQueue).count() >= 3
        assert db.query(Document).count() == 1
        assert db.query(PdfProcessingQueue).count() == 1

        document = db.query(Document).first()
        assert document.url.startswith("https://drive.google.com/uc?id=pdf-001")
        assert document.processing_status == "PENDING"
    finally:
        db.query(PdfProcessingQueue).delete()
        db.query(Document).delete()
        db.query(CrawlQueue).delete()
        db.commit()
        db.close()


def test_run_discovery_fans_out_across_multiple_districts(monkeypatch):
    db = SessionLocal()
    try:
        db.query(PdfProcessingQueue).delete()
        db.query(Document).delete()
        db.query(CrawlQueue).delete()
        db.commit()

        def fake_fetch_html(url, client=None):
            if url.endswith("notices_issued.html"):
                return MULTI_ROOT_HTML
            if url == "https://drive.google.com/drive/folders/root-district-id":
                return DISTRICT_HTML
            if url == "https://drive.google.com/drive/folders/folder-001":
                return FOLDER_HTML
            if url == "https://drive.google.com/drive/folders/root-belagavi-id":
                return BELAGAVI_DISTRICT_HTML
            if url == "https://drive.google.com/drive/folders/folder-002":
                return BELAGAVI_FOLDER_HTML
            raise AssertionError(f"Unexpected URL: {url}")

        monkeypatch.setattr(discovery_service, "fetch_html", fake_fetch_html)

        result = discovery_service.run_discovery_for_all_districts(
            db,
            source_url="https://ceo.karnataka.gov.in/notices_issued.html",
        )

        assert result["district"] == "ALL"
        assert result["subdistricts_discovered"] == 2
        assert result["pdfs_discovered"] == 2

        districts = sorted({doc.district for doc in db.query(Document).all()})
        assert districts == ["Bagalkot", "Belagavi"]
        assert db.query(Document).count() == 2
        assert db.query(PdfProcessingQueue).count() == 2
        assert db.query(CrawlQueue).count() >= 5
    finally:
        db.query(PdfProcessingQueue).delete()
        db.query(Document).delete()
        db.query(CrawlQueue).delete()
        db.commit()
        db.close()