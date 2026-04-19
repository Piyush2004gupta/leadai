"""
BACKEND — FastAPI Server
Frontend se requests aati hain, agent pipeline trigger hoti hai.
"""

import json
import os
import asyncio
import uuid
import sys
from datetime import datetime
import shutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="LeadAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: dict[str, dict] = {}
LEADS_FILE = "leads.json"


class RunRequest(BaseModel):
    category: str
    location: str
    limit:    int | None = 5
    base_message: str | None = None
    prompt:   str | None = None
    city:     str | None = None
    script:   str | None = None


@app.get("/")
def root():
    return {"status": "LeadAgent API running"}

@app.head("/")
def head():
    return {}

@app.get("/health")
def health():
    return {"ok": True}


@app.post("/run")
async def start_agent(
    bg: BackgroundTasks,
    category: str = Form(...),
    location: str = Form(...),
    limit: int = Form(...),
    base_message: str = Form(None),
    file: UploadFile = File(None)
):
    job_id = str(uuid.uuid4())

    file_path = None
    if file:
        os.makedirs("uploads", exist_ok=True)
        file_path = os.path.join("uploads", f"{job_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    JOBS[job_id] = {
        "id":        job_id,
        "category":  category,
        "location":  location,
        "limit":     limit,
        "status":    "queued",
        "progress":  0,
        "logs":      [],
        "stats":     {},
        "created_at": datetime.now().isoformat(),
        "attachment": file_path
    }
    bg.add_task(run_pipeline, job_id, category, location, limit, base_message, file_path)
    return {"job_id": job_id, "message": "Agent started"}


@app.post("/run-agent")
async def start_agent_json(bg: BackgroundTasks, req: RunRequest):
    category = req.category
    location = req.location or req.city
    base_msg = req.base_message or req.script

    if not category or not location:
        return {"error": "category and location (or city) are required"}

    job_id = str(uuid.uuid4())
    limit = req.limit if req.limit else 5

    JOBS[job_id] = {
        "id":        job_id,
        "category":  category,
        "location":  location,
        "limit":     limit,
        "status":    "queued",
        "progress":  0,
        "logs":      [],
        "stats":     {},
        "created_at": datetime.now().isoformat(),
    }
    bg.add_task(run_pipeline, job_id, category, location, limit, base_msg, None)
    return {"job_id": job_id, "message": "Agent started from JSON"}


@app.get("/job/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return {"error": "Job not found"}
    return job


@app.get("/leads")
def get_leads():
    try:
        with open(LEADS_FILE) as f:
            leads = json.load(f)
        return {"leads": leads, "total": len(leads)}
    except Exception:
        return {"leads": [], "total": 0}


@app.get("/stats")
def get_stats():
    try:
        with open(LEADS_FILE) as f:
            leads = json.load(f)
        stats = {"total": len(leads), "pending": 0, "sent": 0, "failed": 0}
        for l in leads:
            s = l.get("status", "pending")
            stats[s] = stats.get(s, 0) + 1
        return stats
    except Exception:
        return {"total": 0, "pending": 0, "sent": 0, "failed": 0}


@app.post("/send")
async def send_messages(bg: BackgroundTasks):
    job_id = "SEND-" + str(uuid.uuid4())[:4]
    JOBS[job_id] = {
        "id":        job_id,
        "status":    "sending",
        "progress":  0,
        "logs":      [],
        "created_at": datetime.now().isoformat(),
    }
    bg.add_task(run_outreach_pipeline, job_id)
    return {"job_id": job_id, "message": "Outreach started"}


async def run_outreach_pipeline(job_id: str):
    def log(msg: str, progress: int = None):
        JOBS[job_id]["logs"].append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
        if progress is not None:
            JOBS[job_id]["progress"] = progress
        print(f"[{job_id}] {msg}")

    try:
        from agents.outreach_agent import outreach_agent
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            leads = json.load(f)

        pending = [l for l in leads if l.get("status") == "pending" and l.get("message")]

        if not pending:
            log("❌ No pending leads with messages found.", 100)
            JOBS[job_id]["status"] = "done"
            return

        log(f"📲 Starting outreach for {len(pending)} leads...", 10)
        log("🌐 Opening WhatsApp Web...", 20)

        state = {"leads_with_msg": pending}
        result = await outreach_agent(state)

        log(f"✅ Done! Sent: {result.get('sent_count', 0)}, Failed: {result.get('failed_count', 0)}", 100)
        JOBS[job_id]["status"] = "done"
    except Exception as e:
        log(f"❌ Error: {str(e)}", 100)
        JOBS[job_id]["status"] = "error"


@app.delete("/leads/reset")
def reset_leads():
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    return {"ok": True}


# ── Background pipeline ───────────────────────────────────────

async def run_pipeline(job_id: str, category: str, location: str, limit: int, base_message: str = None, attachment: str = None):

    def log(msg: str, progress: int = None):
        JOBS[job_id]["logs"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "msg":  msg
        })
        if progress is not None:
            JOBS[job_id]["progress"] = progress
        print(f"[{job_id}] {msg}")

    try:
        JOBS[job_id]["status"] = "scraping"
        log(f"🕷 Scraping Google Maps: '{category}' in '{location}'", 10)

        from agents.scraper_agent  import scrape_maps
        from agents.analyzer_agent import analyze_leads
        from agents.writer_agent   import write_messages

        # ── KEY FIX: Progress callback jo har lead pe update kare ──
        found_so_far = [0]

        def on_lead_found(lead_name: str, lead_phone: str):
            if lead_name == "SYSTEM_STATUS":
                if "Opening" in lead_phone:
                    log(lead_phone, 12)
                elif "loaded" in lead_phone:
                    log(lead_phone, 18)
                else:
                    log(lead_phone)
                return

            found_so_far[0] += 1
            scrape_progress = min(18 + (found_so_far[0] * 2), 28)
            log(f"✅ Lead {found_so_far[0]}: {lead_name[:30]} — {lead_phone}", scrape_progress)

        raw_leads = await scrape_maps(category, location, limit, progress_cb=on_lead_found)
        log(f"✅ {len(raw_leads)} leads scraped", 30)

        for l in raw_leads:
            l["attachment"] = attachment

        # ── Analyze ───────────────────────────────────────────────
        JOBS[job_id]["status"] = "analyzing"
        log(f"🔍 Analyzing {len(raw_leads)} leads...", 40)
        analyzed = await asyncio.to_thread(analyze_leads, raw_leads)
        log(f"✅ {len(analyzed)} valid leads", 60)

        # ── Write messages ────────────────────────────────────────
        JOBS[job_id]["status"] = "writing"
        log(f"✍️  Writing personalized messages...", 70)
        leads_with_msg = await asyncio.to_thread(write_messages, analyzed, category, location, base_message)
        log(f"✅ Messages ready", 85)

        # ── Save ──────────────────────────────────────────────────
        _merge_json(leads_with_msg)
        log(f"💾 Saved to leads.json", 90)

        script_path = _generate_wa_script(leads_with_msg)
        log(f"📲 WhatsApp script ready: {script_path}", 95)

        JOBS[job_id]["status"]   = "done"
        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["stats"] = {
            "scraped":  len(raw_leads),
            "analyzed": len(analyzed),
            "messages": len(leads_with_msg),
        }
        log(f"🎉 Done! {len(leads_with_msg)} leads ready.")

    except Exception as e:
        JOBS[job_id]["status"] = "error"
        log(f"❌ Error: {e}", 100)
        print(f"[{job_id}] ERROR: {e}")


def _merge_json(leads: list):
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except:
        existing = []

    existing_phones = {l["phone"] for l in existing if l.get("phone")}
    new = [l for l in leads if l.get("phone") not in existing_phones]

    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing + new, f, indent=2, ensure_ascii=False)


def _generate_wa_script(leads: list) -> str:
    lines = [
        "# WhatsApp Sender — apne PC pe run karo",
        "# pip install playwright && playwright install chromium",
        "import time, urllib.parse",
        "from playwright.sync_api import sync_playwright",
        "",
        "LEADS = " + json.dumps([
            {"name": l["name"], "phone": l["phone"], "message": l.get("message", "")}
            for l in leads if l.get("phone") and l.get("message")
        ], indent=2, ensure_ascii=False),
        "",
        "def send():",
        "    with sync_playwright() as p:",
        "        ctx = p.chromium.launch_persistent_context('./wa_session', headless=False)",
        "        page = ctx.new_page()",
        "        page.goto('https://web.whatsapp.com')",
        "        input('WhatsApp mein QR scan karo, phir Enter dabaao...')",
        "        for i, lead in enumerate(LEADS):",
        "            phone = lead['phone'].replace('+','').replace(' ','')",
        "            msg   = urllib.parse.quote(lead['message'])",
        "            page.goto(f'https://web.whatsapp.com/send?phone={phone}&text={msg}')",
        "            page.wait_for_selector('div[contenteditable=\"true\"]', timeout=15000)",
        "            page.keyboard.press('Enter')",
        "            print(f'[{i+1}] Sent to {lead[\"name\"]} ({lead[\"phone\"]})')",
        "            time.sleep(10)",
        "        ctx.close()",
        "",
        "send()",
    ]
    path = "wa_sender.py"
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
