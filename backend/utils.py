import secrets
import ipaddress
import re


# Generate a random slug (fallback)
def gen_random_slug(n: int = 8) -> str:
    """Generate a secure random alphanumeric slug."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))


def slugify(text: str) -> str:
    """Convert title into a clean, URL-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "qr"


def gen_slug(title: str | None = None, n: int = 8) -> str:
    """
    Generate a human-readable slug if a title is given.
    Falls back to random secure slug otherwise.
    """
    if title and title.strip():
        return slugify(title)
    return gen_random_slug(n)


def mask_ip(ip: str | None) -> str | None:
    """Simple anonymizer: replaces last IPv4 segment with 0."""
    if not ip:
        return None
    try:
        addr = ip.split(":")[0]  # Strip port if present
        ipaddress.ip_address(addr)
        parts = addr.split(".")
        if len(parts) == 4:
            parts[-1] = "0"
            return ".".join(parts)
        return addr
    except Exception:
        return None
