"""Cryptographic primitives used by the runnable prototype.

The project requires ML-KEM-512 from pqcrypto. There is deliberately no
classical fallback: a missing PQ backend is an environment error, not a
successful experiment.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

try:
    from pqcrypto.kem import ml_kem_512
except ImportError as exc:  # pragma: no cover - exercised by environment setup
    ml_kem_512 = None
    _IMPORT_ERROR = exc


def require_pq_backend() -> None:
    if ml_kem_512 is None:
        raise RuntimeError(
            "ML-KEM backend unavailable. Run `pip install -r requirements.txt`; "
            "the prototype refuses a classical fallback."
        ) from _IMPORT_ERROR


def hkdf_extract_expand(ikm: bytes, info: bytes, length: int = 32) -> bytes:
    """Small dependency-free HKDF-SHA256 implementation."""
    salt = b"pq-mqtt-prototype-hkdf-v1"
    pseudorandom_key = hmac.new(salt, ikm, hashlib.sha256).digest()
    output = b""
    previous = b""
    for counter in range(1, (length + 31) // 32 + 1):
        previous = hmac.new(
            pseudorandom_key, previous + info + bytes([counter]), hashlib.sha256
        ).digest()
        output += previous
    return output[:length]


def mac(key: bytes, message: bytes) -> bytes:
    return hmac.new(key, message, hashlib.sha256).digest()


@dataclass(frozen=True)
class KEMKeyPair:
    public_key: bytes
    secret_key: bytes


def generate_keypair() -> KEMKeyPair:
    require_pq_backend()
    public_key, secret_key = ml_kem_512.generate_keypair()
    return KEMKeyPair(public_key=public_key, secret_key=secret_key)


def encapsulate(public_key: bytes) -> tuple[bytes, bytes]:
    require_pq_backend()
    ciphertext, shared_secret = ml_kem_512.encrypt(public_key)
    return ciphertext, shared_secret


def decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    require_pq_backend()
    return ml_kem_512.decrypt(secret_key, ciphertext)
