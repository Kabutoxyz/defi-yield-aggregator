"""Protocol metadata, TVL tracking, and risk scoring."""

from src.yields import ESTABLISHED_PROTOCOLS, HIGH_RISK_PROTOCOLS

# Risk tiers: 1 (lowest) to 5 (highest)
RISK_SCORES = {
    "aave-v3": 1, "aave-v2": 2, "compound-v3": 1, "compound-v2": 2,
    "lido": 1, "maker": 1, "uniswap-v3": 2, "curve-dex": 2,
    "convex-finance": 2, "yearn-finance": 2, "morpho": 2, "spark": 2,
    "sky": 2, "rocket-pool": 2, "pendle": 3, "eigenlayer": 3,
}

# Human-readable descriptions
PROTOCOL_DESCRIPTIONS = {
    "aave-v3": "Leading lending/borrowing protocol, multi-chain",
    "compound-v3": "Pioneer lending protocol, Comet upgrade",
    "lido": "Liquid staking for Ethereum",
    "curve-dex": "Stableswap DEX with deep liquidity",
    "uniswap-v3": "Concentrated liquidity AMM",
    "rocket-pool": "Decentralized ETH staking",
    "morpho": "Optimized lending aggregator on Aave/Compound",
    "pendle": "Yield tokenization and trading",
    "convex-finance": "Curve yield booster",
    "yearn-finance": "Automated yield vault strategies",
    "maker": "DAI stablecoin issuer, CDP protocol",
    "spark": "MakerDAO's lending arm (fork of Aave V3)",
    "eigenlayer": "ETH restaking protocol",
}


def get_risk_score(project: str) -> int:
    """Return risk score 1-5 for a protocol. Higher = riskier."""
    p = project.lower().strip()
    if p in RISK_SCORES:
        return RISK_SCORES[p]
    if p in HIGH_RISK_PROTOCOLS or any(k in p for k in HIGH_RISK_PROTOCOLS):
        return 5
    if p in ESTABLISHED_PROTOCOLS:
        return 2
    return 4  # unknown protocol default


def get_risk_label(score: int) -> str:
    """Convert numeric risk score to label."""
    labels = {1: "Very Low", 2: "Low", 3: "Medium", 4: "High", 5: "Very High"}
    return labels.get(score, "Unknown")


def compute_pool_risk(pool: dict) -> int:
    """Compute composite risk score for a pool (1-5)."""
    base = get_risk_score(pool.get("project", ""))

    # IL risk bump
    if pool.get("il_risk") == "yes":
        base = min(base + 1, 5)

    # Very high APY is suspicious
    apy = pool.get("apy", 0)
    if apy > 100:
        base = min(base + 1, 5)
    if apy > 1000:
        base = 5

    # Low TVL = more risk
    tvl = pool.get("tvl_usd", 0)
    if tvl < 100_000:
        base = min(base + 1, 5)
    elif tvl < 1_000_000:
        base = min(base + 0.5, 5)

    # Stablecoin pools are inherently safer
    if pool.get("stablecoin"):
        base = max(base - 1, 1)

    return int(round(base))


def protocol_summary(pools: list[dict]) -> dict:
    """Aggregate TVL and pool count per protocol."""
    summary: dict[str, dict] = {}
    for p in pools:
        proj = p.get("project", "unknown")
        if proj not in summary:
            summary[proj] = {"pool_count": 0, "total_tvl": 0.0, "chains": set()}
        summary[proj]["pool_count"] += 1
        summary[proj]["total_tvl"] += p.get("tvl_usd", 0)
        summary[proj]["chains"].add(p.get("chain", ""))
    # Convert sets to lists for serialization
    for v in summary.values():
        v["chains"] = sorted(v["chains"])
    return summary
