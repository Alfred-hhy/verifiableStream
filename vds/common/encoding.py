from __future__ import annotations

import struct
from typing import Tuple


def encode_item(data: bytes, tag: bytes, index: int) -> bytes:
    """Encode as: [u32 len(data)] [u32 len(tag)] [data] [tag] [u64 index].

    - All integers big-endian.
    - Deterministic, self-delimiting, no ambiguity.
    """
    if index < 0:
        raise ValueError("index must be non-negative")
    return (
        struct.pack(">I", len(data))
        + struct.pack(">I", len(tag))
        + data
        + tag
        + struct.pack(">Q", index)
    )


def decode_item(b: bytes) -> Tuple[bytes, bytes, int]:
    if len(b) < 8:
        raise ValueError("buffer too short")
    dlen = struct.unpack_from(">I", b, 0)[0]
    tlen = struct.unpack_from(">I", b, 4)[0]
    offset = 8
    if len(b) < offset + dlen + tlen + 8:
        raise ValueError("buffer truncated")
    data = b[offset : offset + dlen]
    offset += dlen
    tag = b[offset : offset + tlen]
    offset += tlen
    index = struct.unpack_from(">Q", b, offset)[0]
    return data, tag, index

