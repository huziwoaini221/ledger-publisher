"""
Main build logic for ledger-publisher.

Orchestrates the entire bundle building process.
"""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from . import merkle
from . import normalizers
from . import manifest


def load_profile(profile_dir: Path, profile_id: str) -> Dict[str, Any]:
    """Load profile definition."""
    profile_file = profile_dir / profile_id / "profile.json"
    return json.loads(profile_file.read_text(encoding="utf-8"))


def load_records(input_file: Path) -> List[Dict[str, Any]]:
    """Load records from JSONL file."""
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def normalize_record(record: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Apply normalizers to a record."""
    normalized = {}
    for field, normalizer_name in profile["normalizers"].items():
        if field in record or normalizer_name.endswith("_optional"):
            value = record.get(field, "")
            normalized[field] = normalizers.apply(normalizer_name, value)

    # Handle missing optional fields
    for field in profile["canonical_fields"]:
        if field not in normalized:
            normalized[field] = ""

    return normalized


def canonicalize_record(record: Dict[str, Any], profile: Dict[str, Any]) -> str:
    """Convert record to canonical bytes."""
    # Apply normalizers
    normalized = normalize_record(record, profile)

    # Build canonical string
    fields = profile["canonical_fields"]
    separator = profile.get("canonical_record_separator", "|")
    line_ending = profile.get("canonical_line_ending", "\n")

    canonical = separator.join(normalized.get(f, "") for f in fields)
    return canonical + line_ending


def sort_key(record: Dict[str, Any], profile: Dict[str, Any]) -> tuple:
    """Generate sort key for a record."""
    normalized = normalize_record(record, profile)
    canonical_bytes = canonicalize_record(record, profile)

    sort_keys = profile["sort_keys"]

    # Special handling for canonical_bytes in sort_keys
    key_parts = []
    for key in sort_keys:
        if key == "canonical_bytes":
            key_parts.append(canonical_bytes)
        else:
            key_parts.append(normalized.get(key, ""))

    return tuple(key_parts)


def build_bundle(
    input_file: Path,
    profile_dir: Path,
    profile_id: str,
    date: str,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Build a complete proof bundle.

    Args:
        input_file: Path to input JSONL file
        profile_dir: Path to profiles directory
        profile_id: Profile ID to use
        date: Bundle date (YYYY-MM-DD)
        output_dir: Output directory

    Returns:
        Dictionary with build results
    """
    # Load profile
    profile = load_profile(profile_dir, profile_id)

    # Load records
    records = load_records(input_file)

    # Validate required fields
    for i, record in enumerate(records):
        for field in profile["required_fields"]:
            if field not in record or not record[field]:
                raise ValueError(f"Record {i}: missing required field '{field}'")

    # Sort records
    sorted_records = sorted(records, key=lambda r: sort_key(r, profile))

    # Compute canonical bytes and leaves
    leaves = []
    canonical_bytes_list = []

    for record in sorted_records:
        canonical = canonicalize_record(record, profile)
        canonical_bytes_list.append(canonical)
        leaf = merkle.compute_leaf(canonical)
        leaves.append(leaf)

    # Build Merkle tree
    root = merkle.build_merkle_tree(leaves)

    # Generate output files
    bundle_dir = output_dir / f"proofs/{date}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Write records
    records_per_file = 10000
    for i in range(0, len(sorted_records), records_per_file):
        chunk = sorted_records[i:i+records_per_file]
        file_num = i // records_per_file
        records_file = bundle_dir / f"records-{file_num:03d}.jsonl"

        with open(records_file, 'w', encoding='utf-8') as f:
            for record in chunk:
                f.write(json.dumps(record) + '\n')

    # Write daily_root.txt
    root_file = bundle_dir / "daily_root.txt"
    root_file.write_text(root + '\n', encoding='utf-8')

    # Write core_spec.json
    core_spec = {
        "core_spec_version": "1.2.1",
        "hash": "sha256",
        "merkle": "binary",
        "odd_leaf": "duplicate_last",
        "hex": "lowercase",
        "encoding": "utf-8",
        "canonical_line_ending": "\n",
        "canonical_record_separator": "|"
    }
    core_spec_file = bundle_dir / "core_spec.json"
    core_spec_file.write_text(json.dumps(core_spec, indent=2) + '\n', encoding='utf-8')

    # Write profile.json
    profile_json = {
        "profile_id": profile_id,
        "profile_version": profile["profile_version"],
        "profile_sha256": "..."  # TODO: compute from profile files
    }
    profile_file = bundle_dir / "profile.json"
    profile_file.write_text(json.dumps(profile_json, indent=2) + '\n', encoding='utf-8')

    # Generate manifest
    files_list = list(bundle_dir.glob("records-*.jsonl"))
    files_list.append(root_file)
    files_list.append(core_spec_file)
    files_list.append(profile_file)

    manifest_data = manifest.generate_manifest(
        date=date,
        files=files_list,
        daily_root=root
    )

    manifest_file = bundle_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2) + '\n', encoding='utf-8')

    # Write checkpoint.json
    checkpoint = {
        "version": "1",
        "date": date,
        "manifest_sha256": hashlib.sha256(manifest_file.read_bytes()).hexdigest(),
        "daily_root": root,
        "prev_checkpoint_sha256": "0000000000000000000000000000000000000000000000000000000000000"
    }
    checkpoint_file = bundle_dir / "checkpoint.json"
    checkpoint_file.write_text(json.dumps(checkpoint, indent=2) + '\n', encoding='utf-8')

    # Generate Merkle proofs for all records
    print(f"📝 Generating Merkle proofs...")
    from .generate_proofs import generate_proofs_for_bundle
    generate_proofs_for_bundle(str(bundle_dir))

    return {
        "date": date,
        "records_count": len(sorted_records),
        "daily_root": root,
        "bundle_dir": bundle_dir
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Build proof bundle")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--profile-dir", required=True, help="Profile directory")
    parser.add_argument("--profile", default="domain-onchain-payments", help="Profile ID")
    parser.add_argument("--date", help="Bundle date (YYYY-MM-DD)")
    parser.add_argument("--output", required=True, help="Output directory")

    args = parser.parse_args()

    # Default to today
    if not args.date:
        args.date = datetime.now().strftime("%Y-%m-%d")

    # Build bundle
    result = build_bundle(
        input_file=Path(args.input),
        profile_dir=Path(args.profile_dir),
        profile_id=args.profile,
        date=args.date,
        output_dir=Path(args.output)
    )

    print(f"✅ Bundle built successfully!")
    print(f"   Date: {result['date']}")
    print(f"   Records: {result['records_count']}")
    print(f"   Daily Root: {result['daily_root']}")
    print(f"   Output: {result['bundle_dir']}")


if __name__ == "__main__":
    main()
