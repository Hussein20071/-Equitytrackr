"""UK Equity Research & Portfolio Tracker.

An audit-ready equity research and portfolio attribution system covering
FTSE 100 names. Each published research note records its thesis date,
explicit valuation inputs, price target, data sources, and a rolling
3-month performance vs the FTSE 100.

Package layout:
    config      -- static universe, weights, data-source policy
    data        -- live market data (yfinance) with a full fetch audit log
    valuation   -- DCF, comparables, blended price target
    research    -- research-note lifecycle (draft -> publish) with immutable
                   snapshots of the inputs used at publication time
    performance -- portfolio vs FTSE 100 attribution and hit-rate tracking
    refresh     -- scheduled live updates (default every 5 minutes)
    reporting   -- self-audit checks and the generated HTML dashboard
"""

__version__ = "0.1.0"
