from http.server import BaseHTTPRequestHandler
import os, json, datetime, re, urllib.request
import httpx
from bs4 import BeautifulSoup

SOURCES = {
    "grand_openings": "https://www.in-n-out.com/locations/grand-openings",
    "locations": "https://www.in-n-out.com/locations",
}

def looks_open_from_locations(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")  # built-in parser
    text = soup.get_text(" ", strip=True).lower()
    return ("ridgefield" in text and "washington" in text) and ("hours" in text or "directions" in text or "open" in text)

def ridgefield_listed_in_grand_openings(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")  # built-in parser
    text = soup.get_text(" ", strip=True).lower()
    if "ridgefield" not in text:
        return False
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

def write_blob(token: str, data: dict):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        "https://blob.vercel-storage.com/status.json?addRandomSuffix=false",
        data=body,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-vercel-blob-ttl": "31536000"
        }
    )
    with urllib.request.urlopen(req) as _:
        pass

def run_check():
    try:
        with httpx.Client(timeout=20, headers={"User-Agent":"ridgefield-open-check/1.0"}) as client:
            pages = {k: client.get(v).text for k,v in SOURCES.items()}
        result = decide_status(pages)

        token = os.environ.get("VERCEL_BLOB_READ_WRITE_TOKEN") or os.environ.get("BLOB_READ_WRITE_TOKEN")
        if token:
            try:
                write_blob(token, result)
                result = {"ok": True, "saved": "status.json", **result}
            except Exception as e:
                result = {"ok": False, "save_error": str(e), **result}
        else:
            result = {"ok": False, "save_error": "Missing VERCEL_BLOB_READ_WRITE_TOKEN", **result}
        return 200, result
    except Exception as e:
        return 500, {"ok": False, "error": str(e)}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code, payload = run_check()
        body = json.dumps(payload, indent=2).encode()
        self.send_response(code)
        self.send_header("content-type","application/json")
        self.end_headers()
        self.wfile.write(body)
