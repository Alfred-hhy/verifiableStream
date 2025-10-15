from __future__ import annotations

"""Chameleon Vector Commitment (CVC) primitives (Construction 2).

实现 Commit/Open/Verify 与 KeyGen；更新与变色龙更新暂未实现。
"""

from typing import Any, List, Dict
import os

from charm.toolbox.pairinggroup import G1, ZR, pair

from ..common.types import CVCParamsPK, CVCParamsSK
from ..common import sig


def keygen(grp: Any, q: int) -> tuple[CVCParamsPK, CVCParamsSK, dict]:
    # generator in G1
    g = grp.random(G1)
    # slot trapdoors z_i and bases h_i = g^{z_i}
    z_list = [grp.random(ZR) for _ in range(q + 1)]
    h_list = [g ** z for z in z_list]
    # h_{i,j} for i!=j: deterministically h_{i,j} = g^{z_i * z_j}
    hij: Dict[tuple[int, int], bytes] = {}
    for i in range(q + 1):
        for j in range(q + 1):
            if i == j:
                continue
            hij[(i + 1, j + 1)] = grp.serialize(g ** (z_list[i] * z_list[j]))
    # sign h_i values (public key compression; here仅打包h_i，验签可后续补)
    ssk, vk = sig.keygen()
    signed_hi: List[bytes] = []
    for i, h in enumerate(h_list, start=1):
        b = grp.serialize(h)
        s = sig.sign(ssk, b + i.to_bytes(4, "big"))
        # 打包 (h_i, sig_i)
        signed_hi.append(b + s)

    pk = CVCParamsPK(g=grp.serialize(g), signed_hi=signed_hi, q=q)
    sk = CVCParamsSK(prf_key=os.urandom(32), trapdoors=[grp.serialize(z) for z in z_list], q=q)
    server_bootstrap = {
        "h_list": [grp.serialize(h) for h in h_list],
        "hij": hij,
        "vk": vk,
    }
    return pk, sk, server_bootstrap


def commit_vec(grp: Any, g_b: bytes, h_list_b: List[bytes], m_list: List[Any], r: Any) -> bytes:
    g = grp.deserialize(g_b)
    C = g ** r
    for i, m in enumerate(m_list):
        if m is None:
            continue
        if int(str(m)) == 0:
            continue
        h_i = grp.deserialize(h_list_b[i])
        C *= h_i ** m
    return grp.serialize(C)


def open_slot(grp: Any, h_i_b: bytes, hij_row: Dict[int, bytes], m_list: List[Any], r: Any) -> bytes:
    # π_i = h_i^r * ∏_{j≠i} h_{i,j}^{m_j}
    h_i = grp.deserialize(h_i_b)
    pi = h_i ** r
    # index of i not given; hij_row keyed by j
    for j, m in enumerate(m_list, start=1):
        if j in hij_row:
            hij = grp.deserialize(hij_row[j])
            pi *= hij ** m
    return grp.serialize(pi)


def verify_slot(grp: Any, g_b: bytes, C_b: bytes, h_i_b: bytes, m_i: Any, pi_b: bytes) -> bool:
    g = grp.deserialize(g_b)
    C = grp.deserialize(C_b)
    h_i = grp.deserialize(h_i_b)
    pi = grp.deserialize(pi_b)
    lhs = pair(C * (h_i ** (-m_i)), h_i)
    rhs = pair(pi, g)
    return lhs == rhs


def update_commit(grp: Any, C_b: bytes, h_i_b: bytes, delta: Any) -> bytes:
    C = grp.deserialize(C_b)
    h_i = grp.deserialize(h_i_b)
    C2 = C * (h_i ** delta)
    return grp.serialize(C2)
