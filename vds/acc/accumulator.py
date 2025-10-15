from __future__ import annotations

"""Bilinear accumulator primitives (Nguyen-style) helpers.

We use asymmetric pairings. Conventions:
- g1 ∈ G1 is the base for accumulator and witnesses
- h ∈ G2 is the base for public parameters, with secret s ∈ ZR and hs = h^s
- Accumulator value A ∈ G1

Public verification equation for non-membership of y ∈ ZR with witness (w ∈ G1, v ∈ ZR):
    e(w, h^y · hs) == e(A · g1^(-v), h)
"""

from typing import Any, List, Tuple

from charm.toolbox.pairinggroup import G1, G2, ZR, pair

from ..common.types import ACCKey, ACCState
from ..common.errors import StorageError


def _serialize(grp: Any, elem: Any) -> bytes:
    return grp.serialize(elem)


def _deserialize(grp: Any, data: bytes) -> Any:
    return grp.deserialize(data)


def acc_setup(grp: Any) -> tuple[ACCKey, ACCState]:
    """Generate accumulator secret/public and initial state.

    - Secret trapdoor s ∈ ZR
    - Generators: g1 ∈ G1, h ∈ G2, and hs = h^s
    - Accumulator A starts as g1 (empty set)
    - Cache powers for Q(s): powers[k] = g1^{s^k}, initially [g1, g1^s]
    """
    s = grp.random(ZR)
    g1 = grp.random(G1)
    h = grp.random(G2)
    hs = h ** s
    A = g1  # empty product
    # powers: g1^{s^0}, g1^{s^1}
    p0 = g1
    p1 = g1 ** s
    key = ACCKey(s=_serialize(grp, s), g=_serialize(grp, g1), gs=_serialize(grp, hs))
    st = ACCState(value=_serialize(grp, A), upto=0, cache=[_serialize(grp, p0), _serialize(grp, p1)])
    # We do not expose h in ACCKey; pack (h, hs) together into gs when publishing.
    # Higher layers (VDSACC) will carry h via packing into ACCPublic.gs bytes.
    return key, st


def next_power(grp: Any, last_power_bytes: bytes, s_bytes: bytes) -> bytes:
    """Compute next power g1^{s^{k+1}} from last = g1^{s^k}."""
    last = _deserialize(grp, last_power_bytes)
    s = _deserialize(grp, s_bytes)
    nxt = last ** s
    return _serialize(grp, nxt)


def acc_add(grp: Any, key: ACCKey, st: ACCState, x_zr: Any) -> None:
    """Add x to blacklist set E on the accumulator value and extend powers.

    Mutates ACCState in-place:
    - A <- A^{(x + s)}
    - upto += 1
    - cache append next power g1^{s^{upto}}
    """
    s = _deserialize(grp, key.s)
    A = _deserialize(grp, st.value)
    # exponent (x + s)
    exp = x_zr + s
    A_new = A ** exp
    st.value = _serialize(grp, A_new)
    st.upto += 1
    # extend powers: from the current last element
    last = st.cache[-1]
    st.cache.append(next_power(grp, last, key.s))


def acc_nonmem_verify(grp: Any, g1_bytes: bytes, h_bytes: bytes, hs_bytes: bytes, acc_bytes: bytes, y_zr: Any, w_bytes: bytes, v_zr: Any) -> bool:
    """Verify non-membership proof.

    Check: e(w, h^y · hs) == e(A · g1^{-v}, h)
    """
    try:
        g1 = _deserialize(grp, g1_bytes)
        h = _deserialize(grp, h_bytes)
        hs = _deserialize(grp, hs_bytes)
        A = _deserialize(grp, acc_bytes)
        w = _deserialize(grp, w_bytes)
        lhs = pair(w, (h ** y_zr) * hs)
        rhs = pair(A * (g1 ** (-v_zr)), h)
        return lhs == rhs
    except Exception:
        return False


# --- Product tree placeholder (for performance optimization) ---
class PolyTree:
    """A simple product tree for f(X)=∏(X+x_i).

    This placeholder stores coefficients at the root and leaves for compatibility.
    Future optimization: compute f(-y) and Q(X) in O(U log U) with less overhead.
    """

    def __init__(self, grp: Any):
        self.grp = grp
        self.xs: List[Any] = []  # elements in ZR
        self.coeffs: List[Any] = [grp.init(ZR, 1)]  # ascending coeffs of f(X)

    def add(self, x: Any) -> None:
        from .accumulator import poly_mul

        X_plus_x = [x, self.grp.init(ZR, 1)]
        self.coeffs = poly_mul(self.grp, self.coeffs, X_plus_x)
        self.xs.append(x)

    def eval_and_quot(self, y: Any) -> tuple[Any, List[Any]]:
        v = poly_eval(self.grp, self.coeffs, -y)
        g_coeffs = self.coeffs.copy()
        g_coeffs[0] = g_coeffs[0] - v
        Q, rem = poly_div_linear(self.grp, g_coeffs, y)
        if str(rem) != str(self.grp.init(ZR, 0)):
            raise StorageError("poly division remainder non-zero")
        return v, Q


# Polynomial helpers over ZR
def poly_mul(grp: Any, a: List[Any], b: List[Any]) -> List[Any]:
    res = [grp.init(ZR, 0) for _ in range(len(a) + len(b) - 1)]
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            res[i + j] = res[i + j] + (ai * bj)
    return res


def poly_eval(grp: Any, coeffs: List[Any], x: Any) -> Any:
    # Horner with ascending coeffs: coeffs[k] * x^k
    acc = grp.init(ZR, 0)
    pow_x = grp.init(ZR, 1)
    for c in coeffs:
        acc = acc + c * pow_x
        pow_x = pow_x * x
    return acc


def poly_div_linear_desc(grp: Any, coeff_desc: List[Any], a: Any) -> Tuple[List[Any], Any]:
    """Divide polynomial (descending coeffs) by (X - a).

    Return (quotient_desc, remainder).
    """
    n = len(coeff_desc) - 1
    if n < 0:
        return [], grp.init(ZR, 0)
    if n == 0:
        # Constant polynomial divided by linear factor: quotient 0, remainder const
        return [], coeff_desc[0]
    q = [None] * n  # type: ignore[list-item]
    q[0] = coeff_desc[0]
    for i in range(1, n):
        q[i] = coeff_desc[i] + a * q[i - 1]
    r = coeff_desc[-1] + a * q[-1]
    return q, r


def poly_div_linear(grp: Any, coeffs: List[Any], y: Any) -> Tuple[List[Any], Any]:
    """Divide g(X) by (X + y) i.e., (X - (-y)). coeffs are ascending.

    Returns (Q_coeffs ascending, remainder).
    """
    if not coeffs:
        return [], grp.init(ZR, 0)
    # Convert to descending for synthetic division
    desc = list(reversed(coeffs))
    a = -y
    q_desc, rem = poly_div_linear_desc(grp, desc, a)
    q_asc = list(reversed(q_desc)) if q_desc else []
    return q_asc, rem
