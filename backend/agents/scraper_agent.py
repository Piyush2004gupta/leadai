"""
AGENT 1 — SCRAPER
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
            timeout=300
        )
    except asyncio.TimeoutError:
        print("   ⚠️ Scraper timeout — returning partial results")
        leads = []
    except Exception as e:
        print(f"   ❌ Scraper crashed: {e}")
        leads = []
    state["raw_leads"] = leads
    return state


# ── progress_cb parameter add kiya — main.py se real-time update milega ──
async def scrape_maps(category: str, location: str, limit: int = 10, progress_cb=None) -> list:
    print(f"\n{'─'*45}")
    print(f"🕷  SCRAPING: '{category}' in '{location}' (Limit: {limit})")
    print(f"{'─'*45}")

    leads = []
    browser = None

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--single-process",
                    "--disable-gpu",
                    "--no-zygote",
                    "--disable-setuid-sandbox",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-sync",
                    "--metrics-recording-only",
                    "--mute-audio",
                    "--no-first-run",
                    "--safebrowsing-disable-auto-update",
                ]
            )
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await ctx.new_page()

            # Block images/fonts — saves ~40% RAM
            await page.route(
                "**/*.{png,jpg,jpeg,svg,webp,gif,css,font,woff,woff2,ttf,ico}",
                lambda route: route.abort()
            )

            search_url = (
                f"https://www.google.com/maps/search/"
                f"{urllib.parse.quote(category)} in {urllib.parse.quote(location)}"
            )
            try:
                print("   🌐 Opening Google Maps (Ultra-lite)")
                await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
                print("   ✅ Page opened successfully")
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"   ⚠️ Goto Error: {e}")

            try:
                await page.wait_for_selector('div[role="feed"]', timeout=30000)
                print("   ✅ Results loaded")
            except:
                print("   ⚠️ Results feed not found, attempting to proceed...")

            feed = await page.query_selector('div[role="feed"]')
            if feed:
                prev = 0
                for _ in range(8):
                    await page.evaluate("(el) => el.scrollBy(0, 1000)", feed)
                    await asyncio.sleep(1.5)
                    items = await page.query_selector_all('div[role="feed"] > div > div > a')
                    cur = len(items)
                    if cur == prev or cur >= 40:
                        break
                    prev = cur

            listings = await page.query_selector_all('div[role="feed"] > div > div > a')
            for i in range(len(listings)):
                if len(leads) >= limit:
                    break

                current_listings = await page.query_selector_all('div[role="feed"] > div > div > a')
                if i >= len(current_listings):
                    break
                item = current_listings[i]

                try:
                    try:
                        await item.scroll_into_view_if_needed(timeout=5000)
                    except:
                        pass

                    await item.click()
                    await asyncio.sleep(3)
                    lead = await _extract(page, i + 1, category, location)

                    if lead and lead.get("phone"):
                        name_lower = lead.get("name", "").strip().lower()
                        phone = lead["phone"]
                        is_dup = any(
                            l["phone"] == phone or l["name"].strip().lower() == name_lower
                            for l in leads
                        )
                        if not is_dup:
                            leads.append(lead)
                            print(f"   ✅ [{len(leads):02d}] {lead['name'][:35]:<35} {lead['phone']}")

                            # ── Real-time progress callback ──
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
                if phone:
                    break
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
    except Exception:
        return None


def _fmt(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 10: return None
    if digits.startswith("91") and len(digits) == 12: return f"+{digits}"
    if len(digits) == 10: return f"+91{digits}"
    if digits.startswith("0") and len(digits) == 11: return f"+91{digits[1:]}"
    return f"+{digits}"


def _save_json(leads: list):
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    existing_phones = {l["phone"] for l in existing if l.get("phone")}
    existing_names  = {l["name"].strip().lower() for l in existing if l.get("name")}

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
