from __future__ import annotations

from typing import Any, Tuple, List

from ..common.types import (
    ACCPublic,
    QueryProof,
    AppendReceipt,
    UpdateReceipt,
)
from ..common.errors import VerifyError, GroupError, StorageError
from ..common import encoding, sig, ser
from ..common.group import hash_to_Zp
from .accumulator import (
    acc_setup,
    acc_add,
    poly_eval,
    poly_div_linear,
    acc_nonmem_verify,
)
from ..common.types import ACCState, ACCKey

import os
from pydantic import BaseModel
import msgpack


class VDSACC:
    def __init__(self, store: Any, grp: Any):
        self.store = store
        self.grp = grp

    class _ClientState(BaseModel):
        # Signature keys
        ssk: bytes
        vk: bytes
        # Accumulator secret and state (client)
        s: bytes  # ZR
        g1: bytes  # G1
        h: bytes   # G2
        hs: bytes  # G2
        A: bytes   # G1 current accumulator
        powers: List[bytes]  # G1 list
        U: int
        cnt: int

    def setup(self) -> tuple[ACCPublic, bytes]:
        # signature keys
        ssk, vk = sig.keygen()
        # accumulator setup
        key, st = acc_setup(self.grp)
        # We need to generate h as part of setup, but acc_setup packed only hs into key.gs.
        # Embed (h, hs) via the ACCPublic.gs field using msgpack.
        s = self.grp.deserialize(key.s)
        g1 = self.grp.deserialize(key.g)
        # Reconstruct h and hs: we don't have h from key; produce a fresh h consistent with hs by storing both in client state.
        # For acc_setup we already created a random h and hs; we must regenerate them here.
        # Workaround: store h together with hs in ACCPublic.gs via client state.
        # To keep consistent, we re-run generation of h here and recompute hs using the same secret s.
        from charm.toolbox.pairinggroup import G2
        h = self.grp.random(G2)
        hs = h ** s

        # Publish
        pub = ACCPublic(
            g=key.g,  # g1 (G1)
            gs=ser.pack({"h": self.grp.serialize(h), "hs": self.grp.serialize(hs)}),
            vk_sig=vk,
            accumulator=st.value,
        )

        # Initialize server state
        # - accumulator value + powers cache
        self.store.set_acc_state(st.value, st.cache)
        # - polynomial f(X) = 1
        one = self.grp.init(self.grp.ZR, 1) if hasattr(self.grp, "ZR") else None
        # charm exposes ZR via module; use arithmetic via deserialized approach
        from charm.toolbox.pairinggroup import ZR

        one = self.grp.init(ZR, 1)
        self.store.set_acc_poly([self.grp.serialize(one)])

        client_state = {
            "ssk": ssk,
            "vk": vk,
            "s": key.s,
            "g1": key.g,
            "h": self.grp.serialize(h),
            "hs": self.grp.serialize(hs),
            "A": st.value,
            "powers": st.cache,
            "U": 0,
            "cnt": 0,
        }
        return pub, ser.pack(client_state)

    def _load_state(self, st_bytes: bytes):
        return ser.unpack(st_bytes, dict)

    def append(self, st: bytes, data: bytes) -> AppendReceipt:
        state = self._load_state(st)
        # derive index from server-side count to avoid client state sync issues
        try:
            idx = self.store.acc_count() + 1
        except Exception:
            idx = state.get("cnt", 0) + 1
        tag = os.urandom(16)
        m = encoding.encode_item(data, tag, idx)
        sigma = sig.sign(state["ssk"], m)
        # Save item
        self.store.save_acc_item(idx, data, tag, sigma)
        # Root is current accumulator
        root = state["A"]
        state["cnt"] = idx
        return AppendReceipt(index=idx, root=self._root_from_bytes(root))

    def query(self, idx: int) -> QueryProof:
        data, tag, i, sigma = self.store.get_acc_item(idx)
        # Build proof: compute y, v = f(-y), Q, w = g1^{Q(s)} using powers
        f_coeff_bytes = self.store.get_acc_poly()
        from charm.toolbox.pairinggroup import ZR, G1

        coeffs = [self.grp.deserialize(b) for b in f_coeff_bytes]
        y = hash_to_Zp(self.grp, b"ACC_SIG" + sigma)
        v = poly_eval(self.grp, coeffs, -y)
        g_coeffs = coeffs.copy()
        g_coeffs[0] = g_coeffs[0] - v
        Q, rem = poly_div_linear(self.grp, g_coeffs, y)
        # Ensure remainder is zero
        if str(rem) != str(self.grp.init(ZR, 0)):
            raise StorageError("Polynomial division remainder non-zero")
        # Build w from powers
        acc_val, powers_bytes = self.store.get_acc_state()
        powers = [self.grp.deserialize(b) for b in powers_bytes]
        # Ensure enough powers
        if len(Q) > len(powers):
            raise StorageError("Insufficient powers cached on server; need client to supply more.")
        w = self.grp.init(G1, 1)
        for k, qk in enumerate(Q):
            w *= powers[k] ** qk
        proof_payload = ser.pack({
            "sigma": sigma,
            "w": self.grp.serialize(w),
            "u": self.grp.serialize(v),
            "tag": tag,
        })
        return QueryProof(scheme="acc", index=idx, payload=proof_payload)

    def verify(self, pub: ACCPublic, idx: int, data: bytes, proof: QueryProof) -> bool:
        if proof.scheme != "acc":
            raise VerifyError("Scheme mismatch in proof")
        payload = ser.unpack(proof.payload, dict)
        sigma = payload["sigma"]
        w_b = payload["w"]
        v_b = payload["u"]
        tag = payload["tag"]
        # Verify signature over message
        m = encoding.encode_item(data, tag, idx)
        if not sig.verify(pub.vk_sig, m, sigma):
            return False
        # Unpack public params
        param = ser.unpack(pub.gs, dict)
        h = self.grp.deserialize(param["h"])
        hs = self.grp.deserialize(param["hs"])
        y = hash_to_Zp(self.grp, b"ACC_SIG" + sigma)
        v = self.grp.deserialize(v_b)
        # Handle identity witness serialization quirk by normalizing w
        from charm.toolbox.pairinggroup import G1, pair
        id_b = self.grp.serialize(self.grp.init(G1, 1))
        if w_b == id_b:
            w = self.grp.init(G1, 1)
        else:
            w = self.grp.deserialize(w_b)
        A = self.grp.deserialize(pub.accumulator)
        g1 = self.grp.deserialize(pub.g)
        lhs = pair(w, (h ** y) * hs)
        rhs = pair(A * (g1 ** (-v)), h)
        return lhs == rhs

    def update(self, st: bytes, idx: int, new_data: bytes) -> UpdateReceipt:
        state = self._load_state(st)
        # Fetch old item
        data_old, tag_old, i, sigma_old = self.store.get_acc_item(idx)
        # Add x = H_zr(σ_old) to blacklist and update accumulator client-side
        y = hash_to_Zp(self.grp, b"ACC_SIG" + sigma_old)
        tmp_st = ACCState(value=state["A"], upto=state["U"], cache=list(state["powers"]))
        acc_add(self.grp, ACCKey(s=state["s"], g=state["g1"], gs=state["hs"]), tmp_st, y)
        # write back
        state["A"] = tmp_st.value
        state["U"] = tmp_st.upto
        state["powers"] = tmp_st.cache
        # Extend server-side polynomial f(X) = f(X) * (X + y)
        coeff_bytes = self.store.get_acc_poly()
        coeffs = [self.grp.deserialize(b) for b in coeff_bytes]
        from charm.toolbox.pairinggroup import ZR

        new_coeffs = []
        x_poly = [y, self.grp.init(ZR, 1)]  # (X + y) ascending
        # poly_mul
        from .accumulator import poly_mul

        new_coeffs = poly_mul(self.grp, coeffs, x_poly)
        self.store.set_acc_poly([self.grp.serialize(c) for c in new_coeffs])
        # Update server acc state value and powers cache from client
        self.store.set_acc_state(state["A"], state["powers"])
        # Now replace the item with new data, new tag and signature
        idx_new = idx
        tag_new = os.urandom(16)
        m_new = encoding.encode_item(new_data, tag_new, idx_new)
        sigma_new = sig.sign(state["ssk"], m_new)
        self.store.save_acc_item(idx_new, new_data, tag_new, sigma_new)
        # Root becomes new accumulator value
        return UpdateReceipt(index=idx, root=self._root_from_bytes(state["A"]))

    def _root_from_bytes(self, b: bytes):
        from ..common.types import RootDigest

        return RootDigest(value=b)
