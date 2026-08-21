"""Measure rejection of replayed resume tokens."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from pq_mqtt.crypto import generate_keypair
from pq_mqtt.session import establish_pair
from pq_mqtt.session.replay_guard import ReplayError


def run(trials: int) -> list[dict[str, object]]:
    rows = []
    for trial in range(trials):
        client_keys = generate_keypair()
        broker_keys = generate_keypair()
        client, broker = establish_pair(client_keys, broker_keys)
        token = client.resume_token()
        broker.accept_resume(token)
        started = time.perf_counter_ns()
        try:
            broker.accept_resume(token)
        except ReplayError:
            rejected = True
        else:
            rejected = False
        rows.append({"trial": trial, "replay_rejected": rejected, "check_ns": time.perf_counter_ns() - started})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("results/raw/sem1_replay.csv"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["trial", "replay_rejected", "check_ns"])
        writer.writeheader()
        writer.writerows(run(args.trials))
    print(f"wrote {args.trials} trials to {args.output}")


if __name__ == "__main__":
    main()
