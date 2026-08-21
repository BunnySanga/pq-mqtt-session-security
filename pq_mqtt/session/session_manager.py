"""Session lifecycle state machine for Semester 1."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import hmac
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..crypto import KEMKeyPair, mac
from .epoch_derivation import derive_epoch_key, derive_resume_key
from .handshake import complete_broker_handshake, complete_client_handshake, perform_handshake
from .replay_guard import ReplayError, ReplayGuard


class SessionError(ValueError):
    """Raised for invalid session state or authentication data."""


UTF8_TOPIC_LIMIT = 256


def _encode(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _token(epoch: int, nonce: bytes, authenticator: bytes) -> bytes:
    return _encode({
        "epoch": epoch,
        "nonce": base64.b64encode(nonce).decode(),
        "auth": base64.b64encode(authenticator).decode(),
    })


def _decode_token(token: bytes) -> tuple[int, bytes, bytes]:
    try:
        value = json.loads(token)
        if not isinstance(value, dict):
            raise TypeError("token must be an object")
        return (
            int(value["epoch"]),
            base64.b64decode(value["nonce"], validate=True),
            base64.b64decode(value["auth"], validate=True),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SessionError("malformed resume token") from exc


@dataclass
class ClientSession:
    session_secret: bytes
    epoch: int = 0
    counter: int = 0

    def resume_token(self) -> bytes:
        nonce = os.urandom(16)
        body = self.epoch.to_bytes(8, "big") + nonce
        return _token(self.epoch, nonce, mac(derive_resume_key(self.session_secret, self.epoch), body))

    def advance_epoch(self) -> None:
        self.epoch += 1
        self.counter = 0

    def rekey(self) -> bytes:
        """Advance to a fresh epoch and return its one-use resume token."""
        self.advance_epoch()
        return self.resume_token()

    def seal(self, topic: str, payload: bytes) -> tuple[bytes, bytes]:
        if not isinstance(topic, str) or not topic or len(topic.encode()) > UTF8_TOPIC_LIMIT:
            raise SessionError("topic must be a non-empty string within the size limit")
        if not isinstance(payload, bytes):
            raise SessionError("topic and byte payload are required")
        self.counter += 1
        nonce = os.urandom(12)
        aad = _encode({"epoch": self.epoch, "counter": self.counter, "topic": topic})
        ciphertext = AESGCM(derive_epoch_key(self.session_secret, self.epoch)).encrypt(nonce, payload, aad)
        envelope = _encode({
            "epoch": self.epoch,
            "counter": self.counter,
            "topic": topic,
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
        })
        return envelope, aad


@dataclass
class BrokerSession:
    session_secret: bytes
    guard: ReplayGuard

    def accept_resume(self, token: bytes) -> int:
        epoch, nonce, authenticator = _decode_token(token)
        if epoch <= self.guard.highest_epoch:
            raise ReplayError("resume token epoch was already used")
        expected = mac(derive_resume_key(self.session_secret, epoch), epoch.to_bytes(8, "big") + nonce)
        if not hmac.compare_digest(authenticator, expected):
            raise SessionError("resume token authentication failed")
        self.guard.accept_epoch(epoch)
        return epoch

    @property
    def epoch(self) -> int:
        return self.guard.highest_epoch

    def open(self, envelope: bytes) -> tuple[str, bytes]:
        try:
            value = json.loads(envelope)
            if not isinstance(value, dict):
                raise TypeError("message must be an object")
            epoch = int(value["epoch"])
            counter = int(value["counter"])
            topic = str(value["topic"])
            nonce = base64.b64decode(value["nonce"], validate=True)
            ciphertext = base64.b64decode(value["ciphertext"], validate=True)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SessionError("malformed message envelope") from exc
        if len(nonce) != 12 or not topic or len(topic.encode()) > UTF8_TOPIC_LIMIT:
            raise SessionError("invalid message envelope fields")
        self.guard.validate_message(epoch, counter)
        aad = _encode({"epoch": epoch, "counter": counter, "topic": topic})
        try:
            payload = AESGCM(derive_epoch_key(self.session_secret, epoch)).decrypt(nonce, ciphertext, aad)
        except Exception as exc:
            raise SessionError("message authentication failed") from exc
        self.guard.accept_message(epoch, counter)
        return topic, payload


def establish_pair(client_keys: KEMKeyPair, broker_keys: KEMKeyPair) -> tuple[ClientSession, BrokerSession]:
    """Establish both endpoints from one handshake transcript."""
    transcript = perform_handshake(client_keys, broker_keys)
    client_secret = complete_client_handshake(client_keys, broker_keys, transcript)
    broker_secret = complete_broker_handshake(client_keys, broker_keys, transcript)
    if client_secret != broker_secret:
        raise SessionError("initial handshake did not derive a common secret")
    return ClientSession(client_secret), BrokerSession(broker_secret, ReplayGuard())
