"""Benchmark initial establishment and epoch resume in the prototype."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from pq_mqtt.crypto import generate_keypair
from pq_mqtt.session import establish_pair


def run(trials: int) -> list[dict[str, object]]:
    rows = []
    for trial in range(trials):
        client_keys = generate_keypair()
        broker_keys = generate_keypair()
        started = time.perf_counter_ns()
        client, broker = establish_pair(client_keys, broker_keys)
        handshake_ns = time.perf_counter_ns() - started
        started = time.perf_counter_ns()
        broker.accept_resume(client.resume_token())
        resume_ns = time.perf_counter_ns() - started
        rows.append({"trial": trial, "handshake_ns": handshake_ns, "resume_ns": resume_ns})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("results/raw/sem1_session.csv"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["trial", "handshake_ns", "resume_ns"])
        writer.writeheader()
        writer.writerows(run(args.trials))
    print(f"wrote {args.trials} trials to {args.output}")


if __name__ == "__main__":
    main()
