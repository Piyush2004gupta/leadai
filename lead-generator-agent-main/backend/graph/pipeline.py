"""
LANGGRAPH PIPELINE — 4 agents connected.

START → scraper → analyzer → writer → outreach → END
"""

from langgraph.graph import StateGraph, END
from graph.state             import AgentState
from agents.scraper_agent    import scraper_agent
from agents.analyzer_agent   import analyzer_agent
from agents.writer_agent     import writer_agent
from agents.outreach_agent   import outreach_agent


def _check_leads(state: AgentState) -> str:
    if not state.get("raw_leads"):
        print("\n❌ Koi leads nahi — pipeline stop")
        return "end"
    return "next"


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("scraper",  scraper_agent)
    g.add_node("analyzer", analyzer_agent)
    g.add_node("writer",   writer_agent)
    g.add_node("outreach", outreach_agent)

    g.set_entry_point("scraper")

    # Scraper ke baad check karo leads mile ya nahi
    g.add_conditional_edges(
        "scraper",
        _check_leads,
        {"next": "analyzer", "end": END}
    )

    g.add_edge("analyzer", "writer")
    g.add_edge("writer",   "outreach")
    g.add_edge("outreach", END)

    return g.compile()
