from __future__ import annotations

from typing import Any, Type

import msgpack
from pydantic import BaseModel


def _default(obj: Any):
    if isinstance(obj, BaseModel):
        return {"__pydantic__": obj.__class__.__name__, "data": obj.model_dump()}
    raise TypeError(f"Type not serializable: {type(obj)}")


def pack(obj: Any) -> bytes:
    return msgpack.packb(obj, default=_default, use_bin_type=True)


def unpack(b: bytes, cls: Type[Any]) -> Any:
    try:
        data = msgpack.unpackb(b, raw=False)
        if isinstance(data, dict) and "__pydantic__" in data and "data" in data:
            # Best-effort for our own packed models
            return cls(**data["data"])  # type: ignore[arg-type]
        if issubclass(cls, BaseModel):
            return cls(**data)  # type: ignore[arg-type]
        return data
    except Exception as e:
        raise ValueError("msgpack decode failed") from e

