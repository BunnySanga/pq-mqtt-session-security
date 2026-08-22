# Semester 1 Threat Model

The network attacker can observe, copy, delay, reorder, modify, and replay session tokens and MQTT-style message envelopes. The baseline attacker cannot directly read endpoint memory.

Security goals:

1. A reconnect token from an already accepted epoch is rejected.
2. A message counter cannot be accepted twice in one epoch.
3. Modified ciphertext or authenticated metadata fails verification.
4. Both endpoints derive the same initial session secret.
5. Epoch keys are domain-separated.

A later compromise of the live ratchet state is considered in the lifecycle design. Each epoch secret is replaced by a one-way HMAC-derived value and the predecessor is not retained by the session object, so the current state is not intended to derive earlier epoch keys. This is a prototype forward-secrecy mechanism, not a proof; secure memory erasure, endpoint compromise details, and formal verification remain required for a production claim.

Physical AVR power analysis, real radio transmission, privileged packet-loss injection, and production broker hardening are out of scope for the Kaggle-first version.
