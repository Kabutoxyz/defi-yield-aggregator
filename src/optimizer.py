"""Yield optimizer - suggest best opportunities based on user preferences."""

from typing import Optional
from src.yields import fetch_all_pools, filter_pools, is_stablecoin_pool
from src.protocols import compute_pool_risk, get_risk_label
from src.chains import resolve_chain, DEFAULT_CHAINS


def score_pool(pool: dict, risk_tolerance: int, prefer_stablecoins: bool) -> float:
    """
    Score a pool from 0-100. Higher = better match for user preferences.

    Args:
        pool: Parsed pool dict
        risk_tolerance: 1 (conservative) to 5 (aggressive)
        prefer_stablecoins: Whether to boost stablecoin pool scores
    """
    risk = compute_pool_risk(pool)
    apy = pool.get("apy", 0)
    tvl = pool.get("tvl_usd", 0)

    # Penalize if pool risk exceeds user tolerance
    risk_delta = risk - risk_tolerance
    if risk_delta > 0:
        risk_penalty = risk_delta * 20
    else:
        risk_penalty = 0

    # APY component (diminishing returns above 50%)
    import math
    apy_score = min(apy, 50) * 1.2 + max(0, math.log(apy + 1) - 4) * 5 if apy > 0 else 0

    # TVL confidence bonus
    if tvl >= 100_000_000:
        tvl_bonus = 10
    elif tvl >= 10_000_000:
        tvl_bonus = 7
    elif tvl >= 1_000_000:
        tvl_bonus = 4
    else:
        tvl_bonus = 0

    # Stablecoin preference bonus
    stable_bonus = 8 if prefer_stablecoins and is_stablecoin_pool(pool) else 0

    score = apy_score + tvl_bonus + stable_bonus - risk_penalty
    return max(0, min(100, score))


def find_best_yields(
    chains: Optional[list[str]] = None,
    risk_tolerance: int = 3,
    prefer_stablecoins: bool = False,
    min_tvl: float = 100_000,
    min_apy: float = 0,
    limit: int = 20,
) -> list[dict]:
    """
    Fetch live data and return top yield opportunities ranked by score.

    Args:
        chains: List of chain names (None = all supported)
        risk_tolerance: 1 (conservative) to 5 (aggressive)
        prefer_stablecoins: Boost stablecoin pool scores
        min_tvl: Minimum TVL in USD
        min_apy: Minimum APY %
        limit: Max results
    """
    if chains:
        chains = [resolve_chain(c) for c in chains]

    all_pools = fetch_all_pools()

    # Generous pre-filter, let scoring handle ranking
    candidates = filter_pools(
        all_pools,
        chains=chains,
        stablecoins_only=False,
        min_tvl=min_tvl,
        min_apy=min_apy,
        limit=500,
    )

    # Score and rank
    for pool in candidates:
        pool["risk_score"] = compute_pool_risk(pool)
        pool["risk_label"] = get_risk_label(pool["risk_score"])
        pool["match_score"] = score_pool(pool, risk_tolerance, prefer_stablecoins)

    candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return candidates[:limit]


def compare_pools(pool_ids: list[str]) -> list[dict]:
    """Fetch live data and return details for specific pool IDs."""
    all_pools = fetch_all_pools()
    pool_id_set = set(pid.lower() for pid in pool_ids)
    results = []
    for raw in all_pools:
        pid = raw.get("pool", "").lower()
        if pid in pool_id_set:
            from src.yields import parse_pool
            p = parse_pool(raw)
            if p:
                p["risk_score"] = compute_pool_risk(p)
                p["risk_label"] = get_risk_label(p["risk_score"])
                results.append(p)
    results.sort(key=lambda x: x["apy"], reverse=True)
    return results
