import re
from typing import List, Dict, Any, Optional

# Standard EPIC format: 3 letters + 7 numbers (e.g. ABC1234567)
EPIC_STRICT_REGEX = re.compile(r'\b([A-Z]{3}\d{7})\b', re.IGNORECASE)
# Generic EPIC format: 3-4 alphanumeric + 6-7 digits
EPIC_GENERIC_REGEX = re.compile(r'\b([A-Z]{2,4}\/?\d{6,8})\b', re.IGNORECASE)

def normalize_epic(epic: str) -> Optional[str]:
    """
    Normalizes EPIC input:
    - Trims whitespace
    - Uppercases string
    - Strips internal slashes if standard format
    Returns normalized string or None if invalid.
    """
    if not epic or not isinstance(epic, str):
        return None
    
    clean = epic.strip().upper()
    clean = re.sub(r'[\s\-]', '', clean)
    
    # Check strict format ABC1234567
    match = EPIC_STRICT_REGEX.search(clean)
    if match:
        return match.group(1).upper()
        
    # Check if 10 alphanumeric chars
    if len(clean) == 10 and clean[:3].isalpha() and clean[3:].isdigit():
        return clean

    return None

def is_valid_epic(epic: str) -> bool:
    return normalize_epic(epic) is not None

def extract_epics_with_context(text: str, page_num: int = 1) -> List[Dict[str, Any]]:
    """
    Parses text line-by-line or block-by-block to extract EPIC numbers
    along with contextual details (Name, District, Constituency, Reason, etc.)
    """
    if not text:
        return []
        
    results = []
    lines = text.split('\n')
    
    # Track current document headers if available
    current_district = None
    current_ac = None
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        
        # Check for district or AC headers
        if "DISTRICT:" in line_clean.upper():
            current_district = line_clean.split(":", 1)[-1].strip()
        if "CONSTITUENCY:" in line_clean.upper() or "AC:" in line_clean.upper():
            current_ac = line_clean.split(":", 1)[-1].strip()
            
        matches = EPIC_STRICT_REGEX.findall(line_clean)
        if not matches:
            # Fallback check generic
            generic_matches = EPIC_GENERIC_REGEX.findall(line_clean)
            matches = [m.replace("/", "") for m in generic_matches if len(m.replace("/", "")) == 10]
            
        for epic_raw in matches:
            epic_norm = normalize_epic(epic_raw)
            if not epic_norm:
                continue
                
            # Extract surrounding context (surrounding lines)
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context_block = " | ".join([l.strip() for l in lines[start:end] if l.strip()])
            
            # Simple heuristic extraction of Name / Serial / Reason from context block
            name = extract_field(context_block, ["NAME", "NAME:", "ELECTOR NAME"])
            reason = extract_field(context_block, ["REASON", "NOTICE REASON", "REASON FOR NOTICE", "CATEGORY"])
            part_num = extract_field(context_block, ["PART", "PART NO", "PART NUMBER"])
            serial_num = extract_field(context_block, ["SL NO", "SERIAL", "SL.NO", "SER"])

            # Pipe-delimited table row parsing fallback (common in notice PDF tables)
            if "|" in line_clean:
                parts = [p.strip() for p in line_clean.split("|")]
                for idx, p in enumerate(parts):
                    if normalize_epic(p) == epic_norm:
                        if not name and idx + 1 < len(parts) and parts[idx + 1]:
                            cand_name = parts[idx + 1]
                            if not cand_name.isdigit() and len(cand_name) > 1:
                                name = cand_name
                        if not part_num and idx - 1 >= 0 and parts[idx - 1].isdigit():
                            part_num = parts[idx - 1]
                        if not serial_num and idx - 2 >= 0 and parts[idx - 2].isdigit():
                            serial_num = parts[idx - 2]

            results.append({
                "epic_normalized": epic_norm,
                "epic_raw": epic_raw,
                "epic_match_confidence": "HIGH" if epic_raw.isupper() and len(epic_norm) == 10 else "MEDIUM",
                "page_number": page_num,
                "name": name or "Record Holder",
                "district": current_district,
                "constituency": current_ac,
                "part_number": part_num,
                "serial_number": serial_num,
                "notice_reason": reason or "Listed under CEO Karnataka Notice Document",
                "extracted_text": context_block[:500]
            })
            
    return results

def extract_field(context: str, keywords: List[str]) -> Optional[str]:
    context_upper = context.upper()
    for kw in keywords:
        if kw in context_upper:
            idx = context_upper.find(kw)
            substring = context[idx + len(kw):].strip(" :-|")
            parts = re.split(r'[|;,\n]', substring)
            if parts and parts[0].strip():
                return parts[0].strip()[:100]
    return None
