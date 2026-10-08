import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .config import settings
from .models import Community

def _text(node):
    return " ".join(node.stripped_strings) if node else ""

def scrape_communities() -> list[Community]:
    """
    Scrape all paginated community cards. This intentionally follows pagination
    instead of assuming page 1 is complete.
    """
    session = requests.Session()
    session.headers["User-Agent"] = "Bellhaven-CRM-Reconciliation/1.0"
    results = []
    seen = set()

    for page in range(1, 101):
        url = settings.website + "/communities"
        if page > 1:
            url += f"?page={page}"
        r = session.get(url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        cards = []
        for selector in ["article", ".community-card", ".card", "[data-community]"]:
            cards = soup.select(selector)
            if cards:
                break

        if not cards:
            # Generic fallback: identify links/cards that look like communities.
            links = soup.find_all("a", href=True)
            for a in links:
                txt = _text(a)
                href = a.get("href", "")
                if txt and ("/commun" in href.lower() or "/location" in href.lower()):
                    cards.append(a)

        page_added = 0
        for card in cards:
            text = _text(card)
            if not text:
                continue
            lines = [x.strip() for x in card.stripped_strings if x.strip()]
            name = lines[0] if lines else text

            # Heuristic field extraction. The parser also supports labels when present.
            address = ""
            city = state = zip_code = ""
            care = []

            labeled = {k.lower(): v for k, v in re.findall(
                r"(address|city|state|zip|postal|care offerings?|services?)\s*[:\-]\s*([^\n|]+)",
                text, re.I
            )}

            address = labeled.get("address", "")
            city = labeled.get("city", "")
            state = labeled.get("state", "")
            zip_code = labeled.get("zip", labeled.get("postal", ""))

            if not (city and state and zip_code):
                m = re.search(r"([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", text)
                if m:
                    city, state, zip_code = m.groups()

            if not address:
                for line in lines[1:]:
                    if re.search(r"\d+\s+.+", line) and not re.search(r"\b\d{5}\b", line):
                        address = line
                        break

            # Collect likely care/service labels.
            for line in lines:
                low = line.lower()
                if any(k in low for k in ["assisted", "memory", "independent", "skilled", "care", "respite"]):
                    if line != name:
                        care.append(line)

            key = (name.lower(), address.lower(), city.lower(), state.lower(), zip_code)
            if key in seen:
                continue
            seen.add(key)
            results.append(Community(
                name=name,
                address=address,
                city=city.strip(),
                state=state.strip(),
                zip=zip_code.strip(),
                care_offerings=sorted(set(care)),
                source_url=url,
            ))
            page_added += 1

        # Stop when pagination ends.
        next_links = [
            a.get("href") for a in soup.find_all("a", href=True)
            if "next" in _text(a).lower()
        ]
        if page > 1 and page_added == 0:
            break
        if page == 1 and not next_links and page_added == 0:
            break

    # Remove obviously non-community cards if the generic parser found navigation.
    return [c for c in results if c.name and (c.address or c.city or c.zip)]
