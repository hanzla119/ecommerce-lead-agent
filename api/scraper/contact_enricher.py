import re
import urllib.parse
from typing import Dict, Optional, List, Tuple
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

# Common email domains/placeholders to filter out
DISALLOWED_EMAIL_DOMAINS = {
    "shopify.com", "myshopify.com", "example.com", "domain.com", 
    "sentry.io", "wixpress.com", "google.com", "facebook.com", "schema.org", "w3.org"
}

def extract_brand_name(soup: BeautifulSoup, base_url: str) -> str:
    """Extracts clean brand name from OG tags, title, or domain."""
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        return og_site["content"].strip()
        
    title = soup.title.string if soup.title else ""
    if title:
        clean_title = re.split(r'[|\-–—:]', title)[0].strip()
        if clean_title and len(clean_title) < 35:
            return clean_title
            
    parsed = urllib.parse.urlparse(base_url)
    domain_part = parsed.netloc.replace("www.", "").split(".")[0]
    return domain_part.capitalize()

def find_emails_in_html(html_text: str) -> List[str]:
    """Finds valid email addresses in text/html with strict validation."""
    raw_emails = re.findall(EMAIL_REGEX, html_text)
    valid_emails = []
    
    for email in raw_emails:
        email = email.lower().strip(".,;:()\"' ")
        if any(email.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".css", ".js", ".woff", ".ttf"]):
            continue
        if "@" not in email:
            continue
        domain = email.split("@")[-1]
        if domain in DISALLOWED_EMAIL_DOMAINS or len(domain) < 4:
            continue
        if ".." in email or len(email) > 60:
            continue
        if email not in valid_emails:
            valid_emails.append(email)
            
    return valid_emails

def extract_social_links(soup: BeautifulSoup) -> Dict[str, str]:
    """Finds and normalizes official Instagram, Facebook, TikTok, and LinkedIn links."""
    socials = {
        "instagram": "",
        "instagram_handle": "",
        "facebook": "",
        "tiktok": "",
        "tiktok_handle": "",
        "linkedin_company": ""
    }
    
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        
        # Instagram
        if "instagram.com/" in href and not socials["instagram"]:
            if not any(x in href.lower() for x in ["/p/", "/reel/", "/explore/", "/stories/", "sharer"]):
                clean_ig = href.split("?")[0].rstrip("/")
                parts = clean_ig.split("instagram.com/")
                if len(parts) > 1 and parts[1]:
                    handle = parts[1].strip("/")
                    if handle.lower() not in ["shopify", "p", "explore"]:
                        socials["instagram"] = clean_ig
                        socials["instagram_handle"] = f"@{handle}"
                        
        # Facebook
        elif "facebook.com/" in href and not socials["facebook"]:
            if not any(x in href.lower() for x in ["/sharer", "/share", "/dialog", "tr?id="]):
                socials["facebook"] = href.split("?")[0]
                
        # TikTok
        elif "tiktok.com/" in href and not socials["tiktok"]:
            clean_tt = href.split("?")[0].rstrip("/")
            if "@" in clean_tt:
                socials["tiktok"] = clean_tt
                socials["tiktok_handle"] = "@" + clean_tt.split("@")[-1]
                
        # LinkedIn Company
        elif "linkedin.com/company/" in href and not socials["linkedin_company"]:
            socials["linkedin_company"] = href.split("?")[0]
            
    return socials

def find_founder_linkedin(brand_name: str, region: str = "UK") -> Dict[str, str]:
    """
    Finds founder/decision-maker's LinkedIn profile via free Google/DuckDuckGo X-Ray search.
    """
    if not brand_name or len(brand_name) < 2 or brand_name.lower().startswith("http"):
        return {"founder_name": "", "founder_title": "", "linkedin_url": "", "snippet": ""}
        
    query = f'site:linkedin.com/in ("Founder" OR "Owner" OR "CEO" OR "Co-Founder" OR "Managing Director") "{brand_name}"'
    
    ddgs = DDGS()
    try:
        results = ddgs.text(query, max_results=3)
        if results:
            for r in results:
                url = r.get("href", "")
                title = r.get("title", "")
                snippet = r.get("body", "")
                
                if "linkedin.com/in/" in url:
                    # Clean title: "John Doe - Founder & CEO - Brand | LinkedIn"
                    name_parts = re.split(r'[-–—|]', title)
                    founder_name = name_parts[0].strip() if name_parts else ""
                    founder_title = name_parts[1].strip() if len(name_parts) > 1 else "Founder / Owner"
                    
                    # Remove "LinkedIn" from name if present
                    founder_name = founder_name.replace("LinkedIn", "").strip()
                    
                    return {
                        "founder_name": founder_name,
                        "founder_title": founder_title,
                        "linkedin_url": url,
                        "snippet": snippet
                    }
    except Exception:
        pass
        
    return {"founder_name": "", "founder_title": "", "linkedin_url": "", "snippet": ""}

def enrich_store_contacts(store_url: str, region: str = "UK") -> Dict:
    """
    Crawls store homepage + contact subpages to extract emails, Instagram, TikTok, Facebook, and founder LinkedIn.
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
        "founder_linkedin": ""
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    html_corpus = ""
    soup = None
    
    # 1. Fetch Homepage
    try:
        res = requests.get(store_url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            html_corpus += " " + res.text
            contacts["brand_name"] = extract_brand_name(soup, store_url)
            socials = extract_social_links(soup)
            contacts.update(socials)
            
            # Check for mailto links on homepage
            for a in soup.find_all("a", href=True):
                if a["href"].startswith("mailto:"):
                    raw_mail = a["href"].replace("mailto:", "").split("?")[0].strip()
                    if raw_mail and "@" in raw_mail:
                        contacts["email"] = raw_mail.lower()
    except Exception as e:
        print(f"[ContactEnricher] Homepage fetch warning for {store_url}: {e}")
        return contacts

    # 2. Check Subpages for Contact/Support Email
    subpaths = ["/pages/contact", "/pages/contact-us", "/pages/about-us", "/pages/about", "/policies/privacy-policy", "/pages/get-in-touch"]
    for path in subpaths:
        try:
            sub_url = urllib.parse.urljoin(store_url, path)
            sub_res = requests.get(sub_url, headers=headers, timeout=6)
            if sub_res.status_code == 200:
                html_corpus += " " + sub_res.text
                sub_soup = BeautifulSoup(sub_res.text, "html.parser")
                
                # Check mailto links on subpages
                for a in sub_soup.find_all("a", href=True):
                    if a["href"].startswith("mailto:"):
                        raw_mail = a["href"].replace("mailto:", "").split("?")[0].strip()
                        if raw_mail and "@" in raw_mail and not contacts["email"]:
                            contacts["email"] = raw_mail.lower()
                            
                sub_socials = extract_social_links(sub_soup)
                for k, v in sub_socials.items():
                    if v and not contacts[k]:
                        contacts[k] = v
        except Exception:
            continue

    # 3. Extract & prioritize primary email
    all_emails = find_emails_in_html(html_corpus)
    contacts["all_emails"] = all_emails
    if all_emails and not contacts["email"]:
        contacts["email"] = all_emails[0]
        # Prefer business prefixes
        for em in all_emails:
            if any(prefix in em for prefix in ["hello@", "info@", "contact@", "support@", "team@", "sales@", "press@", "founder@"]):
                contacts["email"] = em
                break

    # 4. Find Founder / Decision Maker LinkedIn
    brand = contacts["brand_name"]
    founder_info = find_founder_linkedin(brand, region=region)
    contacts["founder_name"] = founder_info.get("founder_name", "")
    contacts["founder_title"] = founder_info.get("founder_title", "")
    contacts["founder_linkedin"] = founder_info.get("linkedin_url", "")

    return contacts
