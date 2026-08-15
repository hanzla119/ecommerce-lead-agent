import os
import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import BASE_DIR, OUTPUT_DIR, DEFAULT_REGIONS, DEFAULT_NICHES, SENDER_EMAIL, GMAIL_APP_PASSWORD
from scraper.store_finder import find_shopify_stores
from scraper.instagram_finder import find_instagram_brands
from scraper.contact_enricher import enrich_store_contacts
from scraper.email_verifier import verify_email_deliverability
from auditor.store_auditor import audit_store_frontend
from agent.pitch_generator import generate_personalized_pitches
from agent.email_sender import send_outreach_email
from exporter.excel_exporter import export_leads_to_files

app = FastAPI(title="AI E-Commerce Lead Gen & Outreach Dashboard")

# Static directory
STATIC_DIR = BASE_DIR / "dashboard" / "static"
try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Thread lock for thread-safe status updates
status_lock = threading.Lock()

agent_status = {
    "is_running": False,
    "progress": 0,
    "total": 0,
    "current_step": "Idle",
    "logs": []
}

def load_leads_from_csv() -> List[Dict]:
    """Reads latest leads from CSV or returns empty list."""
    latest_csv = OUTPUT_DIR / "leads_latest.csv"
    if not latest_csv.exists():
        return []
    try:
        df = pd.read_csv(latest_csv, encoding="utf-8-sig")
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

def save_leads_to_csv(leads: List[Dict]):
    """Overwrites leads_latest.csv and leads_latest.xlsx with updated lead list."""
    if not leads:
        return
    df = pd.DataFrame(leads)
    latest_csv = OUTPUT_DIR / "leads_latest.csv"
    latest_excel = OUTPUT_DIR / "leads_latest.xlsx"
    df.to_csv(latest_csv, index=False, encoding="utf-8-sig")
    try:
        with pd.ExcelWriter(latest_excel, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Leads")
    except Exception:
        pass

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"status": "Dashboard frontend is ready"})

@app.get("/api/leads")
def get_leads():
    leads = load_leads_from_csv()
    return {"leads": leads, "count": len(leads)}

@app.get("/api/stats")
def get_stats():
    leads = load_leads_from_csv()
    if not leads:
        return {
            "total_leads": 0,
            "emails_found": 0,
            "linkedin_found": 0,
            "missing_pixels": 0,
            "high_opportunity": 0
        }
    
    total = len(leads)
    emails = sum(1 for l in leads if l.get("Contact Email"))
    linkedin = sum(1 for l in leads if l.get("Founder LinkedIn Profile"))
    missing_pixels = sum(1 for l in leads if "MISSING" in str(l.get("Meta Pixel Active", "")) or "MISSING" in str(l.get("TikTok Pixel Active", "")))
    high_opp = sum(1 for l in leads if (l.get("Contact Email") or l.get("Founder LinkedIn Profile")) and missing_pixels > 0)
    
    return {
        "total_leads": total,
        "emails_found": emails,
        "linkedin_found": linkedin,
        "missing_pixels": missing_pixels,
        "high_opportunity": high_opp
    }

class SearchRequest(BaseModel):
    niche: str
    region: str = "UK"
    count: int = 10
    source: str = "web"  # "web" or "instagram"

def process_single_store_worker(store_info: Dict, region: str) -> Optional[Dict]:
    """Worker function executed in parallel threads."""
    url = store_info.get("url", "")
    known_ig = store_info.get("instagram", "")
    known_handle = store_info.get("instagram_handle", "")
    known_brand = store_info.get("brand_name", "")
    
    try:
        # 1. Audit store
        audit = audit_store_frontend(url)
        
        # 2. Enrich contacts
        contacts = enrich_store_contacts(url, region=region)
        if known_ig and not contacts["instagram"]:
            contacts["instagram"] = known_ig
            contacts["instagram_handle"] = known_handle
        if known_brand and not contacts["brand_name"]:
            contacts["brand_name"] = known_brand
            
        brand = contacts.get("brand_name", "") or known_brand or url
        
        # 3. Email MX Deliverability Verification
        primary_email = contacts.get("email", "")
        if primary_email:
            verify_res = verify_email_deliverability(primary_email)
            contacts["email_deliverability"] = verify_res.get("status", "Unknown")
            contacts["is_deliverable"] = verify_res.get("mx_found", False)
        else:
            contacts["email_deliverability"] = "No Email"
            contacts["is_deliverable"] = False

        # 4. AI Pitch Generator
        pitches = generate_personalized_pitches(
            brand_name=brand,
            store_url=url,
            region=region,
            contact_data=contacts,
            audit_data=audit
        )
        
        return {
            "url": url,
            "region": region,
            "contacts": contacts,
            "audit": audit,
            "pitches": pitches
        }
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def background_lead_generation(niche: str, region: str, count: int, source: str = "web"):
    global agent_status
    with status_lock:
        agent_status["is_running"] = True
        agent_status["progress"] = 0
        agent_status["total"] = count
        agent_status["current_step"] = f"Discovering {source.upper()} leads for '{niche}' in {region}..."
        agent_status["logs"] = [f"🚀 Starting parallel AI Discovery ({source.upper()}) for '{niche}' ({region})"]
    
    try:
        candidates = []
        if source == "instagram":
            ig_brands = find_instagram_brands(niche=niche, region=region, max_results=count)
            for b in ig_brands:
                candidates.append({
                    "url": b["store_url"],
                    "brand_name": b["brand_name"],
                    "instagram": b["instagram_url"],
                    "instagram_handle": b["instagram_handle"]
                })
        else:
            stores = find_shopify_stores(niche=niche, region=region, max_results=count)
            for s in stores:
                candidates.append({"url": s})
                
        if not candidates:
            with status_lock:
                agent_status["logs"].append("No stores found with this query. Try adjusting keywords.")
                agent_status["is_running"] = False
            return
            
        with status_lock:
            agent_status["logs"].append(f"✅ Found {len(candidates)} brand candidates. Launching 8 parallel worker threads...")
            
        new_leads = []
        # Multi-threaded parallel processing (8 concurrent workers)
        max_workers = min(8, len(candidates))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cand = {
                executor.submit(process_single_store_worker, cand, region): cand for cand in candidates
            }
            
            completed_count = 0
            for future in as_completed(future_to_cand):
                completed_count += 1
                lead_res = future.result()
                if lead_res:
                    new_leads.append(lead_res)
                    brand_name = lead_res["contacts"].get("brand_name") or lead_res["url"]
                    email = lead_res["contacts"].get("email") or "No email"
                    email_status = lead_res["contacts"].get("email_deliverability", "")
                    founder = lead_res["contacts"].get("founder_name") or "Founder"
                    
                    with status_lock:
                        agent_status["progress"] = completed_count
                        agent_status["current_step"] = f"Processed {completed_count}/{len(candidates)}: {brand_name}"
                        agent_status["logs"].append(f"✓ [{completed_count}/{len(candidates)}] {brand_name} (Email: {email} [{email_status}], Founder: {founder})")
                else:
                    with status_lock:
                        agent_status["progress"] = completed_count
                        
        # Export all new leads
        if new_leads:
            export_leads_to_files(new_leads, filename_prefix=f"{source}_{niche.replace(' ', '_')}_{region}")
            with status_lock:
                agent_status["logs"].append(f"🎉 Successfully exported {len(new_leads)} enriched leads to spreadsheet in under 2 minutes!")
                
    except Exception as e:
        with status_lock:
            agent_status["logs"].append(f"Pipeline error: {e}")
    finally:
        with status_lock:
            agent_status["is_running"] = False
            agent_status["current_step"] = "Completed"

@app.post("/api/run")
def trigger_search(req: SearchRequest, background_tasks: BackgroundTasks):
    global agent_status
    if agent_status["is_running"]:
        raise HTTPException(status_code=400, detail="Agent is already running a task.")
    
    background_tasks.add_task(background_lead_generation, req.niche, req.region, req.count, req.source)
    return {"status": "Started", "message": f"Agent is discovering {req.count} leads ({req.source.upper()}) for '{req.niche}' in {req.region}"}

@app.get("/api/status")
def get_agent_status():
    return agent_status

class AuditSingleRequest(BaseModel):
    url: str
    region: str = "UK"

@app.post("/api/audit-single")
def audit_single(req: AuditSingleRequest):
    url = req.url.strip()
    if not url.startswith("http"):
        url = "https://" + url
        
    audit = audit_store_frontend(url)
    contacts = enrich_store_contacts(url, region=req.region)
    primary_email = contacts.get("email", "")
    if primary_email:
        verify_res = verify_email_deliverability(primary_email)
        contacts["email_deliverability"] = verify_res.get("status", "Unknown")
        contacts["is_deliverable"] = verify_res.get("mx_found", False)
        
    brand = contacts.get("brand_name", "") or url
    pitches = generate_personalized_pitches(
        brand_name=brand,
        store_url=url,
        region=req.region,
        contact_data=contacts,
        audit_data=audit
    )
    
    lead_data = {
        "url": url,
        "region": req.region,
        "contacts": contacts,
        "audit": audit,
        "pitches": pitches
    }
    
    # Save to file
    res = export_leads_to_files([lead_data], filename_prefix="single_audit")
    return {"lead": lead_data, "export": res}

class UpdateStatusRequest(BaseModel):
    store_url: str
    new_status: str

@app.post("/api/update-status")
def update_status(req: UpdateStatusRequest):
    leads = load_leads_from_csv()
    updated = False
    for l in leads:
        if l.get("Store URL") == req.store_url:
            l["Outreach Status"] = req.new_status
            updated = True
            break
    if updated:
        save_leads_to_csv(leads)
        return {"status": "success", "message": "Lead status updated"}
    return {"status": "not_found", "message": "Lead not found"}

@app.get("/api/download/excel")
def download_excel():
    excel_file = OUTPUT_DIR / "leads_latest.xlsx"
    if excel_file.exists():
        return FileResponse(
            str(excel_file), 
            filename="ecommerce_leads_latest.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    raise HTTPException(status_code=404, detail="No Excel file generated yet.")

@app.get("/api/download/csv")
def download_csv():
    csv_file = OUTPUT_DIR / "leads_latest.csv"
    if csv_file.exists():
        return FileResponse(
            str(csv_file), 
            filename="ecommerce_leads_latest.csv",
            media_type="text/csv"
        )
    raise HTTPException(status_code=404, detail="No CSV file generated yet.")

class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    store_url: Optional[str] = ""
    sender_email: Optional[str] = ""
    app_password: Optional[str] = ""

@app.post("/api/send-email")
def send_email_endpoint(req: SendEmailRequest):
    # Retrieve current configured values
    sender = req.sender_email or os.environ.get("SENDER_EMAIL", SENDER_EMAIL)
    pwd = req.app_password or os.environ.get("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD)
    
    result = send_outreach_email(
        to_email=req.to_email,
        subject=req.subject,
        body_text=req.body,
        sender_email=sender,
        app_password=pwd
    )
    
    if result.get("success"):
        # Update lead status to 'Email Sent (Contacted)'
        if req.store_url:
            leads = load_leads_from_csv()
            for l in leads:
                if l.get("Store URL") == req.store_url:
                    l["Outreach Status"] = "Contacted"
                    break
            save_leads_to_csv(leads)
            
        return {"status": "success", "message": result.get("message")}
    else:
        raise HTTPException(status_code=400, detail=result.get("error"))

class SMTPSettingsRequest(BaseModel):
    sender_email: str
    app_password: str

@app.post("/api/save-smtp-settings")
def save_smtp_settings(req: SMTPSettingsRequest):
    os.environ["SENDER_EMAIL"] = req.sender_email.strip()
    os.environ["GMAIL_APP_PASSWORD"] = req.app_password.strip()
    
    # Save to .env in workspace for persistence
    env_file = BASE_DIR / ".env"
    with open(env_file, "w") as f:
        f.write(f"SENDER_EMAIL={req.sender_email.strip()}\n")
        f.write(f"GMAIL_APP_PASSWORD={req.app_password.strip()}\n")
        
    return {"status": "success", "message": "Email settings saved successfully!"}

@app.get("/api/get-smtp-settings")
def get_smtp_settings():
    sender = os.environ.get("SENDER_EMAIL", SENDER_EMAIL)
    has_pwd = bool(os.environ.get("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD))
    return {
        "sender_email": sender,
        "is_configured": has_pwd
    }
