from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional


class GroupParams(BaseModel):
    curve: str
    g1: bytes
    g2: bytes


class CVCParams(BaseModel):
    q: int


class RootDigest(BaseModel):
    value: bytes


class CVCNodeRecord(BaseModel):
    idx: int
    parent: Optional[int]
    slot: int
    commit: bytes
    proof_data_slot1: bytes
    proof_to_parent_slot: bytes
    acc_update_token: Optional[bytes] = None


class CVCAuthPathSeg(BaseModel):
    node_commit: bytes
    proof_for_child_slot: bytes
    signed_hi: bytes


class CVCAuthPath(BaseModel):
    segments: List[CVCAuthPathSeg]


class ACCPublic(BaseModel):
    g: bytes
    gs: bytes
    vk_sig: bytes
    accumulator: bytes


class ACCProof(BaseModel):
    sigma: bytes
    w: bytes
    u: bytes


class QueryProof(BaseModel):
    scheme: str  # 'cvc' or 'acc'
    index: int
    payload: bytes


class AppendReceipt(BaseModel):
    index: int
    root: RootDigest


class UpdateReceipt(BaseModel):
    index: int
    root: RootDigest


# CVC key material (public parameters and secret), Construction 2/3 wrappers
class CVCParamsPK(BaseModel):
    g: bytes
    signed_hi: List[bytes]
    q: int


class CVCParamsSK(BaseModel):
    prf_key: bytes
    trapdoors: List[bytes]
    q: int


# ACC primitives state and keys
class ACCParams(BaseModel):
    curve: str


class ACCKey(BaseModel):
    s: bytes  # secret trapdoor (client only)
    g: bytes
    gs: bytes


class ACCState(BaseModel):
    value: bytes  # accumulator value f0(E)
    upto: int
    cache: List[bytes]

