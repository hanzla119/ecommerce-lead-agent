import re
import dns.resolver
from typing import Dict

# Cache to avoid repetitive DNS lookups for the same domain
MX_CACHE: Dict[str, bool] = {}

def verify_email_deliverability(email: str) -> Dict[str, any]:
    """
    Validates email format and performs a live DNS MX lookup to check if
    the domain is configured to receive emails.
    """
    if not email or not isinstance(email, str):
        return {"email": email, "is_valid_format": False, "mx_found": False, "status": "Invalid Format"}
        
    email = email.strip().lower()
    
    # 1. Syntax Regex Check
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, email):
        return {"email": email, "is_valid_format": False, "mx_found": False, "status": "Invalid Syntax"}
        
    domain = email.split("@")[1]
    
    # Check cache first
    if domain in MX_CACHE:
        has_mx = MX_CACHE[domain]
        return {
            "email": email,
            "is_valid_format": True,
            "mx_found": has_mx,
            "status": "Verified (Deliverable)" if has_mx else "No MX Record"
        }
        
    # 2. DNS MX Record Lookup
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3.0
        resolver.lifetime = 3.0
        records = resolver.resolve(domain, "MX")
        has_mx = len(records) > 0
        MX_CACHE[domain] = has_mx
        return {
            "email": email,
            "is_valid_format": True,
            "mx_found": has_mx,
            "status": "Verified (Deliverable)" if has_mx else "No MX Record"
        }
    except Exception:
        # If MX lookup fails, check for A record fallback
        try:
            records = resolver.resolve(domain, "A")
            has_a = len(records) > 0
            MX_CACHE[domain] = has_a
            return {
                "email": email,
                "is_valid_format": True,
                "mx_found": has_a,
                "status": "Verified (Deliverable)" if has_a else "No Mail Server"
            }
        except Exception:
            MX_CACHE[domain] = False
            return {
                "email": email,
                "is_valid_format": True,
                "mx_found": False,
                "status": "Undeliverable Domain"
            }
