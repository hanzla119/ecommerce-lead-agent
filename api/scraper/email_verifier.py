import re
from typing import Dict, Tuple
import dns.resolver

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

# Cache verified domains in memory to avoid duplicate DNS lookups
_MX_CACHE: Dict[str, Tuple[bool, str]] = {}

def verify_email_deliverability(email: str) -> Dict[str, any]:
    """
    Verifies email syntax and checks domain MX (Mail Exchange) DNS records to confirm deliverability.
    Returns deliverability status, primary MX host, and reason.
    """
    if not email or not isinstance(email, str):
        return {"email": "", "is_valid": False, "mx_found": False, "status": "Empty Email"}
        
    email = email.strip().lower()
    
    # 1. Regex Syntax Check
    if not re.match(EMAIL_REGEX, email):
        return {"email": email, "is_valid": False, "mx_found": False, "status": "Invalid Syntax"}
        
    domain = email.split("@")[-1]
    
    # 2. Check MX Cache
    if domain in _MX_CACHE:
        is_mx, host = _MX_CACHE[domain]
        return {
            "email": email,
            "is_valid": True,
            "mx_found": is_mx,
            "mx_host": host,
            "status": "Verified (Deliverable)" if is_mx else "No Mail Server (Undeliverable)"
        }
        
    # 3. Perform DNS MX Query
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2.0
        resolver.lifetime = 2.0
        records = resolver.resolve(domain, 'MX')
        
        if records and len(records) > 0:
            # Sort by priority
            sorted_records = sorted(records, key=lambda r: r.preference)
            primary_mx = str(sorted_records[0].exchange).rstrip(".")
            _MX_CACHE[domain] = (True, primary_mx)
            return {
                "email": email,
                "is_valid": True,
                "mx_found": True,
                "mx_host": primary_mx,
                "status": "Verified (Deliverable)"
            }
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        # Fallback: Check if domain has an A record that handles mail
        try:
            a_records = resolver.resolve(domain, 'A')
            if a_records:
                _MX_CACHE[domain] = (True, "A Record Fallback")
                return {
                    "email": email,
                    "is_valid": True,
                    "mx_found": True,
                    "mx_host": "A Record Fallback",
                    "status": "Verified (A-Record)"
                }
        except Exception:
            pass
            
    _MX_CACHE[domain] = (False, "None")
    return {
        "email": email,
        "is_valid": True,
        "mx_found": False,
        "mx_host": "None",
        "status": "No Mail Server (Undeliverable)"
    }

if __name__ == "__main__":
    test1 = verify_email_deliverability("info@samedaytrainers.co.uk")
    print("Test 1 (Valid):", test1)
    test2 = verify_email_deliverability("fakeuser@fakeinvalidnonexistentdomain12345.com")
    print("Test 2 (Invalid domain):", test2)
