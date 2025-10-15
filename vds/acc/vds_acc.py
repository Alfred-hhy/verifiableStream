from __future__ import annotations

from typing import Any, Tuple

from ..common.types import (
    ACCPublic,
    QueryProof,
    AppendReceipt,
    UpdateReceipt,
)
from ..common.errors import VerifyError, GroupError, StorageError
from ..common import encoding, sig


class VDSACC:
    def __init__(self, store: Any, grp: Any):
        self.store = store
        self.grp = grp

    def setup(self) -> tuple[ACCPublic, bytes]:  # client state as bytes placeholder
        raise GroupError("VDS-ACC setup not implemented (requires accumulator).")

    def append(self, st: bytes, data: bytes) -> AppendReceipt:
        raise GroupError("VDS-ACC append not implemented.")

    def query(self, idx: int) -> QueryProof:
        raise GroupError("VDS-ACC query not implemented.")

    def verify(self, pub: ACCPublic, idx: int, data: bytes, proof: QueryProof) -> bool:
        raise GroupError("VDS-ACC verify not implemented.")

    def update(self, st: bytes, idx: int, new_data: bytes) -> UpdateReceipt:
        raise GroupError("VDS-ACC update not implemented.")

