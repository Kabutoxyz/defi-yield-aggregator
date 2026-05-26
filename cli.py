#!/usr/bin/env python3
"""CLI for DeFi Yield Aggregator."""

import argparse
import sys
from tabulate import tabulate

from src.yields import fetch_all_pools, filter_pools, parse_pool
from src.optimizer import find_best_yields, compare_pools
from src.protocols import compute_pool_risk, get_risk_label, protocol_summary
from src.chains import DEFAULT_CHAINS, SUPPORTED_CHAINS, format_chain_label
from src.portfolio import (
    add_position, remove_position, get_positions, calculate_portfolio_apy,
)


def cmd_scan(args):
    """Scan yields with filters."""
    chains = [args.chain] if args.chain else None
    pools = fetch_all_pools()
    filtered = filter_pools(
        pools,
        chains=chains,
        stablecoins_only=args.stable,
        min_tvl=args.min_tvl,
        min_apy=args.min_apy,
        limit=args.limit,
    )

    if not filtered:
        print("No pools match your filters.")
        return

    rows = []
    for p in filtered:
        risk = compute_pool_risk(p)
        rows.append([
            p["pool"][:12],
            p["chain"][:10],
            p["project"][:18],
            p["symbol"][:25],
            f"{p['apy']:.2f}%",
            f"${p['tvl_usd']:,.0f}",
            get_risk_label(risk),
        ])

    headers = ["Pool ID", "Chain", "Protocol", "Symbol", "APY", "TVL", "Risk"]
    print(f"\n🔍 Found {len(filtered)} pools\n")
    print(tabulate(rows, headers=headers, tablefmt="simple"))


def cmd_best(args):
    """Find best yield opportunities."""
    chains = args.chains.split(",") if args.chains else None
    results = find_best_yields(
        chains=chains,
        risk_tolerance=args.risk,
        prefer_stablecoins=args.stable,
        min_tvl=args.min_tvl,
        min_apy=args.min_apy,
        limit=args.limit,
    )

    if not results:
        print("No yields match your criteria.")
        return

    print(f"\n🏆 Top {len(results)} Yield Opportunities")
    print(f"   Risk tolerance: {args.risk}/5 | Stablecoins: {'yes' if args.stable else 'no'}")
    if chains:
        print(f"   Chains: {', '.join(chains)}")
    print()

    rows = []
    for i, p in enumerate(results, 1):
        rows.append([
            i,
            p["chain"][:10],
            p["project"][:18],
            p["symbol"][:25],
            f"{p['apy']:.2f}%",
            f"${p['tvl_usd']:,.0f}",
            p["risk_label"],
            f"{p['match_score']:.1f}",
        ])

    headers = ["#", "Chain", "Protocol", "Symbol", "APY", "TVL", "Risk", "Score"]
    print(tabulate(rows, headers=headers, tablefmt="simple"))


def cmd_compare(args):
    """Compare specific pool IDs."""
    pool_ids = args.pool_ids
    results = compare_pools(pool_ids)

    if not results:
        print("No matching pools found. Check your pool IDs.")
        return

    rows = []
    for p in results:
        rows.append([
            p["pool"][:12],
            p["chain"],
            p["project"],
            p["symbol"][:25],
            f"{p['apy']:.2f}%",
            f"{p['apy_base']:.2f}%",
            f"{p['apy_reward']:.2f}%",
            f"${p['tvl_usd']:,.0f}",
            f"{p.get('apy_mean_30d', 0):.2f}%",
            p["risk_label"],
        ])

    headers = ["Pool ID", "Chain", "Protocol", "Symbol", "APY", "Base", "Reward", "TVL", "30d Avg", "Risk"]
    print(f"\n📊 Comparing {len(results)} pools\n")
    print(tabulate(rows, headers=headers, tablefmt="simple"))


def cmd_portfolio(args):
    """Manage and view portfolio."""
    if args.action == "add":
        pos = add_position(args.pool_id, args.amount, args.date, args.notes or "")
        print(f"✅ Added position: {pos['pool_id']} (${pos['amount_usd']:,.0f})")
        return

    if args.action == "remove":
        if remove_position(args.pool_id):
            print(f"✅ Removed position: {args.pool_id}")
        else:
            print(f"❌ Position not found: {args.pool_id}")
        return

    if args.action == "list":
        positions = get_positions()
        if not positions:
            print("No positions tracked. Use: cli.py portfolio add <pool_id> <amount>")
            return
        rows = []
        for p in positions:
            rows.append([p["pool_id"], f"${p['amount_usd']:,.0f}", p.get("entry_date", ""), p.get("notes", "")])
        print(tabulate(rows, headers=["Pool ID", "Amount", "Entry Date", "Notes"], tablefmt="simple"))
        return

    if args.action == "summary":
        results = calculate_portfolio_apy()
        if not results:
            print("No positions tracked.")
            return

        total = results[0].get("portfolio_total", 0)
        weighted_apy = results[0].get("weighted_apy", 0)
        projected = results[0].get("portfolio_projected_yearly", 0)

        print(f"\n💼 Portfolio Summary")
        print(f"   Total invested: ${total:,.0f}")
        print(f"   Weighted APY:   {weighted_apy:.2f}%")
        print(f"   Projected yearly: ${projected:,.0f}\n")

        rows = []
        for r in results:
            rows.append([
                r["pool_id"][:12],
                r.get("chain", "?")[:10],
                r.get("symbol", "?")[:25],
                f"${r['amount_usd']:,.0f}",
                f"{r['current_apy']:.2f}%" if r.get("current_apy") else "N/A",
                r.get("risk_label", "?"),
                f"${r.get('estimated_return', 0):,.2f}" if r.get("status") == "live" else "N/A",
            ])
        headers = ["Pool ID", "Chain", "Symbol", "Amount", "APY", "Risk", "Est. Return"]
        print(tabulate(rows, headers=headers, tablefmt="simple"))


def cmd_protocols(args):
    """Show protocol overview."""
    pools = fetch_all_pools()
    parsed = [p for raw in pools if (p := parse_pool(raw)) is not None]
    summary = protocol_summary(parsed)

    # Sort by TVL
    sorted_protos = sorted(summary.items(), key=lambda x: x[1]["total_tvl"], reverse=True)

    rows = []
    for name, info in sorted_protos[:args.limit]:
        rows.append([
            name[:20],
            info["pool_count"],
            f"${info['total_tvl']:,.0f}",
            ", ".join(info["chains"][:4]),
        ])

    headers = ["Protocol", "Pools", "Total TVL", "Chains"]
    print(f"\n📋 Top {min(args.limit, len(sorted_protos))} Protocols by TVL\n")
    print(tabulate(rows, headers=headers, tablefmt="simple"))


def main():
    parser = argparse.ArgumentParser(
        description="DeFi Yield Aggregator - Find the best yields across chains"
    )
    sub = parser.add_subparsers(dest="command")

    # scan
    p_scan = sub.add_parser("scan", help="Scan yield pools with filters")
    p_scan.add_argument("--chain", help="Filter by chain (e.g. Ethereum, Arbitrum)")
    p_scan.add_argument("--stable", action="store_true", help="Stablecoins only")
    p_scan.add_argument("--min-tvl", type=float, default=0, help="Min TVL in USD")
    p_scan.add_argument("--min-apy", type=float, default=0, help="Min APY %%")
    p_scan.add_argument("--limit", type=int, default=30, help="Max results")
    p_scan.set_defaults(func=cmd_scan)

    # best
    p_best = sub.add_parser("best", help="Find best yield opportunities")
    p_best.add_argument("--chains", help="Comma-separated chains (e.g. Ethereum,Arbitrum)")
    p_best.add_argument("--risk", type=int, default=3, choices=[1, 2, 3, 4, 5], help="Risk tolerance 1-5")
    p_best.add_argument("--stable", action="store_true", help="Prefer stablecoins")
    p_best.add_argument("--min-tvl", type=float, default=100000, help="Min TVL")
    p_best.add_argument("--min-apy", type=float, default=0, help="Min APY")
    p_best.add_argument("--limit", type=int, default=15, help="Max results")
    p_best.set_defaults(func=cmd_best)

    # compare
    p_cmp = sub.add_parser("compare", help="Compare specific pool IDs")
    p_cmp.add_argument("pool_ids", nargs="+", help="Pool IDs to compare")
    p_cmp.set_defaults(func=cmd_compare)

    # portfolio
    p_port = sub.add_parser("portfolio", help="Manage portfolio positions")
    p_port.add_argument("action", choices=["add", "remove", "list", "summary"])
    p_port.add_argument("pool_id", nargs="?", help="Pool ID")
    p_port.add_argument("amount", nargs="?", type=float, help="Amount in USD")
    p_port.add_argument("--date", help="Entry date (YYYY-MM-DD)")
    p_port.add_argument("--notes", help="Position notes")
    p_port.set_defaults(func=cmd_portfolio)

    # protocols
    p_proto = sub.add_parser("protocols", help="Protocol overview by TVL")
    p_proto.add_argument("--limit", type=int, default=20, help="Max protocols")
    p_proto.set_defaults(func=cmd_protocols)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
