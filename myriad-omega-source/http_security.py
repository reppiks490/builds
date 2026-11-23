"""Strict loopback Host guard for an otherwise unauthenticated local research UI.

This guard mitigates DNS rebinding; it does not replace authentication, TLS,
CSRF tokens or perimeter controls for any remote deployment.
"""
from __future__ import annotations
import re

_HOST=re.compile(r'^(?:localhost|127\.0\.0\.1)(?::([0-9]{1,5}))?$|^\[::1\](?::([0-9]{1,5}))?$',re.I)

def localhost_host_allowed(host:str)->bool:
    if not isinstance(host,str) or any(c in host for c in '\r\n\t /@\\'):
        return False
    match=_HOST.fullmatch(host)
    if not match:return False
    port=next((x for x in match.groups() if x is not None),None)
    return port is None or 1<=int(port)<=65535


def mutation_request_allowed(host:str, origin:str, content_type:str)->bool:
    """CSRF surface restriction for loopback JSON mutations, not remote auth."""
    from urllib.parse import urlsplit
    if not localhost_host_allowed(host) or not isinstance(origin,str) or not isinstance(content_type,str):
        return False
    if content_type.split(';',1)[0].strip().lower()!='application/json':return False
    if not origin:return True  # CLI clients have no Origin; still local-only.
    parsed=urlsplit(origin)
    return (parsed.scheme in ('http','https') and parsed.netloc.lower()==host.lower()
            and parsed.username is None and parsed.password is None and not parsed.path
            and not parsed.query and not parsed.fragment)
