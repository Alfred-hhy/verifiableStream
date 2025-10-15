class VerifyError(Exception):
    """Raised when a cryptographic verification fails."""


class DecodeError(Exception):
    """Raised when decoding/serialization fails or is malformed."""


class GroupError(Exception):
    """Raised for pairing/group-related failures or unsupported ops."""


class StorageError(Exception):
    """Raised for storage-layer issues (IO, consistency, etc.)."""

