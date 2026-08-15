"""
Model Context Protocol (MCP) Server for E-Commerce Lead Generation & Store Auditing.
Exposes standard MCP tools that any LLM (Gemini, Claude, Antigravity) can call autonomously.
"""
from typing import Dict, List
from mcp.server.fastmcp import FastMCP
from scraper.store_finder import find_shopify_stores
from scraper.contact_enricher import enrich_store_contacts, find_founder_linkedin
from auditor.store_auditor import audit_store_frontend
from agent.pitch_generator import generate_personalized_pitches
from exporter.excel_exporter import export_leads_to_files

# Initialize MCP Server
mcp = FastMCP("Ecommerce-Lead-Outreach-Agent")

@mcp.tool()
def search_stores(niche: str, region: str = "UK", max_results: int = 10) -> List[str]:
    """
    Discovers live Shopify and e-commerce stores in a specific niche and country (UK, US, Australia, Europe).
    """
    return find_shopify_stores(niche=niche, region=region, max_results=max_results)

@mcp.tool()
def extract_contacts_and_linkedin(store_url: str, region: str = "UK") -> Dict:
    """
    Crawls a store to extract contact emails, social links (Instagram/TikTok/Facebook), and finds the Founder's LinkedIn profile.
    """
    return enrich_store_contacts(store_url=store_url, region=region)

@mcp.tool()
def audit_ecommerce_store(store_url: str) -> Dict:
    """
    Audits an e-commerce website for platform, Meta pixel, TikTok pixel, GA4/GTM, Klaviyo, and CRO gaps.
    """
    return audit_store_frontend(store_url=store_url)

@mcp.tool()
def generate_ai_pitches(brand_name: str, store_url: str, region: str, contact_data: Dict, audit_data: Dict) -> Dict[str, str]:
    """
    Uses Gemini AI to generate 3 hyper-personalized pitches: Cold Email, LinkedIn Connection Note, and Instagram DM.
    """
    return generate_personalized_pitches(
        brand_name=brand_name,
        store_url=store_url,
        region=region,
        contact_data=contact_data,
        audit_data=audit_data
    )

@mcp.tool()
def export_leads_to_spreadsheet(leads: List[Dict]) -> Dict[str, str]:
    """
    Exports all enriched leads with their audit findings and custom pitches to Excel (.xlsx) and CSV files.
    """
    return export_leads_to_files(leads=leads)

if __name__ == "__main__":
    mcp.run()
