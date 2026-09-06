# Blockchain audit trail

This optional, local Ethereum-compatible layer makes completed screening outcomes tamper-evident. It does not verify passports and it never stores passport data, selfies, names, document numbers, DOBs, or biometric embeddings on-chain.

## Local demo

```powershell
cd blockchain; npm install; npm run blockchain:node
```

Deploy `contracts/ScreeningAudit.sol` with Hardhat and set these development-only variables in `backend/.env`:

```text
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
BLOCKCHAIN_CONTRACT_ADDRESS=0x...
BLOCKCHAIN_PRIVATE_KEY=0x...  # local Hardhat account only
```

Then run the backend and frontend normally. Without these variables or when the node is stopped, screenings still complete and return `blockchain_audit.status = UNAVAILABLE`.

## Stored contract fields

`screeningId`, `documentHash`, `reportHash`, and the chain timestamp. Upload bytes are SHA-256 hashed locally. The canonical local audit report contains only those hashes plus risk level/score, outcome statuses, and recommendation.

Use `GET /api/audit/{screening_id}` to compare the saved canonical report hash to the immutable contract record metadata. A different canonical report hash is returned as `TAMPERED`.
