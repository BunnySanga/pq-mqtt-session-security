"""Local MQTT-style broker/client simulation for Semester 1.

This models publish/subscribe routing without claiming to be a Mosquitto
implementation or a wire-compatible MQTT broker.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .crypto import KEMKeyPair
from .session import BrokerSession, ClientSession, establish_pair


@dataclass
class SimulatedClient:
    client_id: str
    session: ClientSession
    received: list[tuple[str, bytes]] = field(default_factory=list)


class SimulatedBroker:
    def __init__(self, broker_keys: KEMKeyPair) -> None:
        self.broker_keys = broker_keys
        self.clients: dict[str, tuple[SimulatedClient, BrokerSession]] = {}
        self.subscriptions: dict[str, set[str]] = {}

    def connect(self, client_id: str, client_keys: KEMKeyPair) -> SimulatedClient:
        client, broker_session = establish_pair(client_keys, self.broker_keys)
        simulated = SimulatedClient(client_id, client)
        broker_session.accept_resume(client.resume_token())
        self.clients[client_id] = (simulated, broker_session)
        return simulated

    def reconnect(self, client_id: str) -> int:
        client, broker_session = self.clients[client_id]
        return broker_session.accept_resume(client.session.rekey())

    def subscribe(self, client_id: str, topic: str) -> None:
        if client_id not in self.clients:
            raise ValueError("client is not connected")
        self.subscriptions.setdefault(topic, set()).add(client_id)

    def publish(self, client_id: str, topic: str, payload: bytes) -> int:
        client, broker_session = self.clients[client_id]
        envelope, _ = client.session.seal(topic, payload)
        broker_session.open(envelope)
        delivered = 0
        for subscriber_id in self.subscriptions.get(topic, set()):
            subscriber, _ = self.clients[subscriber_id]
            subscriber.received.append((topic, payload))
            delivered += 1
        return delivered