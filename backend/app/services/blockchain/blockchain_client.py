"""Optional Ethereum-compatible client for the local Hardhat audit contract.

The screening service never depends on this client succeeding. Credentials and
contract addresses are supplied through development-only environment variables.
"""

import os
from typing import Any, Dict, Optional

CONTRACT_ABI = [
    {"type": "function", "name": "recordAudit", "stateMutability": "nonpayable", "inputs": [
        {"name": "screeningId", "type": "string"}, {"name": "documentHash", "type": "bytes32"}, {"name": "reportHash", "type": "bytes32"}], "outputs": []},
    {"type": "function", "name": "audits", "stateMutability": "view", "inputs": [{"name": "", "type": "string"}], "outputs": [
        {"name": "screeningId", "type": "string"}, {"name": "documentHash", "type": "bytes32"}, {"name": "reportHash", "type": "bytes32"}, {"name": "timestamp", "type": "uint256"}]},
]


class BlockchainUnavailable(RuntimeError):
    pass


class BlockchainClient:
    def __init__(self) -> None:
        self.rpc_url = os.getenv("BLOCKCHAIN_RPC_URL")
        self.contract_address = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS")
        self.private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")  # DEVELOPMENT ONLY

    def _contract(self):
        if not all([self.rpc_url, self.contract_address, self.private_key]):
            raise BlockchainUnavailable("Local blockchain is not configured")
        try:
            from web3 import Web3
        except ImportError as exc:
            raise BlockchainUnavailable("web3 dependency is not installed") from exc
        web3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 3}))
        if not web3.is_connected():
            raise BlockchainUnavailable("Local blockchain is offline")
        account = web3.eth.account.from_key(self.private_key)
        return web3, web3.eth.contract(address=Web3.to_checksum_address(self.contract_address), abi=CONTRACT_ABI), account

    @staticmethod
    def _bytes32(value: str) -> bytes:
        return bytes.fromhex(value.removeprefix("0x"))

    def record(self, screening_id: str, document_hash: str, report_hash: str) -> Dict[str, Any]:
        web3, contract, account = self._contract()
        try:
            tx = contract.functions.recordAudit(screening_id, self._bytes32(document_hash), self._bytes32(report_hash)).build_transaction({
                "from": account.address, "nonce": web3.eth.get_transaction_count(account.address), "chainId": web3.eth.chain_id,
                "gas": 250000, "gasPrice": web3.eth.gas_price,
            })
            signed = account.sign_transaction(tx)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
            return {"transaction_hash": receipt.transactionHash.hex(), "block_number": receipt.blockNumber}
        except Exception as exc:
            raise BlockchainUnavailable(str(exc)) from exc

    def fetch(self, screening_id: str) -> Optional[Dict[str, Any]]:
        web3, contract, _ = self._contract()
        try:
            stored_id, document_hash, report_hash, timestamp = contract.functions.audits(screening_id).call()
            if not stored_id:
                return None
            return {"screening_id": stored_id, "document_hash": document_hash.hex(), "report_hash": report_hash.hex(), "timestamp": timestamp}
        except Exception as exc:
            raise BlockchainUnavailable(str(exc)) from exc
