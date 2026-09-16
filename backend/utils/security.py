from __future__ import annotations

import ipaddress
import os
import re
import socket
from urllib.parse import urlparse

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "100"))
ALLOW_LOCAL_URLS = os.getenv("ALLOW_LOCAL_URLS", "false").lower() in ("true", "1", "yes")

# Allowed cloud object storage hosts / patterns if configured
ALLOWED_HOSTS_PATTERN = os.getenv("ALLOWED_STORAGE_HOSTS", "")


def is_allowed_file_extension(filename: str) -> bool:
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


def validate_remote_url(url: str) -> None:
    """Validate remote video URL to protect against SSRF and private network access."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: missing hostname")

    if not ALLOW_LOCAL_URLS:
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
            raise ValueError("Access to internal/localhost addresses is prohibited.")

        # Resolve IP to check for private or link-local subnets
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip = ipaddress.ip_address(ip_str)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise ValueError(f"Access to private IP address {ip_str} is prohibited.")
        except socket.gaierror as exc:
            raise ValueError(f"Could not resolve hostname '{hostname}': {exc}")

    # If domain allowlist is configured, verify
    if ALLOWED_HOSTS_PATTERN:
        pattern = re.compile(ALLOWED_HOSTS_PATTERN)
        if not pattern.search(hostname):
            raise ValueError(f"Host '{hostname}' is not in the approved storage domain list.")
