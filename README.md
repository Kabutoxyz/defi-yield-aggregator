# DeFi Yield Aggregator

Find the best DeFi yield opportunities across Ethereum, Arbitrum, Optimism, Base, Polygon, and Solana. Powered by [DeFiLlama](https://defillama.com/) yield data.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Scan Pools

```bash
# Scan all pools with >$1M TVL
python cli.py scan --min-tvl 1000000

# Stablecoin pools on Arbitrum
python cli.py scan --chain Arbitrum --stable --min-tvl 500000

# High-yield pools
python cli.py scan --min-apy 10 --limit 20
```

### Find Best Yields

```bash
# Conservative, stablecoin-focused
python cli.py best --risk 1 --stable --min-tvl 5000000

# Aggressive on L2s
python cli.py best --risk 5 --chains Arbitrum,Base,Optimism

# Balanced multi-chain
python cli.py best --risk 3 --limit 10
```

### Compare Pools

```bash
python cli.py compare <pool_id_1> <pool_id_2> <pool_id_3>
```

### Portfolio Tracking

```bash
# Add positions
python cli.py portfolio add <pool_id> 10000 --date 2025-01-15 --notes "DeFi position"
python cli.py portfolio add <pool_id> 5000

# View positions
python cli.py portfolio list

# Live summary with APY and projected returns
python cli.py portfolio summary

# Remove a position
python cli.py portfolio remove <pool_id>
```

### Protocol Overview

```bash
python cli.py protocols --limit 30
```

## Risk Scoring

Each pool gets a composite risk score (1-5):
- **1 (Very Low)**: Blue-chip protocols (Aave V3, Lido), high TVL, stablecoins
- **2 (Low)**: Established protocols, solid TVL
- **3 (Medium)**: Newer protocols or moderate TVL
- **4 (High)**: Unknown protocols, low TVL, high APY
- **5 (Very High)**: Suspiciously high APY, tiny TVL, known risky patterns

## Architecture

```
src/
├── yields.py      # DeFiLlama API integration, pool filtering
├── protocols.py   # Protocol metadata, risk scoring
├── chains.py      # Multi-chain configuration
├── optimizer.py   # Yield optimization with scoring
└── portfolio.py   # Position tracking, real APY calculation
cli.py             # CLI with scan/best/compare/portfolio subcommands
```

## API

All yield data comes from DeFiLlama's free API (`https://yields.llama.fi/pools`). No API key required.

## License

MIT
