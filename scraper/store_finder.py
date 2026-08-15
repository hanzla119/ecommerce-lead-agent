import re
import urllib.parse
from typing import List, Set
from ddgs import DDGS

# List of domains to exclude (aggregators, search engines, marketplaces)
EXCLUDED_DOMAINS = {
    "shopify.com", "apps.shopify.com", "community.shopify.com",
    "facebook.com", "instagram.com", "tiktok.com", "linkedin.com", "youtube.com",
    "amazon.com", "amazon.co.uk", "ebay.com", "ebay.co.uk", "etsy.com", "pinterest.com",
    "reddit.com", "twitter.com", "x.com", "trustpilot.com", "yelp.com", "wikipedia.org",
    "quora.com", "medium.com", "aliexpress.com", "walmart.com", "target.com",
    "stockx.com", "asos.com", "zalando.co.uk", "shein.co.uk", "temu.com", "nike.com", "adidas.com",
    "costco.com", "wayfair.com", "sephora.com", "nordstrom.com", "zara.com", "hm.com"
}

def clean_url(url: str) -> str:
    """Extract clean base URL (protocol + domain)."""
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}".lower()

def is_valid_store_domain(domain_url: str) -> bool:
    """Check if the extracted domain is a valid independent e-commerce store."""
    if not domain_url:
        return False
    parsed = urllib.parse.urlparse(domain_url)
    netloc = parsed.netloc.lower()
    
    # Check if domain or any excluded domain matches
    for excluded in EXCLUDED_DOMAINS:
        if excluded in netloc or netloc.endswith(excluded):
            # Allow individual *.myshopify.com stores, but exclude main shopify.com
            if netloc != "shopify.com" and netloc.endswith(".myshopify.com"):
                continue
            return False
            
    # Filter common non-store patterns
    if any(p in domain_url for p in ["blog", "article", "news", "forum", "wiki", "youtube"]):
        return False
        
    return True

def find_shopify_stores(niche: str, region: str = "UK", max_results: int = 20) -> List[str]:
    """
    Discovers live e-commerce stores in target niches and regions using search queries (supports up to 200 leads).
    """
    discovered_stores: Set[str] = set()
    
    # Sub-queries to ensure we can scale up to 200+ unique stores
    queries = [
        f'{niche} online store {region} free delivery',
        f'{niche} {region} "powered by shopify"',
        f'{niche} "add to cart" {region} brand',
        f'site:myshopify.com {niche} {region}',
        f'{niche} boutique shop {region} "shipping"',
        f'best independent {niche} brands {region} "shop now"',
        f'{niche} direct to consumer store {region}',
        f'{niche} brand "checkout" {region}'
    ]
    
    # Add major cities for deeper regional search if needed
    if region.upper() == "UK":
        queries.extend([
            f'{niche} London store "add to cart"',
            f'{niche} Manchester online shop "shopify"',
            f'{niche} Birmingham e-commerce brand'
        ])
    elif region.upper() == "US":
        queries.extend([
            f'{niche} California store "powered by shopify"',
            f'{niche} New York boutique "checkout"',
            f'{niche} Texas online store'
        ])
    
    ddgs = DDGS()
    
    for query in queries:
        if len(discovered_stores) >= max_results:
            break
        try:
            results = ddgs.text(query, max_results=min(max_results * 2, 100))
            if results:
                for r in results:
                    raw_url = r.get("href", "")
                    base_url = clean_url(raw_url)
                    if base_url and is_valid_store_domain(base_url):
                        discovered_stores.add(base_url)
                        if len(discovered_stores) >= max_results:
                            break
        except Exception as e:
            print(f"[StoreFinder] Query note for '{query}': {e}")
            
    return list(discovered_stores)[:max_results]

if __name__ == "__main__":
    stores = find_shopify_stores("streetwear sneakers", "UK", max_results=10)
    print(f"Discovered Stores ({len(stores)}): {stores}")
