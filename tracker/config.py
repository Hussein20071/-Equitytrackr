"""Static configuration: universe, portfolio weights, benchmark, data policy."""

from __future__ import annotations

# Research universe: ticker -> display name. Yahoo uses ".L" suffix for LSE.
UNIVERSE: dict[str, str] = {
    "AZN.L": "AstraZeneca",
    "SHEL.L": "Shell",
    "HSBA.L": "HSBC Holdings",
    "ULVR.L": "Unilever",
    "GSK.L": "GSK",
    "BP.L": "BP",
    "NG.L": "National Grid",
    "RIO.L": "Rio Tinto",
}

BENCHMARK: str = "^FTSE"  # FTSE 100 index on Yahoo Finance
CURRENCY_NOTE: str = "All LSE prices are quoted in GBp (pence); "
"figures are converted to GBP where shown."

# Model portfolio: ticker -> target weight (sums to 1.0)
PORTFOLIO: dict[str, float] = {
    "AZN.L": 0.20,
    "SHEL.L": 0.15,
    "HSBA.L": 0.15,
    "ULVR.L": 0.10,
    "GSK.L": 0.10,
    "BP.L": 0.10,
    "NG.L": 0.10,
    "RIO.L": 0.10,
}

REFRESH_INTERVAL_MINUTES: int = 5

# Where everything is written. Relative to the project root.
DATA_DIR = "data"
NOTES_DIR = "notes"
DASHBOARD_PATH = "dashboard/index.html"

# Data-source policy: every fetch is logged to the audit trail so a note's
# inputs can be traced back to the exact download that produced them.
DATA_SOURCES: dict[str, str] = {
    "prices": "Yahoo Finance via yfinance (daily + intraday snapshots)",
    "fundamentals": "Yahoo Finance via yfinance Ticker.info / financials",
    "benchmark": "Yahoo Finance ^FTSE daily closes",
}

DISCLAIMER = (
    "Educational project. Not investment advice. Data may be delayed or "
    "inaccurate; verify independently before acting on anything here."
)

FOOTER_DISCLAIMER = (
    "Personal educational project. Not investment advice. "
    "Not affiliated with any firm."
)

REPO_URL = "https://github.com/Hussein20071/-Equitytrackr"

# Short-tenor UK risk-free rate for portfolio metrics (Sharpe): OECD 3-month
# immediate/interbank rate via FRED. IR3MGBM156N was tested and does not exist
# (404); IR3TIB01GBM156N does. fundamentals.short_rate_uk() falls back to the
# 10Y gilt (disclosed) if the 3M series is unavailable.
RF_SHORT_SERIES = "IR3TIB01GBM156N"
