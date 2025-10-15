from __future__ import annotations

import hmac
import hashlib
import struct
from typing import Any


def prf(key: bytes, counter: int) -> bytes:
    """HMAC-SHA256 PRF over an 8-byte big-endian counter."""
    return hmac.new(key, struct.pack(">Q", counter), hashlib.sha256).digest()


def prf_zr(key: bytes, counter: int, grp: Any) -> Any:
    """Map PRF output into ZR using charm's PairingGroup.hash."""
    try:
        from charm.toolbox.pairinggroup import ZR as CHARM_ZR

        h = prf(key, counter)
        return grp.hash(h, CHARM_ZR)
    except Exception as e:
        raise RuntimeError("Group does not support prf_zr mapping to ZR") from e
