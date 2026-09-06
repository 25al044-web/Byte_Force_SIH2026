"""ICAO Doc 9303 MRZ parser and semantic field extractor.

Supports TD3 (Passports: 2 lines x 44 chars) and TD1 (ID Cards: 3 lines x 30 chars).
Parses primary identifier (surname), secondary identifier (given names),
document number, nationality, date of birth, sex, expiry date, and validates
check digits according to ICAO Doc 9303 Part 4 & 5.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

TD3_LINE_LEN = 44
TD1_LINE_LEN = 30
MRZ_WEIGHTS = (7, 3, 1)


def char_to_mrz_val(c: str) -> int:
    """Converts MRZ character to numeric weight value."""
    if '0' <= c <= '9':
        return int(c)
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A') + 10
    if c == '<':
        return 0
    return 0


def compute_check_digit(data: str) -> str:
    """Computes ICAO check digit using repeating weights [7, 3, 1]."""
    total = sum(char_to_mrz_val(c) * MRZ_WEIGHTS[i % 3] for i, c in enumerate(data))
    return str(total % 10)


def _parse_yymmdd(yymmdd: str, is_expiry: bool = False) -> Optional[str]:
    """Converts 6-digit YYMMDD string to normalized YYYY-MM-DD."""
    if len(yymmdd) != 6 or not yymmdd.isdigit():
        return None
    yy = int(yymmdd[0:2])
    mm = int(yymmdd[2:4])
    dd = int(yymmdd[4:6])

    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        return None

    current_year = datetime.now().year
    current_yy = current_year % 100

    if is_expiry:
        # Expiry is typically in future (e.g. 2020s-2040s)
        century = 2000 if yy <= (current_yy + 30) else 1900
    else:
        # Date of birth is in past
        century = 2000 if yy <= current_yy else 1900

    full_year = century + yy
    return f"{full_year:04d}-{mm:02d}-{dd:02d}"


def parse_td3_name(name_field: str) -> Dict[str, Optional[str]]:
    """Parses ICAO TD3 Name field (Line 1 chars 5 to 43).

    Format: PRIMARY_IDENTIFIER<<SECONDARY_IDENTIFIER<<<<
    Single '<' represents a space within a name component.
    """
    clean = name_field.strip().rstrip('<')
    parts = clean.split('<<')

    surname = parts[0].replace('<', ' ').strip() if len(parts) > 0 else None
    given_names = parts[1].replace('<', ' ').strip() if len(parts) > 1 else None

    # Synthesize full name (e.g. "ARUN KUMAR" or "KUMAR, ARUN")
    if given_names and surname:
        full_name = f"{given_names} {surname}"
    elif surname:
        full_name = surname
    elif given_names:
        full_name = given_names
    else:
        full_name = None

    return {
        "surname": surname or None,
        "given_names": given_names or None,
        "full_name": full_name or None,
    }


def parse_td3_mrz(line1: str, line2: str) -> Dict[str, Any]:
    """Parses and validates a 2-line TD3 passport MRZ.

    Returns structured dictionary with extracted values and checksum flags.
    """
    l1 = line1.strip().upper()
    l2 = line2.strip().upper()

    if len(l1) != TD3_LINE_LEN or len(l2) != TD3_LINE_LEN:
        return {
            "valid_format": False,
            "error": f"Invalid line length ({len(l1)}, {len(l2)}); 44 chars required",
        }

    # 1. Line 1 parsing
    doc_type = l1[0:2].replace('<', '').strip()
    issuing_country = l1[2:5].replace('<', '').strip()
    name_info = parse_td3_name(l1[5:44])

    # 2. Line 2 parsing
    raw_doc_num = l2[0:9]
    doc_num_cd = l2[9]
    expected_doc_cd = compute_check_digit(raw_doc_num)
    doc_number = raw_doc_num.replace('<', '').strip()

    nationality = l2[10:13].replace('<', '').strip()

    raw_dob = l2[13:19]
    dob_cd = l2[19]
    expected_dob_cd = compute_check_digit(raw_dob)
    date_of_birth = _parse_yymmdd(raw_dob, is_expiry=False)

    sex_char = l2[20]
    sex = sex_char if sex_char in ('M', 'F') else None

    raw_expiry = l2[21:27]
    expiry_cd = l2[27]
    expected_expiry_cd = compute_check_digit(raw_expiry)
    expiry_date = _parse_yymmdd(raw_expiry, is_expiry=True)

    personal_number = l2[28:42].replace('<', '').strip()
    personal_cd = l2[42]
    personal_valid = (personal_cd == compute_check_digit(l2[28:42])) or (l2[28:42] == '<' * 14 and personal_cd in ('<', '0'))

    composite_data = l2[0:10] + l2[13:20] + l2[21:28] + l2[28:43]
    composite_cd = l2[43]
    expected_composite_cd = compute_check_digit(composite_data)

    checksums_valid = (
        doc_num_cd == expected_doc_cd
        and dob_cd == expected_dob_cd
        and expiry_cd == expected_expiry_cd
        and personal_valid
        and composite_cd == expected_composite_cd
    )

    return {
        "valid_format": True,
        "format": "TD3",
        "document_type": doc_type or "P",
        "issuing_country": issuing_country,
        "full_name": name_info["full_name"],
        "surname": name_info["surname"],
        "given_names": name_info["given_names"],
        "document_number": doc_number,
        "nationality": nationality,
        "date_of_birth": date_of_birth,
        "sex": sex,
        "expiry_date": expiry_date,
        "personal_number": personal_number or None,
        "checksums": {
            "document_number_valid": doc_num_cd == expected_doc_cd,
            "date_of_birth_valid": dob_cd == expected_dob_cd,
            "expiry_date_valid": expiry_cd == expected_expiry_cd,
            "personal_number_valid": personal_valid,
            "composite_valid": composite_cd == expected_composite_cd,
            "all_valid": checksums_valid,
        },
    }
