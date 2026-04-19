"""
AGENT 1 — SCRAPER (SerpApi Version)
Using SerpApi to search Google Maps and extract business leads.
Reliable, fast, and no browser needed.
"""

import os
import json
import re
from serpapi import GoogleSearch
from graph.state import AgentState
from dotenv import load_dotenv

load_dotenv()

JSON_FILE = "leads.json"
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

async def scraper_agent(state: AgentState) -> AgentState:
    try:
        leads = await scrape_maps(
            state["category"], 
            state["location"], 
            state.get("limit", 10)
        )
    except Exception as e:
        print(f"   ❌ Scraper crashed: {e}")
        leads = []
    
    state["raw_leads"] = leads
    return state

async def scrape_maps(category: str, location: str, limit: int = 10, progress_cb=None) -> list:
    print(f"\n{'─'*45}")
    print(f"🔍 SERPAPI SEARCH: '{category}' in '{location}' (Limit: {limit})")
    print(f"{'─'*45}")

    if not SERPAPI_KEY:
        print("   ❌ ERROR: SERPAPI_KEY not found in environment!")
        if progress_cb:
            progress_cb("SYSTEM_STATUS", "Error: SerpApi Key Missing")
        return []

    if progress_cb:
        progress_cb("SYSTEM_STATUS", f"Searching Google Maps for '{category}'...")

    params = {
        "engine": "google_maps",
        "q": f"{category} in {location}",
        "type": "search",
        "api_key": SERPAPI_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        local_results = results.get("local_results", [])
        
        print(f"   ✅ Found {len(local_results)} results initially")
        
        leads = []
        for idx, item in enumerate(local_results):
            if len(leads) >= limit:
                break
                
            lead = {
                "name": item.get("title"),
                "phone": item.get("phone"),
                "address": item.get("address"),
                "rating": item.get("rating"),
                "website": item.get("website"),
                "has_website": item.get("website") is not None,
                "category": category,
                "location": location,
                "status": "pending"
            }
            
            if lead["phone"]:
                # Normalize phone
                lead["phone"] = _fmt(lead["phone"])
                
                if lead["phone"]:
                    leads.append(lead)
                    print(f"   ✅ [{len(leads):02d}] {lead['name'][:35]:<35} {lead['phone']}")
                    if progress_cb:
                        progress_cb(lead["name"], lead["phone"])

        # Final progress update
        if progress_cb:
            progress_cb("SYSTEM_STATUS", f"Extracted {len(leads)} leads successfully.")

        _save_json(leads)
        return leads

    except Exception as e:
        print(f"   ❌ SerpApi Error: {e}")
        if progress_cb:
            progress_cb("SYSTEM_STATUS", f"Search failed: {str(e)[:50]}")
        return []

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
