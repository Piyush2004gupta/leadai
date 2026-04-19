"""
AGENT 2 — ANALYZER (OpenAI gpt-4o-mini)
Har lead ko OpenAI se analyze karo —
valid hai ya nahi, pitch type decide karo.
"""

import json, sys, io
import requests
from graph.state import AgentState
from openai_utils import generate_text

# Fix for Windows Unicode printing errors
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


import os
OPENAI_MODEL = "gpt-4o-mini"
JSON_FILE   = "leads.json"


def analyzer_agent(state: AgentState) -> AgentState:
    analyzed = analyze_leads(state["raw_leads"])
    state["raw_leads"] = analyzed
    return state


def analyze_leads(leads: list) -> list:
    print(f"\n{'─'*45}")
    print(f"🔍  ANALYZING: {len(leads)} leads")
    print(f"{'─'*45}")

    analyzed = []
    for i, lead in enumerate(leads):
        if not lead.get("phone"): continue

        print(f"   [{i+1:02d}] {lead['name'][:35]}...", end=" ", flush=True)
        result = _analyze(lead)
        lead["pitch_type"]  = result.get("pitch_type", "new_website")
        lead["is_valid"]    = result.get("is_valid", True)

        if lead["is_valid"]:
            analyzed.append(lead)
            print(f"✅")
        else:
            print(f"⚠️")

    _update_json(analyzed)
    return analyzed


def _analyze(lead: dict) -> dict:
    """OpenAI se lead analyze karo."""
    prompt = f"""Analyze this business lead briefly.
Business: {lead['name']}
Has website: {lead['has_website']}
Rating: {lead.get('rating', 'unknown')}

Reply with JSON only, no extra text:
{{"is_valid": true, "pitch_type": "new_website"}}

pitch_type must be "new_website" if has_website is false,
or "upgrade_website" if has_website is true.
is_valid is true if business seems real and contactable."""

    try:
        text = generate_text(prompt, model_name=OPENAI_MODEL)
        if not text:
            raise Exception("No response from OpenAI")

        # JSON parse karo
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])

    except Exception as e:
        print(f"\n   OpenAI error: {e} — using fallback")

    # Fallback if OpenAI fails
    return {
        "is_valid":   bool(lead.get("phone")),
        "pitch_type": "new_website" if not lead.get("has_website") else "upgrade_website"
    }


def _update_json(leads: list):
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            all_leads = json.load(f)
    except Exception:
        all_leads = leads

    phones = {l["phone"] for l in leads}
    updated = []
    for l in all_leads:
        if l.get("phone") in phones:
            match = next((x for x in leads if x["phone"] == l["phone"]), None)
            updated.append(match if match else l)
        else:
            updated.append(l)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)
