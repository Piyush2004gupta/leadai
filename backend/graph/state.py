from typing import TypedDict

class AgentState(TypedDict):
    category: str        # User input — "Dental Clinic"
    location: str        # User input — "Mumbai"
    limit: int           # User input — "Number of leads"
    raw_leads: list      # Scraper Agent output
    leads_with_msg: list # Writer Agent output
    sent_count: int
    failed_count: int
