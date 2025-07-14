import os
import csv
import time
from datetime import datetime
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
INFURA_URL = os.getenv("INFURA_URL")

# Connect to Ethereum
web3 = Web3(Web3.HTTPProvider(INFURA_URL))
if not web3.is_connected():
    print("❌ Failed to connect to Ethereum node.")
    exit()
print("✅ Connected to Ethereum")

# Constants
UNISWAP_ROUTER_V2 = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
UNISWAP_V3_QUOTER = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
USDC = web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606EB48")
WETH = web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

# ABIs
router_abi = [{
    "name": "getAmountsOut",
    "outputs": [{"name": "", "type": "uint256[]"}],
    "inputs": [
        {"name": "amountIn", "type": "uint256"},
        {"name": "path", "type": "address[]"}
    ],
    "stateMutability": "view",
    "type": "function"
}]

v3_quoter_abi = [{
    "inputs": [
        {"internalType": "address", "name": "tokenIn", "type": "address"},
        {"internalType": "address", "name": "tokenOut", "type": "address"},
        {"internalType": "uint24", "name": "fee", "type": "uint24"},
        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
        {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
    ],
    "name": "quoteExactInputSingle",
    "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}]

# Initialize contracts
router_v2 = web3.eth.contract(address=UNISWAP_ROUTER_V2, abi=router_abi)
quoter_v3 = web3.eth.contract(address=UNISWAP_V3_QUOTER, abi=v3_quoter_abi)

# Create log directory and file
log_path = "logs/arbitrage_log.csv"
os.makedirs("logs", exist_ok=True)

if not os.path.exists(log_path):
    with open(log_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "V2 Price (USDC)", "V3 Price (USDC)", "Difference (%)"])

# Fetch and compare prices
def check_arbitrage():
    amount_in_wei = web3.to_wei(1, 'ether')
    path = [WETH, USDC]

    try:
        # V2
        amounts_v2 = router_v2.functions.getAmountsOut(amount_in_wei, path).call()
        out_v2 = web3.from_wei(amounts_v2[1], 'mwei')  # USDC has 6 decimals

        # V3
        fee = 3000  # 0.3%
        out_v3_raw = quoter_v3.functions.quoteExactInputSingle(WETH, USDC, fee, amount_in_wei, 0).call()
        out_v3 = web3.from_wei(out_v3_raw, 'mwei')

        # Compare
        diff = abs(out_v3 - out_v2)
        avg = (out_v2 + out_v3) / 2
        percent_diff = (diff / avg) * 100

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] V2: {out_v2:.2f}, V3: {out_v3:.2f}, Diff: {percent_diff:.4f}%")

        if percent_diff > 0.5:
            print("🚨 Arbitrage Opportunity Detected!")
            with open(log_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, round(out_v2, 4), round(out_v3, 4), round(percent_diff, 4)])

    except Exception as e:
        print("❌ Error:", e)

# Main loop (run once or on schedule)
if __name__ == "__main__":
    check_arbitrage()
