"""Run the complete local Semester 1 connect/publish/reconnect flow."""

from pq_mqtt.crypto import generate_keypair
from pq_mqtt.mqtt_sim import SimulatedBroker


def main() -> None:
    broker = SimulatedBroker(generate_keypair())
    publisher = broker.connect("publisher", generate_keypair())
    subscriber = broker.connect("subscriber", generate_keypair())
    broker.subscribe("subscriber", "temperature")
    broker.publish("publisher", "temperature", b"21.5 C")
    old_epoch = publisher.session.epoch
    new_epoch = broker.reconnect("publisher")
    broker.publish("publisher", "temperature", b"22.0 C")
    print({
        "initial_epoch": old_epoch,
        "reconnected_epoch": new_epoch,
        "received": subscriber.received,
    })


if __name__ == "__main__":
    main()
