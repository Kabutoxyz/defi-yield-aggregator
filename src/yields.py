"""Fetch and filter yield data from DeFiLlama API."""

import requests
from typing import Optional

DEFILLAMA_POOLS_URL = "https://yields.llama.fi/pools"

# Stablecoin token symbols
STABLECOINS = {
    "USDC", "USDT", "DAI", "BUSD", "TUSD", "USDP", "FRAX", "LUSD",
    "sUSD", "GUSD", "USDD", "USDN", "CUSD", "MIM", "UST", "agEUR",
    "EURT", "USDCE", "USDBC", "USDC.E", "DOLA", "ALUSD", "GHO",
    "CRVUSD", "PYUSD", "USDE", "EUSD", "USDX", "mkUSD", "USDC.E",
    "FRAXBP", "MUSD", "RUSD", "HUSD", "USDJ", "VAI", "DJED",
}

# Well-known protocol identifiers considered lower risk
ESTABLISHED_PROTOCOLS = {
    "aave-v3", "aave-v2", "compound-v3", "compound-v2", "lido",
    "maker", "uniswap-v3", "curve-dex", "convex-finance",
    "yearn-finance", "morpho", "spark", "sky", "rocket-pool",
    "pendle", "eigenlayer",
}

# Protocol identifiers with higher risk
HIGH_RISK_PROTOCOLS = {
    "tomb-finance", "wonderland", "inverse-finance", "cream-finance",
    "iron-finance", "snowball", "popsicle-finance",
}


def fetch_all_pools() -> list[dict]:
    """Fetch all pool data from DeFiLlama yields endpoint."""
    resp = requests.get(DEFILLAMA_POOLS_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def parse_pool(pool: dict) -> Optional[dict]:
    """Normalize a raw DeFiLlama pool into our internal format."""
    apy = pool.get("apy")
    tvl = pool.get("tvlUsd")
    if apy is None or tvl is None:
        return None

    return {
        "pool": pool.get("pool", ""),
        "chain": pool.get("chain", "Unknown"),
        "project": pool.get("project", "unknown"),
        "symbol": pool.get("symbol", "UNKNOWN"),
        "tvl_usd": float(tvl),
        "apy": float(apy),
        "apy_base": pool.get("apyBase") or 0.0,
        "apy_reward": pool.get("apyReward") or 0.0,
        "apy_mean_30d": pool.get("apyMean30d") or apy,
        "stablecoin": pool.get("stablecoin", False),
        "il_risk": pool.get("ilRisk", "no"),
        "exposure": pool.get("exposure", "single"),
        "pool_meta": pool.get("poolMeta", ""),
    }


def is_stablecoin_pool(pool: dict) -> bool:
    """Check if pool involves stablecoins."""
    if pool.get("stablecoin"):
        return True
    symbol = pool.get("symbol", "").upper()
    tokens = symbol.replace("/", "-").replace(" ", "-").split("-")
    return any(t.strip().upper() in STABLECOINS for t in tokens)


def filter_pools(
    pools: list[dict],
    chains: Optional[list[str]] = None,
    stablecoins_only: bool = False,
    min_tvl: float = 0,
    min_apy: float = 0,
    max_apy: float = 10000,
    project: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Filter parsed pools by criteria."""
    results = []
    for raw in pools:
        p = parse_pool(raw)
        if p is None:
            continue
        if chains and p["chain"].upper() not in [c.upper() for c in chains]:
            continue
        if stablecoins_only and not is_stablecoin_pool(p):
            continue
        if p["tvl_usd"] < min_tvl:
            continue
        if p["apy"] < min_apy or p["apy"] > max_apy:
            continue
        if project and p["project"].lower() != project.lower():
            continue
        results.append(p)

    results.sort(key=lambda x: x["apy"], reverse=True)
    return results[:limit]
