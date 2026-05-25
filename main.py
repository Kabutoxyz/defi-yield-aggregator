#!/usr/bin/env python3
"""
Simple DeFi protocol scanner
Checks TVL from DeFiLlama API
"""
import requests
from datetime import datetime

def get_protocol_tvl(protocol):
    """Get protocol TVL from DeFiLlama"""
    url = f"https://api.llama.fi/protocol/{protocol}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tvl = data.get('tvl', [{}])[-1].get('totalLiquidityUSD', 0)
            
            print(f"\n🏦 Protocol: {protocol}")
            print(f"TVL: ${tvl:,.0f}")
            print(f"Chain: {data.get('chain', 'Multi-chain')}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        protocol = sys.argv[1]
    else:
        protocol = "aave"  # Default
    
    print(f"🔍 DeFi Protocol Scanner")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    get_protocol_tvl(protocol)
