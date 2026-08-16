import re
import urllib.parse
from typing import List, Dict, Set
from duckduckgo_search import DDGS
from scraper.store_finder import clean_url_to_root

EXCLUDED_IG_HANDLES = {
    "explore", "p", "reel", "stories", "direct", "accounts", "legal", "about"
}

def clean_instagram_handle(url_or_handle: str) -> str:
    """Extracts @username from instagram URL or raw handle."""
    if not url_or_handle:
        return ""
    m = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", url_or_handle)
    if m:
        handle = m.group(1).strip("/").lower()
        if handle not in EXCLUDED_IG_HANDLES:
            return f"@{handle}"
    if url_or_handle.startswith("@"):
        return url_or_handle
    return f"@{url_or_handle.strip('/')}"

def find_instagram_brands(niche: str, region: str = "UK", limit: int = 20) -> List[Dict[str, str]]:
    """
    Finds direct-to-consumer Instagram brand profiles for a given niche and region,
    extracting their store website and Instagram handle.
    """
    region_term = "" if region.lower() in ["global", "world"] else region
    queries = [
        f'site:instagram.com "{niche}" "link in bio" {region_term}',
        f'site:instagram.com "{niche}" "shop online" {region_term}',
        f'site:instagram.com "{niche}" "official store" {region_term}',
        f'site:instagram.com "{niche}" brand UK London' if region == "UK" else f'site:instagram.com "{niche}" brand USA New York'
    ]
    
    leads: List[Dict[str, str]] = []
    seen_handles: Set[str] = set()
    seen_urls: Set[str] = set()
    
    for q in queries:
        if len(leads) >= limit:
            break
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(q, max_results=min(40, limit * 2)))
                for r in results:
                    href = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")
                    
                    # Extract Instagram Handle
                    handle_match = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", href)
                    if not handle_match:
                        continue
                    handle = handle_match.group(1).strip("/").lower()
                    if handle in EXCLUDED_IG_HANDLES or handle in seen_handles:
                        continue
                    seen_handles.add(handle)
                    
                    # Extract external store link from title or snippet if present
                    store_url = ""
                    url_in_body = re.search(r"(https?://[^\s]+)", body)
                    if url_in_body:
                        candidate = clean_url_to_root(url_in_body.group(1))
                        if candidate and "instagram.com" not in candidate:
                            store_url = candidate
                            
                    # Fallback URL estimation if not directly in bio snippet
                    if not store_url:
                        store_url = f"https://{handle}.com"
                        
                    if store_url in seen_urls:
                        continue
                    seen_urls.add(store_url)
                    
                    # Clean Brand Name from Instagram Title
                    brand_name = title.split("•")[0].split("(@")[0].split("-")[0].replace("Instagram", "").strip()
                    if not brand_name:
                        brand_name = handle.replace("_", " ").replace(".", " ").title()
                        
                    leads.append({
                        "url": store_url,
                        "brand_name": brand_name,
                        "instagram": f"https://www.instagram.com/{handle}",
                        "instagram_handle": f"@{handle}",
                        "niche": niche,
                        "region": region,
                        "source": "Instagram"
                    })
                    
                    if len(leads) >= limit:
                        break
        except Exception as e:
            print(f"Instagram brand search error: {e}")
            
    return leads
