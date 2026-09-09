import os
import re
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

def verify_base_transaction(tx_hash: str, to_address: str, task_id: str) -> Dict[str, Any]:
    """Verify a mined transaction on Base before it is recorded as a ping."""
    if not isinstance(tx_hash, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", tx_hash):
        return {"status": "blocked", "reason": "Invalid transaction hash."}
    if not is_valid_eth_address(to_address):
        return {"status": "blocked", "reason": "Invalid or missing bound address."}

    w3 = Web3(Web3.HTTPProvider(DEFAULT_BASE_RPC))
    if not w3.is_connected():
        return {"status": "blocked", "reason": "Unable to connect to the configured Base RPC."}
    try:
        chain_id = w3.eth.chain_id
        if chain_id != BASE_CHAIN_ID:
            return {"status": "blocked", "reason": f"Configured RPC is chain {chain_id}, expected Base {BASE_CHAIN_ID}."}
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        expected_to = Web3.to_checksum_address(to_address)
        actual_to = tx.get("to")
        if actual_to is None or Web3.to_checksum_address(actual_to) != expected_to:
            return {"status": "blocked", "reason": "Transaction recipient does not match the bound address."}
        expected_data = "0x" + f"OnRecord task={task_id}".encode("utf-8").hex()
        actual_data = tx.get("input", tx.get("data", "0x"))
        if str(actual_data).lower() != expected_data.lower():
            return {"status": "blocked", "reason": "Transaction calldata does not match the filed task."}
        if receipt.status != 1:
            return {"status": "blocked", "reason": "Transaction receipt is not successful."}
        return {"status": "success", "tx_hash": Web3.to_hex(tx.hash), "chain_id": chain_id, "to": expected_to}
    except Exception as e:
        return {"status": "blocked", "reason": f"Unable to verify Base transaction: {e}"}

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
        
        # Only Base Mainnet is an allowed settlement network.
        chain_id = w3.eth.chain_id
        if chain_id != BASE_CHAIN_ID:
            return {
                "status": "blocked",
                "reason": f"Configured RPC is chain {chain_id}, expected Base {BASE_CHAIN_ID}"
            }
        
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
            "chainId": BASE_CHAIN_ID,
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
