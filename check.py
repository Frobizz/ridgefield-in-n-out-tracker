from http.server import BaseHTTPRequestHandler
import os, json, datetime, re
import httpx
from bs4 import BeautifulSoup
import vercel_blob

"
SOURCES = {
    "grand_openings": "https://www.in-n-out.com/locations/grand-openings",
    "locations": "https://www.in-n-out.com/locations",
}

def looks_open_from_locations(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    # If Ridgefield WA shows up alongside typical live-location cues
    return ("ridgefield" in text and "washington" in text) and ("hours" in text or "directions" in text or "open" in text)

def ridgefield_listed_in_grand_openings(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    if "ridgefield" not in text:
        return False
    # Any nearby mention of open/opening with a month/date/year
    return bool(re.search(r"(ridgefield).*?(opening|grand|open).*?(2025|aug|sep|oct|nov|dec)", text))

def decide_status(pages: dict) -> dict:
    open_signals = []
    if ridgefield_listed_in_grand_openings(pages.get("grand_openings","")):
        open_signals.append("Grand openings page mentions Ridgefield with a date")
    if looks_open_from_locations(pages.get("locations","")):
        open_signals.append("Locations directory lists Ridgefield with hours/details")

    status = "OPEN" if open_signals else "NOT_OPEN_YET"
    return {
        "status": status,
        "signals": open_signals,
        "last_checked_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "sources": SOURCES
    }

def run_check():
    # Fetch pages (simple GETs)
    with httpx.Client(timeout=20, headers={"User-Agent":"ridgefield-open-check/1.0"}) as client:
        pages = {k: client.get(v).text for k, v in SOURCES.items()}
    result = decide_status(pages)
    # Save to Vercel Blob (unofficial Python wrapper)
    token = os.environ.get("VERCEL_BLOB_READ_WRITE_TOKEN") or os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        # If missing token, still return result without saving
        return 500, {"ok": False, "error": "Missing VERCEL_BLOB_READ_WRITE_TOKEN", **result}

    vercel_blob.set_token(token)
    # store at root as status.json (stable pathname)
    vercel_blob.put_json("status.json", result, {"addRandomSuffix": False, "contentType": "application/json", "cacheControl": "public, max-age=300"})
    return 200, {"ok": True, "saved": "status.json", **result}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code, payload = run_check()
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)
        return
