"""
Normalizers for ledger-publisher.

Implements field-specific normalization functions.
"""

import json
import re
from typing import Any


def trim_ascii(value: str) -> str:
    """Remove leading/trailing ASCII whitespace."""
    return value.strip()


def lower(value: str) -> str:
    """Convert to lowercase."""
    return value.lower()


def upper(value: str) -> str:
    """Convert to uppercase."""
    return value.upper()


def idna_lower_strip_trailing_dot(value: str) -> str:
    """
    IDNA encode domain, convert to lowercase, remove trailing dot.

    Example: EXAMPLE.COM → example.com
    """
    # IDNA encode
    try:
        encoded = value.encode('idna').decode('ascii')
    except Exception:
        # Fallback if already ASCII
        encoded = value

    # Lowercase
    encoded = encoded.lower()

    # Remove trailing dot
    if encoded.endswith('.'):
        encoded = encoded[:-1]

    return encoded


def lower_hex(value: str) -> str:
    """
    Convert to lowercase hex, validate format.

    Example: 0XABC...123 → 0xabc...123
    """
    value = value.lower()
    if not re.match(r'^0x[0-9a-f]{64}$', value):
        raise ValueError(f"Invalid hex format: {value}")
    return value


def lower_address_optional(value: str) -> str:
    """
    Validate and lowercase EVM address.

    Optional: empty string returns empty string.
    """
    if not value:
        return ""
    value = value.lower()
    if not re.match(r'^0x[0-9a-f]{40}$', value):
        raise ValueError(f"Invalid address format: {value}")
    return value


def iso8601_to_utc(value: str) -> str:
    """
    Parse ISO8601 timestamp, convert to UTC, output as RFC3339.

    Example: 2026-01-17T10:30:00+08:00 → 2026-01-17T02:30:00Z
    """
    from datetime import datetime, timezone

    # Parse ISO8601 string
    # Handle 'Z' suffix (UTC)
    if value.endswith('Z'):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    else:
        dt = datetime.fromisoformat(value)

    # Convert to UTC
    dt_utc = dt.astimezone(timezone.utc)

    # Format as RFC3339
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def decimal_string(value: str) -> str:
    """
    Validate decimal string format.

    Example: "123.45" → "123.45"
    """
    if not re.match(r'^[0-9]+(\.[0-9]+)?$', value):
        raise ValueError(f"Invalid decimal string: {value}")
    return value


def decimal_string_optional(value: str) -> str:
    """Optional version of decimal_string."""
    if not value:
        return ""
    return decimal_string(value)


def lower_enum(value: str) -> str:
    """
    Validate and lowercase enum value.

    Assumes validation against allowed values happens at schema level.
    """
    return value.lower()


def trim_ascii_optional(value: str) -> str:
    """Optional version of trim_ascii."""
    if not value:
        return ""
    return trim_ascii(value)


def lower_enum_optional(value: str) -> str:
    """Optional version of lower_enum."""
    if not value:
        return ""
    return lower_enum(value)


def deterministic_json_optional(value: Any) -> str:
    """
    Convert to deterministic JSON (optional field).

    Uses reference implementation from ledger-spec.
    """
    if not value:
        return ""

    # Import reference implementation
    import sys
    from pathlib import Path
    spec_path = Path(__file__).resolve().parents[2] / 'ledger-spec'
    sys.path.insert(0, str(spec_path))
    from reference_impl import deterministic_json

    return deterministic_json(value)


def apply(normalizer_name: str, value: Any) -> Any:
    """
    Apply a normalizer by name.

    Args:
        normalizer_name: Name of the normalizer function
        value: Value to normalize

    Returns:
        Normalized value
    """
    normalizers_map = {
        'trim_ascii': trim_ascii,
        'lower': lower,
        'upper': upper,
        'idna_lower_strip_trailing_dot': idna_lower_strip_trailing_dot,
        'lower_hex': lower_hex,
        'lower_address_optional': lower_address_optional,
        'iso8601_to_utc': iso8601_to_utc,
        'decimal_string': decimal_string,
        'decimal_string_optional': decimal_string_optional,
        'lower_enum': lower_enum,
        'lower_enum_optional': lower_enum_optional,
        'trim_ascii_optional': trim_ascii_optional,
        'deterministic_json_optional': deterministic_json_optional,
    }

    if normalizer_name not in normalizers_map:
        raise ValueError(f"Unknown normalizer: {normalizer_name}")

    normalizer = normalizers_map[normalizer_name]

    # Handle optional normalizers
    if normalizer_name.endswith('_optional'):
        if not value:
            return ""

    return normalizer(value)
