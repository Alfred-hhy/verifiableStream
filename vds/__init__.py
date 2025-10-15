"""
Verifiable Data Streaming (VDS) package skeleton.

This package provides two interchangeable schemes:
- VDS-CVC: Tree + Chameleon Vector Commitment (skeleton)
- VDS-ACC: Signatures + Bilinear Accumulator (skeleton)

Modules are scaffolded with clear interfaces and exceptions. Concrete
pairing-based crypto is intentionally left unimplemented pending
environment support for charm-crypto.
"""

from .common import errors, types

__version__ = "0.1.0"

__all__ = [
    "errors",
    "types",
]

