"""
Generate Merkle proofs for all records in a bundle.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from .merkle import MerkleTree, verify_proof


def generate_proofs_for_bundle(bundle_dir: str) -> None:
    """
    Generate Merkle proof files for all records in a bundle.

    Args:
        bundle_dir: Path to the bundle directory (e.g., dist/proofs/2026-01-17/)
    """
    bundle_path = Path(bundle_dir)

    # Read manifest
    manifest_path = bundle_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {bundle_dir}")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Read records files to get all leaves
    records_files = sorted([
        f for f in bundle_path.glob("records-*.jsonl")
    ])

    if not records_files:
        raise FileNotFoundError(f"No records-*.jsonl files found in {bundle_dir}")

    # Collect all leaf hashes in order
    leaves = []
    record_data = []

    for records_file in records_files:
        with open(records_file, 'r') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    record_data.append(record)

                    # Compute leaf hash from canonical bytes
                    from .merkle import compute_leaf
                    from ledger_spec.reference_impl import deterministic_json

                    canonical = deterministic_json(record)
                    leaf_hash = compute_leaf(canonical)
                    leaves.append(leaf_hash)

    print(f"📊 Loaded {len(leaves)} records")

    # Build Merkle tree
    print("🌳 Building Merkle tree...")
    tree = MerkleTree(leaves)

    # Verify root matches
    daily_root_path = bundle_path / "daily_root.txt"
    with open(daily_root_path, 'r') as f:
        expected_root = f.read().strip()

    if tree.root != expected_root:
        raise ValueError(f"Merkle root mismatch: computed {tree.root}, expected {expected_root}")

    print(f"✅ Merkle root verified: {tree.root}")

    # Generate proofs for all records
    print(f"📝 Generating proofs for {len(leaves)} records...")

    proofs_dir = bundle_path / "proofs"
    proofs_dir.mkdir(exist_ok=True)

    proof_metadata = []

    for idx in range(len(leaves)):
        proof_data = tree.generate_proof(idx)

        # Save individual proof
        proof_file = proofs_dir / f"{idx}.json"
        with open(proof_file, 'w') as f:
            json.dump(proof_data, f, indent=2)

        proof_metadata.append({
            "record_index": idx,
            "proof_file": f"proofs/{idx}.json",
            "leaf_hash": proof_data["leaf_hash"]
        })

        if (idx + 1) % 100 == 0:
            print(f"   Generated {idx + 1}/{len(leaves)} proofs...")

    # Save proof index
    proof_index_file = bundle_path / "proof_index.json"
    with open(proof_index_file, 'w') as f:
        json.dump({
            "version": "1",
            "total_records": len(leaves),
            "merkle_root": tree.root,
            "proofs": proof_metadata
        }, f, indent=2)

    print(f"✅ Generated {len(leaves)} proofs")
    print(f"📁 Proof index: {proof_index_file}")
    print(f"📁 Proofs directory: {proofs_dir}")

    # Verify a few random proofs
    print("\n🔍 Verifying sample proofs...")
    import random
    sample_indices = random.sample(range(len(leaves)), min(5, len(leaves)))

    for idx in sample_indices:
        proof_data = tree.generate_proof(idx)
        is_valid = verify_proof(
            proof_data["leaf_hash"],
            proof_data["proof"],
            proof_data["expected_root"]
        )

        if is_valid:
            print(f"   ✅ Proof #{idx} verified")
        else:
            print(f"   ❌ Proof #{idx} FAILED verification")
            sys.exit(1)

    print("\n✅ All proofs generated and verified successfully!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Merkle proofs for a bundle")
    parser.add_argument("--bundle-dir", required=True, help="Bundle directory path")

    args = parser.parse_args()

    try:
        generate_proofs_for_bundle(args.bundle_dir)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
