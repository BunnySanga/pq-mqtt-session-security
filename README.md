# Secure Session Lifecycle for PQ-MQTT

Semester 1 software research prototype based on KEM-MQTT/KEMTLS-PDK. It adds epoch-bound session continuity, replay-resistant reconnection, periodic rekeying, and an MQTT-style local broker simulation.

## What is implemented

- ML-KEM-512 initial mutual key establishment.
- Epoch-bound HKDF data and resume keys.
- One-use authenticated reconnect tokens.
- Monotonic epoch and message-counter replay protection.
- AES-GCM authenticated MQTT-style envelopes.
- Local publisher, broker, subscriber, reconnect, and publish flow.
- Replay, tampering, and interrupted-message attacks.
- Tests, CSV benchmarks, plots, and Kaggle notebook.
- Software-only AVR timing estimates marked `SIMULATED`.

## What is not claimed

This is not the authors' handwritten AVR implementation, a physical AVR measurement, a production Mosquitto broker, or a completed formal proof. The Python exchange is protocol-shaped and ML-KEM-backed, but it is not a wire-compatible replacement for KEM-MQTT. Tamarin files should be treated as draft research artifacts until executed and human-reviewed.

## Run on Mac

```bash
cd "/Users/sangabalanarsimha/Desktop/Major Project/pq-mqtt-session-security"
/opt/homebrew/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python experiments/sem1_session_lifecycle/run_end_to_end_demo.py
PYTHONPATH=. .venv/bin/python attacks/replay_transcript_attack.py
PYTHONPATH=. .venv/bin/python attacks/interrupted_handshake_attack.py
PYTHONPATH=. .venv/bin/python experiments/sem1_session_lifecycle/run_replay_benchmark.py --trials 100
PYTHONPATH=. .venv/bin/python experiments/sem1_session_lifecycle/run_session_benchmark.py --trials 100
PYTHONPATH=. .venv/bin/python avr_sim/simulated_timing.py
PYTHONPATH=. .venv/bin/python experiments/sem1_session_lifecycle/analyze_results.py results/raw/sem1_session.csv
```

## Run on Kaggle

Upload the directory to `/kaggle/working/pq-mqtt-session-security`, enable Internet for installation, and run:

```python
%cd /kaggle/working/pq-mqtt-session-security
!pip install -q -r requirements.txt
!pip install -q -r requirements-dev.txt
!PYTHONPATH=. python -m pytest -q
!PYTHONPATH=. python attacks/replay_transcript_attack.py
!PYTHONPATH=. python experiments/sem1_session_lifecycle/run_session_benchmark.py --trials 10
```

## Evidence interpretation

Passing tests show observed behavior in this implementation. They do not prove security. Timing values are environment-specific. The AVR timing script is simulated and must remain labeled that way in the report.
