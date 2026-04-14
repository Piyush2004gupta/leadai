"""
AGENT 4 — OUTREACH
Playwright se WhatsApp Web kholo.
Har lead ko message bhejo — 10 second delay.
Status leads.json mein update hoti hai.
"""

import asyncio, json, urllib.parse, sys, io, re, os
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from graph.state import AgentState

# Fix for Windows Unicode printing errors
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


JSON_FILE  = "leads.json"
WA_SESSION = "./wa_session"
DELAY_SEC  = 5


async def outreach_agent(state: AgentState) -> AgentState:
    print(f"\n{'─'*45}")
    print(f"📲  AGENT 4 — OUTREACH  (WhatsApp Web)")
    print(f"   {len(state['leads_with_msg'])} messages bheje jaayenge")
    print(f"   Delay: {DELAY_SEC}s between each")
    eta = round(len(state['leads_with_msg']) * (DELAY_SEC + 6) / 60)
    print(f"   ETA: ~{eta} min")
    print(f"{'─'*45}\n")

    leads = state["leads_with_msg"]
    sent = failed = 0

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=WA_SESSION,
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            args=[
                "--no-sandbox", 
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            viewport={"width": 1280, "height": 800},
        )
        page = await ctx.new_page()

        # ── WhatsApp Web open + login ──────────────────
        print("   🌐 WhatsApp Web khul raha hai...")
        try:
            await page.goto("https://web.whatsapp.com", wait_until="load", timeout=120000)
        except Exception as e:
            print(f"   ⚠️ Goto error: {e}")

        # Wait for either QR or Chats to appear with a generous timeout
        print("   ⌛ Waiting for page to initialize...")
        try:
            await page.wait_for_selector('canvas[aria-label="Scan me!"], [data-testid="chat-list"], #pane-side', timeout=60000)
        except:
            pass

        # QR check
        qr_canvas = await page.query_selector('canvas[aria-label="Scan me!"]')
        if qr_canvas:
            print("\n" + "═"*42)
            print("  📱  QR CODE SCAN KARO!")
            print("  WhatsApp → Linked Devices → Link a Device")
            print("═"*42 + "\n")
            try:
                await page.wait_for_selector('[data-testid="chat-list"], #pane-side', timeout=120000)
                print("  ✅ Logged in!\n")
                await asyncio.sleep(5)
            except PWTimeout:
                print("  ❌ Login timeout. Please try again.")
                await ctx.close()
                state["sent_count"] = 0
                state["failed_count"] = len(leads)
                return state
        else:
            try:
                await page.wait_for_selector('[data-testid="chat-list"], #pane-side', timeout=30000)
                print("  ✅ Logged in (Session found)\n")
            except:
                print("  ⚠️ Session detection slow, attempting to proceed...")
                await asyncio.sleep(5)

        # ── Send loop ──────────────────────────────────
        for i, lead in enumerate(leads):
            phone   = lead.get("phone", "")
            message = lead.get("message", "")
            name    = lead.get("name", "")

            print(f"  [{i+1:02d}/{len(leads)}] {name[:30]:<30} {phone}", end="  ", flush=True)

            attachment = lead.get("attachment")
            ok = await _send(page, phone, message, attachment)

            if ok:
                sent += 1
                _update_status(phone, "sent")
                print("✅")
            else:
                failed += 1
                _update_status(phone, "failed")
                print("❌")

            if i < len(leads) - 1:
                for s in range(DELAY_SEC, 0, -1):
                    print(f"  ⏱  {s}s...   ", end="\r", flush=True)
                    await asyncio.sleep(1)
                print(" " * 20, end="\r")

        await ctx.close()

    state["sent_count"]   = sent
    state["failed_count"] = failed

    print(f"\n  {'═'*38}")
    print(f"  ✅ Sent:   {sent}")
    print(f"  ❌ Failed: {failed}")
    print(f"  {'═'*38}")
    return state


async def _send(page, phone: str, message: str, attachment_path: str = None) -> bool:
    import os
    try:
        clean = re.sub(r"\D", "", phone)
        if len(clean) == 10:
            clean = "91" + clean
            
        print(f" (Routing to {clean}...) ", end="", flush=True)

        url = f"https://web.whatsapp.com/send?phone={clean}"
        print(f"   🌐 Opening WhatsApp link for {clean}...")
        await page.goto(url, timeout=60000)
        print("   ✅ Page loaded")
        await page.wait_for_timeout(5000)
        
        msg_box_selector = 'div[contenteditable="true"][data-tab="10"], div[contenteditable="true"]'
        try:
            await page.wait_for_selector(msg_box_selector, timeout=25000)
        except:
            if "invalid" in ((await page.content()).lower()):
                print(" (Invalid #) ", end="")
                return False
            return False

        await asyncio.sleep(2)
        msg_box = await page.query_selector(msg_box_selector)
        if not msg_box: return False

        if attachment_path and os.path.exists(attachment_path):
            abs_path = os.path.abspath(attachment_path)
            
            attach_btn = await page.wait_for_selector('div[title="Attach"], [data-testid="clip"], [data-icon="plus"]', timeout=5000)
            if attach_btn:
                await attach_btn.click()
                await asyncio.sleep(1)
                
                file_input = await page.wait_for_selector('input[type="file"]', timeout=5000)
                await file_input.set_input_files(abs_path)
                
                caption_box_selector = 'div[contenteditable="true"][data-tab="6"], div[role="textbox"]'
                await page.wait_for_selector(caption_box_selector, timeout=15000)
                await asyncio.sleep(1)
                
                await page.fill(caption_box_selector, message)
                await asyncio.sleep(1)
                
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                return True
        
        await msg_box.fill(message)
        await asyncio.sleep(1)
        
        send_btn = await page.query_selector('span[data-icon="send"], [data-testid="send"]')
        if send_btn:
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")
            
        await asyncio.sleep(2)
        return True
        
    except Exception as e:
        print(f" (Protocol Error: {e})", end="")
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
    except Exception:
        pass
