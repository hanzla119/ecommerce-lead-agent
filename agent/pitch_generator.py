import os
import re
from typing import Dict, List, Optional
from google import genai
from config import GEMINI_API_KEY, PORTFOLIO_PROOF

def clean_gemini_text(text: str) -> str:
    """Removes markdown code fences and extraneous formatting."""
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.strip()

def build_fallback_pitches(brand_name: str, region: str, founder_name: str = "", audit_data: Optional[Dict] = None) -> Dict[str, str]:
    """Provides high-converting, proven outreach templates if AI is offline."""
    salutation = f"Hi {founder_name.split()[0]}" if founder_name else f"Hi {brand_name} Team"
    
    # Audit insights
    gaps = audit_data.get("critical_gaps", []) if audit_data else []
    gap_summary = gaps[0] if gaps else "product page social proof and mobile retargeting"
    
    # Regional Case Study Selection
    if region.upper() == "UK":
        proof_line = "I recently scaled a UK athletic & lifestyle brand from £4.6k to £696,643.80 (+14,752% growth, £88k in a single month) at a 4.89% CVR and 3.8x ROAS."
        stat_hook = "scaled UK brand from £4.6k to £696k+"
    elif region.upper() in ["US", "USA", "CANADA", "AUSTRALIA"]:
        proof_line = "I recently scaled a US D2C store to $34k+ across 569 orders at a 4.89% conversion rate ($59 AOV) by plugging tracking leaks and dialing in paid search."
        stat_hook = "scaled US store to 4.89% CVR"
    elif region.upper() in ["PAKISTAN", "PK", "UAE"]:
        proof_line = "I recently scaled an e-commerce apparel brand to PKR 11.2M+ (3,540+ orders) while maintaining a 93/100 Meta Ads optimization score across PKR 3.5M+ spend."
        stat_hook = "scaled apparel brand to 11.2M+ PKR"
    else:
        proof_line = "I recently scaled an e-commerce brand from £4.6k to £696k+ (+14,752% growth) at a 4.89% CVR by fixing checkout tracking and ad leaks."
        stat_hook = "scaled brand from £4.6k to £696k+"

    email_body_1 = f"""{salutation},

Love what you've built with {brand_name}—your site design and positioning look great. While auditing the store, I noticed {gap_summary.lower()}, leaving easy revenue on the table.

{proof_line}

Mind if I send over a quick 2-minute video breakdown showing 2 simple tweaks you can make to fix this for {brand_name}?

Best,
Talha"""

    email_body_2 = f"""{salutation},

Quick note regarding {brand_name}—spotted a quick tracking and conversion gap: {gap_summary.lower()}, which might be causing paid traffic to bounce without converting.

Fixing these exact tracking and checkout leaks helped our UK e-commerce partner reach £206k+ YTD (+65% YoY) with a 3.8x ROAS.

Open to a 2-minute video breakdown of how to plug this leak?

Best,
Talha"""

    email_body_3 = f"""{salutation},

I put together a quick technical audit for {brand_name}. Your page speed and branding look solid, but you're leaving revenue on the table due to {gap_summary.lower()}.

Dialing in this exact checkout and ad optimization helped us hit £88,048 in a single month at a 4.89% conversion rate.

Would you be open to seeing a 2-minute video walkthrough?

Best,
Talha"""

    email_body_4 = f"""{salutation},

Spotted a quick fix on {brand_name}'s checkout & tracking setup ({gap_summary.lower()}). 

Recently scaled a similar store to £696k+ by solving this exact issue. Mind if I send a 2-min video showing how to fix it?

Best,
Talha"""

    linkedin_note = f"Hi {founder_name.split()[0] if founder_name else 'there'}, love what you're building at {brand_name}. Recently {stat_hook} by dialing in CRO & tracking. Spotted a quick growth opportunity for {brand_name}—would love to connect!"
    
    instagram_dm = f"Hey team! Love the vibe at {brand_name}. Spotted a quick tracking gap leaking paid traffic. Scaled a similar store to £696k+ recently and made a 2-minute video showing two easy fixes. Mind if I share it here?"

    return {
        "email_subject": f"Idea for {brand_name} ({stat_hook})",
        "email_body": email_body_1.strip(),
        "email_subject_alt": f"Quick observation on {brand_name}'s conversion & tracking",
        "email_body_alt": email_body_2.strip(),
        "email_subject_cro": f"Quick CRO fix for {brand_name} (hit £88k/mo with this)",
        "email_body_cro": email_body_3.strip(),
        "email_subject_short": f"2-min video for {brand_name}?",
        "email_body_short": email_body_4.strip(),
        "linkedin_note": linkedin_note.strip(),
        "instagram_dm": instagram_dm.strip()
    }

def generate_personalized_pitches(
    brand_name: str,
    store_url: str,
    region: str = "UK",
    contact_data: Optional[Dict] = None,
    audit_data: Optional[Dict] = None
) -> Dict[str, str]:
    """
    Generates hyper-personalized cold outreach pitches using Google Gemini Flash,
    injecting verified portfolio proof points with strict NDA client anonymity.
    """
    contact_data = contact_data or {}
    audit_data = audit_data or {}
    
    founder_name = contact_data.get("founder_name", "")
    critical_gaps = audit_data.get("critical_gaps", [])
    strengths = audit_data.get("strengths", [])
    platform = audit_data.get("platform", "Shopify")
    speed_ms = audit_data.get("response_time_ms", 0)

    # If Gemini API Key is missing or default, return proven high-converting templates
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    if not api_key:
        return build_fallback_pitches(brand_name, region, founder_name, audit_data)

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
You are Talha Yousaf, an expert E-commerce Growth & Shopify Specialist with a BS in Computer Science.
You are writing personalized, high-converting cold outreach messages to e-commerce decision-makers.

PROVEN TRACK RECORD & CASE STUDY PROOF (ALWAYS ANONYMIZED - NEVER MENTION CLIENT BRAND NAMES):
- Scaled a UK athletic & lifestyle footwear brand from £4,690 to £696,643.80 Gross Sales (+14,752% growth, £650k net sales) with £88,048 in a single month and £206k+ YTD at 4.89% CVR and 3.8x ROAS.
- Scaled a US D2C specialty store to $34,201 (569 orders, 4.89% CVR, $59.03 AOV).
- Scaled a fashion & suiting apparel brand to PKR 11.2M+ (3,540+ orders) with PKR 3.5M+ ad spend (93/100 Meta optimization score).
- Managed 70k+ Google Ads clicks & achieved 8.14% CTR on TikTok mobile ads.

TARGET STORE INFORMATION:
- Brand Name: {brand_name}
- Store Website: {store_url}
- Region: {region}
- Decision Maker / Founder: {founder_name or 'Not specified'}
- Platform: {platform}
- Server Speed: {speed_ms}ms
- Strengths: {', '.join(strengths) if strengths else 'Solid visual brand'}
- Critical Leaks / Gaps Detected: {', '.join(critical_gaps) if critical_gaps else 'Missing advanced ad retargeting and social proof app'}

RULES:
1. STRICT NDA: NEVER use or mention the client name "Sameday Trainers" or specific client URLs. Refer to them strictly as "a UK footwear & lifestyle brand" or "a similar UK/US store".
2. Keep email under 110 words. Clear, conversational, non-pushy.
3. Call to Action: Offer a free 2-minute video breakdown of 2 specific tweaks.
4. Output EXACTLY in this format with labels:

[EMAIL_SUBJECT_1]
<Subject line with high curiosity & proof>

[EMAIL_BODY_1]
<Email Body 1 - Revenue Scale Hook>

[EMAIL_SUBJECT_2]
<Alternative Subject line focused on tracking/CRO>

[EMAIL_BODY_2]
<Email Body 2 - Tracking & ROAS Leak Hook>

[EMAIL_SUBJECT_3]
<Subject line focused on 4.89% CVR / speed>

[EMAIL_BODY_3]
<Email Body 3 - CRO & Checkout Optimization Hook>

[EMAIL_SUBJECT_4]
<Short 4-line punchy subject>

[EMAIL_BODY_4]
<Email Body 4 - Ultra-short 4-line Founder hook>

[LINKEDIN_NOTE]
<Under 260 characters personalized connection note>

[INSTAGRAM_DM]
<Under 45 words casual, direct Instagram DM>
"""
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        text = response.text if hasattr(response, "text") else str(response)
        
        # Parse sections
        def extract_tag(tag: str, default: str = "") -> str:
            pattern = rf"\[{tag}\]\s*([\s\S]*?)(?=\n\[[A-Z_0-9]+\]|$)"
            m = re.search(pattern, text)
            return m.group(1).strip() if m else default

        fb = build_fallback_pitches(brand_name, region, founder_name, audit_data)
        
        return {
            "email_subject": clean_gemini_text(extract_tag("EMAIL_SUBJECT_1", fb["email_subject"])),
            "email_body": clean_gemini_text(extract_tag("EMAIL_BODY_1", fb["email_body"])),
            "email_subject_alt": clean_gemini_text(extract_tag("EMAIL_SUBJECT_2", fb["email_subject_alt"])),
            "email_body_alt": clean_gemini_text(extract_tag("EMAIL_BODY_2", fb["email_body_alt"])),
            "email_subject_cro": clean_gemini_text(extract_tag("EMAIL_SUBJECT_3", fb["email_subject_cro"])),
            "email_body_cro": clean_gemini_text(extract_tag("EMAIL_BODY_3", fb["email_body_cro"])),
            "email_subject_short": clean_gemini_text(extract_tag("EMAIL_SUBJECT_4", fb["email_subject_short"])),
            "email_body_short": clean_gemini_text(extract_tag("EMAIL_BODY_4", fb["email_body_short"])),
            "linkedin_note": clean_gemini_text(extract_tag("LINKEDIN_NOTE", fb["linkedin_note"])),
            "instagram_dm": clean_gemini_text(extract_tag("INSTAGRAM_DM", fb["instagram_dm"]))
        }
    except Exception as e:
        print(f"Gemini generation error: {e}, using fallback.")
        return build_fallback_pitches(brand_name, region, founder_name, audit_data)
