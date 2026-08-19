from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # makes langdetect deterministic

# Keyword rules: (category, [keywords]) — checked in order, first match wins
CATEGORY_RULES = [
    ("roads", ["pothole", "road", "street", "highway", "footpath", "sidewalk", "bridge",
               "सड़क", "गड्ढा", "गड्ढे", "पुल", "फुटपाथ"]),
    ("water", ["water", "pipe", "leak", "sewage", "drain", "flood", "tap",
               "पानी", "पाइप", "नाली", "बाढ़", "नल", "रिसाव"]),
    ("electricity", ["light", "electricity", "power", "streetlight", "transformer", "wire", "outage",
                      "बिजली", "लाइट", "बत्ती", "तार", "ट्रांसफार्मर"]),
    ("sanitation", ["garbage", "waste", "trash", "sanitation", "toilet", "sewer", "dump",
                     "कचरा", "कूड़ा", "गंदगी", "शौचालय", "सफाई"]),
    ("healthcare", ["hospital", "clinic", "doctor", "medicine", "ambulance", "health",
                     "अस्पताल", "डॉक्टर", "दवा", "एम्बुलेंस", "स्वास्थ्य"]),
    ("education", ["school", "college", "teacher", "classroom", "education",
                    "स्कूल", "कॉलेज", "शिक्षक", "शिक्षा"]),
    ("safety", ["crime", "unsafe", "accident", "danger", "police", "theft", "violence",
                "दुर्घटना", "अपराध", "पुलिस", "खतरा", "चोरी", "असुरक्षित"]),
]

URGENCY_KEYWORDS = {
    "high": ["urgent", "emergency", "danger", "accident", "collapse", "fire", "flooding", "critical", "immediately",
              "तुरंत", "आपातकाल", "खतरा", "दुर्घटना", "आग", "गंभीर"],
    "medium": ["broken", "damaged", "not working", "problem", "issue", "repeated",
               "टूटा", "खराब", "समस्या", "बार-बार"],
}


def detect_language(text: str) -> str:
    """Detect language code (e.g. 'en', 'hi', 'pt'). Falls back to 'unknown'."""
    try:
        return detect(text)
    except Exception:
        return "unknown"


def classify_category(text: str) -> str:
    """Return the first matching category based on keyword rules."""
    lowered = text.lower()
    for category, keywords in CATEGORY_RULES:
        if any(kw in lowered for kw in keywords):
            return category
    return "general"


def classify_urgency(text: str) -> str:
    """Return urgency level: high, medium, or low."""
    lowered = text.lower()
    if any(kw in lowered for kw in URGENCY_KEYWORDS["high"]):
        return "high"
    if any(kw in lowered for kw in URGENCY_KEYWORDS["medium"]):
        return "medium"
    return "low"


def analyze_request(text: str) -> dict:
    """Run full NLU pipeline on raw citizen text."""
    return {
        "language": detect_language(text),
        "category": classify_category(text),
        "urgency": classify_urgency(text),
    }