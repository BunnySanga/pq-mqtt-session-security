import pytest

from pq_mqtt.crypto import generate_keypair
from pq_mqtt.mqtt_sim import SimulatedBroker
from pq_mqtt.session import establish_pair
from pq_mqtt.session.replay_guard import ReplayError


def established():
    client_keys = generate_keypair()
    broker_keys = generate_keypair()
    return establish_pair(client_keys, broker_keys)


def test_initial_resume_and_encrypted_message():
    client, broker = established()
    broker.accept_resume(client.resume_token())
    envelope, _ = client.seal("temperature", b"21.5 C")
    assert broker.open(envelope) == ("temperature", b"21.5 C")


def test_replayed_resume_token_is_rejected():
    client, broker = established()
    token = client.resume_token()
    broker.accept_resume(token)
    with pytest.raises(ReplayError):
        broker.accept_resume(token)


def test_epoch_transition_requires_new_epoch():
    client, broker = established()
    broker.accept_resume(client.resume_token())
    client.advance_epoch()
    broker.accept_resume(client.resume_token())
    envelope, _ = client.seal("status", b"ok")
    assert broker.open(envelope) == ("status", b"ok")


def test_replayed_message_counter_is_rejected():
    client, broker = established()
    broker.accept_resume(client.resume_token())
    envelope, _ = client.seal("status", b"ok")
    assert broker.open(envelope) == ("status", b"ok")
    with pytest.raises(ReplayError):
        broker.open(envelope)


def test_tampered_message_is_rejected():
    client, broker = established()
    broker.accept_resume(client.resume_token())
    envelope, _ = client.seal("status", b"ok")
    tampered = envelope.replace(b"status", b"attacked")
    with pytest.raises(ValueError):
        broker.open(tampered)
    assert broker.open(envelope) == ("status", b"ok")


def test_failed_message_authentication_does_not_consume_counter():
    client, broker = established()
    broker.accept_resume(client.resume_token())
    envelope, _ = client.seal("status", b"ok")
    tampered = envelope.replace(b"status", b"attacked")
    with pytest.raises(ValueError):
        broker.open(tampered)
    assert broker.open(envelope) == ("status", b"ok")


def test_periodic_rekey_and_mqtt_publish_flow():
    broker = SimulatedBroker(generate_keypair())
    publisher_keys = generate_keypair()
    subscriber_keys = generate_keypair()
    publisher = broker.connect("publisher", publisher_keys)
    subscriber = broker.connect("subscriber", subscriber_keys)
    broker.subscribe("subscriber", "temperature")
    assert broker.publish("publisher", "temperature", b"21.5 C") == 1
    assert broker.reconnect("publisher") == 1
    assert broker.publish("publisher", "temperature", b"22.0 C") == 1
    assert subscriber.received == [("temperature", b"21.5 C"), ("temperature", b"22.0 C")]
    assert publisher.session.epoch == 1
