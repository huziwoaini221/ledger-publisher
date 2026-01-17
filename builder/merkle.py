"""
Merkle tree implementation for ledger-publisher.

Implements binary Merkle tree with odd leaf duplicate_last strategy.
Includes Merkle proof generation and verification.
"""

import hashlib
from typing import List, Dict, Tuple


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


class MerkleTree:
    """
    Merkle tree with proof generation support.
    """

    def __init__(self, leaves: List[str]):
        """
        Build a Merkle tree from leaf hashes.

        Args:
            leaves: List of SHA256 hashes (lowercase hex strings)
        """
        if len(leaves) == 0:
            raise ValueError("Cannot build Merkle tree from empty leaves")

        self.leaves = leaves.copy()
        self.layers = self._build_tree_layers(leaves)
        self.root = self.layers[-1][0] if self.layers else leaves[0]

    def _build_tree_layers(self, leaves: List[str]) -> List[List[str]]:
        """
        Build all layers of the Merkle tree.

        Args:
            leaves: List of leaf hashes

        Returns:
            List of layers, where each layer is a list of hashes
        """
        layers = [leaves.copy()]
        current = leaves.copy()

        while len(current) > 1:
            # Odd leaf: duplicate last
            if len(current) % 2 == 1:
                current.append(current[-1])

            # Build next level
            next_level = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i+1]
                parent = hashlib.sha256(
                    (left + right).encode('utf-8')
                ).hexdigest()
                next_level.append(parent)

            layers.append(next_level)
            current = next_level

        return layers

    def generate_proof(self, leaf_index: int) -> Dict:
        """
        Generate a Merkle proof for a leaf.

        Args:
            leaf_index: Index of the leaf in the original leaves list

        Returns:
            Dictionary containing:
                - leaf_index: Original index of the leaf
                - leaf_hash: Hash of the leaf
                - proof: List of sibling hashes on the path to root
                - expected_root: Expected Merkle root

        Raises:
            IndexError: If leaf_index is out of range
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError(f"leaf_index {leaf_index} out of range [0, {len(self.leaves)-1}]")

        leaf_hash = self.leaves[leaf_index]
        proof = []

        # Traverse from bottom to top
        current_index = leaf_index

        for layer_idx in range(len(self.layers) - 1):
            current_layer = self.layers[layer_idx]

            # Determine if current node is left or right child
            is_left = (current_index % 2 == 0)

            if is_left:
                # Current node is left, get right sibling
                sibling_index = current_index + 1
            else:
                # Current node is right, get left sibling
                sibling_index = current_index - 1

            # Get sibling hash
            sibling_hash = current_layer[sibling_index]

            # Add to proof
            proof.append({
                "direction": "left" if is_left else "right",
                "sibling_hash": sibling_hash
            })

            # Move to parent level
            current_index = current_index // 2

        return {
            "leaf_index": leaf_index,
            "leaf_hash": leaf_hash,
            "proof": proof,
            "expected_root": self.root
        }


def verify_proof(leaf_hash: str, proof: List[Dict], expected_root: str) -> bool:
    """
    Verify a Merkle proof.

    Args:
        leaf_hash: Hash of the leaf to verify
        proof: List of proof steps, each containing:
            - direction: "left" or "right"
            - sibling_hash: Hash of the sibling node
        expected_root: Expected Merkle root

    Returns:
        True if proof is valid, False otherwise
    """
    current = leaf_hash

    for step in proof:
        direction = step["direction"]
        sibling = step["sibling_hash"]

        if direction == "left":
            # Current is left child
            current = hashlib.sha256(
                (current + sibling).encode('utf-8')
            ).hexdigest()
        else:
            # Current is right child
            current = hashlib.sha256(
                (sibling + current).encode('utf-8')
            ).hexdigest()

    return current == expected_root
