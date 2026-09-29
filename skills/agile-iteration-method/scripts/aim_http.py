# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_http.py
"""Local HTTP trust boundary for the AIM control room."""

from __future__ import annotations

from email.message import Message


def local_request_allowed(headers: Message, port: int, *, mutation: bool = False) -> bool:
    """Reject rebinding/ambiguous authorities before serving any local data.

    An Origin matching an attacker-controlled Host is not evidence of locality.
    Compare Host to the actual listener port, without consulting DNS or forwarded
    headers. Require a same-origin browser request for mutations.
    """
    hosts = headers.get_all("Host", [])
    origins = headers.get_all("Origin", [])
    if len(hosts) != 1 or hosts[0] not in {
        f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}",
    }:
        return False
    if len(origins) > 1:
        return False
    expected = f"http://{hosts[0]}"
    if origins and origins[0] != expected:
        return False
    return not mutation or origins == [expected]
