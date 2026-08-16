import os
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent

# Determine safe output directory (fallback to /tmp for Vercel/serverless environments)
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    OUTPUT_DIR = Path("/tmp/output")
else:
    OUTPUT_DIR = BASE_DIR / "output"

try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# Helper to dynamically parse .env
def load_env_file():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k not in os.environ:
                        os.environ[k] = v

load_env_file()

# API Keys & Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "marketingbytalha@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Default Search Regions & Niches
DEFAULT_REGIONS = [
    "UK",
    "US",
    "Pakistan",
    "Canada",
    "Australia",
    "UAE",
    "Germany",
    "Europe"
]

DEFAULT_NICHES = [
    "Footwear & Sneakers",
    "Fashion & Apparel",
    "Beauty & Skincare",
    "Jewelry & Accessories",
    "Home & Living",
    "Fitness & Gym Wear",
    "Electronics & Gadgets",
    "Health & Supplements",
    "Pet Supplies",
    "Books & Specialty Gifts"
]

# Verified Portfolio Statistics (Strict Client NDA Protected - Always Anonymized)
PORTFOLIO_PROOF = {
    "uk_lifestyle_scale": {
        "client_description": "a UK athletic & lifestyle footwear brand",
        "gross_sales": "£696,643.80",
        "net_sales": "£650,191.19",
        "growth": "+14,752%",
        "peak_month": "£88,048.50 in a single month",
        "ytd_2026": "£206,664.69 YTD (+65% YoY)",
        "cvr": "4.89%",
        "roas": "3.8x",
        "key_tactics": "Shopify CRO, Google Shopping UK feeds, Meta retargeting & TikTok ads"
    },
    "us_bookstore_scale": {
        "client_description": "a US D2C specialty retail brand",
        "sales": "$34,201.56",
        "orders": "569 orders",
        "cvr": "4.89%",
        "aov": "$59.03",
        "key_tactics": "Shopify build, checkout optimization, Meta & Google search ads"
    },
    "pakistan_fashion_scale": {
        "client_description": "a leading apparel & fashion brand",
        "revenue": "PKR 11,239,465.90 (3,543 orders)",
        "ad_spend_managed": "PKR 3.5M+ on Meta & TikTok",
        "opt_score": "93/100 Meta Optimization Score",
        "key_tactics": "High-CTR creative testing, seasonal scaling (Eid/Ramzan/Wedding)"
    },
    "paid_ads_performance": {
        "google_clicks": "70,000+ clicks & 1,200 conversions (£25.7k spend)",
        "google_cpc": "$1.36 avg CPC with 2,170 conversions",
        "tiktok_ctr": "7.98% - 8.14% CTR on mobile ad sets"
    }
}
