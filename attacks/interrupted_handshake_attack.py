"""Negative test helper for malformed or truncated lifecycle messages."""

from pq_mqtt.crypto import generate_keypair
from pq_mqtt.session import SessionError, establish_pair


def run() -> dict[str, bool]:
    client_keys = generate_keypair()
    broker_keys = generate_keypair()
    client, broker = establish_pair(client_keys, broker_keys)
    token = client.resume_token()
    broker.accept_resume(token)
    try:
        broker.open(b'{"epoch": 1, "counter": 1}')
    except (SessionError, ValueError):
        rejected = True
    else:
        rejected = False
    return {"interrupted_message_rejected": rejected}


if __name__ == "__main__":
    print(run())
