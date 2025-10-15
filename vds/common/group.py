from __future__ import annotations

from typing import Any
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
    try:
        from charm.toolbox.pairinggroup import ZR

        return grp.hash(data, ZR)
    except Exception as e:  # pragma: no cover
        raise GroupError("hash_to_Zp requires charm PairingGroup") from e


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

