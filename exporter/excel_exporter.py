import os
import re
from datetime import datetime
from typing import List, Dict
import pandas as pd
from config import OUTPUT_DIR

def export_leads_to_files(leads: List[Dict], filename_prefix: str = "ecommerce_leads") -> Dict[str, str]:
    """
    Exports lead data to formatted CSV and Excel (.xlsx) files safely.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = OUTPUT_DIR / f"{filename_prefix}_{timestamp}.csv"
    excel_path = OUTPUT_DIR / f"{filename_prefix}_{timestamp}.xlsx"
    latest_csv = OUTPUT_DIR / "leads_latest.csv"
    latest_excel = OUTPUT_DIR / "leads_latest.xlsx"
    
    if not leads:
        return {
            "csv": str(csv_path),
            "excel": str(excel_path),
            "latest_csv": str(latest_csv),
            "latest_excel": str(latest_excel),
            "count": 0
        }
        
    flattened_data = []
    for lead in leads:
        contacts = lead.get("contacts", {})
        audit = lead.get("audit", {})
        pitches = lead.get("pitches", {})
        
        row = {
            "Date Added": datetime.now().strftime("%Y-%m-%d"),
            "Brand Name": contacts.get("brand_name", "") or lead.get("domain", ""),
            "Store URL": lead.get("url", ""),
            "Target Region": lead.get("region", "UK"),
            "Contact Email": contacts.get("email", ""),
            "Email Deliverability": contacts.get("email_deliverability", "MX Checked"),
            "All Emails Found": ", ".join(contacts.get("all_emails", [])),
            "Founder / Owner": contacts.get("founder_name", ""),
            "Founder Title": contacts.get("founder_title", ""),
            "Founder LinkedIn Profile": contacts.get("founder_linkedin", ""),
            "Instagram Profile": contacts.get("instagram", ""),
            "Instagram Handle": contacts.get("instagram_handle", ""),
            "Facebook Page": contacts.get("facebook", ""),
            "TikTok Profile": contacts.get("tiktok", ""),
            "Store Platform": audit.get("platform", "Shopify"),
            "Meta Pixel Active": "Yes" if audit.get("has_meta_pixel") else "NO (Missing)",
            "TikTok Pixel Active": "Yes" if audit.get("has_tiktok_pixel") else "NO (Missing)",
            "Google Analytics / GTM": "Yes" if audit.get("has_google_analytics") else "NO (Missing)",
            "Klaviyo / Email Active": "Yes" if audit.get("has_klaviyo") else "No",
            "Response Speed (TTFB)": f"{audit.get('response_time_ms', 0)} ms",
            "Key Gaps Identified": "; ".join(audit.get("critical_gaps", [])),
            "Email Subject (Template 1)": pitches.get("email_subject", ""),
            "Email Pitch Body (Template 1)": pitches.get("email_body", ""),
            "Email Subject (Template 2)": pitches.get("email_subject_alt", ""),
            "Email Pitch Body (Template 2)": pitches.get("email_body_alt", ""),
            "LinkedIn Connection Note": pitches.get("linkedin_note", ""),
            "Instagram DM Pitch": pitches.get("instagram_dm", ""),
            "Outreach Status": "Ready to Send"
        }
        flattened_data.append(row)
        
    df = pd.DataFrame(flattened_data)
    
    try:
        # Save timestamped CSV
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        # Save timestamped Excel
        try:
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Leads")
        except Exception:
            pass
            
        # Overwrite / Append to leads_latest
        if latest_csv.exists():
            try:
                existing_df = pd.read_csv(latest_csv, encoding="utf-8-sig")
                combined_df = pd.concat([df, existing_df]).drop_duplicates(subset=["Store URL"], keep="first")
                combined_df.to_csv(latest_csv, index=False, encoding="utf-8-sig")
                try:
                    with pd.ExcelWriter(latest_excel, engine="openpyxl") as writer:
                        combined_df.to_excel(writer, index=False, sheet_name="All Leads")
                except Exception:
                    pass
            except Exception:
                df.to_csv(latest_csv, index=False, encoding="utf-8-sig")
        else:
            df.to_csv(latest_csv, index=False, encoding="utf-8-sig")
            try:
                with pd.ExcelWriter(latest_excel, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="All Leads")
            except Exception:
                pass
    except Exception as e:
        print(f"Non-critical export error (ignoring for serverless): {e}")
            
    return {
        "csv": str(csv_path),
        "excel": str(excel_path),
        "latest_csv": str(latest_csv),
        "latest_excel": str(latest_excel),
        "count": len(flattened_data)
    }
