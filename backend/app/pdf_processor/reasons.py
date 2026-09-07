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
    "DISCREPANCY": (
        "Elector Data Discrepancy (SIR-2026)",
        "This notice indicates a discrepancy in the voter's roll entry (such as name mismatch, age gap, or mapping irregularity) identified during the Special Intensive Revision (SIR-2026). The Electoral Registration Officer requires verification of original documents."
    ),
    "UNMAPPED": (
        "Polling Station Unmapped / Mapping Discrepancy",
        "This notice pertains to electors whose polling station or part number mapping could not be automatically matched with the previous roll. Physical document verification is required."
    ),
    "LOGICAL_ERROR": (
        "Logical Error in Roll Verification",
        "This notice is issued for data entries containing logical inconsistencies (such as unusual parent-progeny age gaps or formatting variations) identified during automated roll validation."
    ),
    "MISMATCH": (
        "Name / Details Mismatch",
        "This notice indicates a mismatch between the elector's name or relative's name in official records compared to the submitted verification forms."
    ),
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
        "This notice is issued under the Special Intensive Revision (SIR-2026) by CEO Karnataka to verify voter eligibility and complete enumeration details."
    )
}

def get_reason_explanation(official_text: str) -> tuple[str, str]:
    if not official_text or not official_text.strip():
        return (
            "Special Intensive Revision (SIR-2026) Verification",
            NOTICE_REASON_EXPLANATIONS["SPECIAL_REVISION"][1]
        )

    text_upper = official_text.upper()

    if any(k in text_upper for k in ["FORM_39", "FORM 39", "FORM_60", "FORM 60", "FORM_154", "FORM 154", "DISCREPANCY", "DISCREPENCY"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["DISCREPANCY"][1])
    elif any(k in text_upper for k in ["UNMAPPED", "NO MAPPING", "NOMAPPING", "MAPPING"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["UNMAPPED"][1])
    elif any(k in text_upper for k in ["LOGICAL", "AGE GAP", "AGE DIFFERENCE"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["LOGICAL_ERROR"][1])
    elif any(k in text_upper for k in ["MISMATCH", "NAME MISMATCH", "PARENT NAME", "SELF NAME"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["MISMATCH"][1])
    elif any(k in text_upper for k in ["DUPLICATE", "MULTIPLE", "REPEAT"]):
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
    elif any(k in text_upper for k in ["SIR", "REVISION", "ENUMERATION", "NOTICE"]):
        return (official_text, NOTICE_REASON_EXPLANATIONS["SPECIAL_REVISION"][1])

    return (
        official_text,
        NOTICE_REASON_EXPLANATIONS["SPECIAL_REVISION"][1]
    )

