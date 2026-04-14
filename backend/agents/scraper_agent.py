"""
AGENT 1 — SCRAPER
Playwright se Google Maps kholo, saari businesses dhundho,
data extract karo aur leads.json mein save karo.
"""

import time, re, json, sys, io, urllib.parse, os
from playwright.sync_api import sync_playwright
from graph.state import AgentState

# Fix for Windows Unicode printing errors
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


JSON_FILE = "leads.json"


def scraper_agent(state: AgentState) -> AgentState:
    leads = scrape_maps(state["category"], state["location"], state.get("limit", 10))
    state["raw_leads"] = leads
    return state


def scrape_maps(category: str, location: str, limit: int = 10) -> list:
    print(f"\n{'─'*45}")
    print(f"🕷  SCRAPING: '{category}' in '{location}' (Limit: {limit})")
    print(f"{'─'*45}")

    leads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ).new_page()

        # ── Google Maps search direct URL ────────────────
        search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(category)} in {urllib.parse.quote(location)}"
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
        except Exception:
            pass

        # ── Scroll to load more ────────────────────────
        feed = page.query_selector('div[role="feed"]')
        if feed:
            prev = 0
            for _ in range(8):
                page.evaluate("(el) => el.scrollBy(0, 1000)", feed)
                time.sleep(1.8)
                cur = len(page.query_selector_all('div[role="feed"] > div > div > a'))
                if cur == prev or cur >= 40: break
                prev = cur

        # ── Extract each listing ───────────────────────
        listings = page.query_selector_all('div[role="feed"] > div > div > a')
        for i in range(len(listings)):
            if len(leads) >= limit: break
            
            # Re-fetch listings to avoid detachment
            current_listings = page.query_selector_all('div[role="feed"] > div > div > a')
            if i >= len(current_listings): break
            item = current_listings[i]

            try:
                try: item.scroll_into_view_if_needed(timeout=5000)
                except: pass
                
                item.click()
                time.sleep(3.5)
                lead = _extract(page, i+1, category, location)
                
                if lead and lead.get("phone"):
                    name_lower = lead.get("name", "").strip().lower()
                    phone = lead["phone"]
                    
                    is_dup = any(l["phone"] == phone or l["name"].strip().lower() == name_lower for l in leads)
                    
                    if not is_dup:
                        leads.append(lead)
                        print(f"   ✅ [{len(leads):02d}] {lead['name'][:35]:<35} {lead['phone']}")
            except: continue

        browser.close()

    _save_json(leads)
    return leads


def _extract(page, idx, category, location) -> dict | None:
    try:
        d = {}
        el = page.query_selector("h1.DUwDvf, h1.fontHeadlineLarge")
        d["name"] = el.inner_text().strip() if el else f"Business {idx}"

        phone = None
        for sel in [
            'button[data-item-id*="phone"] .fontBodyMedium',
            '[data-tooltip="Copy phone number"]',
            'button[aria-label*="phone"] span',
        ]:
            el = page.query_selector(sel)
            if el:
                phone = _fmt(el.inner_text().strip())
                if phone:
                    break
        d["phone"] = phone

        el = page.query_selector("div.F7nice span[aria-hidden='true']")
        d["rating"] = float(el.inner_text().strip()) if el else None

        el = page.query_selector('button[data-item-id="address"] .fontBodyMedium')
        d["address"] = el.inner_text().strip() if el else ""

        el = page.query_selector('a[data-item-id*="authority"]')
        d["website"] = el.get_attribute("href") if el else None
        d["has_website"] = d["website"] is not None

        d["category"] = category
        d["location"] = location
        d["status"]   = "pending"
        return d
    except Exception:
        return None


def _fmt(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 10:
        return None
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+91{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"+91{digits[1:]}"
    return f"+{digits}"


def _save_json(leads: list):
    """Save/merge leads into leads.json — no duplicates by phone."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    existing_phones = {l["phone"] for l in existing if l.get("phone")}
    existing_names = {l["name"].strip().lower() for l in existing if l.get("name")}
    
    new_leads = []
    for l in leads:
        name_lower = l.get("name", "").strip().lower()
        phone = l.get("phone")
        
        if phone and phone not in existing_phones and name_lower not in existing_names:
            new_leads.append(l)
            existing_phones.add(phone)
            existing_names.add(name_lower)
            
    all_leads = existing + new_leads

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_leads, f, indent=2, ensure_ascii=False)
