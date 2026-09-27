from urllib.parse import urlparse
from urllib.parse import ParseResult
import re
import pandas as pd
import ipaddress

suspicious_keywords = set(["login", "secure", "verify", "update","confirm", "free", "win", "password", "account", "bank", "ebay", "ebayisapi", "paypal", "signin", "validate", "support", "admin"])

suspicious_tlds = set(["zip", "cricket", "link", "work", "download", "party", "gq", "ml", "cf", "tk", "cn", "ru", "xyz", "top", "info", "biz", "men", "loan", "click", "date"])

executable_exts = set([".exe", ".msi", ".bat", ".cmd", ".scr", ".pif", ".jar", ".wsf", ".vbs", ".js", ".jse", ".ps1", ".sh", ".gadget", ".reg", ".dll", ".drv", ".sys", ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".img"])

with open("model/datasets/top-1m.csv") as f:
    top_domains = set(line.strip().split(",")[1].lower() for line in f)

def add_scheme(url):
    if pd.isna(url):
        return None

    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        parsed = urlparse('http://' + url)

    return parsed



def fix_ipv6_url(parsed):
    netloc = parsed.netloc

    if '@' in netloc:
        userinfo, hostport = netloc.rsplit('@', 1)
    else:
        userinfo, hostport = '', netloc

    if hostport.startswith('[') and ']' in hostport:
        return parsed
    
    ipv6_no_bracket_pattern = r'^([0-9a-fA-F:]+)(:\d+)?$'

    if re.match(ipv6_no_bracket_pattern, hostport) and not (hostport.startswith('[') and ']' in hostport):
        if ':' in hostport:
            host, port = hostport.rsplit(':', 1)
            if port.isdigit():
                hostport = f"[{host}]:{port}"
            else:
                hostport = f"[{hostport}]"
        else:
            hostport = f"[{hostport}]"
 

    new_netloc = f"{userinfo}@{hostport}" if userinfo else hostport

    return parsed._replace(netloc=new_netloc)



def is_ip_address(hostname):
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False
    


def is_valid_url(url):
    if not isinstance(url, str) or not url.strip():
        return False
    
    if '.' not in url or '/' not in url:
        return False
    
    return True



def safe_parse_url(url):
    try:
        if not is_valid_url(url):
            return None
        
        parsed = add_scheme(url)
        parsed = fix_ipv6_url(parsed)

        return parsed
    
    except Exception as e:
        print(f"Error parsing URL {repr(url)}: {e}")
        return None
    


def extract_features(url):
    # url = urlparse(url).scheme
    url = url.strip()
    parsed = safe_parse_url(url)
    
    if parsed is None:
        return {
            "url_length": 0,
            "hostname_length": 0,
            "num_dots": 0,
            "num_hyphens": 0,
            "num_digits": 0,
            "num_subdomains": 0,
            "path_depth": 0,
            "path_length": 0,
            "has_suspicious_keywords": 0,
            "has_suspicious_tlds": 0,
            "common_domain": 0,
            "has_ip": 0,
            "has_executable_ext": 0,
            "has_double_extension": 0,
            "has_query": 0
        }

    hostname = (parsed.hostname or "").lower()
    parts = hostname.split('.') if hostname else  []
    tld = parts[-1] if parts else ""
    path = parsed.path.lower()

    features = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "num_dots": hostname.count('.'),
        "num_hyphens": hostname.count('-'),
        "num_digits": sum(c.isdigit() for c in hostname),
        "num_subdomains": hostname.count(".") - 1 if hostname else 0,
        "path_depth": path.rstrip('/').count('/'),
        "path_length": len(path),

        "has_suspicious_keywords": int(any(sus_key in hostname for sus_key in suspicious_keywords)),
        "has_suspicious_tlds": int(tld in suspicious_tlds),
        "common_domain": 1 if hostname in top_domains else 0,
        "has_ip": int(is_ip_address(hostname)),
        
        "has_executable_ext": int(any(path.endswith(ext) for ext in executable_exts)),
        "has_double_extension": int(path.count('.') >= 2 and (any(path.endswith(ext) for ext in executable_exts))),
        "has_query": int(bool(parsed.query))
    }

    return features



def is_top_domain(url):
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        
        parts = hostname.split('.')

        for i in range(len(parts) - 1):
            candidate = ".".join(parts[i:])
            if candidate in top_domains:
                return True
        
        return False
    
    except Exception as e:
        print("Error Processing URL:", url, e)
        return False