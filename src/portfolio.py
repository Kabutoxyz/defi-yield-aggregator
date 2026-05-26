"""Portfolio tracker - manage positions and calculate real APY."""

import json
import os
import time
from typing import Optional
from pathlib import Path

from src.yields import fetch_all_pools, parse_pool
from src.protocols import compute_pool_risk, get_risk_label

DEFAULT_PORTFOLIO_PATH = os.path.expanduser("~/.defi-yield-portfolio.json")


def _load_portfolio(path: str) -> dict:
    """Load portfolio from JSON file."""
    if not os.path.exists(path):
        return {"positions": [], "updated_at": None}
    with open(path, "r") as f:
        return json.load(f)


def _save_portfolio(portfolio: dict, path: str):
    """Save portfolio to JSON file."""
    portfolio["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(portfolio, f, indent=2)


def add_position(
    pool_id: str,
    amount_usd: float,
    entry_date: Optional[str] = None,
    notes: str = "",
    path: str = DEFAULT_PORTFOLIO_PATH,
) -> dict:
    """Add a new position to the portfolio."""
    portfolio = _load_portfolio(path)
    position = {
        "pool_id": pool_id,
        "amount_usd": amount_usd,
        "entry_date": entry_date or time.strftime("%Y-%m-%d"),
        "notes": notes,
        "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    portfolio["positions"].append(position)
    _save_portfolio(portfolio, path)
    return position


def remove_position(pool_id: str, path: str = DEFAULT_PORTFOLIO_PATH) -> bool:
    """Remove a position from the portfolio by pool ID."""
    portfolio = _load_portfolio(path)
    before = len(portfolio["positions"])
    portfolio["positions"] = [p for p in portfolio["positions"] if p["pool_id"] != pool_id]
    if len(portfolio["positions"]) < before:
        _save_portfolio(portfolio, path)
        return True
    return False


def get_positions(path: str = DEFAULT_PORTFOLIO_PATH) -> list[dict]:
    """Return all tracked positions."""
    portfolio = _load_portfolio(path)
    return portfolio.get("positions", [])


def calculate_portfolio_apy(path: str = DEFAULT_PORTFOLIO_PATH) -> list[dict]:
    """
    Fetch live yield data and match against portfolio positions.
    Returns enriched position data with current APY, risk, and projected earnings.
    """
    positions = get_positions(path)
    if not positions:
        return []

    all_pools = fetch_all_pools()
    pool_map = {}
    for raw in all_pools:
        p = parse_pool(raw)
        if p:
            pool_map[p["pool"].lower()] = p

    results = []
    total_invested = 0.0
    total_projected = 0.0

    for pos in positions:
        pid = pos["pool_id"].lower()
        pool_data = pool_map.get(pid)

        entry_date = pos.get("entry_date", "unknown")
        amount = pos.get("amount_usd", 0)
        total_invested += amount

        if pool_data:
            apy = pool_data["apy"]
            risk = compute_pool_risk(pool_data)
            projected_yearly = amount * (apy / 100)
            total_projected += projected_yearly

            # Calculate time-weighted return if entry date available
            try:
                entry = time.strptime(entry_date, "%Y-%m-%d")
                now = time.gmtime()
                days_held = max(1, (time.mktime(now) - time.mktime(entry)) / 86400)
                daily_rate = apy / 365
                realized_return = amount * ((1 + daily_rate / 100) ** days_held - 1)
            except (ValueError, TypeError):
                days_held = 0
                realized_return = 0

            results.append({
                "pool_id": pos["pool_id"],
                "chain": pool_data["chain"],
                "project": pool_data["project"],
                "symbol": pool_data["symbol"],
                "amount_usd": amount,
                "current_apy": apy,
                "apy_base": pool_data["apy_base"],
                "apy_reward": pool_data["apy_reward"],
                "tvl_usd": pool_data["tvl_usd"],
                "risk_score": risk,
                "risk_label": get_risk_label(risk),
                "projected_yearly": projected_yearly,
                "days_held": int(days_held),
                "estimated_return": realized_return,
                "entry_date": entry_date,
                "notes": pos.get("notes", ""),
                "status": "live",
            })
        else:
            results.append({
                "pool_id": pos["pool_id"],
                "amount_usd": amount,
                "current_apy": None,
                "risk_label": "Unknown",
                "projected_yearly": 0,
                "entry_date": entry_date,
                "notes": pos.get("notes", ""),
                "status": "pool not found",
            })

    # Summary
    for r in results:
        r["portfolio_total"] = total_invested
        r["portfolio_projected_yearly"] = total_projected
        r["weighted_apy"] = (total_projected / total_invested * 100) if total_invested > 0 else 0

    return results
