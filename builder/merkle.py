"""
Merkle tree implementation for ledger-publisher.

Implements binary Merkle tree with odd leaf duplicate_last strategy.
"""

import hashlib
from typing import List


def compute_leaf(canonical_bytes: str) -> str:
    """
    Compute leaf hash from canonical bytes.

    Args:
        canonical_bytes: Canonical string representation

    Returns:
        SHA256 hash as lowercase hex string
    """
    return hashlib.sha256(canonical_bytes.encode('utf-8')).hexdigest()


def build_merkle_tree(leaves: List[str]) -> str:
    """
    Build Merkle tree from leaf hashes.

    Args:
        leaves: List of SHA256 hashes (lowercase hex strings)

    Returns:
        Merkle root as lowercase hex string

    Raises:
        ValueError: If leaves list is empty
    """
    if len(leaves) == 0:
        raise ValueError("Cannot build Merkle tree from empty leaves")

    if len(leaves) == 1:
        return leaves[0]

    # Odd leaf: duplicate last
    if len(leaves) % 2 == 1:
        leaves.append(leaves[-1])

    # Build next level
    next_level = []
    for i in range(0, len(leaves), 2):
        left = leaves[i]
        right = leaves[i+1]
        parent = hashlib.sha256(
            (left + right).encode('utf-8')
        ).hexdigest()
        next_level.append(parent)

    # Recurse
    return build_merkle_tree(next_level)
