"""
Notice Reason Translator / Explainer

IMPORTANT ACCURACY RULE:
The explanation MUST be based ONLY on official government notice categories.
Never invent legal consequences, allegations, intent, reasons not mentioned,
or electoral conclusions.
If the source wording is insufficient, fallback to:
"The available source document does not provide enough information for us to explain this reason reliably."
"""

NOTICE_REASON_EXPLANATIONS = {
    "DUPLICATE": (
        "Duplicate / Multiple Registration",
        "This notice indicates that the voter's details appear in more than one entry in the draft electoral roll. The Electoral Registration Officer requires verification to retain the correct entry."
    ),
    "SHIFTED": (
        "Shifted Residence / Absentee",
        "This notice indicates that during field verification, the elector was found to have shifted from the registered address or was absent. The elector is requested to verify their active address."
    ),
    "DECEASED": (
        "Deceased / Deletion Notice",
        "This notice pertains to records marked for potential deletion due to report of death during roll revision."
    ),
    "DEMOGRAPHIC": (
        "Demographic Similar Entry (DSE)",
        "This notice indicates a similarity in name, relative name, or age with another voter entry requiring confirmation by the Electoral Officer."
    ),
    "PHOTO_MISMATCH": (
        "Photo Mismatch / Blur",
        "This notice requests updating or verifying the photo image associated with the EPIC record."
    ),
    "UNCOLLECTED_EPIC": (
        "Uncollected EPIC Card / Undelivered Notice",
        "This notice lists electors whose official EPIC cards or notices were undelivered by post."
    ),
    "SPECIAL_REVISION": (
        "Special Intensive Revision (SIR-2026) Verification",
        "This notice is issued under the Special Intensive Revision (SIR-2026) to verify voter eligibility and complete enumeration details."
    )
}

def get_reason_explanation(official_text: str) -> tuple[str, str]:
    if not official_text or not official_text.strip():
        return (
            "Notice Issued under SIR-2026",
            "The available source document does not provide enough information for us to explain this reason reliably."
        )

    text_upper = official_text.upper()
    
    if any(k in text_upper for k in ["DUPLICATE", "MULTIPLE", "REPEAT"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["DUPLICATE"][1])
    elif any(k in text_upper for k in ["SHIFTED", "ABSENT", "MOVED"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["SHIFTED"][1])
    elif any(k in text_upper for k in ["DECEASED", "DEATH", "EXPIRED"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["DECEASED"][1])
    elif any(k in text_upper for k in ["DSE", "DEMOGRAPHIC", "SIMILAR"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["DEMOGRAPHIC"][1])
    elif any(k in text_upper for k in ["PHOTO", "IMAGE", "BLUR"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["PHOTO_MISMATCH"][1])
    elif any(k in text_upper for k in ["UNCOLLECTED", "UNDELIVERED"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["UNCOLLECTED_EPIC"][1])
    elif any(k in text_upper for k in ["SIR", "REVISION", "ENUMERATION"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["SPECIAL_REVISION"][1])
    
    return (
        official_text,
        "The available source document does not provide enough information for us to explain this reason reliably."
    )
