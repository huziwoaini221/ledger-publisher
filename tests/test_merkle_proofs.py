"""
Test Merkle proof generation and verification.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ledger-spec"))

from builder.merkle import MerkleTree, verify_proof, compute_leaf
from reference_impl import deterministic_json


def test_merkle_proof_small():
    """Test Merkle proof with small tree."""
    print("🧪 Test 1: Small tree (4 leaves)")

    # Create sample leaves (use even number to avoid duplicate complexity)
    leaves = [
        compute_leaf("record1"),
        compute_leaf("record2"),
        compute_leaf("record3"),
        compute_leaf("record4")
    ]

    # Build tree
    tree = MerkleTree(leaves)

    print(f"   Merkle root: {tree.root}")

    # Test proof for each leaf
    for i in range(len(leaves)):
        proof = tree.generate_proof(i)
        is_valid = verify_proof(
            proof["leaf_hash"],
            proof["proof"],
            proof["expected_root"]
        )

        if is_valid:
            print(f"   ✅ Proof for leaf {i} verified")
        else:
            print(f"   ❌ Proof for leaf {i} FAILED")
            return False

    print("   ✅ All proofs verified\n")
    return True


def test_merkle_proof_large():
    """Test Merkle proof with larger tree."""
    print("🧪 Test 2: Large tree (100 leaves)")

    # Create 100 sample leaves
    leaves = []
    for i in range(100):
        record = {"index": str(i), "data": f"record_{i}"}  # Convert index to string
        canonical = deterministic_json(record)
        leaf = compute_leaf(canonical)
        leaves.append(leaf)

    # Build tree
    tree = MerkleTree(leaves)

    print(f"   Merkle root: {tree.root}")

    # Test proof for random leaves
    import random
    test_indices = random.sample(range(100), 10)

    for i in test_indices:
        proof = tree.generate_proof(i)
        is_valid = verify_proof(
            proof["leaf_hash"],
            proof["proof"],
            proof["expected_root"]
        )

        if is_valid:
            print(f"   ✅ Proof for leaf {i} verified")
        else:
            print(f"   ❌ Proof for leaf {i} FAILED")
            return False

    print("   ✅ All sample proofs verified\n")
    return True


def test_proof_structure():
    """Test that proof has correct structure."""
    print("🧪 Test 3: Proof structure validation")

    leaves = [compute_leaf(f"record{i}") for i in range(10)]
    tree = MerkleTree(leaves)

    proof = tree.generate_proof(0)

    # Check structure
    assert "leaf_index" in proof, "Missing leaf_index"
    assert "leaf_hash" in proof, "Missing leaf_hash"
    assert "proof" in proof, "Missing proof list"
    assert "expected_root" in proof, "Missing expected_root"

    # Check proof steps
    for step in proof["proof"]:
        assert "direction" in step, "Missing direction"
        assert "sibling_hash" in step, "Missing sibling_hash"
        assert step["direction"] in ["left", "right"], f"Invalid direction: {step['direction']}"

    print(f"   ✅ Proof structure validated")
    print(f"   ✅ Proof depth: {len(proof['proof'])} levels")
    print(f"   ✅ Expected root: {proof['expected_root']}\n")
    return True


def test_tampering_detection():
    """Test that proof verification detects tampering."""
    print("🧪 Test 4: Tampering detection")

    leaves = [compute_leaf(f"record{i}") for i in range(10)]
    tree = MerkleTree(leaves)

    # Generate valid proof
    proof = tree.generate_proof(0)

    # Test with valid data
    is_valid = verify_proof(
        proof["leaf_hash"],
        proof["proof"],
        proof["expected_root"]
    )

    if not is_valid:
        print("   ❌ Valid proof failed verification")
        return False

    print("   ✅ Valid proof accepted")

    # Test with tampered leaf
    tampered_hash = compute_leaf("TAMPERED_DATA")
    is_valid = verify_proof(
        tampered_hash,
        proof["proof"],
        proof["expected_root"]
    )

    if is_valid:
        print("   ❌ Tampered proof ACCEPTED (should fail)")
        return False

    print("   ✅ Tampered proof rejected\n")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Merkle Proof Tests")
    print("=" * 60)
    print()

    tests = [
        test_merkle_proof_small,
        test_merkle_proof_large,
        test_proof_structure,
        test_tampering_detection
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
