"""Executable replay attack against the Semester 1 session controls."""

from pq_mqtt.crypto import generate_keypair
from pq_mqtt.session import establish_pair
from pq_mqtt.session.replay_guard import ReplayError


def run() -> dict[str, bool]:
    client_keys = generate_keypair()
    broker_keys = generate_keypair()
    client, broker = establish_pair(client_keys, broker_keys)
    first_token = client.resume_token()
    broker.accept_resume(first_token)
    client.advance_epoch()
    second_token = client.resume_token()
    broker.accept_resume(second_token)
    try:
        broker.accept_resume(second_token)
    except ReplayError:
        replay_rejected = True
    else:
        replay_rejected = False
    return {"replay_rejected": replay_rejected}


if __name__ == "__main__":
    print(run())
