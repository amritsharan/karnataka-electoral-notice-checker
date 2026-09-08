export const translations = {
  en: {
    // Header
    headerTitle: "Karnataka Electoral Notice Checker",
    headerSubtitle: "Official public search tool for notices published by the Chief Electoral Officer, Karnataka.",

    // Language switch
    langEnglish: "English",
    langKannada: "ಕನ್ನಡ",

    // Status Banner & Alerts
    indexingInProgress: "Indexing in progress ({processed} / {discovered} PDFs processed). Records already processed are searchable.",
    dbUpdateInProgress: "Database update in progress: Some recently published documents may not yet be indexed.",
    searchErrorTitle: "We couldn't complete the search.",
    networkErrorMsg: "Unable to connect to the search server. Please check backend status.",
    genericErrorMsg: "We couldn't complete the search. Please try again.",

    // Search Card
    searchTitle: "Check Your EPIC Number",
    searchDescription: "Enter your Voter ID / EPIC number for instant verification against published notice records.",
    epicPlaceholder: "e.g. ABC1234567",
    ariaEpicInput: "Enter EPIC Number",
    btnCheckStatus: "CHECK STATUS",
    btnChecking: "Checking...",
    errEmptyEpic: "Please enter an EPIC number.",
    errInvalidEpic: "Please enter a valid EPIC number (e.g. ABC1234567).",

    // Result Card - Not Found
    noNoticeTitle: "No Notice Issued",
    noNoticeDesc: "No notice record was found in published documents for EPIC number:",
    btnViewOfficialSource: "View Official CEO Karnataka Source",

    // Result Card - Found
    matchFoundTitle: "Match Found in Notice Records",
    matchFoundReferences: "References Found",
    matchDesc: "Query ({query}) appears in published notice documents from CEO Karnataka.",
    multipleRecordsBanner: "Multiple Records Found ({count} documents reference this search item). Please inspect each source reference below.",
    referenceHeader: "Reference #{index}: {docName} (Page {page})",
    possibleOcrMatch: "Possible Match: This record was extracted via OCR from a scanned document image and may contain minor OCR character variations. Please verify the original document.",

    // Table Fields
    epicNumber: "EPIC Number",
    electorName: "Elector Name",
    relativeName: "Relative / Parent Name",
    age: "Age",
    gender: "Gender",
    male: "Male",
    female: "Female",
    district: "District",
    assemblyConstituency: "Assembly Constituency",
    subdistrictTaluk: "Subdistrict / Taluk",
    partNumber: "Part Number",
    serialNumber: "Serial Number",
    noticeDate: "Notice Date",

    // Reason & Explanation
    reasonHeading: "Reason / Category for Notice",
    whatThisMeans: "What this means",

    // Source Meta
    docNameLabel: "Document Name:",
    pageNumberLabel: "Page Number:",
    districtLabel: "District:",
    publishedDateLabel: "Published Date:",
    sourceAuthorityLabel: "Source Authority:",
    sourceAuthorityValue: "Chief Electoral Officer, Karnataka",
    pageText: "Page",
    btnViewPdf: "View Original Government PDF",

    // Footer
    disclaimerLabel: "Disclaimer:",
    disclaimerText: "This is an independent information/search tool and is not affiliated with or operated by the Election Commission of India or the Chief Electoral Officer, Karnataka. It searches information contained in publicly available government documents. For authoritative confirmation, please refer to the original CEO Karnataka publication."
  },

  kn: {
    // Header
    headerTitle: "ಕರ್ನಾಟಕ ಮತದಾರರ ನೋಟಿಸ್ ಪರಿಶೀಲಕ",
    headerSubtitle: "ಕರ್ನಾಟಕ ಮುಖ್ಯ ಚುನಾವಣಾಧಿಕಾರಿಗಳು ಪ್ರಕಟಿಸಿದ ನೋಟಿಸ್‌ಗಳ ಅಧಿಕೃತ ಸಾರ್ವಜನಿಕ ಹುಡುಕಾಟ ಉಪಕರಣ.",

    // Language switch
    langEnglish: "English",
    langKannada: "ಕನ್ನಡ",

    // Status Banner & Alerts
    indexingInProgress: "ಇಂಡೆಕ್ಸಿಂಗ್ ಪ್ರಗತಿಯಲ್ಲಿದೆ ({processed} / {discovered} PDF ಗಳನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗಿದೆ). ಈಗಾಗಲೇ ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾದ ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಬಹುದು.",
    dbUpdateInProgress: "ಡೇಟಾಬೇಸ್ ಅಪ್‌ಡೇಟ್ ಪ್ರಗತಿಯಲ್ಲಿದೆ: ಇತ್ತೀಚೆಗೆ ಪ್ರಕಟಿಸಲಾದ ಕೆಲವು ದಾಖಲೆಗಳನ್ನು ಇನ್ನೂ ಸೇರಿಸಲಾಗಿಲ್ಲದಿರಬಹುದು.",
    searchErrorTitle: "ಹುಡುಕಾಟ ಪೂರ್ಣಗೊಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.",
    networkErrorMsg: "ಹುಡುಕಾಟ ಸರ್ವರ್‌ಗೆ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಬ್ಯಾಕೆಂಡ್ ಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.",
    genericErrorMsg: "ಹುಡುಕಾಟವನ್ನು ಪೂರ್ಣಗೊಳಿಸಲು ನಮಗೆ ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",

    // Search Card
    searchTitle: "ನಿಮ್ಮ EPIC ಸಂಖ್ಯೆಯನ್ನು ಪರಿಶೀಲಿಸಿ",
    searchDescription: "ಪ್ರಕಟಿತ ನೋಟಿಸ್ ದಾಖಲೆಗಳಲ್ಲಿ ತ್ವರಿತ ಪರಿಶೀಲನೆಗಾಗಿ ನಿಮ್ಮ ಮತದಾರರ ಗುರುತಿನ ಚೀಟಿ / EPIC ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.",
    epicPlaceholder: "ಉದಾ: ABC1234567",
    ariaEpicInput: "EPIC ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ",
    btnCheckStatus: "ಸ್ಥಿತಿ ಪರಿಶೀಲಿಸಿ",
    btnChecking: "ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
    errEmptyEpic: "ದಯವಿಟ್ಟು EPIC ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.",
    errInvalidEpic: "ದಯವಿಟ್ಟು ಮಾನ್ಯವಾದ EPIC ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ (ಉದಾ: ABC1234567).",

    // Result Card - Not Found
    noNoticeTitle: "ಯಾವುದೇ ನೋಟಿಸ್ ಜಾರಿಯಾಗಿಲ್ಲ",
    noNoticeDesc: "EPIC ಸಂಖ್ಯೆಗೆ ಪ್ರಕಟಿತ ದಾಖಲೆಗಳಲ್ಲಿ ಯಾವುದೇ ನೋಟಿಸ್ ದಾಖಲೆ ಕಂಡುಬಂದಿಲ್ಲ:",
    btnViewOfficialSource: "ಅಧಿಕೃತ CEO ಕರ್ನಾಟಕ ಮೂಲವನ್ನು ವೀಕ್ಷಿಸಿ",

    // Result Card - Found
    matchFoundTitle: "ನೋಟಿಸ್ ದಾಖಲೆಗಳಲ್ಲಿ ಹೊಂದಾಣಿಕೆ ಕಂಡುಬಂದಿದೆ",
    matchFoundReferences: "ದಾಖಲೆ ಉಲ್ಲೇಖಗಳು ಕಂಡುಬಂದಿವೆ",
    matchDesc: "ಹುಡುಕಾಟದ ವಿಷಯ ({query}) CEO ಕರ್ನಾಟಕದ ಪ್ರಕಟಿತ ನೋಟಿಸ್ ದಾಖಲೆಗಳಲ್ಲಿ ಕಂಡುಬಂದಿದೆ.",
    multipleRecordsBanner: "ಹಲವು ದಾಖಲೆಗಳು ಕಂಡುಬಂದಿವೆ ({count} ದಾಖಲೆಗಳು ಈ ಹುಡುಕಾಟ ವಿಷಯವನ್ನು ಉಲ್ಲೇಖಿಸುತ್ತವೆ). ದಯವಿಟ್ಟು ಕೆಳಗಿನ ಪ್ರತಿಯೊಂದು ಮೂಲ ಉಲ್ಲೇಖವನ್ನು ಪರಿಶೀಲಿಸಿ.",
    referenceHeader: "ಉಲ್ಲೇಖ #{index}: {docName} (ಪುಟ {page})",
    possibleOcrMatch: "ಸಾಧ್ಯತೆಯಿರುವ ಹೊಂದಾಣಿಕೆ: ಈ ದಾಖಲೆಯನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿದ ಪತ್ರದ ಚಿತ್ರದಿಂದ OCR ಮೂಲಕ ಪಡೆದುಕೊಳ್ಳಲಾಗಿದೆ, ಆದ್ದರಿಂದ ಸಣ್ಣ ಅಕ್ಷರ ವ್ಯತ್ಯಾಸಗಳಿರಬಹುದು. ದಯವಿಟ್ಟು ಮೂಲ ದಾಖಲೆಯನ್ನು ಪರಿಶೀಲಿಸಿ.",

    // Table Fields
    epicNumber: "EPIC ಸಂಖ್ಯೆ",
    electorName: "ಮತದಾರರ ಹೆಸರು",
    relativeName: "ಸಂಬಂಧಿ / ಪೋಷಕರ ಹೆಸರು",
    age: "ವಯಸ್ಸು",
    gender: "ಲಿಂಗ",
    male: "ಪುರುಷ",
    female: "ಮಹಿಳೆ",
    district: "ಜಿಲ್ಲೆ",
    assemblyConstituency: "ವಿಧಾನಸಭಾ ಕ್ಷೇತ್ರ",
    subdistrictTaluk: "ತಾಲೂಕು / ಉಪಜಿಲ್ಲೆ",
    partNumber: "ಭಾಗ ಸಂಖ್ಯೆ",
    serialNumber: "ಕ್ರಮೊ ಸಂಖ್ಯೆ",
    noticeDate: "ನೋಟಿಸ್ ದಿನಾಂಕ",

    // Reason & Explanation
    reasonHeading: "ನೋಟಿಸ್‌ಗೆ ಕಾರಣ / ವರ್ಗ",
    whatThisMeans: "ಇದರ ಅರ್ಥವೇನು",

    // Source Meta
    docNameLabel: "ದಾಖಲೆಯ ಹೆಸರು:",
    pageNumberLabel: "ಪುಟ ಸಂಖ್ಯೆ:",
    districtLabel: "ಜಿಲ್ಲೆ:",
    publishedDateLabel: "ಪ್ರಕಟಿತ ದಿನಾಂಕ:",
    sourceAuthorityLabel: "ಮೂಲ ಪ್ರಾಧಿಕಾರ:",
    sourceAuthorityValue: "ಮುಖ್ಯ ಚುನಾವಣಾಧಿಕಾರಿ, ಕರ್ನಾಟಕ",
    pageText: "ಪುಟ",
    btnViewPdf: "ಅಧಿಕೃತ ಸರ್ಕಾರಿ PDF ವೀಕ್ಷಿಸಿ",

    // Footer
    disclaimerLabel: "ಹಕ್ಕುತ್ಯಾಗ:",
    disclaimerText: "ಇದು ಸ್ವತಂತ್ರ ಮಾಹಿತಿ/ಹುಡುಕಾಟ ಉಪಕರಣವಾಗಿದ್ದು, ಭಾರತೀಯ ಚುನಾವಣಾ ಆಯೋಗ ಅಥವಾ ಕರ್ನಾಟಕ ಮುಖ್ಯ ಚುನಾವಣಾಧಿಕಾರಿಗಳೊಂದಿಗೆ ಸಂಯೋಜಿತವಾಗಿಲ್ಲ. ಇದು ಸಾರ್ವಜನಿಕವಾಗಿ ಲಭ್ಯವಿರುವ ಸರ್ಕಾರಿ ದಾಖಲೆಗಳಲ್ಲಿರುವ ಮಾಹಿತಿಯನ್ನು ಹುಡುಕುತ್ತದೆ. ಅಧಿಕೃತ ದೃಢೀಕರಣಕ್ಕಾಗಿ, ದಯವಿಟ್ಟು ಮೂಲ CEO ಕರ್ನಾಟಕ ಪ್ರಕಟಣೆಯನ್ನು ವೀಕ್ಷಿಸಿ."
  }
};
