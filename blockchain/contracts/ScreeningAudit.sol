// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Stores hashes only. Never submit identity documents, selfies, or PII.
contract ScreeningAudit {
    struct AuditRecord { string screeningId; bytes32 documentHash; bytes32 reportHash; uint256 timestamp; }
    mapping(string => AuditRecord) public audits;
    event AuditRecorded(string indexed screeningId, bytes32 documentHash, bytes32 reportHash, uint256 timestamp);

    function recordAudit(string calldata screeningId, bytes32 documentHash, bytes32 reportHash) external {
        require(bytes(audits[screeningId].screeningId).length == 0, "Audit already exists");
        audits[screeningId] = AuditRecord(screeningId, documentHash, reportHash, block.timestamp);
        emit AuditRecorded(screeningId, documentHash, reportHash, block.timestamp);
    }
}
