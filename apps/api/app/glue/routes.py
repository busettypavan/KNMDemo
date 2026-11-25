# Scaffold-owned glue file (KNM-085). Modules register at the markers below; do not edit the marked lines by hand.
# knm:imports
from app.auth.routes import mount as mount_accounts  # knm:module accounts
from app.stocks.routes import mount as mount_stocks  # knm:module stocks

routes: list[dict[str, object]] = [
    # knm:entries
    {"id": "accounts", "mount": mount_accounts},  # knm:module accounts
    {"id": "stocks", "mount": mount_stocks},  # knm:module stocks
    # knm:entries-end
]
