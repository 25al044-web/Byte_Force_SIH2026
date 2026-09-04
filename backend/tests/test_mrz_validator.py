"""Unit tests for ICAO Doc 9303 TD3 Passport MRZ Validator.

All test MRZ strings use publicly documented standard ICAO samples or purely
synthetic data. No real personal information is used.
"""

import pytest
from app.services.mrz_validator import compute_mrz_check_digit, validate_td3_mrz

# Publicly documented standard ICAO Doc 9303 Part 4 sample (Utopia / Anna Maria Eriksson)
VALID_ICAO_SAMPLE_L1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
VALID_ICAO_SAMPLE_L2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"

# Synthetic development sample (India / Arun Kumar)
VALID_SYNTHETIC_L1 = "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
VALID_SYNTHETIC_L2 = "P1234567<1IND0408204M3208140<<<<<<<<<<<<<<<4"


def test_valid_td3_mrz_icao_sample():
    """Verify that a valid ICAO Doc 9303 TD3 sample passes all checksums."""
    res = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, VALID_ICAO_SAMPLE_L2)
    assert res["status"] == "PASS"
    assert res["score"] == 0
    assert res["reason"] == "All MRZ checksums are valid"
    assert res["details"]["format_valid"] is True
    assert res["details"]["document_number_valid"] is True
    assert res["details"]["date_of_birth_valid"] is True
    assert res["details"]["expiry_date_valid"] is True
    assert res["details"]["personal_number_valid"] is True
    assert res["details"]["composite_valid"] is True


def test_valid_td3_mrz_synthetic_sample():
    """Verify that a synthetic passport with filler optional data passes all checksums."""
    res = validate_td3_mrz(VALID_SYNTHETIC_L1, VALID_SYNTHETIC_L2)
    assert res["status"] == "PASS"
    assert res["score"] == 0
    assert res["reason"] == "All MRZ checksums are valid"
    assert res["details"]["format_valid"] is True
    assert res["details"]["document_number_valid"] is True
    assert res["details"]["date_of_birth_valid"] is True
    assert res["details"]["expiry_date_valid"] is True
    assert res["details"]["personal_number_valid"] is True
    assert res["details"]["composite_valid"] is True


def test_incorrect_document_number_check_digit():
    """Verify detection of a tampered or invalid document number check digit."""
    # Correct doc check digit at index 9 is '6'; change it to '7'
    tampered_l2 = VALID_ICAO_SAMPLE_L2[:9] + "7" + VALID_ICAO_SAMPLE_L2[10:]
    res = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, tampered_l2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid document-number checksum" in res["reason"]
    assert res["details"]["format_valid"] is True
    assert res["details"]["document_number_valid"] is False


def test_incorrect_date_of_birth_check_digit():
    """Verify detection of an invalid date of birth check digit."""
    # Correct DOB check digit at index 19 is '2'; change it to '9'
    tampered_l2 = VALID_ICAO_SAMPLE_L2[:19] + "9" + VALID_ICAO_SAMPLE_L2[20:]
    res = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, tampered_l2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid date-of-birth checksum" in res["reason"]
    assert res["details"]["format_valid"] is True
    assert res["details"]["date_of_birth_valid"] is False


def test_incorrect_expiry_date_check_digit():
    """Verify detection of an invalid expiration date check digit."""
    # Correct expiry check digit at index 27 is '9'; change it to '0'
    tampered_l2 = VALID_ICAO_SAMPLE_L2[:27] + "0" + VALID_ICAO_SAMPLE_L2[28:]
    res = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, tampered_l2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid expiration-date checksum" in res["reason"]
    assert res["details"]["format_valid"] is True
    assert res["details"]["expiry_date_valid"] is False


def test_incorrect_personal_number_check_digit():
    """Verify detection of an invalid personal number check digit."""
    # Correct personal check digit at index 42 is '1'; change it to '8'
    tampered_l2 = VALID_ICAO_SAMPLE_L2[:42] + "8" + VALID_ICAO_SAMPLE_L2[43:]
    res = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, tampered_l2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid personal-number checksum" in res["reason"]
    assert res["details"]["format_valid"] is True
    assert res["details"]["personal_number_valid"] is False


def test_incorrect_composite_check_digit():
    """Verify detection of an invalid composite check digit."""
    # Correct composite check digit at index 43 is '0'; change it to '5'
    tampered_l2 = VALID_ICAO_SAMPLE_L2[:43] + "5"
    res = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, tampered_l2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid composite checksum" in res["reason"]
    assert res["details"]["format_valid"] is True
    assert res["details"]["composite_valid"] is False
    # All individual field checksums remain valid
    assert res["details"]["document_number_valid"] is True
    assert res["details"]["date_of_birth_valid"] is True
    assert res["details"]["expiry_date_valid"] is True
    assert res["details"]["personal_number_valid"] is True


def test_line_too_short():
    """Verify that lines shorter than 44 characters are rejected."""
    short_l1 = "P<UTOERIKSSON<<ANNA<MARIA<<<"
    res = validate_td3_mrz(short_l1, VALID_ICAO_SAMPLE_L2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid line length" in res["reason"]
    assert res["details"]["format_valid"] is False


def test_line_too_long():
    """Verify that lines longer than 44 characters are rejected."""
    long_l2 = VALID_ICAO_SAMPLE_L2 + "<<"
    res = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, long_l2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid line length" in res["reason"]
    assert res["details"]["format_valid"] is False


def test_invalid_mrz_characters():
    """Verify rejection of characters outside [A-Z0-9<] such as lowercase and symbols."""
    # Lowercase character in line 1
    bad_l1 = "P<UTOeriksson<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    res = validate_td3_mrz(bad_l1, VALID_ICAO_SAMPLE_L2)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid character" in res["reason"]
    assert res["details"]["format_valid"] is False

    # Special symbol in line 2
    bad_l2 = VALID_ICAO_SAMPLE_L2[:5] + "@" + VALID_ICAO_SAMPLE_L2[6:]
    res2 = validate_td3_mrz(VALID_ICAO_SAMPLE_L1, bad_l2)
    assert res2["status"] == "FAIL"
    assert res2["score"] == 25
    assert "invalid character" in res2["reason"]
    assert res2["details"]["format_valid"] is False


def test_empty_input():
    """Verify safe rejection when empty strings are passed."""
    res = validate_td3_mrz("", "")
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "invalid line length" in res["reason"]
    assert res["details"]["format_valid"] is False


def test_malformed_input():
    """Verify validator never crashes on None or non-string inputs."""
    res_none = validate_td3_mrz(None, None)
    assert res_none["status"] == "FAIL"
    assert res_none["score"] == 25
    assert "must be non-null strings" in res_none["reason"]

    res_mixed = validate_td3_mrz(12345, VALID_ICAO_SAMPLE_L2)
    assert res_mixed["status"] == "FAIL"
    assert res_mixed["score"] == 25
    assert "must be non-null strings" in res_mixed["reason"]


def test_compute_mrz_check_digit_function():
    """Directly test the check digit calculation algorithm with known test strings."""
    # AB2134 -> A(10)*7 + B(11)*3 + 2*1 + 1*7 + 3*3 + 4*1 = 70+33+2+7+9+4 = 125 % 10 = 5
    assert compute_mrz_check_digit("AB2134") == "5"

    # All filler '<'
    assert compute_mrz_check_digit("<<<<") == "0"
