"""
AGENT 1 — SCRAPER (Playwright Version)
Playwright se Google Maps kholo, saari businesses dhundho,
data extract karo aur leads.json mein save karo.
"""

import asyncio, re, json, sys, io, urllib.parse, os
from playwright.async_api import async_playwright
from graph.state import AgentState

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JSON_FILE = "leads.json"

async def scraper_agent(state: AgentState) -> AgentState:
    try:
        leads = await asyncio.wait_for(
            scrape_maps(state["category"], state["location"], state.get("limit", 10)),
            timeout=600
        )
    except asyncio.TimeoutError:
        print("   ⚠️ Scraper timeout — returning partial results")
        leads = []
    except Exception as e:
        print(f"   ❌ Scraper crashed: {e}")
        leads = []
    state["raw_leads"] = leads
    return state

async def scrape_maps(category: str, location: str, limit: int = 10, progress_cb=None) -> list:
    print(f"\n{'─'*45}")
    print(f"🕷  SCRAPING: '{category}' in '{location}' (Limit: {limit})")
    print(f"{'─'*45}")

    leads = []
    browser = None

    async with async_playwright() as p:
        try:
            # Local use: headless=False might be better if they want to see it, 
            # but I'll stick to True for stability unless asked.
            browser = await p.chromium.launch(
                headless=False, # Shared local context: showing browser is helpful
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await ctx.new_page()

            search_url = (
                f"https://www.google.com/maps/search/"
                f"{urllib.parse.quote(category)} in {urllib.parse.quote(location)}"
            )
            
            try:
                print("   🌐 Opening Google Maps...")
                if progress_cb:
                    progress_cb("SYSTEM_STATUS", "Opening Google Maps...")
                
                await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
                print("   ✅ Page opened successfully")
                
                if progress_cb:
                    progress_cb("SYSTEM_STATUS", "Searching leads...")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"   ❌ Maps load failed: {e}")
                return []

            try:
                await page.wait_for_selector('div[role="feed"]', timeout=30000)
            except:
                pass

            feed = await page.query_selector('div[role="feed"]')
            if feed:
                prev = 0
                for _ in range(10):
                    await page.evaluate("(el) => el.scrollBy(0, 1500)", feed)
                    await asyncio.sleep(2)
                    items = await page.query_selector_all('div[role="feed"] > div > div > a')
                    if len(items) == prev or len(items) >= limit * 2:
                        break
                    prev = len(items)

            listings = await page.query_selector_all('div[role="feed"] > div > div > a')
            for i in range(len(listings)):
                if len(leads) >= limit:
                    break

                current_listings = await page.query_selector_all('div[role="feed"] > div > div > a')
                if i >= len(current_listings): break
                item = current_listings[i]

                try:
                    await item.scroll_into_view_if_needed()
                    await item.click()
                    await asyncio.sleep(4)
                    lead = await _extract(page, i + 1, category, location)

                    if lead and lead.get("phone"):
                        leads.append(lead)
                        print(f"   ✅ [{len(leads):02d}] {lead['name'][:35]:<35} {lead['phone']}")
                        if progress_cb:
                            progress_cb(lead["name"], lead["phone"])
                except:
                    continue

        except Exception as e:
            print(f"   ❌ Browser error: {e}")
        finally:
            if browser:
                await browser.close()

    _save_json(leads)
    return leads

async def _extract(page, idx, category, location) -> dict | None:
    try:
        d = {}
        el = await page.query_selector("h1.DUwDvf, h1.fontHeadlineLarge")
        d["name"] = (await el.inner_text()).strip() if el else f"Business {idx}"

        phone = None
        for sel in [
            'button[data-item-id*="phone"] .fontBodyMedium',
            '[data-tooltip="Copy phone number"]',
            'button[aria-label*="phone"] span',
        ]:
            el = await page.query_selector(sel)
            if el:
                phone = _fmt((await el.inner_text()).strip())
                if phone: break
        d["phone"] = phone

        el = await page.query_selector("div.F7nice span[aria-hidden='true']")
        d["rating"] = float((await el.inner_text()).strip()) if el else None

        el = await page.query_selector('button[data-item-id="address"] .fontBodyMedium')
        d["address"] = (await el.inner_text()).strip() if el else ""

        el = await page.query_selector('a[data-item-id*="authority"]')
        d["website"] = await el.get_attribute("href") if el else None
        d["has_website"] = d["website"] is not None

        d["category"] = category
        d["location"] = location
        d["status"]   = "pending"
        return d
    except:
        return None

def _fmt(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 10: return None
    if digits.startswith("91") and len(digits) == 12: return f"+{digits}"
    if len(digits) == 10: return f"+91{digits}"
    return f"+{digits}"

def _save_json(leads: list):
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except:
        existing = []

    existing_phones = {l["phone"] for l in existing if l.get("phone")}
    new_leads = [l for l in leads if l.get("phone") not in existing_phones]
    
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(existing + new_leads, f, indent=2, ensure_ascii=False)
