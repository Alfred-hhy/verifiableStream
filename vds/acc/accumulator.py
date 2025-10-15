from __future__ import annotations

"""Bilinear accumulator primitives skeleton.

Interfaces follow Nguyen accumulator with non-membership proofs.
"""

from typing import Any, Tuple, List

from ..common.types import ACCKey, ACCState
from ..common.errors import GroupError


def acc_setup(grp: Any) -> tuple[ACCKey, ACCState]:
    raise GroupError("Accumulator setup not implemented (pairing required).")


def acc_add(grp: Any, key: ACCKey, st: ACCState, x: int) -> None:
    raise GroupError("Accumulator add not implemented.")


def acc_nonmem_prove(grp: Any, pub: tuple, x: int) -> tuple[bytes, bytes]:
    raise GroupError("Accumulator non-membership proof not implemented.")


def acc_nonmem_verify(grp: Any, pub: tuple, x: int, w: bytes, u: bytes) -> bool:
    raise GroupError("Accumulator verify not implemented.")

