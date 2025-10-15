from __future__ import annotations

from typing import Any
import hashlib
from charm.toolbox.pairinggroup import ZR, G1
from .errors import GroupError


class _GroupWrapper:
    def __init__(self, curve: str):
        try:
            from charm.toolbox.pairinggroup import PairingGroup

            self.grp = PairingGroup(curve)
        except Exception as e:  # pragma: no cover - environment dependent
            raise GroupError(
                "charm-crypto PairingGroup unavailable. Install charm-crypto to use pairing primitives."
            ) from e

    def obj(self) -> Any:
        return self.grp

    # Basic serialization helpers proxying charm's API
    def serialize(self, elem: Any) -> bytes:
        return self.grp.serialize(elem)

    def deserialize_G1(self, b: bytes) -> Any:
        from charm.toolbox.pairinggroup import G1

        return self.grp.deserialize(b)

    def deserialize_G2(self, b: bytes) -> Any:
        from charm.toolbox.pairinggroup import G2

        return self.grp.deserialize(b)


def get_group(curve: str = "MNT224") -> Any:
    """Return an initialized pairing group (charm-crypto)."""
    return _GroupWrapper(curve).obj()


def hash_to_Zp(grp: Any, data: bytes) -> Any:
    """Canonical map bytes -> ZR via SHA-256 then mod p.

    Using grp.init(ZR, int) ensures reduction modulo group order.
    """
    try:
        n = int.from_bytes(hashlib.sha256(data).digest(), "big")
        return grp.init(ZR, n)
    except Exception as e:  # pragma: no cover
        raise GroupError("hash_to_Zp failed") from e


def serialize_elem(grp: Any, elem: Any) -> bytes:
    try:
        return grp.serialize(elem)
    except Exception as e:  # pragma: no cover
        raise GroupError("serialize failed") from e


def deserialize_elem(grp: Any, b: bytes) -> Any:
    try:
        return grp.deserialize(b)
    except Exception as e:  # pragma: no cover
        raise GroupError("deserialize failed") from e


def pair(grp: Any, a: Any, b: Any) -> Any:
    try:
        from charm.toolbox.pairinggroup import pair

        return pair(a, b)
    except Exception as e:  # pragma: no cover
        raise GroupError("pairing failed or charm not present") from e


def serialize_G1(grp: Any, elem: Any) -> bytes:
    """Canonical serializer for G1 elements (used for pointer hashing)."""
    return serialize_elem(grp, elem)


def H_zr(grp: Any, b: bytes) -> Any:
    """Alias of hash_to_Zp for clarity in CVC code."""
    return hash_to_Zp(grp, b)
