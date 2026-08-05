"""
Security utility functions for input sanitization and validation.

These helpers provide safe escaping/validation for contexts where
parameterized queries are not available (e.g., Salesforce SOQL).
"""
import re


def sanitize_soql_string(value: str) -> str:
    """
    Sanitize a string value for safe use in a SOQL string literal.

    SOQL uses single quotes for string delimiters. This function escapes
    backslashes and single quotes to prevent SOQL injection.

    Args:
        value: Raw input string.

    Returns:
        Escaped string safe for use inside single-quoted SOQL literals.
    """
    # Must escape backslash first, then single quote
    return value.replace("\\", "\\\\").replace("'", "\\'")


def sanitize_soql_like(value: str) -> str:
    """
    Sanitize a string value for safe use in a SOQL LIKE pattern.

    In addition to basic string escaping, this also escapes SOQL wildcards
    (% and _) so they are treated as literals rather than pattern characters.

    Args:
        value: Raw input string.

    Returns:
        Escaped string safe for use in a SOQL LIKE pattern.
    """
    # Escape SOQL wildcards first, then special chars
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    escaped = escaped.replace("%", "\\%").replace("_", "\\_")
    return escaped


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
