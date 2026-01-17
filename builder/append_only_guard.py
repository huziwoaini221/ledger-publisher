"""
Append-only guard for ledger-publisher.

Ensures that existing bundles cannot be modified.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional


def get_existing_manifest(remote_url: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Get existing manifest from remote GitHub Pages.

    Args:
        remote_url: Base URL of GitHub Pages
        date: Bundle date (YYYY-MM-DD)

    Returns:
        Manifest dict or None if not found
    """
    try:
        import urllib.request
        manifest_url = f"{remote_url}/proofs/{date}/manifest.json"
        with urllib.request.urlopen(manifest_url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return None


def check_append_only(
    bundle_dir: Path,
    remote_url: Optional[str] = None
) -> bool:
    """
    Check append-only constraint.

    Args:
        bundle_dir: Local bundle directory
        remote_url: Remote GitHub Pages URL (optional)

    Returns:
        True if append-only constraint satisfied

    Raises:
        RuntimeError: If append-only constraint violated
    """
    manifest_file = bundle_dir / "manifest.json"

    if not manifest_file.exists():
        return True  # New bundle, OK

    # Load local manifest
    local_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    local_manifest_sha256 = hashlib.sha256(manifest_file.read_bytes()).hexdigest()

    # If remote URL provided, check remote
    if remote_url:
        date = bundle_dir.parent.name  # Should be YYYY-MM-DD
        remote_manifest = get_existing_manifest(remote_url, date)

        if remote_manifest:
            remote_manifest_sha256 = remote_manifest.get("daily_root_sha256", "")
            if local_manifest_sha256 != remote_manifest_sha256:
                raise RuntimeError(
                    f"Append-only violation: {date} already exists with different manifest"
                )

    return True


def main():
    """CLI entry point for append-only guard."""
    import argparse

    parser = argparse.ArgumentParser(description="Check append-only constraint")
    parser.add_argument("--bundle-dir", required=True, help="Bundle directory")
    parser.add_argument("--remote-url", help="Remote GitHub Pages URL")

    args = parser.parse_args()

    try:
        result = check_append_only(
            bundle_dir=Path(args.bundle_dir),
            remote_url=args.remote_url
        )
        if result:
            print("✅ Append-only constraint satisfied")
        else:
            print("❌ Append-only constraint violated")
            raise SystemExit(1)
    except RuntimeError as e:
        print(f"❌ {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
