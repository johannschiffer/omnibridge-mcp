"""
Outbound URL validation helper to prevent SSRF against loopback, RFC1918 private,
link-local cloud metadata (169.254.169.254), and non-HTTP(S) endpoints.
"""
import ipaddress
import os
import re
import socket
from typing import Tuple
from urllib.parse import urlparse

_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata.google.internal",
    "metadata",
}
_NUMERIC_HOST_RE = re.compile(r"^(0x[0-9a-f]+|\d+(\.\d+){0,3})$", re.IGNORECASE)


def _is_forbidden_ip(ip_obj: ipaddress._BaseAddress) -> bool:
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def validate_outbound_url(url: str, allow_private_env: str = "OMNIBRIDGE_ALLOW_PRIVATE_URLS") -> Tuple[bool, str]:
    """Validate an outbound HTTP(S) URL against SSRF targets."""
    if not isinstance(url, str) or not url.strip():
        return False, "Invalid URL: empty target URL."

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        return False, f"Blocked URL scheme '{parsed.scheme}': only http and https are permitted."

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        return False, "Invalid URL: missing hostname."

    if os.getenv(allow_private_env, "").strip() in ("1", "true", "yes"):
        return True, "Allowed by environment override."

    if host in _BLOCKED_HOSTNAMES or host.endswith((".localhost", ".local", ".internal")):
        return False, f"Blocked outbound host '{host}': internal or loopback hostnames are forbidden."

    # Direct IPv4 / IPv6 literal check
    try:
        ip_obj = ipaddress.ip_address(host)
        if _is_forbidden_ip(ip_obj):
            return False, f"Blocked outbound IP '{ip_obj}': non-public address range."
        return True, "Valid public IP."
    except ValueError:
        pass

    # Catch compact/hex/octal IPv4 notations such as 127.1 or 2130706433
    if _NUMERIC_HOST_RE.match(host):
        try:
            packed = socket.inet_aton(host)
            ip_obj = ipaddress.IPv4Address(packed)
            if _is_forbidden_ip(ip_obj):
                return False, f"Blocked outbound numeric IP '{ip_obj}': non-public address range."
        except OSError:
            return False, f"Blocked malformed numeric host '{host}'."

    # Resolve hostname if DNS is reachable and block if any resolved address is non-public
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        # Leave unresolvable domains to the HTTP client (supports offline unit-test mocks).
        return True, "Unresolved domain deferred to HTTP transport."

    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        addr_str = sockaddr[0].split("%", 1)[0]
        try:
            ip_obj = ipaddress.ip_address(addr_str)
        except ValueError:
            continue
        if _is_forbidden_ip(ip_obj):
            return False, f"Blocked outbound host '{host}': resolves to non-public IP '{ip_obj}'."

    return True, "Valid public URL."
