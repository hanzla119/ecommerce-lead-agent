import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load local .env if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Google Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.7-flash"  # Ultra-fast, highly intelligent Gemini 3.7 Flash

# Email Outreach Sender Credentials (Gmail SMTP)
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "marketingbytalha@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# Talha's Case Study & Track Record Details (Injected into AI prompts)
PORTFOLIO_PROOF = {
    "name": "Talha Yousaf",
    "title": "Shopify Developer & E-Commerce Paid Growth Partner",
    "key_results": [
        "Scaled UK e-commerce store from £4.6k to £696,643+ Gross Sales (+14,752% revenue growth) with a 4.89% conversion rate and 3.8x ROAS.",
        "Generated £88,000+ in gross revenue in a single month through checkout CRO and multi-channel paid traffic.",
        "Delivered £206,600+ YTD revenue in 2026 (+65% YoY growth) for lifestyle and footwear brands.",
        "Built custom Shopify stores and optimized technical tracking (Meta CAPI, TikTok Pixel, Google Ads PMax feeds)."
    ],
    "specialties": [
        "Shopify & WooCommerce Custom Development & Mobile Speed / TTFB Optimization",
        "Conversion Rate Optimization (CRO), A/B Testing & Checkout Funnel Redesign",
        "Meta Ads, Google Shopping / Performance Max & TikTok Ads Scaling",
        "Server-Side Tracking (Meta CAPI, GA4, Klaviyo Retention Flows)"
    ],
    "calendar_link": "https://cal.com/talha-yousaf/15min"
}

# Target Markets & Footprints
DEFAULT_REGIONS = ["UK", "US", "Australia", "Europe"]

DEFAULT_NICHES = [
    "clothing fashion apparel",
    "footwear shoes sneakers",
    "supplements health wellness",
    "jewelry accessories",
    "skincare beauty cosmetics",
    "home decor furniture"
]
