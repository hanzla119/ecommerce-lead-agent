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

# Rich curated niche seed database to guarantee results across regions
CURATED_NICHE_SEEDS = {
    "footwear": {
        "UK": ["https://footdistrict.com", "https://offspring.co.uk", "https://size.co.uk", "https://schuh.co.uk", "https://tower-london.com", "https://footpatrol.com", "https://allsole.com", "https://lanxshoes.com", "https://crownnorthampton.com", "https://walshshoes.co.uk"],
        "America (US)": ["https://www.apbstore.com", "https://kith.com", "https://undefeated.com", "https://bodega.com", "https://featuresneakerboutique.com", "https://cncpts.com", "https://packershoes.com", "https://lapstoneandhammer.com", "https://atmosusa.com", "https://socialstatuspgh.com", "https://baitme.com", "https://extrabutterny.com", "https://saintalfred.com"],
        "Europe": ["https://www.overkillshop.com", "https://www.afew-store.com", "https://www.bstn.com", "https://www.titolo.ch", "https://caliroots.com", "https://sneakersnstuff.com", "https://www.patta.nl", "https://www.solebox.com", "https://www.sivasdescalzo.com"],
        "Australia": ["https://uptherestore.com", "https://www.subtypestore.com", "https://sneakerboy.com", "https://highsandlows.net.au", "https://supplystore.com.au", "https://laced.com.au", "https://usgstore.com.au", "https://abovegroundstore.com"]
    },
    "apparel": {
        "UK": ["https:// Representclo.com", "https://trapstarlondon.com", "https://corteiz.com", "https://manieredevoir.com", "https://pegador.com", "https://colebuxton.com", "https://persecloth.com", "https://unknownlondon.com"],
        "America (US)": ["https://rhude.com", "https://gallerydept.com", "https://johnelliott.com", "https://buckmason.com", "https://taylorstitch.com", "https://vuoriclothing.com", "https://aloyoga.com", "https://chubbieshorts.com"],
        "Europe": ["https://arte-antwerp.com", "https://daily-paper.com", "https://fillingpieces.com", "https://olafhussein.com", "https://waxlondon.com", "https://drole-de-monsieur.com"],
        "Australia": ["https://buttergoods.com", "https://pass-port.cc", "https://geedupclothing.com", "https://zanerobe.com", "https://assemblylabel.com", "https://venroy.com.au"]
    },
    "skincare": {
        "UK": ["https://bybi.com", "https://pai-skincare.com", "https://renskincare.com", "https://medik8.com", "https://facetheory.com", "https://wildcosmetics.com"],
        "America (US)": ["https://drunkelephant.com", "https://glossier.com", "https://summerfridays.com", "https://youthtothepeople.com", "https://supergoop.com", "https://herbivorebotanicals.com"],
        "Europe": ["https://typology.com", "https://rowse.co", "https://caudalie.com", "https://nuxe.com", "https://lixirskin.co.uk"],
        "Australia": ["https://gopurebeauty.com", "https://aussiecosmetics.com.au", "https://frankbody.com", "https://sandandsky.com", "https://bangnbody.com"]
    }
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
    reg_clean = region.replace("Market", "").replace("🇬🇧", "").replace("🇺🇸", "").replace("🇪🇺", "").replace("🇦🇺", "").replace("🇵🇰", "").strip()
    
    queries = [
        f'"{niche}" site:.co.uk "powered by shopify"' if "UK" in reg_clean.upper() else f'"{niche}" store "powered by shopify" {reg_clean}',
        f'best "{niche}" direct to consumer brands {reg_clean}',
        f'shop "{niche}" online "cart" "checkout" {reg_clean}',
        f'"{niche}" boutiques online {reg_clean}',
        f'independent "{niche}" online stores {reg_clean}',
        f'top trending "{niche}" brands {reg_clean}',
        f'"{niche}" "free shipping on orders over" {reg_clean}',
        f'"{niche}" "add to bag" "view cart" {reg_clean}',
        f'"{niche}" "customer reviews" "secure checkout" {reg_clean}'
    ]
    return queries

def search_duckduckgo(query: str, max_results: int = 40) -> List[str]:
    """Searches DuckDuckGo for e-commerce stores with safe timeout."""
    urls = []
    try:
        with DDGS(timeout=10) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            for r in results:
                href = r.get("href") or r.get("link") or ""
                root = clean_url_to_root(href)
                if root and root not in urls:
                    urls.append(root)
    except Exception:
        pass
    return urls

def search_html_direct(query: str, max_results: int = 30) -> List[str]:
    """Fallback HTML parser if standard search is throttled."""
    urls = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        res = requests.post(url, data={"q": query}, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", class_="result__url", href=True):
                href = a.get("href", "")
                if "//duckduckgo.com/l/?uddg=" in href:
                    href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
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
            
        results = search_duckduckgo(q, max_results=min(30, limit * 2))
        if not results:
            results = search_html_direct(q, max_results=min(25, limit * 2))
            
        for u in results:
            if u not in found_urls:
                found_urls.add(u)
                leads.append({
                    "url": u,
                    "query": q,
                    "region": region,
                    "source": "web"
                })
                if len(leads) >= limit:
                    break

    # If search returned fewer than needed, inject verified niche seeds
    if len(leads) < limit:
        niche_key = "footwear" if any(k in niche.lower() for k in ["footwear", "shoe", "sneaker"]) else ("skincare" if any(k in niche.lower() for k in ["skin", "beauty", "cosmetic"]) else "apparel")
        reg_map = "America (US)" if any(k in region.lower() for k in ["us", "america", "united states"]) else ("Europe" if "europe" in region.lower() else ("Australia" if "australia" in region.lower() else "UK"))
        
        seeds = CURATED_NICHE_SEEDS.get(niche_key, {}).get(reg_map, [])
        for s in seeds:
            clean_s = clean_url_to_root(s)
            if clean_s and clean_s not in found_urls:
                found_urls.add(clean_s)
                leads.append({
                    "url": clean_s,
                    "query": f"Curated {niche} in {region}",
                    "region": region,
                    "source": "curated_d2c"
                })
                if len(leads) >= limit:
                    break

    return leads[:limit]
