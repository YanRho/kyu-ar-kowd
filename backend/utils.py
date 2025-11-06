import secrets
import ipaddress


# Generate a random slug of given length
def gen_slug(n: int = 8 ) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

# Simple IP anonymizer so that we don't store full IPs
def mask_ip(ip: str | None) -> str | None:
    """Simple anonymizer: replaces last IPv4 segment with 0."""
    if not ip:
        return None
    try:
        addr = ip.split(":")[0]  
        ipaddress.ip_address(addr) 
        parts = addr.split(".")    
        if len(parts) == 4:         
            parts[-1] = "0"
            return ".".join(parts)
        return addr                 
    except Exception:
        return None