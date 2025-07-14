import os
import json
import time
import decimal
from decimal import Decimal
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from web3 import Web3
from datetime import datetime

# Load environment variables
load_dotenv()
INFURA_URL = os.getenv("WEB3_INFURA_URL")

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Load Uniswap V2 Router ABI
with open("src/abis/uniswap_v2_router.json") as f:
    router_abi = json.load(f)

# Contract address for Uniswap V2 Router
UNISWAP_ROUTER_ADDRESS = Web3.to_checksum_address("0xf164fC0Ec4E93095b804a4795bBe1e041497b92a")
router = w3.eth.contract(address=UNISWAP_ROUTER_ADDRESS, abi=router_abi)

# Token addresses (Mainnet)
WETH = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0E5C4F27eAD9083C756Cc2")  # WETH
USDC = Web3.to_checksum_address("0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")  # USDC

# Decimal context to avoid float errors
decimal.getcontext().prec = 8

# Auto-refresh every 10 seconds
if "last_refresh" not in st.session_state or time.time() - st.session_state.last_refresh > 10:
    st.session_state.last_refresh = time.time()
    st.query_params.update({"t": int(time.time())})
    st.rerun()

# Streamlit UI
st.set_page_config(page_title="Uniswap Arbitrage", layout="centered")
st.title("💱 Uniswap Arbitrage Dashboard")

# Fetch prices
try:
    eth_amount = w3.to_wei(1, "ether")
    usdc_out = router.functions.getAmountsOut(eth_amount, [WETH, USDC]).call()[1]
    price_eth_to_usdc = Decimal(usdc_out) / Decimal(10**6)

    usdc_amount = int(1 * 10**6)
    weth_out = router.functions.getAmountsOut(usdc_amount, [USDC, WETH]).call()[1]
    price_usdc_to_eth = Decimal(weth_out) / Decimal(10**18)

    # Display prices
    st.subheader("WETH ➡ USDC")
    st.metric(label="Price", value=f"${price_eth_to_usdc:.2f}")

    st.subheader("USDC ➡ WETH")
    st.metric(label="Price", value=f"{price_usdc_to_eth:.6f} ETH")

    # Arbitrage Calculation
    inverse = Decimal(1) / price_usdc_to_eth
    profit_percent = float(((price_eth_to_usdc - inverse) / inverse) * 100)

    st.markdown(f"**Potential Arbitrage Profit:** `{profit_percent:.2f}%`")

    # Save to CSV
    log_path = "price_log.csv"
    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "eth_to_usdc": float(price_eth_to_usdc),
        "usdc_to_eth": float(price_usdc_to_eth),
        "profit_percent": profit_percent,
    }

    if os.path.exists(log_path):
        df = pd.read_csv(log_path)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])

    df.to_csv(log_path, index=False)

    # Chart
    st.subheader("📈 Price Trend (ETH ➡ USDC)")
    st.line_chart(df.tail(20).set_index("timestamp")["eth_to_usdc"])

except Exception as e:
    st.error(f"Failed to fetch prices: {e}")
    st.warning("Could not fetch price data. Check ABI, token addresses, or Infura.")
