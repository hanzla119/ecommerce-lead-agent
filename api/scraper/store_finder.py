import re
import urllib.parse
from typing import List, Dict, Set
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Excluded generic marketplaces and directories
EXCLUDED_DOMAINS = {
    "amazon.com", "amazon.co.uk", "ebay.com", "ebay.co.uk", "etsy.com",
    "walmart.com", "target.com", "aliexpress.com", "alibaba.com",
    "shopify.com", "myshopify.com", "facebook.com", "instagram.com",
    "twitter.com", "x.com", "linkedin.com", "youtube.com", "pinterest.com",
    "tiktok.com", "wikipedia.org", "reddit.com", "quora.com", "medium.com",
    "yelp.com", "trustpilot.com", "google.com", "bing.com", "yahoo.com",
    "asos.com", "zara.com", "shein.com", "temu.com", "wayfair.com"
}

def clean_url_to_root(url: str) -> str:
    """Extracts https://domain.com from any raw URL string."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain in EXCLUDED_DOMAINS or any(domain.endswith("." + exc) for exc in EXCLUDED_DOMAINS):
            return ""
        return f"https://{domain}"
    except Exception:
        return ""

def generate_search_queries(niche: str, region: str) -> List[str]:
    """Generates multiple search variations to discover up to 200 high-converting stores."""
    region_term = "" if region.lower() in ["global", "world"] else region
    
    queries = [
        f'"{niche}" site:.co.uk "powered by shopify"' if region == "UK" else f'"{niche}" store "powered by shopify" {region_term}',
        f'best "{niche}" direct to consumer brands {region_term}',
        f'shop "{niche}" online "cart" "checkout" {region_term}',
        f'"{niche}" boutiques online {region_term}',
        f'independent "{niche}" clothing footwear stores {region_term}',
        f'top trending "{niche}" brands {region_term}',
        f'"{niche}" "free shipping on orders over" {region_term}',
        f'"{niche}" "add to bag" "view cart" {region_term}',
        f'"{niche}" "powered by shopify" London Manchester' if region == "UK" else f'"{niche}" "powered by shopify" New York Los Angeles',
        f'"{niche}" "customer reviews" "secure checkout" {region_term}'
    ]
    return queries

def search_duckduckgo(query: str, max_results: int = 40) -> List[str]:
    """Searches DuckDuckGo for e-commerce stores."""
    urls = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            for r in results:
                href = r.get("href") or r.get("link") or ""
                root = clean_url_to_root(href)
                if root and root not in urls:
                    urls.append(root)
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
    return urls

def search_bing_fallback(query: str, max_results: int = 30) -> List[str]:
    """Fallback web search parser if DDG is throttled."""
    urls = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}&count={max_results}"
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http") and "bing.com" not in href and "microsoft.com" not in href:
                    root = clean_url_to_root(href)
                    if root and root not in urls:
                        urls.append(root)
    except Exception:
        pass
    return urls

def find_shopify_stores(niche: str, region: str = "UK", limit: int = 20) -> List[Dict[str, str]]:
    """
    Finds up to `limit` e-commerce stores (Shopify, WooCommerce, D2C)
    matching the niche and region.
    """
    found_urls: Set[str] = set()
    leads: List[Dict[str, str]] = []
    
    queries = generate_search_queries(niche, region)
    
    for q in queries:
        if len(leads) >= limit:
            break
            
        results = search_duckduckgo(q, max_results=min(40, limit * 2))
        if not results:
            results = search_bing_fallback(q, max_results=30)
            
        for url in results:
            if url not in found_urls:
                found_urls.add(url)
                leads.append({
                    "url": url,
                    "niche": niche,
                    "region": region,
                    "source": "Web Search"
                })
                if len(leads) >= limit:
                    break
                    
    return leads
