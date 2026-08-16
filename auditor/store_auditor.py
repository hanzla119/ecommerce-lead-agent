import re
import time
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

def audit_store_frontend(url: str) -> Dict[str, any]:
    """
    Performs a technical conversion and tracking audit on the e-commerce store.
    Checks Shopify Web Pixel Manager, Meta CAPI, TikTok pixel, GA4, Klaviyo,
    reviews apps, currency switcher, and server TTFB response speed.
    """
    if not url.startswith("http"):
        url = "https://" + url
        
    audit_results = {
        "store_url": url,
        "is_shopify": False,
        "platform": "Unknown",
        "response_time_ms": 0,
        "has_meta_pixel": False,
        "has_tiktok_pixel": False,
        "has_google_analytics": False,
        "has_klaviyo": False,
        "has_reviews_app": False,
        "reviews_app_name": "",
        "has_currency_switcher": False,
        "critical_gaps": [],
        "strengths": []
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        t0 = time.time()
        res = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        t1 = time.time()
        
        audit_results["response_time_ms"] = int((t1 - t0) * 1000)
        html = res.text
        html_lower = html.lower()
        
        # 1. Platform Detection
        if "cdn.shopify.com" in html_lower or "shopify.theme" in html_lower or "myshopify.com" in html_lower:
            audit_results["is_shopify"] = True
            audit_results["platform"] = "Shopify"
        elif "wp-content" in html_lower or "woocommerce" in html_lower:
            audit_results["is_shopify"] = False
            audit_results["platform"] = "WooCommerce / WordPress"
        elif "magento" in html_lower or "mage/" in html_lower:
            audit_results["platform"] = "Magento"
        elif "bigcommerce" in html_lower:
            audit_results["platform"] = "BigCommerce"
        else:
            audit_results["platform"] = "Custom / Headless"
            
        # 2. Meta Pixel & Shopify Web Pixel Manager (WPM) Detection
        meta_indicators = [
            "connect.facebook.net", "fbevents.js", "fbq(", "fbq=",
            "facebook pixel", "wpm@shopify", "trekkie", "facebook_pixel",
            "facebook-pixel", "meta pixel", "tr?id="
        ]
        has_meta = any(ind in html_lower for ind in meta_indicators)
        # Check script tags
        if not has_meta:
            soup = BeautifulSoup(html, "html.parser")
            for s in soup.find_all("script"):
                src = s.get("src", "").lower()
                if "facebook" in src or "fbevents" in src:
                    has_meta = True
                    break
        audit_results["has_meta_pixel"] = has_meta
        
        # 3. TikTok Pixel Detection
        tt_indicators = [
            "analytics.tiktok.com", "ttq.load", "ttq.page", "tiktok pixel",
            "tiktok-pixel", "ttq.track"
        ]
        audit_results["has_tiktok_pixel"] = any(ind in html_lower for ind in tt_indicators)
        
        # 4. Google Analytics / Google Tag Manager Detection
        ga_indicators = [
            "googletagmanager.com", "google-analytics.com", "gtag(",
            "ga('create'", "gtm.js", "gtag('config'"
        ]
        audit_results["has_google_analytics"] = any(ind in html_lower for ind in ga_indicators)
        
        # 5. Email Marketing & Retention Flows (Klaviyo, Omnisend, Mailchimp)
        retention_indicators = [
            "klaviyo.com", "static.klaviyo.com", "_learnq", "omnisend",
            "privy.com", "mailchimp"
        ]
        audit_results["has_klaviyo"] = any(ind in html_lower for ind in retention_indicators)
        
        # 6. Reviews & Social Proof App Detection
        review_apps = {
            "Trustpilot": ["trustpilot", "tp-widget"],
            "Judge.me": ["judge.me", "judgeme"],
            "Loox": ["loox.io", "loox-reviews"],
            "Yotpo": ["yotpo.com", "yotpo-reviews"],
            "Stamped.io": ["stamped.io", "stamped-main-widget"],
            "Okendo": ["okendo.io", "okendo-widget"],
            "Reviews.io": ["reviews.io", "reviews-widget"],
            "Junip": ["junip.co"]
        }
        for app_name, patterns in review_apps.items():
            if any(p in html_lower for p in patterns):
                audit_results["has_reviews_app"] = True
                audit_results["reviews_app_name"] = app_name
                break
                
        # 7. Currency Switcher (International Scaling)
        currency_indicators = ["currency-selector", "localization-form", "shopify-currency-switcher", "country-switcher"]
        audit_results["has_currency_switcher"] = any(ind in html_lower for ind in currency_indicators)
        
        # 8. Synthesize Critical Gaps and Strengths
        if not audit_results["has_meta_pixel"]:
            audit_results["critical_gaps"].append("Missing Meta Pixel / CAPI tracking (blind ad spend on FB & IG)")
        else:
            audit_results["strengths"].append("Meta Pixel / Tracking is active")
            
        if not audit_results["has_tiktok_pixel"]:
            audit_results["critical_gaps"].append("Missing TikTok Pixel (losing out on TikTok ad retargeting & catalog ads)")
        else:
            audit_results["strengths"].append("TikTok Pixel is active")
            
        if not audit_results["has_google_analytics"]:
            audit_results["critical_gaps"].append("No Google Analytics 4 / GTM detected")
        else:
            audit_results["strengths"].append("Google Analytics / GTM active")
            
        if not audit_results["has_reviews_app"]:
            audit_results["critical_gaps"].append("No structured review / social proof app detected on product pages")
        else:
            audit_results["strengths"].append(f"Social proof active ({audit_results['reviews_app_name']})")
            
        if not audit_results["has_klaviyo"]:
            audit_results["critical_gaps"].append("No automated email retention (Klaviyo) detected (losing cart recovery revenue)")
        else:
            audit_results["strengths"].append("Automated email retention / pop-up flow active")
            
        if audit_results["response_time_ms"] > 1500:
            audit_results["critical_gaps"].append(f"Slow server response time ({audit_results['response_time_ms']}ms) hurting mobile conversion rate")
        else:
            audit_results["strengths"].append(f"Fast initial response ({audit_results['response_time_ms']}ms)")
            
    except Exception as e:
        audit_results["critical_gaps"].append(f"Could not connect or site timed out: {str(e)[:50]}")
        
    return audit_results
