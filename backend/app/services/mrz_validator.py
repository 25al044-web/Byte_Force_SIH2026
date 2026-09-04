"""ICAO Doc 9303 compliant TD3 Passport MRZ Validator.

This module validates Machine Readable Zone (MRZ) data for TD3 format
(standard 44-character x 2-line machine readable passports).

ICAO Doc 9303 Part 4 TD3 Layout Specification:
------------------------------------------------
Line 1 (44 characters):
  Pos 1-2   (chars 0..1)   : Document code ('P<', 'P ', etc.)
  Pos 3-5   (chars 2..4)   : Issuing state or organization (ISO 3166-1 alpha-3 or standard ICAO code)
  Pos 6-44  (chars 5..43)  : Name of holder (Primary Identifier <<< Secondary Identifier)

Line 2 (44 characters):
  Pos 1-9   (chars 0..8)   : Document / Passport number (9 characters)
  Pos 10    (char 9)       : Check digit over document number
  Pos 11-13 (chars 10..12) : Nationality of holder (ISO 3166-1 alpha-3 code)
  Pos 14-19 (chars 13..18) : Date of birth (YYMMDD, 6 digits)
  Pos 20    (char 19)      : Check digit over date of birth
  Pos 21    (char 20)      : Sex ('M', 'F', or '<' for unspecified)
  Pos 22-27 (chars 21..26) : Expiry date of document (YYMMDD, 6 digits)
  Pos 28    (char 27)      : Check digit over expiry date
  Pos 29-42 (chars 28..41) : Optional data / Personal number (14 characters)
  Pos 43    (char 42)      : Check digit over optional data / personal number
  Pos 44    (char 43)      : Composite check digit over concatenated fields

Checksum Calculation Rules (ICAO Doc 9303-3):
----------------------------------------------
  1. Character values:
       '0'-'9' -> 0-9
       'A'-'Z' -> 10-35
       '<'     -> 0
  2. Weight sequence: [7, 3, 1] repeating sequentially.
  3. Formula: sum(char_value * weight) % 10.
"""

from typing import Any, Dict, List, Optional, Tuple

TD3_LINE_LENGTH = 44
MRZ_WEIGHTS = (7, 3, 1)


def char_to_mrz_value(c: str) -> int:
    """Converts an MRZ character to its numeric value according to ICAO rules.

    0-9 -> 0-9
    A-Z -> 10-35
    <   -> 0
    """
    if '0' <= c <= '9':
        return int(c)
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A') + 10
    if c == '<':
        return 0
    raise ValueError(f"Character '{c}' is not a valid ICAO MRZ character.")


def compute_mrz_check_digit(data: str) -> str:
    """Computes the ICAO check digit for a string using repeating weights (7, 3, 1).

    Args:
        data: The alphanumeric MRZ substring to calculate the checksum for.

    Returns:
        A single character string representing the check digit ('0'-'9').
    """
    total = 0
    for i, char in enumerate(data):
        total += char_to_mrz_value(char) * MRZ_WEIGHTS[i % 3]
    return str(total % 10)


def is_valid_mrz_charset(line: str) -> bool:
    """Checks whether every character in the line is within allowed MRZ characters (A-Z, 0-9, <)."""
    for c in line:
        if not (('0' <= c <= '9') or ('A' <= c <= 'Z') or c == '<'):
            return False
    return True


def validate_td3_mrz(mrz_line_1: Any, mrz_line_2: Any) -> Dict[str, Any]:
    """Validates two lines of an ICAO TD3 passport MRZ.

    Args:
        mrz_line_1: First 44-character MRZ line.
        mrz_line_2: Second 44-character MRZ line.

    Returns:
        A dictionary containing:
          - status: "PASS" or "FAIL"
          - score: 0 (PASS) or 25 (FAIL)
          - reason: Diagnostic explanation
          - details: Dict with boolean validation flags for individual checks
    """
    details = {
        "format_valid": False,
        "document_number_valid": False,
        "date_of_birth_valid": False,
        "expiry_date_valid": False,
        "personal_number_valid": False,
        "composite_valid": False,
    }

    # 1. Type and existence checks
    if not isinstance(mrz_line_1, str) or not isinstance(mrz_line_2, str):
        return {
            "status": "FAIL",
            "score": 25,
            "reason": "MRZ validation failed: MRZ lines must be non-null strings",
            "details": details,
        }

    # 2. Length check (TD3 requires exactly 44 characters per line)
    len1 = len(mrz_line_1)
    len2 = len(mrz_line_2)
    if len1 != TD3_LINE_LENGTH or len2 != TD3_LINE_LENGTH:
        return {
            "status": "FAIL",
            "score": 25,
            "reason": (
                f"MRZ validation failed: invalid line length (Line 1: {len1} chars, "
                f"Line 2: {len2} chars; exactly {TD3_LINE_LENGTH} required per line)"
            ),
            "details": details,
        }

    # 3. Permitted character set check (strictly [A-Z0-9<])
    if not is_valid_mrz_charset(mrz_line_1) or not is_valid_mrz_charset(mrz_line_2):
        return {
            "status": "FAIL",
            "score": 25,
            "reason": "MRZ validation failed: invalid character(s) detected. Only uppercase A-Z, 0-9, and '<' are permitted",
            "details": details,
        }

    details["format_valid"] = True
    errors: List[str] = []

    # 4. Document / Passport Number check digit
    # Position: Line 2 chars 0..8 (9 chars), check digit at char 9
    doc_number = mrz_line_2[0:9]
    actual_doc_cd = mrz_line_2[9]
    expected_doc_cd = compute_mrz_check_digit(doc_number)
    if actual_doc_cd == expected_doc_cd:
        details["document_number_valid"] = True
    else:
        errors.append(
            f"invalid document-number checksum (expected '{expected_doc_cd}', got '{actual_doc_cd}')"
        )

    # 5. Date of Birth check digit
    # Position: Line 2 chars 13..18 (YYMMDD, 6 chars), check digit at char 19
    dob = mrz_line_2[13:19]
    actual_dob_cd = mrz_line_2[19]
    expected_dob_cd = compute_mrz_check_digit(dob)
    if actual_dob_cd == expected_dob_cd:
        details["date_of_birth_valid"] = True
    else:
        errors.append(
            f"invalid date-of-birth checksum (expected '{expected_dob_cd}', got '{actual_dob_cd}')"
        )

    # 6. Expiration Date check digit
    # Position: Line 2 chars 21..26 (YYMMDD, 6 chars), check digit at char 27
    expiry = mrz_line_2[21:27]
    actual_expiry_cd = mrz_line_2[27]
    expected_expiry_cd = compute_mrz_check_digit(expiry)
    if actual_expiry_cd == expected_expiry_cd:
        details["expiry_date_valid"] = True
    else:
        errors.append(
            f"invalid expiration-date checksum (expected '{expected_expiry_cd}', got '{actual_expiry_cd}')"
        )

    # 7. Optional Data / Personal Number check digit
    # Position: Line 2 chars 28..41 (14 chars), check digit at char 42
    personal_num = mrz_line_2[28:42]
    actual_personal_cd = mrz_line_2[42]

    # ICAO 9303 allows optional data to be filler '<'. If entirely filler, check digit can be '<' or '0'.
    if personal_num == '<' * 14:
        if actual_personal_cd in ('<', '0'):
            details["personal_number_valid"] = True
        else:
            errors.append(
                f"invalid personal-number checksum for filler (expected '<' or '0', got '{actual_personal_cd}')"
            )
    else:
        expected_personal_cd = compute_mrz_check_digit(personal_num)
        if actual_personal_cd == expected_personal_cd:
            details["personal_number_valid"] = True
        else:
            errors.append(
                f"invalid personal-number checksum (expected '{expected_personal_cd}', got '{actual_personal_cd}')"
            )

    # 8. Composite Check Digit
    # Position: Line 2 char 43 (44th character)
    # Checks concatenation of:
    #   - chars 0..9   (document number + check digit, 10 chars)
    #   - chars 13..19 (date of birth + check digit, 7 chars)
    #   - chars 21..27 (expiry date + check digit, 7 chars)
    #   - chars 28..42 (personal number + check digit, 15 chars)
    # Total concatenated length = 39 characters.
    composite_data = (
        mrz_line_2[0:10]
        + mrz_line_2[13:20]
        + mrz_line_2[21:28]
        + mrz_line_2[28:43]
    )
    actual_composite_cd = mrz_line_2[43]
    expected_composite_cd = compute_mrz_check_digit(composite_data)
    if actual_composite_cd == expected_composite_cd:
        details["composite_valid"] = True
    else:
        errors.append(
            f"invalid composite checksum (expected '{expected_composite_cd}', got '{actual_composite_cd}')"
        )

    # 9. Evaluate final status
    if not errors:
        return {
            "status": "PASS",
            "score": 0,
            "reason": "All MRZ checksums are valid",
            "details": details,
        }
    else:
        return {
            "status": "FAIL",
            "score": 25,
            "reason": f"MRZ validation failed: {', '.join(errors)}",
            "details": details,
        }
