import os
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

infura_url = os.getenv("WEB3_INFURA_URL")

if not infura_url:
    print("❌ WEB3_INFURA_URL not found in .env")
    exit()

# Connect to Infura
w3 = Web3(Web3.HTTPProvider(infura_url))

if w3.is_connected():
    print("✅ Connected to Infura Mainnet")
else:
    print("❌ Connection failed. Check your Infura URL in the .env file.")
