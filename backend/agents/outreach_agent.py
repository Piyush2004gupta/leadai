"""
AGENT 4 — OUTREACH
Playwright se WhatsApp Web kholo aur messages bhejo.
"""

import asyncio, json, urllib.parse, sys, io, re, os
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from graph.state import AgentState

WA_SESSION = "./wa_session"
DELAY_SEC  = 8
JSON_FILE  = "leads.json"

async def outreach_agent(state: AgentState) -> AgentState:
    print(f"\n📲  STARTING WHATSAPP OUTREACH...")
    
    leads = state["leads_with_msg"]
    sent = failed = 0

    async with async_playwright() as p:
        try:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=WA_SESSION,
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 800},
            )
            page = await ctx.new_page()

            print("   🌐 Opening WhatsApp Web...")
            await page.goto("https://web.whatsapp.com")

            print("   ⌛ Waiting for login (Manually scan if needed)...")
            try:
                await page.wait_for_selector('[data-testid="chat-list"], #pane-side', timeout=60000)
                print("   ✅ Logged in!")
            except:
                print("   ⚠️ Login taking long, please verify in browser window.")
                await asyncio.sleep(10)

            for i, lead in enumerate(leads):
                phone   = lead.get("phone", "")
                message = lead.get("message", "")
                name    = lead.get("name", "")

                print(f"   [{i+1}/{len(leads)}] Sending to {name} ({phone})...", end=" ", flush=True)
                
                ok = await _send(page, phone, message)
                if ok:
                    sent += 1
                    _update_status(phone, "sent")
                    print("✅")
                else:
                    failed += 1
                    _update_status(phone, "failed")
                    print("❌")
                
                await asyncio.sleep(DELAY_SEC)
        finally:
            await ctx.close()

    state["sent_count"]   = sent
    state["failed_count"] = failed
    return state

async def _send(page, phone: str, message: str) -> bool:
    try:
        clean = re.sub(r"\D", "", phone)
        url = f"https://web.whatsapp.com/send?phone={clean}&text={urllib.parse.quote(message)}"
        await page.goto(url)
        
        # Wait for send button
        btn_selector = 'span[data-icon="send"], [data-testid="send"]'
        await page.wait_for_selector(btn_selector, timeout=20000)
        await asyncio.sleep(2)
        await page.click(btn_selector)
        await asyncio.sleep(3)
        return True
    except Exception as e:
        print(f"(Error: {e})", end="")
        return False

def _update_status(phone: str, status: str):
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            leads = json.load(f)
        for l in leads:
            if l.get("phone") == phone:
                l["status"] = status
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
    except:
        pass
