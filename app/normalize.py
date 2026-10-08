import re
import unicodedata

STREET_WORDS = {
    "street": "st", "st": "st", "road": "rd", "rd": "rd",
    "avenue": "ave", "ave": "ave", "boulevard": "blvd", "blvd": "blvd",
    "drive": "dr", "dr": "dr", "lane": "ln", "ln": "ln",
    "court": "ct", "ct": "ct", "highway": "hwy", "hwy": "hwy",
    "parkway": "pkwy", "pkwy": "pkwy", "place": "pl", "pl": "pl",
    "circle": "cir", "cir": "cir", "terrace": "ter", "ter": "ter",
}

def normalize(value: object) -> str:
    s = "" if value is None else str(value)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def normalize_address(value: object) -> str:
    s = normalize(value)
    words = [STREET_WORDS.get(w, w) for w in s.split()]
    return " ".join(words)

def normalize_zip(value: object) -> str:
    s = re.sub(r"\D", "", "" if value is None else str(value))
    return s[:5]

def normalize_name(value: object) -> str:
    s = normalize(value)
    for token in ("senior living", "senior care", "assisted living", "memory care"):
        s = s.replace(token, " ")
    return re.sub(r"\s+", " ", s).strip()
