"""Best-effort client for the local Hardhat AuditTrail contract."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

CONTRACT_ABI = [{"type":"function","name":"recordAudit","stateMutability":"nonpayable","inputs":[{"name":"recordType","type":"string"},{"name":"recordId","type":"string"},{"name":"action","type":"string"},{"name":"dataHash","type":"bytes32"},{"name":"previousHash","type":"bytes32"}],"outputs":[{"name":"auditId","type":"uint256"}]},{"type":"function","name":"getAudit","stateMutability":"view","inputs":[{"name":"auditId","type":"uint256"}],"outputs":[{"name":"id","type":"uint256"},{"name":"recordType","type":"string"},{"name":"recordId","type":"string"},{"name":"action","type":"string"},{"name":"dataHash","type":"bytes32"},{"name":"timestamp","type":"uint256"},{"name":"previousHash","type":"bytes32"}]},{"type":"function","name":"getAuditCount","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint256"}]},{"type":"function","name":"verifyAudit","stateMutability":"view","inputs":[{"name":"auditId","type":"uint256"},{"name":"dataHash","type":"bytes32"}],"outputs":[{"name":"","type":"bool"}]}]

class BlockchainUnavailable(RuntimeError): pass

class BlockchainClient:
    def __init__(self) -> None:
        artifact = Path(__file__).resolve().parents[4] / "blockchain" / "deployments" / "localhost.json"
        try: deployed = json.loads(artifact.read_text(encoding="utf-8"))
        except Exception: deployed = {}
        self.rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.contract_address = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS") or deployed.get("address")
        self.private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")

    def _contract(self):
        if not self.contract_address: raise BlockchainUnavailable("AuditTrail contract address is not configured")
        try: from web3 import Web3
        except ImportError as exc: raise BlockchainUnavailable("web3 dependency is not installed") from exc
        web3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 3}))
        if not web3.is_connected(): raise BlockchainUnavailable("Local blockchain is offline")
        return web3, web3.eth.contract(address=Web3.to_checksum_address(self.contract_address), abi=CONTRACT_ABI)

    @staticmethod
    def _bytes32(value: str) -> bytes: return bytes.fromhex(value.removeprefix("0x"))

    def health(self) -> Dict[str, Any]:
        try:
            web3, contract = self._contract()
            if not web3.eth.get_code(contract.address): raise BlockchainUnavailable("No contract bytecode at configured address")
            return {"ready": True, "network": "Ethereum / Hardhat", "chain_id": web3.eth.chain_id, "contract_address": contract.address, "latest_block": web3.eth.block_number, "audit_count": contract.functions.getAuditCount().call()}
        except Exception as exc: return {"ready": False, "error": str(exc)}

    def record(self, record_type: str, record_id: str, action: str, data_hash: str, previous_hash: str = "0" * 64) -> Dict[str, Any]:
        web3, contract = self._contract()
        if not self.private_key: raise BlockchainUnavailable("Blockchain signing key is not configured")
        try:
            account = web3.eth.account.from_key(self.private_key)
            tx = contract.functions.recordAudit(record_type, record_id, action, self._bytes32(data_hash), self._bytes32(previous_hash)).build_transaction({"from": account.address, "nonce": web3.eth.get_transaction_count(account.address), "chainId": web3.eth.chain_id, "gas": 350000, "gasPrice": web3.eth.gas_price})
            signed = account.sign_transaction(tx)
            receipt = web3.eth.wait_for_transaction_receipt(web3.eth.send_raw_transaction(signed.raw_transaction), timeout=15)
            if receipt.status != 1: raise BlockchainUnavailable("Blockchain transaction reverted")
            return {"transaction_hash": receipt.transactionHash.hex(), "block_number": receipt.blockNumber, "blockchain_audit_id": contract.functions.getAuditCount().call() - 1}
        except BlockchainUnavailable: raise
        except Exception as exc: raise BlockchainUnavailable(str(exc)) from exc

    def fetch(self, audit_id: int) -> Optional[Dict[str, Any]]:
        try:
            _, contract = self._contract(); row = contract.functions.getAudit(audit_id).call()
            return {"audit_id": row[0], "record_type": row[1], "record_id": row[2], "action": row[3], "data_hash": row[4].hex(), "timestamp": row[5], "previous_hash": row[6].hex()}
        except Exception as exc: raise BlockchainUnavailable(str(exc)) from exc
