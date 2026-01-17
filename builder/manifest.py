"""
Manifest generation for ledger-publisher.

Generates manifest.json with file hashes and sizes.
"""

import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def compute_file_size(file_path: Path) -> int:
    """Compute file size in bytes."""
    return file_path.stat().st_size


def generate_manifest(
    date: str,
    files: List[Path],
    daily_root: str,
    base_url: str = ""
) -> Dict[str, Any]:
    """
    Generate manifest.json.

    Args:
        date: Bundle date (YYYY-MM-DD)
        files: List of file paths
        daily_root: Merkle root hash
        base_url: Base URL for proof bundle

    Returns:
        Manifest dictionary
    """
    files_data = []

    for file_path in sorted(files):
        relative_path = file_path.name
        sha256 = compute_file_hash(file_path)
        size = compute_file_size(file_path)

        files_data.append({
            "path": relative_path,
            "sha256": sha256,
            "size": size
        })

    # Compute total bytes
    total_bytes = sum(f["size"] for f in files_data)

    # Create manifest
    manifest = {
        "version": "1",
        "date": date,
        "files": files_data,
        "core_spec_sha256": "...",  # TODO: compute from core_spec.json
        "profile_sha256": "...",   # TODO: compute from profile.json
        "daily_root_sha256": daily_root
    }

    return manifest
