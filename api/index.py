import os
import re
import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd
from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from mangum import Mangum
import sys

# Ensure api directory and project root are in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for p in [str(CURRENT_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from config import BASE_DIR, OUTPUT_DIR, DEFAULT_REGIONS, DEFAULT_NICHES, SENDER_EMAIL, GMAIL_APP_PASSWORD
    from scraper.store_finder import find_shopify_stores
    from scraper.instagram_finder import find_instagram_brands
    from scraper.contact_enricher import enrich_store_contacts
    from scraper.email_verifier import verify_email_deliverability
    from auditor.store_auditor import audit_store_frontend
    from agent.pitch_generator import generate_personalized_pitches
    from agent.email_sender import send_outreach_email
    from exporter.excel_exporter import export_leads_to_files
except Exception as e:
    import traceback
    print(f"Import warning in api/index.py: {e}\n{traceback.format_exc()}")

app = FastAPI(title="Talha Yousaf | AI E-Commerce Lead Gen & Outreach Agent")
router = APIRouter()

status_lock = threading.Lock()

agent_status = {
    "is_running": False,
    "progress": 0,
    "total": 0,
    "current_step": "Idle",
    "logs": []
}

def load_leads_from_csv() -> List[Dict]:
    try:
        paths = [
            OUTPUT_DIR / "leads_latest.csv",
            PROJECT_ROOT / "output" / "leads_latest.csv",
            CURRENT_DIR / "output" / "leads_latest.csv"
        ]
        for p in paths:
            if p.exists():
                df = pd.read_csv(p, encoding="utf-8-sig")
                df = df.fillna("")
                return df.to_dict(orient="records")
        return []
    except Exception as e:
        return []

def save_leads_to_csv(leads: List[Dict]):
    if not leads:
        return
    try:
        df = pd.DataFrame(leads)
        latest_csv = OUTPUT_DIR / "leads_latest.csv"
        latest_excel = OUTPUT_DIR / "leads_latest.xlsx"
        df.to_csv(latest_csv, index=False, encoding="utf-8-sig")
        try:
            with pd.ExcelWriter(latest_excel, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Qualified Leads")
        except Exception:
            pass
    except Exception:
        pass

@app.get("/")
def serve_index():
    for p in [PROJECT_ROOT / "index.html", PROJECT_ROOT / "public" / "index.html", CURRENT_DIR / "index.html"]:
        if p.exists():
            return FileResponse(str(p))
    return JSONResponse({"status": "Dashboard frontend is ready"})

@router.get("/leads")
def get_leads():
    leads = load_leads_from_csv()
    return {"leads": leads, "count": len(leads)}

@router.get("/stats")
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
    count: int = 20
    source: str = "web"

def process_single_store_worker(store_info: Dict, region: str) -> Optional[Dict]:
    url = store_info.get("url")
    if not url:
        return None
        
    known_ig = store_info.get("instagram", "")
    known_handle = store_info.get("instagram_handle", "")
    known_brand = store_info.get("brand_name", "")
    
    try:
        audit = audit_store_frontend(url)
        contacts = enrich_store_contacts(url, region=region)
        if known_ig and not contacts.get("instagram"):
            contacts["instagram"] = known_ig
            contacts["instagram_handle"] = known_handle
        if known_brand and not contacts.get("brand_name"):
            contacts["brand_name"] = known_brand
            
        brand = contacts.get("brand_name", "") or known_brand or url
        primary_email = contacts.get("email", "")
        if primary_email:
            verify_res = verify_email_deliverability(primary_email)
            contacts["email_deliverability"] = verify_res.get("status", "Unknown")
            contacts["is_deliverable"] = verify_res.get("mx_found", False)
        else:
            contacts["email_deliverability"] = "No Email"
            contacts["is_deliverable"] = False

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

def execute_lead_generation(niche: str, region: str, count: int, source: str = "web") -> List[Dict]:
    global agent_status
    with status_lock:
        agent_status["is_running"] = True
        agent_status["progress"] = 0
        agent_status["total"] = count
        agent_status["current_step"] = f"Discovering stores ({source.upper()})..."
        agent_status["logs"] = [f"🚀 Agent started: Finding up to {count} stores for '{niche}' in {region}..."]

    try:
        if source == "instagram":
            raw_stores = find_instagram_brands(niche, region=region, limit=count)
        else:
            raw_stores = find_shopify_stores(niche, region=region, limit=count)
            
        total_discovered = len(raw_stores)
        with status_lock:
            agent_status["total"] = total_discovered
            agent_status["current_step"] = f"Auditing {total_discovered} stores in parallel (20 threads)..."
            agent_status["logs"].append(f"⚡ Discovered {total_discovered} stores. Starting ultra-fast multi-threaded audit (20 workers) & pitch generation...")

        new_leads = []
        max_workers = min(20, max(1, total_discovered))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_store = {
                executor.submit(process_single_store_worker, store, region): store 
                for store in raw_stores
            }
            
            completed_count = 0
            for future in as_completed(future_to_store):
                completed_count += 1
                lead_data = future.result()
                
                with status_lock:
                    agent_status["progress"] = completed_count
                    
                if lead_data:
                    new_leads.append(lead_data)
                    brand = lead_data["contacts"].get("brand_name") or lead_data["url"]
                    has_email = bool(lead_data["contacts"].get("email"))
                    email_tag = f"📧 {lead_data['contacts']['email']} [{lead_data['contacts'].get('email_deliverability', '')}]" if has_email else "⚠️ No Email"
                    ig_tag = f"📷 {lead_data['contacts'].get('instagram_handle')}" if lead_data["contacts"].get("instagram_handle") else ""
                    founder_tag = f"👤 {lead_data['contacts'].get('founder_name')}" if lead_data["contacts"].get("founder_name") else ""
                    
                    with status_lock:
                        agent_status["logs"].append(
                            f"[{completed_count}/{total_discovered}] ✅ {brand} | {email_tag} {founder_tag} {ig_tag}"
                        )

        if new_leads:
            with status_lock:
                agent_status["current_step"] = "Exporting qualified leads..."
            prefix = f"{source}_{niche.replace(' ', '_')}_{region}"
            export_leads_to_files(new_leads, filename_prefix=prefix)
            
            with status_lock:
                agent_status["logs"].append(f"🎉 Successfully enriched and saved {len(new_leads)} qualified leads!")
                
        return new_leads

    except Exception as e:
        with status_lock:
            agent_status["logs"].append(f"Pipeline error: {e}")
        return []
    finally:
        with status_lock:
            agent_status["is_running"] = False
            agent_status["current_step"] = "Completed"

@router.post("/run")
def trigger_search(req: SearchRequest, background_tasks: BackgroundTasks):
    global agent_status
    if agent_status["is_running"]:
        raise HTTPException(status_code=400, detail="Agent is already running a discovery task.")
    
    if os.environ.get("VERCEL"):
        leads = execute_lead_generation(req.niche, req.region, min(req.count, 15), req.source)
        exported = load_leads_from_csv()
        return {
            "status": "Completed",
            "message": f"Discovered {len(leads)} leads for '{req.niche}' in {req.region}",
            "leads": exported
        }
        
    background_tasks.add_task(execute_lead_generation, req.niche, req.region, req.count, req.source)
    return {
        "status": "Started",
        "message": f"Agent started discovering {req.count} leads ({req.source.upper()}) for '{req.niche}' in {req.region}"
    }

@router.get("/status")
def get_agent_status():
    return agent_status

class AuditSingleRequest(BaseModel):
    url: str
    region: str = "UK"

@router.post("/audit-single")
def audit_single(req: AuditSingleRequest):
    url = req.url.strip()
    url = re.sub(r"[,;.'\"\s]+$", "", url).strip()
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
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
        
        res = export_leads_to_files([lead_data], filename_prefix="single_audit")
        return {"lead": lead_data, "export": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to audit store: {e}")

class UpdateStatusRequest(BaseModel):
    store_url: str
    new_status: str

@router.post("/update-status")
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

@router.get("/download/excel")
def download_excel():
    paths = [
        OUTPUT_DIR / "leads_latest.xlsx",
        PROJECT_ROOT / "output" / "leads_latest.xlsx",
        CURRENT_DIR / "output" / "leads_latest.xlsx"
    ]
    for p in paths:
        if p.exists():
            return FileResponse(
                str(p),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename="talha_ecom_leads.xlsx"
            )
    raise HTTPException(status_code=404, detail="No leads exported yet.")

@router.get("/download/csv")
def download_csv():
    paths = [
        OUTPUT_DIR / "leads_latest.csv",
        PROJECT_ROOT / "output" / "leads_latest.csv",
        CURRENT_DIR / "output" / "leads_latest.csv"
    ]
    for p in paths:
        if p.exists():
            return FileResponse(
                str(p),
                media_type="text/csv",
                filename="talha_ecom_leads.csv"
            )
    raise HTTPException(status_code=404, detail="No leads exported yet.")

class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    store_url: str = ""

@router.post("/send-email")
def send_email_endpoint(req: SendEmailRequest):
    sender = os.environ.get("SENDER_EMAIL", SENDER_EMAIL)
    password = os.environ.get("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD)
    
    if not password:
        raise HTTPException(
            status_code=400, 
            detail="Gmail App Password is not configured. Click 'Email Setup' in the header to configure it."
        )
        
    result = send_outreach_email(
        sender_email=sender,
        app_password=password,
        recipient_email=req.to_email,
        subject=req.subject,
        body_text=req.body
    )
    
    if result.get("success"):
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

@router.post("/save-smtp-settings")
def save_smtp_settings(req: SMTPSettingsRequest):
    os.environ["SENDER_EMAIL"] = req.sender_email.strip()
    os.environ["GMAIL_APP_PASSWORD"] = req.app_password.strip()
    
    try:
        env_file = BASE_DIR / ".env"
        with open(env_file, "w") as f:
            f.write(f"SENDER_EMAIL={req.sender_email.strip()}\n")
            f.write(f"GMAIL_APP_PASSWORD={req.app_password.strip()}\n")
    except Exception:
        pass
        
    return {"status": "success", "message": "Email settings saved successfully!"}

@router.get("/get-smtp-settings")
def get_smtp_settings():
    sender = os.environ.get("SENDER_EMAIL", SENDER_EMAIL)
    has_pwd = bool(os.environ.get("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD))
    return {
        "sender_email": sender,
        "is_configured": has_pwd
    }

app.include_router(router, prefix="/api")
app.include_router(router, prefix="")
app.include_router(router, prefix="/api/index.py")
app.include_router(router, prefix="/index.py")
app.include_router(router, prefix="/api/index")

# AWS Lambda / Vercel Serverless Handler
handler = Mangum(app, lifespan="off")
