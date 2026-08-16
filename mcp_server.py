import json
import sys
from typing import Dict, List, Optional
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scraper.store_finder import find_shopify_stores
from scraper.instagram_finder import find_instagram_brands
from scraper.contact_enricher import enrich_store_contacts
from scraper.email_verifier import verify_email_deliverability
from auditor.store_auditor import audit_store_frontend
from agent.pitch_generator import generate_personalized_pitches
from agent.email_sender import send_outreach_email
from exporter.excel_exporter import export_leads_to_files

def tool_discover_leads(niche: str, region: str = "UK", count: int = 10, source: str = "web") -> str:
    """Discovers e-commerce stores, audits them, extracts verified emails, and generates pitches."""
    if source == "instagram":
        raw_stores = find_instagram_brands(niche, region=region, limit=count)
    else:
        raw_stores = find_shopify_stores(niche, region=region, limit=count)
        
    leads = []
    for s in raw_stores:
        url = s.get("url")
        if not url:
            continue
        audit = audit_store_frontend(url)
        contacts = enrich_store_contacts(url, region=region)
        primary_email = contacts.get("email", "")
        if primary_email:
            verify_res = verify_email_deliverability(primary_email)
            contacts["email_deliverability"] = verify_res.get("status", "Unknown")
            contacts["is_deliverable"] = verify_res.get("mx_found", False)
            
        brand = contacts.get("brand_name", "") or s.get("brand_name", "") or url
        pitches = generate_personalized_pitches(
            brand_name=brand,
            store_url=url,
            region=region,
            contact_data=contacts,
            audit_data=audit
        )
        leads.append({
            "url": url,
            "region": region,
            "contacts": contacts,
            "audit": audit,
            "pitches": pitches
        })
        
    if leads:
        export_leads_to_files(leads, filename_prefix=f"mcp_{niche}")
        
    return json.dumps({"discovered_count": len(leads), "leads": leads}, indent=2)

def tool_audit_store(store_url: str, region: str = "UK") -> str:
    """Performs deep technical conversion and tracking audit on a store."""
    audit = audit_store_frontend(store_url)
    contacts = enrich_store_contacts(store_url, region=region)
    primary_email = contacts.get("email", "")
    if primary_email:
        verify_res = verify_email_deliverability(primary_email)
        contacts["email_deliverability"] = verify_res.get("status", "Unknown")
        contacts["is_deliverable"] = verify_res.get("mx_found", False)
        
    brand = contacts.get("brand_name", "") or store_url
    pitches = generate_personalized_pitches(
        brand_name=brand,
        store_url=store_url,
        region=region,
        contact_data=contacts,
        audit_data=audit
    )
    
    lead_data = {
        "url": store_url,
        "region": region,
        "contacts": contacts,
        "audit": audit,
        "pitches": pitches
    }
    export_leads_to_files([lead_data], filename_prefix="mcp_single_audit")
    return json.dumps(lead_data, indent=2)

def tool_send_email(recipient_email: str, subject: str, body: str) -> str:
    """Sends cold outreach email directly via Gmail SMTP."""
    res = send_outreach_email(
        recipient_email=recipient_email,
        subject=subject,
        body_text=body
    )
    return json.dumps(res, indent=2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "audit" and len(sys.argv) > 2:
            print(tool_audit_store(sys.argv[2]))
        elif cmd == "discover" and len(sys.argv) > 2:
            niche = sys.argv[2]
            reg = sys.argv[3] if len(sys.argv) > 3 else "UK"
            cnt = int(sys.argv[4]) if len(sys.argv) > 4 else 5
            print(tool_discover_leads(niche, reg, cnt))
        else:
            print("MCP Server ready. Available tools: discover, audit, send_email")
    else:
        print("MCP Server ready for integration with Antigravity / Claude Desktop / Cursor.")
