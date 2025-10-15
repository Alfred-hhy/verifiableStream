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
from ..common.errors import VerifyError, GroupError
from ..common.group import hash_to_Zp
from ..common import ser
from .cvc_core import keygen as cvc_keygen, commit_vec, open_slot, verify_slot, update_commit
from charm.toolbox.pairinggroup import ZR, G1


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
        # 内部节点状态：idx -> {r: ZR, m: List[ZR], C: G1}
        self._nodes: dict[int, dict] = {}
        self._bootstrap: dict | None = None
        self._pk: CVCParamsPK | None = None
        self._sk: CVCParamsSK | None = None

    def setup(self) -> tuple[CVCClientState, dict]:
        pk, sk, bootstrap = cvc_keygen(self.grp, self.q)
        self._bootstrap = bootstrap
        self._pk = pk
        self._sk = sk
        # 预置根节点（idx=1），r_1 = PRF(1)，m 全 0
        r1 = self._prf(1)
        m0 = [self.grp.init(ZR, 0) for _ in range(self.q + 1)]
        C_root = self.grp.deserialize(commit_vec(self.grp, pk.g, bootstrap["h_list"], m0, r1))
        self._nodes[1] = {"r": r1, "m": m0, "C": C_root}
        root = RootDigest(value=self.grp.serialize(C_root))
        st = CVCClientState(pk=pk, sk=sk, root=root, cnt=0)
        return st, {"note": "server caches hij and h_list"}

    def append(self, st: CVCClientState, data: bytes) -> AppendReceipt:
        if not self._bootstrap or not self._pk or not self._sk:
            raise GroupError("setup not completed")
        h_list = self._bootstrap["h_list"]
        hij = self._bootstrap["hij"]
        g_b = self._pk.g
        # 新叶编号
        i = st.cnt + 1
        # 叶
        r_i = self._prf(i)
        m_data = hash_to_Zp(self.grp, data)
        leaf_m = [self.grp.init(ZR, 0) for _ in range(self.q + 1)]
        leaf_m[0] = m_data
        C_leaf_b = commit_vec(self.grp, g_b, h_list, leaf_m, r_i)
        C_leaf = self.grp.deserialize(C_leaf_b)
        self._nodes[i] = {"r": r_i, "m": leaf_m, "C": C_leaf}
        # 向上更新父链（堆式 q 叉树）
        def parent(x: int) -> int:
            return (x - 2) // self.q + 1 if x != 1 else 1
        def slot_in_parent(x: int) -> int:
            p = parent(x)
            return x - (self.q * (p - 1) + 2) + 1 if x != 1 else 0

        child = i
        while child != 1:
            p = parent(child)
            slot = slot_in_parent(child)  # 1..q
            slot_idx = slot + 1           # 槽2..q+1 为子指针
            # 初始化父节点如未存在
            if p not in self._nodes:
                r_p = self._prf(p)
                m0 = [self.grp.init(ZR, 0) for _ in range(self.q + 1)]
                C0 = self.grp.deserialize(commit_vec(self.grp, g_b, h_list, m0, r_p))
                self._nodes[p] = {"r": r_p, "m": m0, "C": C0}
            # 更新父节点对应槽位值 m_ptr
            m_ptr = hash_to_Zp(self.grp, self.grp.serialize(self._nodes[child]["C"]))
            old = self._nodes[p]["m"][slot_idx]
            delta = m_ptr - old
            self._nodes[p]["m"][slot_idx] = m_ptr
            # 更新父节点承诺
            h_slot_b = h_list[slot_idx]
            self._nodes[p]["C"] = self.grp.deserialize(
                update_commit(self.grp, self.grp.serialize(self._nodes[p]["C"]), h_slot_b, delta)
            )
            child = p
        # 更新根
        root_C = self._nodes[1]["C"]
        st.root = RootDigest(value=self.grp.serialize(root_C))
        st.cnt = i
        return AppendReceipt(index=i, root=st.root)

    def query(self, idx: int) -> QueryProof:
        if idx not in self._nodes:
            raise VerifyError("index not found")
        if not self._bootstrap or not self._pk:
            raise GroupError("setup not completed")
        h_list = self._bootstrap["h_list"]
        hij = self._bootstrap["hij"]
        # 叶段
        leaf = self._nodes[idx]
        r_i = leaf["r"]
        # π_leaf = h_1^r * prod h_{1,j}^{m_j} (此时 j>1 应为 0)
        h1_b = h_list[0]
        hij_row = {j: hij[(1, j)] for j in range(2, self.q + 2)}
        pi_leaf_b = open_slot(self.grp, h1_b, hij_row, leaf["m"], r_i)
        payload = {
            "leaf_commit": self.grp.serialize(leaf["C"]),
            "leaf_pi": pi_leaf_b,
            "leaf_h": h1_b,
            "segments": [],
        }
        # 父链段
        def parent(x: int) -> int:
            return (x - 2) // self.q + 1 if x != 1 else 1
        def slot_in_parent(x: int) -> int:
            p = parent(x)
            return x - (self.q * (p - 1) + 2) + 1 if x != 1 else 0
        child = idx
        while child != 1:
            p = parent(child)
            slot = slot_in_parent(child)
            slot_idx = slot + 1
            node = self._nodes[p]
            # π_slot = h_slot^r_p * ∏_{k≠slot} h_{slot,k}^{m_k}
            hslot_b = h_list[slot_idx]
            hij_row_p = {k: hij[(slot_idx, k)] for k in range(1, self.q + 2) if k != slot_idx}
            pi_b = open_slot(self.grp, hslot_b, hij_row_p, node["m"], node["r"])
            payload["segments"].append({
                "node_commit": self.grp.serialize(node["C"]),
                "proof": pi_b,
                "h": hslot_b,
            })
            child = p
        return QueryProof(scheme="cvc", index=idx, payload=ser.pack(payload))

    def verify(self, st: CVCClientState, idx: int, data: bytes, proof: QueryProof) -> bool:
        if proof.scheme != "cvc":
            raise VerifyError("scheme mismatch")
        if not self._pk:
            raise GroupError("setup not completed")
        g_b = self._pk.g
        pld = ser.unpack(proof.payload, dict)
        # 验证叶
        C_leaf_b = pld["leaf_commit"]
        pi_leaf_b = pld["leaf_pi"]
        h_leaf_b = pld["leaf_h"]
        m_data = hash_to_Zp(self.grp, data)
        if not verify_slot(self.grp, g_b, C_leaf_b, h_leaf_b, m_data, pi_leaf_b):
            return False
        child_C_b = C_leaf_b
        # 逐段向上
        for seg in pld["segments"]:
            C_node_b = seg["node_commit"]
            h_b = seg["h"]
            pi_b = seg["proof"]
            m_ptr = hash_to_Zp(self.grp, child_C_b)
            if not verify_slot(self.grp, g_b, C_node_b, h_b, m_ptr, pi_b):
                return False
            child_C_b = C_node_b
        # 顶层是否等于本地 root
        return child_C_b == st.root.value

    def update(self, st: CVCClientState, idx: int, new_data: bytes) -> UpdateReceipt:
        raise GroupError("VDS-CVC update not implemented in this iteration.")

    def _prf(self, i: int):
        from ..common.prf import prf_zr

        return prf_zr(self._sk.prf_key, i, self.grp)  # type: ignore[union-attr]
