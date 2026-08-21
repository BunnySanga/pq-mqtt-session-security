# Semester 1 Threat Model

The network attacker can observe, copy, delay, reorder, modify, and replay session tokens and MQTT-style message envelopes. The baseline attacker cannot directly read endpoint memory.

Security goals:

1. A reconnect token from an already accepted epoch is rejected.
2. A message counter cannot be accepted twice in one epoch.
3. Modified ciphertext or authenticated metadata fails verification.
4. Both endpoints derive the same initial session secret.
5. Epoch keys are domain-separated.

A long-term-key compromise scenario is a research question. This prototype must not claim forward secrecy from the epoch derivation alone. Formal verification and a reviewed protocol construction are required for that claim.

Physical AVR power analysis, real radio transmission, privileged packet-loss injection, and production broker hardening are out of scope for the Kaggle-first version.
