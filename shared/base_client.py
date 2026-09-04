import os
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Any, Optional
from web3 import Web3
from eth_account import Account

DEFAULT_BASE_RPC = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
BASE_CHAIN_ID = 8453

def is_valid_eth_address(address: str) -> bool:
    if not address or not isinstance(address, str):
        return False
    return Web3.is_address(address)

def execute_base_ping(
    to_address: str,
    task_id: str,
    confirm: bool = False,
    rpc_url: Optional[str] = None,
    private_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes an onchain transaction to to_address on Base.
    Returns status 'success' with authentic tx_hash, or status 'blocked' with reason.
    """
    if not confirm:
        return {
            "status": "blocked",
            "reason": "Operator confirmation required before executing Base ping."
        }

    if not to_address or not is_valid_eth_address(to_address):
        return {
            "status": "blocked",
            "reason": f"Invalid or missing bound address: {to_address}"
        }

    pk = private_key or os.getenv("BASE_PRIVATE_KEY")
    if not pk:
        return {
            "status": "blocked",
            "reason": "No server signing key configured. Sign with connected browser wallet (MetaMask / Coinbase) on the desk."
        }

    rpc = rpc_url or DEFAULT_BASE_RPC
    w3 = Web3(Web3.HTTPProvider(rpc))

    if not w3.is_connected():
        return {
            "status": "blocked",
            "reason": f"Unable to connect to Base RPC at {rpc}"
        }

    try:
        account = Account.from_key(pk)
        checksum_to = Web3.to_checksum_address(to_address)
        
        # Check chain id
        chain_id = w3.eth.chain_id
        
        # Prepare 0 ETH transaction with task reference in calldata
        nonce = w3.eth.get_transaction_count(account.address, "pending")
        gas_price = w3.eth.gas_price
        
        tx_data = f"OnRecord task={task_id}".encode("utf-8").hex()
        
        tx = {
            "to": checksum_to,
            "value": 0,
            "gas": 30000,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": chain_id,
            "data": "0x" + tx_data
        }
        
        signed_tx = account.sign_transaction(tx)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash = Web3.to_hex(tx_hash_bytes)
        
        # Wait for receipt onchain
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=30)
        receipt_hash = Web3.to_hex(receipt.transactionHash)
        
        if receipt.status != 1:
            return {
                "status": "blocked",
                "reason": f"Transaction reverted on Base (receipt status={receipt.status})"
            }
        
        return {
            "status": "success",
            "tx_hash": receipt_hash,
            "chain_id": chain_id,
            "to": checksum_to,
            "from": account.address
        }
    except Exception as e:
        return {
            "status": "blocked",
            "reason": f"Base execution failed: {str(e)}"
        }
