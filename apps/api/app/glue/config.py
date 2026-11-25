# Scaffold-owned glue file (KNM-085). Modules register at the markers below; do not edit the marked lines by hand.
# knm:imports

config: list[dict[str, object]] = [
    # knm:entries
    {"key": "PORT", "default": "8000"},  # knm:module fastapi
    {"key": "DATABASE_URL", "default": "libsql://tursodemo-busettypavan.aws-ap-south-1.turso.io"},  # knm:module sqlalchemy-db
    {"key": "JWT_SECRET", "default": ""},  # knm:module jwt-auth
    {"key": "CACHE_TTL_SECONDS", "default": "30"},  # knm:module memory-cache
    {"key": "COOKIE_SECURE", "default": "true"},  # knm:module accounts
    {"key": "TOKEN_TTL_SECONDS", "default": "3600"},  # knm:module accounts
    {"key": "LOGIN_MAX_FAILURES", "default": "5"},  # knm:module accounts
    {"key": "LOGIN_LOCK_SECONDS", "default": "900"},  # knm:module accounts
    {"key": "RESET_TTL_SECONDS", "default": "900"},  # knm:module accounts
    # knm:entries-end
]
