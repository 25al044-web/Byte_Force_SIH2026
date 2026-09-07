// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Tamper-evident metadata only. PII and biometric data must never be submitted.
contract AuditTrail {
    struct AuditEntry { uint256 id; string recordType; string recordId; string action; bytes32 dataHash; uint256 timestamp; bytes32 previousHash; }
    AuditEntry[] private entries;
    event AuditRecorded(uint256 indexed auditId, string indexed recordType, string indexed recordId, string action, bytes32 dataHash, uint256 timestamp);
    function recordAudit(string calldata recordType, string calldata recordId, string calldata action, bytes32 dataHash, bytes32 previousHash) external returns (uint256 auditId) {
        auditId = entries.length; entries.push(AuditEntry(auditId, recordType, recordId, action, dataHash, block.timestamp, previousHash)); emit AuditRecorded(auditId, recordType, recordId, action, dataHash, block.timestamp);
    }
    function getAudit(uint256 auditId) external view returns (AuditEntry memory) { require(auditId < entries.length, "Unknown audit"); return entries[auditId]; }
    function getAuditCount() external view returns (uint256) { return entries.length; }
    function verifyAudit(uint256 auditId, bytes32 dataHash) external view returns (bool) { return auditId < entries.length && entries[auditId].dataHash == dataHash; }
}
