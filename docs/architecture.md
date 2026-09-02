# System Documentation

## AI-Based Fake Identity & Document Screening System
**Problem Statement:** SIH26188

### Overview
This system provides an end-to-end automated pipeline for screening identity documents and user selfies to detect forged documents, impersonation, tampering, and duplicate identities.

### Architecture Modules (Roadmap)
1. **Document Extraction**: Text and field extraction from IDs/passports using OCR.
2. **MRZ Validation**: Machine Readable Zone checksum and format validation (ICAO Doc 9303 standard).
3. **Document Tamper Screening**: Anomaly detection for font inconsistencies, digital splicing, and physical alterations.
4. **Face Matching**: High-accuracy biometric comparison between document photo and live selfie.
5. **Duplicate Identity Screening**: Cross-referencing against existing database records.
6. **Blacklist Checking**: Automated screening against sanctioned or flagged entities.
7. **Explainable Risk Scoring**: Aggregation of module confidence scores into a unified, interpretable risk assessment.
