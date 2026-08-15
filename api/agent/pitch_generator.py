import json
import re
import urllib.parse
from typing import Dict
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, PORTFOLIO_PROOF

FALLBACK_MODELS = [GEMINI_MODEL, "gemini-flash-latest", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-pro-latest"]

def get_genai_client():
    return genai.Client(api_key=GEMINI_API_KEY)

def sanitize_brand_name(raw_name: str, url: str) -> str:
    """Extracts a clean, natural brand name without raw protocols, URLs or domain extensions."""
    if raw_name and not raw_name.startswith("http") and not raw_name.startswith("www.") and len(raw_name) < 35:
        clean = re.sub(r'\.(com|co\.uk|co|store|shop|io|org|net|us|eu|com\.au|es|de|fr)$', '', raw_name, flags=re.IGNORECASE).strip()
        clean = re.sub(r'[^\w\s\'-]', '', clean).strip()
        if clean and len(clean) >= 2:
            return clean.title()
            
    target_url = url if url.startswith("http") else f"https://{url}"
    parsed = urllib.parse.urlparse(target_url)
    host = parsed.netloc.replace("www.", "")
    base = host.split(".")[0]
    return base.title() if base and len(base) >= 2 else "your brand"

def generate_personalized_pitches(brand_name: str, store_url: str, region: str, contact_data: Dict, audit_data: Dict) -> Dict[str, str]:
    """
    Generates 4 distinct hyper-converting, ultra-attractive outreach pitch templates
    with strict client confidentiality (never mentions past client names like Sameday Trainers).
    """
    clean_brand = sanitize_brand_name(brand_name, store_url)
    raw_founder = contact_data.get("founder_name", "").strip()
    
    # Clean founder first name
    if raw_founder and len(raw_founder.split()) > 0 and raw_founder.lower() not in ["founder", "ceo", "there", "owner", "team"]:
        founder_first_name = raw_founder.split()[0].title()
    else:
        founder_first_name = "there"
        
    gaps = audit_data.get("critical_gaps", [])
    strengths = audit_data.get("strengths", [])
    platform = audit_data.get("platform", "Shopify / WooCommerce")
    speed_ms = audit_data.get("response_time_ms", 0)
    has_meta = audit_data.get("has_meta_pixel", True)
    has_tiktok = audit_data.get("has_tiktok_pixel", True)
    
    gaps_str = "\n- ".join(gaps) if gaps else "Mobile product page speed & checkout UX drop-offs"
    strengths_str = "\n- ".join(strengths) if strengths else "Strong product catalog aesthetic"
    
    system_prompt = f"""
You are an elite E-Commerce Growth Consultant, Senior Shopify Developer, and Conversion Rate Optimization (CRO) Partner.
Your name is {PORTFOLIO_PROOF['name']}.

Target Prospect Details:
- Clean Brand Name: {clean_brand}
- Store URL: {store_url}
- Platform: {platform}
- Target Country / Region: {region}
- Decision Maker First Name: {founder_first_name}

Technical Audit Findings:
- Identified Technical Gaps:
- {gaps_str}
- Server Response Time: {speed_ms}ms
- Meta Pixel Active: {has_meta}
- TikTok Pixel Active: {has_tiktok}
- Store Strengths:
- {strengths_str}

Your Real Verified Case Study Data (DO NOT MENTION SPECIFIC CLIENT NAMES LIKE 'Sameday Trainers' — refer to them anonymously as 'a UK lifestyle/footwear e-commerce brand' or 'a similar D2C store'):
1. Scaled a UK e-commerce store from £4.6k to £696,643+ Gross Sales (+14,752% growth, £650k net sales) with a 4.89% conversion rate and 3.8x ROAS.
2. Generated £88,048 in a single month through checkout CRO & multi-channel ad retargeting.
3. Delivered £206,664 YTD revenue in 2026 (+65% YoY growth).

Strict Writing Rules:
- STRICT PRIVACY: NEVER mention "Sameday Trainers" or specific past client names.
- CLEAN BRANDING: NEVER output raw website URLs like "https://..." inside the subject or greeting. Always refer to the brand naturally as "{clean_brand}".
- AUTHENTIC AUDIT: Only mention tracking gaps that were actually found (e.g. if TikTok pixel is missing, mention TikTok retargeting; if load speed is slow, mention mobile checkout latency; if Meta pixel is active, do not say Meta is missing).
- Tone: Natural, friendly, high-status, zero-fluff (70 to 85 words max).
- Call to Action: Offer a zero-pressure free 2-minute video breakdown of 2 quick fixes.

Generate a valid JSON object with exactly these 6 keys:
1. "email_subject_1": e.g. "Idea for {clean_brand} (scaled similar UK store to £696k)"
2. "email_body_1": High-converting Pitch 1 (Revenue Scaling Proof). Compliment the brand, point out 1 specific audit gap, mention scaling a UK store from £4.6k to £696k+ (£88k in 1 month at 4.89% CVR), offer 2-min video.
3. "email_subject_2": e.g. "Quick observation on {clean_brand}'s checkout & tracking"
4. "email_body_2": High-converting Pitch 2 (Technical / ROAS Leak). Focus on technical drop-off / pixel tracking and how fixing it delivered £206k+ YTD and 3.8x ROAS.
5. "linkedin_note": Connection request message under 260 characters to {founder_first_name} (mention £696k / 4.89% CVR result, no client names).
6. "instagram_dm": Casual, friendly Instagram DM under 45 words to {clean_brand}.

Return ONLY the raw JSON object.
"""

    client = get_genai_client()
    for model_name in FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=system_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text.strip()
            data = json.loads(raw_text)
            
            # Sanitize fallback in case LLM slipped the name
            body1 = data.get("email_body_1", "").replace("Sameday Trainers", "a UK lifestyle brand").replace("sameday trainers", "a UK brand")
            body2 = data.get("email_body_2", "").replace("Sameday Trainers", "a UK lifestyle brand").replace("sameday trainers", "a UK brand")
            
            return {
                "email_subject": data.get("email_subject_1", f"Idea for {clean_brand} (scaled similar store to £696k)"),
                "email_body": body1,
                "email_subject_alt": data.get("email_subject_2", f"Quick observation on {clean_brand}'s checkout & tracking"),
                "email_body_alt": body2,
                "linkedin_note": data.get("linkedin_note", "").replace("Sameday Trainers", "a UK brand"),
                "instagram_dm": data.get("instagram_dm", "").replace("Sameday Trainers", "a UK brand")
            }
        except Exception as e:
            continue

    # Fallback template with verified stats & clean formatting (Zero client names)
    gap_mention = gaps[0] if gaps else "mobile page load speed and retargeting pixels"
    return {
        "email_subject": f"Idea for {clean_brand} (scaled similar store to £696k)",
        "email_body": f"Hi {founder_first_name},\n\nLove what you've built with {clean_brand}—the product collection looks great.\n\nWhile reviewing your store, I noticed a couple of quick technical optimizations around {gap_mention} that are likely causing checkout drop-offs.\n\nRecently, on a similar UK e-commerce brand, fixing these checkout bottlenecks and technical tracking helped scale gross sales from £4.6k to £696,643+ (hitting £88,000+ in a single month at a 4.89% conversion rate).\n\nWould you be open to a 2-minute video breakdown showing 2 quick tweaks you can make to {clean_brand} today?\n\nBest,\nTalha",
        "email_subject_alt": f"Quick observation on {clean_brand}'s checkout & tracking",
        "email_body_alt": f"Hey {founder_first_name},\n\nHope you're having a great week. I was checking out {clean_brand} and spotted a quick optimization around {gap_mention}.\n\nWe recently helped a lifestyle e-commerce brand generate £206,600+ YTD (+65% YoY growth) and 3.8x ROAS by eliminating checkout latency and fixing conversion tracking.\n\nHappy to film a quick 2-minute screen recording showing exactly what to tweak on {clean_brand} if you're interested?\n\nCheers,\nTalha",
        "linkedin_note": f"Hi {founder_first_name}, love what you've built with {clean_brand}. I recently helped scale a similar UK store to £696k+ gross revenue (4.89% CVR) by fixing a few mobile checkout leaks. Would love to connect and share a quick idea!",
        "instagram_dm": f"Hey {clean_brand} team! Love the aesthetic. Noticed a couple of quick checkout & pixel tweaks on your site. I recently helped scale a UK brand to £696k+ by fixing these. Mind if I send a quick 2-minute video audit with some ideas?"
    }

if __name__ == "__main__":
    test_contact = {"founder_name": "Ben Woolford"}
    test_audit = {"critical_gaps": ["Missing TikTok Pixel for catalog retargeting"], "platform": "Shopify"}
    res = generate_personalized_pitches("Footdistrict", "https://footdistrict.com", "UK", test_contact, test_audit)
    print(json.dumps(res, indent=2))
