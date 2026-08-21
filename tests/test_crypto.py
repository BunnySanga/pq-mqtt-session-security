from pq_mqtt.crypto import decapsulate, encapsulate, generate_keypair, hkdf_extract_expand


def test_ml_kem_round_trip():
    keys = generate_keypair()
    ciphertext, sender_secret = encapsulate(keys.public_key)
    assert sender_secret == decapsulate(keys.secret_key, ciphertext)


def test_hkdf_is_deterministic_and_domain_separated():
    first = hkdf_extract_expand(b"secret", b"one")
    second = hkdf_extract_expand(b"secret", b"two")
    assert first == hkdf_extract_expand(b"secret", b"one")
    assert first != second
