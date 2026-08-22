"""Epoch-bound session key derivation for the research prototype."""

from __future__ import annotations

import hashlib
import hmac

from ..crypto import hkdf_extract_expand


def ratchet_forward(epoch_secret: bytes, next_epoch: int) -> bytes:
    """Advance a one-way epoch secret; the caller must discard the old value."""
    if not isinstance(epoch_secret, bytes) or not epoch_secret:
        raise ValueError("epoch_secret must be non-empty bytes")
    if next_epoch < 0:
        raise ValueError("next_epoch must be non-negative")
    return hmac.new(
        epoch_secret,
        b"pq-mqtt/ratchet/v1/" + next_epoch.to_bytes(8, "big"),
        hashlib.sha256,
    ).digest()


def derive_epoch_key(epoch_secret: bytes, epoch: int, purpose: bytes = b"mqtt-data") -> bytes:
    if epoch < 0:
        raise ValueError("epoch must be non-negative")
    if not purpose:
        raise ValueError("purpose must not be empty")
    return hkdf_extract_expand(
        epoch_secret,
        b"pq-mqtt/epoch/v1/" + epoch.to_bytes(8, "big") + b"/" + purpose,
    )


def derive_resume_key(epoch_secret: bytes, epoch: int) -> bytes:
    return derive_epoch_key(epoch_secret, epoch, b"resume-auth")
