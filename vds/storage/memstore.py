from __future__ import annotations

from typing import Dict, List, Tuple, Optional

from ..common.types import (
    RootDigest,
    CVCNodeRecord,
    CVCAuthPath,
)
from ..common.errors import StorageError


class MemStore:
    def __init__(self) -> None:
        self._roots: Dict[str, RootDigest] = {}
        self.nodes: Dict[int, CVCNodeRecord] = {}
        self._acc_items: Dict[int, Tuple[bytes, bytes, int, bytes]] = {}
        self._acc_value: Optional[bytes] = None
        self._acc_cache: List[bytes] = []
        self._acc_poly_coeffs: List[bytes] = []  # ascending coeffs over ZR, serialized
        self._acc_version: str | None = None
        self._acc_curve: str | None = None

    # --- Common root management ---
    def set_root(self, scheme: str, root: RootDigest) -> None:
        self._roots[scheme] = root

    def get_root(self, scheme: str) -> RootDigest:
        if scheme not in self._roots:
            raise StorageError(f"root for scheme {scheme} not set")
        return self._roots[scheme]

    # --- CVC ---
    def put_cvc_insert_path(self, leaf: CVCNodeRecord, parents: List[CVCNodeRecord]) -> None:
        self.nodes[leaf.idx] = leaf
        for p in parents:
            self.nodes[p.idx] = p

    def get_cvc_auth_path(self, idx: int) -> CVCAuthPath:
        # Skeleton: without real tree, return empty path
        return CVCAuthPath(segments=[])

    def apply_cvc_updates(self, update_tokens: List[bytes]) -> None:
        # Skeleton: no-op
        return

    # --- ACC ---
    def save_acc_item(self, idx: int, data: bytes, tag: bytes, sigma: bytes) -> None:
        self._acc_items[idx] = (data, tag, idx, sigma)

    def get_acc_item(self, idx: int) -> Tuple[bytes, bytes, int, bytes]:
        if idx not in self._acc_items:
            raise StorageError("ACC item not found")
        return self._acc_items[idx]

    def set_acc_state(self, acc_value: bytes, cache: List[bytes]) -> None:
        self._acc_value = acc_value
        self._acc_cache = list(cache)

    def get_acc_state(self) -> Tuple[bytes, List[bytes]]:
        if self._acc_value is None:
            raise StorageError("ACC state not set")
        return self._acc_value, list(self._acc_cache)

    # Polynomial coefficients for f(X) = prod (X + x_i), ascending, elements in ZR serialized
    def set_acc_poly(self, coeffs: List[bytes]) -> None:
        self._acc_poly_coeffs = list(coeffs)

    def get_acc_poly(self) -> List[bytes]:
        return list(self._acc_poly_coeffs)

    def acc_count(self) -> int:
        return len(self._acc_items)

    # Powers append (for performance API)
    def append_powers(self, new: List[bytes]) -> None:
        self._acc_cache.extend(new)
