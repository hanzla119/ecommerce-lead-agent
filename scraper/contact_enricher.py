import re
import urllib.parse
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Excluded generic email patterns
EXCLUDED_EMAILS = {
    "support@shopify.com", "info@shopify.com", "contact@shopify.com",
    "example@domain.com", "email@example.com", "your@email.com",
    "name@domain.com", "user@domain.com", "test@test.com", "press@shopify.com"
}

def clean_brand_name(url: str, title: str = "", og_site_name: str = "") -> str:
    """Extracts clean brand name from metadata or domain."""
    if og_site_name and len(og_site_name.strip()) > 1:
        return og_site_name.strip()
    if title:
        parts = re.split(r"[|\-–—:]", title)
        candidate = parts[0].strip()
        if candidate and len(candidate) < 35 and "home" not in candidate.lower():
            return candidate
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.replace("www.", "").split(".")[0]
    return domain.capitalize()

def extract_emails_from_text(text: str) -> List[str]:
    """Finds valid email addresses within HTML/text."""
    if not text:
        return []
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    found = re.findall(email_pattern, text)
    valid = []
    for e in found:
        e = e.lower().strip(".")
        if e not in EXCLUDED_EMAILS and not e.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            if e not in valid:
                valid.append(e)
    return valid

def search_linkedin_founder(brand_name: str, domain: str, region: str = "UK") -> Dict[str, str]:
    """Searches for the Founder, CEO, or Marketing Director on LinkedIn."""
    if not brand_name or len(brand_name) < 2:
        return {"founder_name": "", "founder_title": "", "founder_linkedin": ""}
        
    query = f'site:linkedin.com/in/ "{brand_name}" (founder OR ceo OR "co-founder" OR owner OR "managing director")'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                href = r.get("href", "")
                title = r.get("title", "")
                if "linkedin.com/in/" in href:
                    # Clean title: "John Doe - Founder & CEO - Brand | LinkedIn"
                    clean_title = re.sub(r"\|.*LinkedIn.*$", "", title).strip()
                    parts = re.split(r"[-–—]", clean_title)
                    name = parts[0].strip() if len(parts) > 0 else ""
                    role = parts[1].strip() if len(parts) > 1 else "Founder / Decision Maker"
                    if name and len(name.split()) <= 4:
                        return {
                            "founder_name": name,
                            "founder_title": f"{role} at {brand_name}",
                            "founder_linkedin": href
                        }
    except Exception:
        pass
        
    return {"founder_name": "", "founder_title": "", "founder_linkedin": ""}

def enrich_store_contacts(url: str, region: str = "UK") -> Dict[str, any]:
    """
    Crawls the store website for contact info, social links, brand name,
    and searches LinkedIn for decision-makers.
    """
    contacts = {
        "brand_name": "",
        "email": "",
        "all_emails": [],
        "instagram": "",
        "instagram_handle": "",
        "facebook": "",
        "tiktok": "",
        "tiktok_handle": "",
        "linkedin_company": "",
        "founder_name": "",
        "founder_title": "",
        "founder_linkedin": "",
        "phone": ""
    }
    
    if not url.startswith("http"):
        url = "https://" + url
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    pages_to_crawl = [
        url,
        f"{url.rstrip('/')}/pages/contact",
        f"{url.rstrip('/')}/pages/contact-us",
        f"{url.rstrip('/')}/pages/about",
        f"{url.rstrip('/')}/pages/about-us",
        f"{url.rstrip('/')}/policies/terms-of-service",
        f"{url.rstrip('/')}/policies/privacy-policy"
    ]
    
    found_emails = []
    og_title = ""
    og_site_name = ""
    
    for page_url in pages_to_crawl:
        try:
            res = requests.get(page_url, headers=headers, timeout=5, allow_redirects=True)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Extract meta titles
                if not og_site_name:
                    meta_site = soup.find("meta", property="og:site_name")
                    if meta_site and meta_site.get("content"):
                        og_site_name = meta_site["content"]
                        
                if not og_title and soup.title:
                    og_title = soup.title.string or ""
                    
                # Extract mailto links
                for mailto in soup.select('a[href^="mailto:"]'):
                    href_email = mailto["href"].replace("mailto:", "").split("?")[0].strip()
                    if href_email:
                        cleaned = extract_emails_from_text(href_email)
                        for e in cleaned:
                            if e not in found_emails:
                                found_emails.append(e)
                                
                # Extract page text emails
                text_emails = extract_emails_from_text(res.text)
                for e in text_emails:
                    if e not in found_emails:
                        found_emails.append(e)
                        
                # Extract social links
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "instagram.com/" in href and not contacts["instagram"]:
                        if not any(x in href for x in ["/p/", "/reel/", "/stories/", "/explore/"]):
                            contacts["instagram"] = href
                            m = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", href)
                            if m:
                                contacts["instagram_handle"] = f"@{m.group(1).strip('/')}"
                                
                    elif "facebook.com/" in href and not contacts["facebook"]:
                        if not any(x in href for x in ["/sharer", "/plugins", "/tr?"]):
                            contacts["facebook"] = href
                            
                    elif "tiktok.com/" in href and not contacts["tiktok"]:
                        contacts["tiktok"] = href
                        m = re.search(r"tiktok\.com/@([a-zA-Z0-9_.]+)", href)
                        if m:
                            contacts["tiktok_handle"] = f"@{m.group(1).strip('/')}"
                            
                    elif "linkedin.com/company/" in href and not contacts["linkedin_company"]:
                        contacts["linkedin_company"] = href
                        
                # Extract phone numbers
                if not contacts["phone"]:
                    tel_a = soup.find("a", href=re.compile(r"^tel:"))
                    if tel_a:
                        contacts["phone"] = tel_a["href"].replace("tel:", "").strip()
        except Exception:
            continue
            
    # Brand Name Resolution
    contacts["brand_name"] = clean_brand_name(url, og_title, og_site_name)
    contacts["all_emails"] = found_emails
    
    # Select Primary Contact Email (prioritize hello@, info@, contact@, support@)
    if found_emails:
        priority_emails = [e for e in found_emails if any(e.startswith(p) for p in ["hello@", "info@", "contact@", "support@", "team@", "sales@"])]
        contacts["email"] = priority_emails[0] if priority_emails else found_emails[0]
        
    # Search LinkedIn for Founder / CEO
    parsed_netloc = urllib.parse.urlparse(url).netloc
    founder_info = search_linkedin_founder(contacts["brand_name"], parsed_netloc, region=region)
    contacts.update(founder_info)
    
    return contacts
