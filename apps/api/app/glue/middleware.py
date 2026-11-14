# Scaffold-owned glue file (KNM-085). Modules register at the markers below; do not edit the marked lines by hand.
# knm:imports
from app.cache.middleware import cache_middleware  # knm:module memory-cache
from app.audit.middleware import audit_middleware  # knm:module audit-trail
from app.auth.middleware import authenticate  # knm:module jwt-auth

middleware: list[dict[str, object]] = [
    # knm:entries
    {"id": "jwt-auth", "handler": authenticate},  # knm:module jwt-auth
    {"id": "audit-trail", "handler": audit_middleware},  # knm:module audit-trail
    {"id": "memory-cache", "handler": cache_middleware},  # knm:module memory-cache
    # knm:entries-end
]
