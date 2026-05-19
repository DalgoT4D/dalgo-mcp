"""PII detection and masking for warehouse data.

Uses column-name heuristics to identify personally identifiable information
and masks values before they reach the model context.
"""

import re

# Column name patterns that suggest PII (case-insensitive partial match)
PII_COLUMN_PATTERNS = [
    # Direct identifiers
    r"name",
    r"first.?name",
    r"last.?name",
    r"full.?name",
    r"father.?name",
    r"mother.?name",
    r"spouse.?name",
    r"guardian",
    # Contact info
    r"email",
    r"e.?mail",
    r"phone",
    r"mobile",
    r"contact",
    r"telephone",
    r"whatsapp",
    # Government IDs
    r"aadhaar",
    r"aadhar",
    r"pan.?(card|no|number)",
    r"passport",
    r"voter.?id",
    r"ration.?card",
    r"ssn",
    r"social.?security",
    r"national.?id",
    r"driving.?licen",
    # Address
    r"address",
    r"street",
    r"house.?no",
    r"pin.?code",
    r"zip.?code",
    r"postal",
    # Financial
    r"account.?no",
    r"account.?number",
    r"bank.?account",
    r"ifsc",
    r"card.?number",
    # Other sensitive
    r"date.?of.?birth",
    r"\bdob\b",
    r"birth.?date",
    r"beneficiary.?name",
    r"patient.?name",
    r"student.?name",
    r"member.?name",
]

_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in PII_COLUMN_PATTERNS]


def is_pii_column(column_name: str) -> bool:
    """Check if a column name matches known PII patterns."""
    return any(p.search(column_name) for p in _compiled_patterns)


def mask_value(value) -> str:
    """Replace a PII value with a masked placeholder."""
    if value is None:
        return None
    return "***MASKED***"


def mask_pii_in_rows(rows: list[dict]) -> list[dict]:
    """Mask PII columns in a list of row dicts.

    Detects PII columns by name on the first row, then masks those
    columns across all rows.
    """
    if not rows or not isinstance(rows, list):
        return rows

    first = rows[0] if rows else {}
    if not isinstance(first, dict):
        return rows

    pii_cols = {col for col in first.keys() if is_pii_column(col)}

    if not pii_cols:
        return rows

    masked = []
    for row in rows:
        masked_row = {}
        for col, val in row.items():
            masked_row[col] = mask_value(val) if col in pii_cols else val
        masked.append(masked_row)

    return masked
