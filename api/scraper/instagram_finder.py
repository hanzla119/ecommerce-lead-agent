import re
import urllib.parse
from typing import List, Dict, Set
from ddgs import DDGS

# Excluded Instagram utility paths
EXCLUDED_IG_HANDLES = {
    "explore", "p", "reel", "reels", "stories", "direct", "accounts", 
    "directory", "developer", "about", "legal", "terms", "privacy", "help"
}

def clean_ig_handle(url: str) -> str:
    """Extracts username from Instagram profile URL."""
    parsed = urllib.parse.urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if parts and parts[0]:
        handle = parts[0].lower()
        if handle not in EXCLUDED_IG_HANDLES and not handle.startswith("tag"):
            return handle
    return ""

def extract_website_from_bio_snippet(snippet: str) -> str:
    """Extracts store website URL or domain mentioned in Instagram bio text."""
    # Find domain mentions like brand.co.uk or https://brand.com
    url_match = re.search(r'https?://[^\s,;"\'<>]+', snippet)
    if url_match:
        return url_match.group(0).rstrip(".,;")
        
    domain_match = re.search(r'\b([a-zA-Z0-9-]+\.(?:com|co\.uk|co|us|io|store|shop|online|eu|com\.au))\b', snippet, re.IGNORECASE)
    if domain_match:
        domain = domain_match.group(1).lower()
        if not any(excluded in domain for excluded in ["instagram.com", "facebook.com", "linktr.ee", "tiktok.com"]):
            return f"https://{domain}"
            
    return ""

def find_instagram_brands(niche: str, region: str = "UK", max_results: int = 15) -> List[Dict]:
    """
    Discovers live D2C e-commerce brands on Instagram with bio text and linked store URLs.
    """
    discovered_brands: List[Dict] = []
    seen_handles: Set[str] = set()
    
    queries = [
        f'site:instagram.com "{niche}" ("shop now" OR "free delivery" OR "link in bio") "{region}"',
        f'site:instagram.com "{niche}" ("clothing brand" OR "footwear" OR "organic") "{region}" "shop"',
        f'site:instagram.com "{niche}" ("worldwide shipping" OR "store") "{region}"'
    ]
    
    ddgs = DDGS()
    
    for query in queries:
        if len(discovered_brands) >= max_results:
            break
        try:
            results = ddgs.text(query, max_results=max_results * 2)
            if results:
                for r in results:
                    url = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")
                    
                    if "instagram.com/" in url:
                        handle = clean_ig_handle(url)
                        if handle and handle not in seen_handles:
                            seen_handles.add(handle)
                            
                            # Clean Brand Name from Instagram Title: "Brand Name (@handle) • Instagram photos"
                            raw_name = title.split("(@")[0].split("•")[0].replace("on Instagram", "").strip()
                            brand_name = raw_name if raw_name and len(raw_name) < 40 else handle.capitalize()
                            
                            # Extract Store URL
                            store_url = extract_website_from_bio_snippet(body)
                            if not store_url:
                                store_url = f"https://{handle}.com"
                                
                            brand_entry = {
                                "brand_name": brand_name,
                                "instagram_url": f"https://www.instagram.com/{handle}/",
                                "instagram_handle": f"@{handle}",
                                "store_url": store_url,
                                "bio_snippet": body,
                                "region": region,
                                "source": "Instagram D2C Discovery"
                            }
                            discovered_brands.append(brand_entry)
                            
                            if len(discovered_brands) >= max_results:
                                break
        except Exception as e:
            print(f"[InstagramFinder] Query note for '{query}': {e}")
            
    return discovered_brands[:max_results]

if __name__ == "__main__":
    brands = find_instagram_brands("streetwear apparel", "UK", max_results=3)
    print("Discovered IG Brands:", brands)
