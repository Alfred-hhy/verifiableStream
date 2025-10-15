from __future__ import annotations

import hmac
import hashlib
import struct
from typing import Any


def prf(key: bytes, counter: int) -> bytes:
    """HMAC-SHA256 PRF over an 8-byte big-endian counter."""
    return hmac.new(key, struct.pack(">Q", counter), hashlib.sha256).digest()


def prf_zr(key: bytes, counter: int, grp: Any) -> Any:
    """Map PRF output into the group field Zp using the group's hash API.

    This relies on a charm-crypto style group object providing a ZR type
    and hash method. Raises if the group does not support this operation.
    """
    try:
        # Some PairingGroup interfaces accept bytes directly to ZR via hash.
        h = prf(key, counter)
        # In charm, one typically does: grp.hash(data, ZR)
        ZR = getattr(grp, "ZR", None)
        if ZR is None:
            # Try attribute on module-like impl
            ZR = type(getattr(grp, "random", None))  # best-effort
        return grp.hash(h, ZR)
    except Exception as e:
        raise RuntimeError("Group does not support prf_zr mapping to ZR") from e

