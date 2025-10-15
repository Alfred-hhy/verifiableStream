from __future__ import annotations

"""Simple on-disk msgpack-backed store (skeleton)."""

from ..common.errors import StorageError


class FileStore:
    def __init__(self, base_path: str) -> None:
        self.base_path = base_path

    # Implementations intentionally omitted in scaffold
    def set_root(self, scheme: str, root):  # type: ignore[no-untyped-def]
        raise StorageError("FileStore not implemented in scaffold.")

    def get_root(self, scheme: str):  # type: ignore[no-untyped-def]
        raise StorageError("FileStore not implemented in scaffold.")

    def put_cvc_insert_path(self, leaf, parents):  # type: ignore[no-untyped-def]
        raise StorageError("FileStore not implemented in scaffold.")

    def get_cvc_auth_path(self, idx: int):
        raise StorageError("FileStore not implemented in scaffold.")

    def apply_cvc_updates(self, update_tokens):  # type: ignore[no-untyped-def]
        raise StorageError("FileStore not implemented in scaffold.")

    def save_acc_item(self, idx: int, data: bytes, tag: bytes, sigma: bytes) -> None:
        raise StorageError("FileStore not implemented in scaffold.")

    def get_acc_item(self, idx: int):  # type: ignore[no-untyped-def]
        raise StorageError("FileStore not implemented in scaffold.")

    def set_acc_state(self, acc_value: bytes, cache):  # type: ignore[no-untyped-def]
        raise StorageError("FileStore not implemented in scaffold.")

    def get_acc_state(self):  # type: ignore[no-untyped-def]
        raise StorageError("FileStore not implemented in scaffold.")

