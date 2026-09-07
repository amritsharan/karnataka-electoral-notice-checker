from backend.app.pdf_processor.epic_extractor import normalize_epic, is_valid_epic, extract_epics_with_context

def test_normalize_epic():
    assert normalize_epic("abc1234567") == "ABC1234567"
    assert normalize_epic(" ABC1234567  ") == "ABC1234567"
    assert normalize_epic("abc-1234567") == "ABC1234567"
    assert normalize_epic("klm9876543") == "KLM9876543"

def test_invalid_epic():
    assert normalize_epic("12345") is None
    assert normalize_epic("") is None
    assert normalize_epic(None) is None

def test_extract_epics_with_context():
    sample_text = """
    DISTRICT: TUMAKURU
    CONSTITUENCY: 132 - TUMAKURU CITY
    SL NO: 115
    EPIC: ABC1234567
    NAME: Ramesh Gowda
    REASON: Multiple registration under SIR-2026
    """
    records = extract_epics_with_context(sample_text, page_num=1)
    assert len(records) >= 1
    assert records[0]["epic_normalized"] == "ABC1234567"
    assert records[0]["page_number"] == 1
