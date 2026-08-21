"""Epoch-bound session key derivation for the research prototype."""

from __future__ import annotations

from ..crypto import hkdf_extract_expand


def derive_epoch_key(root_secret: bytes, epoch: int, purpose: bytes = b"mqtt-data") -> bytes:
    if epoch < 0:
        raise ValueError("epoch must be non-negative")
    if not purpose:
        raise ValueError("purpose must not be empty")
    return hkdf_extract_expand(
        root_secret,
        b"pq-mqtt/epoch/v1/" + epoch.to_bytes(8, "big") + b"/" + purpose,
    )


def derive_resume_key(root_secret: bytes, epoch: int) -> bytes:
    return derive_epoch_key(root_secret, epoch, b"resume-auth")
