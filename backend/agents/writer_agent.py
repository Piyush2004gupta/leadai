"""
AGENT 3 — WRITER
Fixed prompt template use karo — OpenAI se message personalize karo.
Base message: "I am Make best AI Integrated website for you"
"""

import json, sys, io
import requests
from graph.state import AgentState
from ollama_utils import generate_text

# Fix for Windows Unicode printing errors
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


import os
OLLAMA_MODEL = "tinyllama"
JSON_FILE    = "leads.json"

# ── Fixed base message (as requested) ─────────────────────────
BASE_MSG = "Hi! I came across your business and noticed you’re not using AI automation yet. I help businesses like yours get more leads and save time by building AI-integrated websites (auto replies, lead capture, WhatsApp automation, etc.) Would you be open to a quick demo? It can genuinely help you get more customers"


def writer_agent(state: AgentState) -> AgentState:
    leads_with_msg = write_messages(state["raw_leads"], state["category"], state["location"], state.get("base_message"))
    state["leads_with_msg"] = leads_with_msg
    return state


def write_messages(leads: list, category: str, location: str, base_message: str = None) -> list:
    print(f"\n{'─'*45}")
    print(f"✍️   WRITING: {len(leads)} messages")
    print(f"{'─'*45}")

    results = []
    for i, lead in enumerate(leads):
        print(f"   [{i+1:02d}] {lead['name'][:35]}...", end=" ", flush=True)
        message = _write_message(lead, base_message)
        lead["message"] = message
        results.append(lead)
        print("✅")

    _update_json(results)
    return results


def _write_message(lead: dict, base_msg: str = None) -> str:
    """
    If user provides a message, use it EXACTLY.
    Otherwise, use OpenAI for AI personalization.
    """
    name     = lead.get("name", "your business")
    category = lead.get("category", "business")
    location = lead.get("location", "")

    # If user gave a specific message, don't let AI mess with it.
    if base_msg:
        return f"Hello {name},\n\n{base_msg}"

    # AI Personalized Message logic (only if no user message)
    target_msg = BASE_MSG
    prompt = f"""Generate a cold outreach message for:
    Category: {category}
    Location: {location}
    Business Name: {name} (keep it professional and very short)
    MUST include this core offer: "{target_msg}" """

    try:
        msg = generate_text(prompt, model_name=OLLAMA_MODEL)
        if msg and target_msg.lower() in msg.lower():
            return msg.strip()
    except:
        pass

    return f"Hello {name},\n\n{target_msg} — specially designed for {category} in {location}."


def _fallback(lead: dict, target_msg: str) -> str:
    name     = lead.get("name", "your business")
    category = lead.get("category", "business")
    location = lead.get("location", "")
    return (
        f"Hello {name},\n\n"
        f"{target_msg} — specially designed for {category} businesses in {location}.\n\n"
        f"Interested? Reply YES"
    )


def _update_json(leads: list):
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            all_leads = json.load(f)
    except Exception:
        all_leads = leads

    phones  = {l["phone"] for l in leads}
    updated = []
    for l in all_leads:
        if l.get("phone") in phones:
            match = next((x for x in leads if x["phone"] == l["phone"]), None)
            updated.append(match if match else l)
        else:
            updated.append(l)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)
