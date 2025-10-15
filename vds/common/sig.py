from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


def keygen() -> tuple[bytes, bytes]:
    sk = Ed25519PrivateKey.generate()
    vk = sk.public_key()
    return (
        sk.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        vk.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ),
    )


def sign(sk_bytes: bytes, msg: bytes) -> bytes:
    sk = Ed25519PrivateKey.from_private_bytes(sk_bytes)
    return sk.sign(msg)


def verify(vk_bytes: bytes, msg: bytes, sig: bytes) -> bool:
    try:
        vk = Ed25519PublicKey.from_public_bytes(vk_bytes)
        vk.verify(sig, msg)
        return True
    except Exception:
        return False

