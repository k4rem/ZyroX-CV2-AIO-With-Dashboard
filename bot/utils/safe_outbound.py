"""Safe outbound HTTP(S) URL validation and bounded fetch (SSRF mitigation)."""

from __future__ import annotations

import ipaddress
import socket
from typing import Optional
from urllib.parse import urljoin, urlparse, urlunparse

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_REDIRECTS = 3

ALLOWED_SCHEMES = frozenset({"http", "https"})


class UnsafeURLError(ValueError):
    pass


def _normalize_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address):
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


def _ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    ip = _normalize_ip(ip)
    return bool(
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _hostname_blocked(name: str) -> bool:
    host = name.strip().lower().rstrip(".")
    if not host:
        return True
    if host == "localhost" or host.endswith(".localhost"):
        return True
    if host.endswith(".local") or host.endswith(".internal"):
        return True
    return False


def _parse_host_as_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    # Decimal / hex / octal IPv4 literals in URLs (e.g. http://3232235777/)
    if host.isdigit():
        try:
            return ipaddress.IPv4Address(int(host))
        except ValueError:
            return None
    if host.startswith("0x"):
        try:
            return ipaddress.IPv4Address(int(host, 16))
        except ValueError:
            return None
    return None


def _resolve_host_to_safe_ips(hostname: str) -> list[str]:
    if _hostname_blocked(hostname):
        raise UnsafeURLError(f"Blocked hostname: {hostname!r}")
    literal = _parse_host_as_ip(hostname)
    if literal is not None:
        if _ip_blocked(literal):
            raise UnsafeURLError(f"Blocked IP address: {hostname!r}")
        return [str(literal)]
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Cannot resolve hostname: {hostname!r}") from exc
    if not infos:
        raise UnsafeURLError(f"No addresses for hostname: {hostname!r}")
    safe: list[str] = []
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _ip_blocked(ip):
            raise UnsafeURLError(
                f"Hostname {hostname!r} resolves to blocked address {addr}"
            )
        safe.append(str(_normalize_ip(ip)))
    if not safe:
        raise UnsafeURLError(f"No usable addresses for hostname: {hostname!r}")
    return safe


def validate_http_url(url: str) -> str:
    if not url or not isinstance(url, str):
        raise UnsafeURLError("URL is required")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"Unsupported URL scheme: {parsed.scheme!r}")
    if parsed.username or parsed.password:
        raise UnsafeURLError("URLs with embedded credentials are not allowed")
    if not parsed.hostname:
        raise UnsafeURLError("URL must include a hostname")
    host = parsed.hostname
    _resolve_host_to_safe_ips(host)
    return urlunparse(parsed)


def _url_with_pinned_ip(url: str, pinned_ip: str) -> tuple[str, str]:
    """Return (request_url_with_ip, original_host_for_host_header_and_sni)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port
    ip_obj = ipaddress.ip_address(pinned_ip)
    if isinstance(ip_obj, ipaddress.IPv6Address):
        netloc_host = f"[{pinned_ip}]"
    else:
        netloc_host = pinned_ip
    if port:
        netloc = f"{netloc_host}:{port}"
    else:
        netloc = netloc_host
    request_url = urlunparse(parsed._replace(netloc=netloc))
    return request_url, host


async def safe_get_bytes(
    url: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    session=None,
) -> bytes:
    import aiohttp

    validate_http_url(url)
    timeout = aiohttp.ClientTimeout(total=15, connect=5)
    own_session = session is None
    if own_session:
        session = aiohttp.ClientSession(
            timeout=timeout,
            max_line_size=8190,
        )
    try:
        current = url
        for _ in range(DEFAULT_MAX_REDIRECTS + 1):
            validate_http_url(current)
            parsed = urlparse(current)
            host = parsed.hostname or ""
            safe_ips = _resolve_host_to_safe_ips(host)
            pinned_ip = safe_ips[0]
            request_url, host_header = _url_with_pinned_ip(current, pinned_ip)
            headers = {"Host": host_header}
            ssl_arg: bool | None = True
            if parsed.scheme == "https":
                ssl_arg = True
            async with session.get(
                request_url,
                allow_redirects=False,
                max_field_size=8190,
                headers=headers,
                ssl=ssl_arg,
                server_hostname=host_header if parsed.scheme == "https" else None,
            ) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    location = resp.headers.get("Location")
                    if not location:
                        raise UnsafeURLError("Redirect without Location header")
                    current = urljoin(current, location)
                    continue
                resp.raise_for_status()
                data = bytearray()
                async for chunk in resp.content.iter_chunked(65536):
                    data.extend(chunk)
                    if len(data) > max_bytes:
                        raise UnsafeURLError("Response exceeds size limit")
                return bytes(data)
        raise UnsafeURLError("Too many redirects")
    finally:
        if own_session:
            await session.close()
