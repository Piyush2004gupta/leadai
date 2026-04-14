"""
AGENT 4 — OUTREACH
Playwright se WhatsApp Web kholo.
Har lead ko message bhejo — 10 second delay.
Status leads.json mein update hoti hai.
"""

import time, json, urllib.parse, sys, io, re
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
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


def outreach_agent(state: AgentState) -> AgentState:
    print(f"\n{'─'*45}")
    print(f"📲  AGENT 4 — OUTREACH  (WhatsApp Web)")
    print(f"   {len(state['leads_with_msg'])} messages bheje jaayenge")
    print(f"   Delay: {DELAY_SEC}s between each")
    eta = round(len(state['leads_with_msg']) * (DELAY_SEC + 6) / 60)
    print(f"   ETA: ~{eta} min")
    print(f"{'─'*45}\n")

    leads = state["leads_with_msg"]
    sent = failed = 0

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=WA_SESSION,
            headless=False,
            args=[
                "--no-sandbox", 
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()

        # ── WhatsApp Web open + login ──────────────────
        print("   🌐 WhatsApp Web khul raha hai...")
        try:
            page.goto("https://web.whatsapp.com", wait_until="load", timeout=120000)
        except Exception as e:
            print(f"   ⚠️ Goto error: {e}")

        # Wait for either QR or Chats to appear with a generous timeout
        print("   ⌛ Waiting for page to initialize...")
        try:
            # WhatsApp indices: Canvas for QR, div[title="Chats"] or div#pane-side for logged in
            page.wait_for_selector('canvas[aria-label="Scan me!"], [data-testid="chat-list"], #pane-side', timeout=60000)
        except:
            pass

        # QR check
        qr_canvas = page.query_selector('canvas[aria-label="Scan me!"]')
        if qr_canvas:
            print("\n" + "═"*42)
            print("  📱  QR CODE SCAN KARO!")
            print("  WhatsApp → Linked Devices → Link a Device")
            print("═"*42 + "\n")
            try:
                # Wait for login success
                page.wait_for_selector('[data-testid="chat-list"], #pane-side', timeout=120000)
                print("  ✅ Logged in!\n")
                time.sleep(5) # Give it extra time to sync
            except PWTimeout:
                print("  ❌ Login timeout. Please try again.")
                ctx.close()
                state["sent_count"] = 0
                state["failed_count"] = len(leads)
                return state
        else:
            # Verify if actually logged in
            try:
                page.wait_for_selector('[data-testid="chat-list"], #pane-side', timeout=30000)
                print("  ✅ Logged in (Session found)\n")
            except:
                print("  ⚠️ Session detection slow, attempting to proceed...")
                time.sleep(5)

        # ── Send loop ──────────────────────────────────
        for i, lead in enumerate(leads):
            phone   = lead.get("phone", "")
            message = lead.get("message", "")
            name    = lead.get("name", "")

            print(f"  [{i+1:02d}/{len(leads)}] {name[:30]:<30} {phone}", end="  ", flush=True)

            # Attempt send
            attachment = lead.get("attachment")
            ok = _send(page, phone, message, attachment)

            if ok:
                sent += 1
                _update_status(phone, "sent")
                print("✅")
            else:
                failed += 1
                _update_status(phone, "failed")
                print("❌")

            # X second delay
            if i < len(leads) - 1:
                for s in range(DELAY_SEC, 0, -1):
                    print(f"  ⏱  {s}s...   ", end="\r", flush=True)
                    time.sleep(1)
                print(" " * 20, end="\r")

        ctx.close()

    state["sent_count"]   = sent
    state["failed_count"] = failed

    print(f"\n  {'═'*38}")
    print(f"  ✅ Sent:   {sent}")
    print(f"  ❌ Failed: {failed}")
    print(f"  {'═'*38}")
    return state


def _send(page, phone: str, message: str, attachment_path: str = None) -> bool:
    import os
    try:
        # Pura saaf number: sirf digits rakho
        clean = re.sub(r"\D", "", phone)
        if len(clean) == 10:
            clean = "91" + clean
            
        print(f" (Routing to {clean}...) ", end="", flush=True)

        # ── 1. Load Chat via Direct URL (The most reliable way) ─────
        url = f"https://web.whatsapp.com/send?phone={clean}"
        page.goto(url, wait_until="load", timeout=60000)
        
        # ── 2. Wait for Message Box ────────────────────────────────
        # We look for the main message box
        msg_box_selector = 'div[contenteditable="true"][data-tab="10"], div[contenteditable="true"]'
        try:
            page.wait_for_selector(msg_box_selector, timeout=25000)
        except:
            # Check if "Phone number shared via url is invalid" showed up
            if "invalid" in (page.content().lower()):
                print(" (Invalid #) ", end="")
                return False
            return False

        time.sleep(2) # Stability pause
        msg_box = page.query_selector(msg_box_selector)
        if not msg_box: return False

        # ── 3. Handle Attachment if present ────────────────────────
        if attachment_path and os.path.exists(attachment_path):
            abs_path = os.path.abspath(attachment_path)
            
            # Click Attach (+) button
            attach_btn = page.wait_for_selector('div[title="Attach"], [data-testid="clip"], [data-icon="plus"]', timeout=5000)
            if attach_btn:
                attach_btn.click()
                time.sleep(1)
                
                # Target the file input that accepts media (usually the first one)
                file_input = page.wait_for_selector('input[type="file"]', timeout=5000)
                file_input.set_input_files(abs_path)
                
                # Wait for the "Preview/Caption" screen to appear
                caption_box_selector = 'div[contenteditable="true"][data-tab="6"], div[role="textbox"]'
                page.wait_for_selector(caption_box_selector, timeout=15000)
                time.sleep(1)
                
                # Fill the message as a caption
                page.fill(caption_box_selector, message)
                time.sleep(1)
                
                # Press Enter to send the attachment + caption
                page.keyboard.press("Enter")
                time.sleep(3)
                return True
        
        # ── 4. Normal Text Send ────────────────────────────────────
        msg_box.fill(message)
        time.sleep(1)
        
        # We also check for the "Send" arrow button to be dual-safe
        send_btn = page.query_selector('span[data-icon="send"], [data-testid="send"]')
        if send_btn:
            send_btn.click()
        else:
            page.keyboard.press("Enter")
            
        time.sleep(2)
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
