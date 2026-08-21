"""Initial mutual ML-KEM exchange used by the prototype."""

from __future__ import annotations

from dataclasses import dataclass
import os

from ..crypto import KEMKeyPair, decapsulate, encapsulate, generate_keypair, hkdf_extract_expand


@dataclass(frozen=True)
class HandshakeTranscript:
	client_ciphertext: bytes
	broker_ciphertext: bytes
	client_secret: bytes
	broker_secret: bytes
	transcript_nonce: bytes


def create_static_identity() -> KEMKeyPair:
	return generate_keypair()


def perform_handshake(client_keys: KEMKeyPair, broker_keys: KEMKeyPair) -> HandshakeTranscript:
	client_ciphertext, client_secret = encapsulate(broker_keys.public_key)
	broker_ciphertext, broker_secret = encapsulate(client_keys.public_key)
	return HandshakeTranscript(
		client_ciphertext=client_ciphertext,
		broker_ciphertext=broker_ciphertext,
		client_secret=client_secret,
		broker_secret=broker_secret,
		transcript_nonce=os.urandom(16),
	)


def complete_client_handshake(
	client_keys: KEMKeyPair,
	broker_keys: KEMKeyPair,
	transcript: HandshakeTranscript,
) -> bytes:
	broker_secret = decapsulate(client_keys.secret_key, transcript.broker_ciphertext)
	if broker_secret != transcript.broker_secret:
		raise ValueError("broker-side handshake secret mismatch")
	return hkdf_extract_expand(
		transcript.client_secret + broker_secret + transcript.transcript_nonce,
		b"pq-mqtt/initial-session/v1",
	)


def complete_broker_handshake(
	client_keys: KEMKeyPair,
	broker_keys: KEMKeyPair,
	transcript: HandshakeTranscript,
) -> bytes:
	client_secret = decapsulate(broker_keys.secret_key, transcript.client_ciphertext)
	if client_secret != transcript.client_secret:
		raise ValueError("client-side handshake secret mismatch")
	return hkdf_extract_expand(
		client_secret + transcript.broker_secret + transcript.transcript_nonce,
		b"pq-mqtt/initial-session/v1",
	)
