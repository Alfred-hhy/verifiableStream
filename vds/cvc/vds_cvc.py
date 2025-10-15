from __future__ import annotations

from typing import Any

from ..common.types import (
    CVCParamsPK,
    CVCParamsSK,
    RootDigest,
    QueryProof,
    AppendReceipt,
    UpdateReceipt,
)
from ..common.errors import VerifyError, GroupError, StorageError


class CVCClientState:
    def __init__(self, pk: CVCParamsPK, sk: CVCParamsSK, root: RootDigest, cnt: int = 0):
        self.pk = pk
        self.sk = sk
        self.root = root
        self.cnt = cnt


class VDSCVC:
    def __init__(self, store: Any, grp: Any, q: int = 64):
        self.store = store
        self.grp = grp
        self.q = q

    def setup(self) -> tuple[CVCClientState, dict]:
        raise GroupError("VDS-CVC setup not implemented (requires pairing).")

    def append(self, st: CVCClientState, data: bytes) -> AppendReceipt:
        raise GroupError("VDS-CVC append not implemented.")

    def query(self, idx: int) -> QueryProof:
        raise GroupError("VDS-CVC query not implemented.")

    def verify(self, st: CVCClientState, idx: int, data: bytes, proof: QueryProof) -> bool:
        raise GroupError("VDS-CVC verify not implemented.")

    def update(self, st: CVCClientState, idx: int, new_data: bytes) -> UpdateReceipt:
        raise GroupError("VDS-CVC update not implemented.")

