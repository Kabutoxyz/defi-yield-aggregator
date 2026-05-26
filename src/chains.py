"""Multi-chain configuration and utilities."""

SUPPORTED_CHAINS = {
    "Ethereum": {"short": "ETH", "gas_tier": "high", "l2": False},
    "Arbitrum": {"short": "ARB", "gas_tier": "low", "l2": True},
    "Optimism": {"short": "OP", "gas_tier": "low", "l2": True},
    "Base": {"short": "BASE", "gas_tier": "low", "l2": True},
    "Polygon": {"short": "MATIC", "gas_tier": "low", "l2": True},
    "Solana": {"short": "SOL", "gas_tier": "low", "l2": False},
    "BSC": {"short": "BSC", "gas_tier": "low", "l2": False},
    "Avalanche": {"short": "AVAX", "gas_tier": "medium", "l2": False},
    "Fantom": {"short": "FTM", "gas_tier": "low", "l2": False},
}

DEFAULT_CHAINS = ["Ethereum", "Arbitrum", "Optimism", "Base", "Polygon", "Solana"]


def resolve_chain(name: str) -> str:
    """Resolve chain alias to canonical name."""
    name_lower = name.lower()
    for canonical, info in SUPPORTED_CHAINS.items():
        if name_lower == canonical.lower() or name_lower == info["short"].lower():
            return canonical
    return name  # pass-through for unknown chains


def get_chain_info(chain: str) -> dict:
    """Get metadata for a chain."""
    canonical = resolve_chain(chain)
    return SUPPORTED_CHAINS.get(canonical, {"short": chain, "gas_tier": "unknown", "l2": False})


def format_chain_label(chain: str) -> str:
    """Return a display label for a chain."""
    info = get_chain_info(chain)
    tag = " [L2]" if info.get("l2") else ""
    return f"{chain}{tag}"
