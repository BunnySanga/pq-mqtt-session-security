# Secure Session Lifecycle for Post-Quantum MQTT
## Semester 1 Project Report

**Project:** Secure Session Lifecycle for KEMTLS-PDK-Based PQ-MQTT  
**Execution environment:** macOS, Apple Silicon, Homebrew Python 3.14, project-local `.venv`  
**Evaluation:** 100 trials  
**Status:** Completed software-prototype evaluation

## Abstract

Post-quantum cryptography creates practical deployment challenges for constrained IoT communication. The Kim-Seo KEM-MQTT work demonstrates ML-KEM-based MQTT key establishment for constrained AVR sensor nodes, but its protocol discussion focuses primarily on the initial handshake and leaves session lifecycle analysis for future work. This project implements a software prototype for a secure session lifecycle around an ML-KEM-backed PQ-MQTT design.

The prototype establishes a shared post-quantum session secret, derives epoch-specific keys, authenticates reconnect tokens, protects MQTT-style messages with AES-GCM, and rejects replayed or modified messages. A local broker, publisher, and subscriber simulation demonstrates connect, publish, reconnect, periodic rekey, and publish behavior. Across 100 local software trials, epoch resumption had a median time of 13,083.5 ns compared with 92,437.5 ns for a fresh initial handshake, giving an observed median speedup of approximately 7.07x.

These results validate the implemented software mechanism. They are not measurements from AVR hardware, a production MQTT broker, or a completed formal proof.

## 1. Introduction

MQTT is widely used in IoT systems because of its lightweight publish-subscribe model. Conventional public-key mechanisms used to establish secure sessions are vulnerable to future quantum attacks. ML-KEM provides a standardized post-quantum key-encapsulation mechanism, but a complete deployment must consider what happens after the initial connection.

Repeatedly performing a full post-quantum handshake after every network interruption can increase computation and latency. This project investigates whether an authenticated, epoch-based session lifecycle can provide secure reconnection at lower software cost while preserving freshness and replay protection.

## 2. Aim and Objectives

### 2.1 Aim

To design, implement, and empirically evaluate a replay-resistant session lifecycle for an ML-KEM-backed PQ-MQTT software prototype.

### 2.2 Objectives

1. Establish a shared session secret using ML-KEM-512.
2. Derive separate keys for each session epoch.
3. Authenticate reconnect and rekey tokens.
4. Reject stale or replayed epochs.
5. Protect MQTT-style messages using authenticated encryption.
6. Reject replayed, modified, malformed, and interrupted messages.
7. Demonstrate an end-to-end publisher, broker, subscriber, reconnect, and rekey workflow.
8. Compare fresh-handshake cost with epoch-resumption cost.
9. Produce reproducible source code, tests, benchmark CSV files, and analysis output.

## 3. Relation to the Base Paper

The project is based on the KEM-MQTT and KEMTLS-PDK ideas described by Kim and Seo in *An Optimized Instantiation of Post-Quantum MQTT Protocol on 8-bit AVR Sensor Nodes* (ASIA CCS 2025).

The implementation does not claim to reproduce the paper in full. In particular, it does not reproduce the authors' handwritten AVR assembly, Signed LUT Reduction implementation, ATmega4808 measurements, physical energy measurements, or complete KEM-MQTT wire protocol. Instead, it implements and evaluates a software session-lifecycle extension motivated by the paper's initial KEM-based design.

## 4. System Design

### 4.1 Components

- **Client/publisher:** owns a static ML-KEM key pair and creates encrypted MQTT-style messages.
- **Broker:** validates reconnect tokens, enforces epoch freshness, decrypts authenticated messages, and routes valid messages.
- **Subscriber:** receives messages routed by the local broker simulation.
- **Session manager:** maintains epoch and message-counter state.
- **Replay guard:** prevents duplicate epochs and duplicate or reordered message counters.
- **Benchmark runner:** measures initial establishment and epoch resumption.

### 4.2 Initial Session Establishment

The client and broker use one shared handshake transcript. Two ML-KEM encapsulations contribute shared secrets: one addressed to the broker and one addressed to the client. Both endpoints combine the contributions and a transcript nonce through HKDF-SHA256 to derive the same root session secret.

### 4.3 Epoch Key Derivation

For epoch $e$, the prototype derives a data key using a domain-separated HKDF label:

$$
K_{data,e} = HKDF(root\_secret,
  \text{"pq-mqtt/epoch/v1/"} \parallel uint64(e) \parallel \text{"mqtt-data"})
$$

A separate resume-authentication key is derived with a different purpose label:

$$
K_{resume,e} = HKDF(root\_secret,
  \text{"pq-mqtt/epoch/v1/"} \parallel uint64(e) \parallel \text{"resume-auth"})
$$

The client advances to a new epoch for reconnection or periodic rekeying. The broker accepts only an epoch greater than its highest accepted epoch.

### 4.4 Message Protection

Each message contains:

- epoch number,
- strictly increasing message counter,
- topic,
- random AES-GCM nonce,
- ciphertext and authentication tag.

Epoch, counter, and topic are authenticated as associated data. The broker validates replay state, decrypts the ciphertext, and only then commits the counter state. This transactional order prevents an unauthenticated forged message from consuming a valid counter.

## 5. Threat Model

The baseline network attacker can observe, copy, delay, reorder, modify, and replay session tokens and MQTT-style message envelopes. The attacker cannot directly read endpoint memory in the baseline experiment.

The evaluated security goals are:

1. Replayed reconnect tokens are rejected.
2. Stale epochs are rejected.
3. Replayed or reordered message counters are rejected.
4. Modified topics, counters, nonces, or ciphertexts fail authentication.
5. Malformed or incomplete messages are rejected.
6. Both endpoints derive the same initial session secret.
7. Different epochs use domain-separated keys.

Forward secrecy under long-term-key compromise is not claimed by this prototype. A formal model and security proof are required before making that claim.

## 6. Implementation

The main implementation files are:

- `pq_mqtt/crypto.py`: ML-KEM-512, HKDF-SHA256, and HMAC utilities.
- `pq_mqtt/session/handshake.py`: shared-transcript initial exchange.
- `pq_mqtt/session/epoch_derivation.py`: epoch-specific key derivation.
- `pq_mqtt/session/replay_guard.py`: monotonic epoch and counter validation.
- `pq_mqtt/session/session_manager.py`: client and broker session state.
- `pq_mqtt/mqtt_sim.py`: local MQTT-style broker and client simulation.
- `attacks/`: replay and interrupted-message demonstrations.
- `experiments/sem1_session_lifecycle/`: end-to-end demo, benchmark runners, and analysis.
- `tests/`: cryptographic, lifecycle, attack, and integration tests.
- `avr_sim/`: clearly labeled software-only timing estimates.

Runtime dependencies are limited to `pqcrypto` and `cryptography`. Pytest is isolated in `requirements-dev.txt`; pandas and matplotlib are not required by the project.

## 7. Experimental Methodology

The benchmark compares two operations:

1. **Initial handshake:** generate ML-KEM identities, perform the two-sided exchange, and derive the root session secret.
2. **Epoch resume:** create and authenticate a new epoch token after the session exists.

The experiment was run for 100 trials in the project-local Python virtual environment. Measurements use `time.perf_counter_ns()`. The benchmark records each trial in:

- `results/raw/sem1_replay.csv`
- `results/raw/sem1_session.csv`

The first trial may include interpreter or cryptographic-library warm-up. Mean and median are therefore reported together.

## 8. Results

### 8.1 Functional Validation

| Validation | Result |
|---|---:|
| Automated tests | 11 passed |
| End-to-end connect/publish/reconnect flow | Passed |
| Replay-token attack | Rejected |
| Interrupted-message attack | Rejected |
| Benchmark trials | 100 |
| Simulated timing model | Completed |

The end-to-end demo produced:

```text
initial_epoch: 0
reconnected_epoch: 1
received: [('temperature', b'21.5 C'), ('temperature', b'22.0 C')]
```

### 8.2 Performance Results

| Operation | Mean (ns) | Median (ns) | Standard deviation (ns) | Minimum (ns) | Maximum (ns) |
|---|---:|---:|---:|---:|---:|
| Initial handshake | 103,002.46 | 92,437.50 | 30,415.63 | 83,625.00 | 224,083.00 |
| Epoch resume | 16,195.85 | 13,083.50 | 9,172.35 | 11,958.00 | 64,958.00 |

The observed speedups are:

$$
\text{Mean speedup} = \frac{103002.46}{16195.85} \approx 6.36\times
$$

$$
\text{Median speedup} = \frac{92437.50}{13083.50} \approx 7.07\times
$$

Epoch resumption was faster than a fresh initial handshake in all measured trials. The result supports the project hypothesis that session continuity can reduce reconnection computation in the software prototype.

### 8.3 Simulated AVR Timing

The software model reported:

```text
full_kem_mqtt_handshake_simulated: 4.319320s
 epoch_resume_simulated: 0.010855s
```

These are model outputs based on assumed cycle counts. They are not hardware measurements and must not be compared directly with the paper's ATmega4808 results as if they were experimentally equivalent.

## 9. Security Evaluation

The test suite verifies:

- ML-KEM encapsulation and decapsulation agreement.
- HKDF determinism and domain separation.
- Initial encrypted message delivery.
- Replayed resume-token rejection.
- Epoch transition behavior.
- Replayed message-counter rejection.
- Tampered-message rejection.
- Preservation of replay state after failed authentication.
- Interrupted-message rejection.
- End-to-end periodic rekey and publish/subscribe behavior.

A passing test demonstrates observed implementation behavior. It is not a formal proof of security.

## 10. Discussion

The implementation meets the software Semester 1 objectives. It provides a working ML-KEM-backed session lifecycle, authenticated epoch resumption, replay protection, encrypted application messages, an end-to-end MQTT-style flow, and repeatable measurements.

The performance result is meaningful within the controlled Python environment because both operations were measured using the same interpreter, machine, cryptographic backend, and timing method. It shows the relative cost of the implemented operations, not a universal network or hardware latency guarantee.

The lower resume cost is expected because epoch resumption uses symmetric derivation and authentication after the initial session, while the initial handshake performs ML-KEM operations and creates the root session state.

## 11. Limitations

1. The broker is a local simulation, not a production Mosquitto or MQTT wire implementation.
2. The protocol is ML-KEM-backed and protocol-shaped but is not a drop-in replacement for the Kim-Seo wire protocol.
3. No ATmega4808 or other AVR hardware was used.
4. No physical energy, SRAM, flash, cycle, or radio measurements were taken.
5. The formal files are draft models and were not used to claim a completed proof.
6. The prototype does not claim forward secrecy under compromise without additional formal analysis.
7. Python timing is machine- and environment-dependent.

## 12. Conclusion

This project successfully implements and evaluates a secure session-lifecycle extension for post-quantum MQTT software. It demonstrates that authenticated epoch-based reconnection can be substantially faster than repeating the initial ML-KEM handshake while rejecting replayed and modified protocol data.

The 100-trial evaluation produced a median speedup of approximately 7.07x for epoch resumption. The functional test suite passed all 11 tests, and the end-to-end publisher/broker/subscriber workflow completed successfully.

The correct conclusion is:

> The Semester 1 software prototype demonstrates replay-resistant ML-KEM session continuity and a substantial reduction in reconnection computation compared with a fresh initial handshake.

It is not a claim of complete AVR hardware replication, production MQTT deployment, or formal security proof.

## 13. Reproducibility Commands

Run from the project directory:

```bash
cd "/Users/sangabalanarsimha/Desktop/Major Project/pq-mqtt-session-security"
source .venv/bin/activate
python -m pytest -q
PYTHONPATH=. python experiments/sem1_session_lifecycle/run_end_to_end_demo.py
PYTHONPATH=. python attacks/replay_transcript_attack.py
PYTHONPATH=. python attacks/interrupted_handshake_attack.py
PYTHONPATH=. python experiments/sem1_session_lifecycle/run_replay_benchmark.py --trials 100
PYTHONPATH=. python experiments/sem1_session_lifecycle/run_session_benchmark.py --trials 100
python avr_sim/simulated_timing.py
PYTHONPATH=. python experiments/sem1_session_lifecycle/analyze_results.py results/raw/sem1_session.csv
```

Expected core result:

```text
11 passed
```
