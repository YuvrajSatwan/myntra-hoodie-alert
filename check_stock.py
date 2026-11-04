"""
Myntra stock watcher for H&M Loose Fit Zip-Through Hoodie (size S).
Pings Telegram when size S flips to in-stock.
"""
import os
import re
import json
import gzip
import random
import sys
import urllib.request
import urllib.parse

STYLE_ID = "35714533"
TARGET_SIZE = "S"
PRODUCT_URL = (
    "https://www.myntra.com/mailers/sweatshirts/h&m/"
    "h&m-loose-fit-zip-through-hoodie/35714533/buy"
)

TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "9173194946:AAG62z1bMRSUOzNooAl1QZM9xpWVpdncRlg"
).strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8800631140").strip()

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

HYPE_LINES = [
    "The hoodie gods have spoken. Size S just materialized.",
    "Breaking: your future drip is now in stock.",
    "Fabric alert! Size S of that H&M zip-through just loaded in.",
    "Stop scrolling. Start checkout. Size S is HERE.",
    "The black hoodie has entered the chat — size S available.",
    "Heads up, legend — size S finally dropped back in.",
    "The hoodie was hiding. The hoodie has returned.",
    "Size S restock just happened. Fingers go brrr on checkout.",
]


def _read_response(resp):
    raw = resp.read()
    if resp.info().get("Content-Encoding") == "gzip" or (len(raw) > 2 and raw[:2] == b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="ignore")


def fetch_product_json():
    """Hit Myntra's public PDP gateway endpoint for this styleId."""
    url = f"https://www.myntra.com/gateway/v2/product/{STYLE_ID}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": PRODUCT_URL,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = _read_response(resp)
        return json.loads(content)


def fetch_from_html():
    """Fallback: scrape pdpData blob from the product HTML page."""
    req = urllib.request.Request(
        PRODUCT_URL,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = _read_response(resp)

    # 1. Look for window.__myx = {...}
    match = re.search(r"window\.__myx\s*=\s*", html)
    if match:
        decoder = json.JSONDecoder()
        try:
            blob, _ = decoder.raw_decode(html[match.end():])
            if "pdpData" in blob:
                return blob["pdpData"]
            return blob
        except Exception as e:
            print(f"JSON raw_decode on window.__myx failed: {e}")

    # 2. Look for "pdpData":{...}
    match = re.search(r'"pdpData"\s*:\s*', html)
    if match:
        decoder = json.JSONDecoder()
        try:
            pdp, _ = decoder.raw_decode(html[match.end():])
            return pdp
        except Exception as e:
            print(f"JSON raw_decode on pdpData failed: {e}")

    # If neither matched, print a diagnostic snippet to help debugging
    snippet = html[:300].replace("\n", " ")
    raise RuntimeError(f"Could not find product data in HTML. Page snippet: {snippet}")


def extract_sizes(pdp):
    """Return list of (label, available_bool) from Myntra's size options."""
    out = []
    style_options = (
        pdp.get("sizes")
        or pdp.get("styleOptions", {}).get("options")
        or []
    )
    for s in style_options:
        label = s.get("label") or s.get("value") or s.get("sizeKey") or ""
        avail = s.get("available")
        if avail is None:
            qty = s.get("inventory") or s.get("skuAvailableInventory") or 0
            avail = bool(qty) and qty > 0
        out.append((str(label).upper().strip(), bool(avail)))
    return out


def send_telegram(text):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram creds missing — printing instead:\n" + text)
        return
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false",
    }).encode("utf-8")
    req = urllib.request.Request(api, data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def main():
    try:
        try:
            pdp = fetch_product_json()
        except Exception as e:
            print(f"Gateway failed ({e}); falling back to HTML.")
            pdp = fetch_from_html()

        sizes = extract_sizes(pdp)
        print("Sizes seen:", sizes)

        target = next((a for (lab, a) in sizes if lab == TARGET_SIZE), None)

        if target is True:
            hype = random.choice(HYPE_LINES)
            msg = (
                f"\U0001F6A8 <b>{hype}</b>\n\n"
                f"<b>H&amp;M Loose Fit Zip-Through Hoodie</b>\n"
                f"Size: <b>{TARGET_SIZE}</b>  |  MRP: ₹1,499\n\n"
                f"\U0001F517 <a href=\"{PRODUCT_URL}\">Grab it on Myntra</a>\n\n"
                f"<i>Move fast — restocks disappear quicker than your paycheck.</i>"
            )
            send_telegram(msg)
            print("ALERT SENT.")
        elif target is False:
            print(f"Size {TARGET_SIZE} still out of stock.")
        else:
            print(f"Size {TARGET_SIZE} not listed at all — maybe discontinued.")
    except Exception as e:
        print(f"Check failed: {e}", file=sys.stderr)
        # non-zero so GH Actions flags it, but don't spam telegram on scraper errors
        sys.exit(1)


if __name__ == "__main__":
    main()
