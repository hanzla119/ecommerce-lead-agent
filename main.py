import sys
import time
from typing import List, Dict
from config import DEFAULT_REGIONS, DEFAULT_NICHES, OUTPUT_DIR, GEMINI_API_KEY, GEMINI_MODEL
from scraper.store_finder import find_shopify_stores
from scraper.contact_enricher import enrich_store_contacts
from auditor.store_auditor import audit_store_frontend
from agent.pitch_generator import generate_personalized_pitches, get_genai_client
from exporter.excel_exporter import export_leads_to_files

def banner():
    print("=" * 70)
    print(" 🚀 AI E-COMMERCE LEAD GENERATION & STORE AUDIT AGENT (100% FREE)")
    print("    UK • US • Europe • Australia Client Acquisition System")
    print("=" * 70)

def process_single_store(store_url: str, region: str = "UK") -> Dict:
    """Processes a single store through the full audit, contact enrichment, and AI pitch pipeline."""
    print(f"\n🔍 [1/3] Auditing Store Frontend: {store_url}")
    audit = audit_store_frontend(store_url)
    print(f"   ✓ Platform: {audit['platform']}")
    print(f"   ✓ Meta Pixel: {'Active' if audit['has_meta_pixel'] else 'MISSING'}")
    print(f"   ✓ TikTok Pixel: {'Active' if audit['has_tiktok_pixel'] else 'MISSING'}")
    print(f"   ✓ Gaps: {', '.join(audit['critical_gaps'][:2]) if audit['critical_gaps'] else 'None'}")

    print(f"📧 [2/3] Extracting Contacts & LinkedIn Founder Profile...")
    contacts = enrich_store_contacts(store_url, region=region)
    brand = contacts.get("brand_name", "") or store_url
    print(f"   ✓ Brand Name: {brand}")
    print(f"   ✓ Email: {contacts.get('email') or 'Not found on page'}")
    print(f"   ✓ Instagram: {contacts.get('instagram') or 'None'}")
    print(f"   ✓ Founder: {contacts.get('founder_name') or 'Founder'}")
    print(f"   ✓ Founder LinkedIn: {contacts.get('founder_linkedin') or 'Searching...'}")

    print(f"🤖 [3/3] Generating Custom Multi-Channel Pitches via Gemini AI...")
    pitches = generate_personalized_pitches(
        brand_name=brand,
        store_url=store_url,
        region=region,
        contact_data=contacts,
        audit_data=audit
    )
    print(f"   ✓ Email Subject: {pitches.get('email_subject')}")
    print(f"   ✓ Generated Cold Email, LinkedIn Note & Instagram DM!")

    return {
        "url": store_url,
        "region": region,
        "contacts": contacts,
        "audit": audit,
        "pitches": pitches
    }

def run_lead_generation_pipeline(niche: str, region: str, count: int = 5):
    """Discovers stores, audits them, generates pitches, and exports to Excel/CSV."""
    print(f"\n🌐 Searching for {count} live e-commerce stores in '{niche}' across {region}...")
    stores = find_shopify_stores(niche=niche, region=region, max_results=count)
    
    if not stores:
        print("❌ No stores discovered with current query. Try adjusting the niche or region.")
        return

    print(f"✅ Found {len(stores)} unique store domains:")
    for idx, s in enumerate(stores, 1):
        print(f"   {idx}. {s}")

    processed_leads = []
    for idx, store_url in enumerate(stores, 1):
        print(f"\n--- Processing Lead [{idx}/{len(stores)}] ---")
        try:
            lead_data = process_single_store(store_url, region=region)
            processed_leads.append(lead_data)
        except Exception as e:
            print(f"⚠️ Error processing {store_url}: {e}")
        time.sleep(1)  # Respectful delay

    # Export
    print("\n📊 Exporting results to Excel & CSV...")
    res = export_leads_to_files(processed_leads, filename_prefix=f"{niche.replace(' ', '_')}_{region}")
    print(f"🎉 Success! Processed {len(processed_leads)} leads.")
    print(f"📁 CSV File:   {res['csv']}")
    print(f"📁 Excel File: {res['excel']}")
    print(f"📁 Latest:     {res['latest_excel']}")

def test_gemini_connection():
    """Tests if the user's Gemini API key is valid."""
    print(f"\nTesting Gemini AI connection with model '{GEMINI_MODEL}'...")
    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Say 'Gemini API is successfully connected and ready for lead generation!'"
        )
        print(f"✅ AI Response: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def main():
    banner()
    while True:
        print("\nSelect an action:")
        print("1. Discover & Generate Leads (Automated Niche Search -> Excel)")
        print("2. Audit & Pitch a Single Store URL")
        print("3. Test Gemini API Connection")
        print("4. Exit")
        
        choice = input("\nEnter choice [1-4]: ").strip()
        
        if choice == "1":
            print(f"\nPopular Niches: {', '.join(DEFAULT_NICHES[:4])}")
            niche = input("Enter niche [default: 'footwear sneakers']: ").strip() or "footwear sneakers"
            print(f"Target Regions: {', '.join(DEFAULT_REGIONS)}")
            region = input("Enter region [default: 'UK']: ").strip() or "UK"
            count_str = input("How many leads to find? [default: 5]: ").strip() or "5"
            try:
                count = int(count_str)
            except ValueError:
                count = 5
            run_lead_generation_pipeline(niche=niche, region=region, count=count)
            
        elif choice == "2":
            url = input("Enter Shopify/Store URL (e.g. https://www.samedaytrainers.co.uk): ").strip()
            if not url.startswith("http"):
                url = "https://" + url
            region = input("Target Region [UK/US/Australia, default: 'UK']: ").strip() or "UK"
            lead = process_single_store(url, region=region)
            res = export_leads_to_files([lead], filename_prefix="single_audit")
            print(f"\n📁 Exported to: {res['excel']}")
            
        elif choice == "3":
            test_gemini_connection()
            
        elif choice == "4":
            print("Goodbye and happy client hunting!")
            sys.exit(0)
        else:
            print("Invalid choice, please select 1, 2, 3, or 4.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_gemini_connection()
    elif len(sys.argv) > 1 and sys.argv[1] == "--auto":
        run_lead_generation_pipeline("streetwear fashion", "UK", count=3)
    else:
        main()
