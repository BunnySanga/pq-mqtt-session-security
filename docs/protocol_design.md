# Semester 1 Protocol Design

The initial exchange uses two ML-KEM encapsulations with pre-distributed static public keys. The client encapsulates to the broker and the broker encapsulates to the client. Both sides combine the two shared secrets and a transcript nonce through HKDF to obtain the root session secret.

The epoch secret is advanced by a one-way ratchet before each new epoch; the previous secret is overwritten:

```text
S_e = HMAC-SHA256(S_(e-1), "pq-mqtt/ratchet/v1" || uint64(e))
```

For epoch `e`:

```text
K_data(e) = HKDF(root_secret, pq-mqtt/epoch/v1 || uint64(e) || mqtt-data)
K_resume(e) = HKDF(root_secret, pq-mqtt/epoch/v1 || uint64(e) || resume-auth)
```

A reconnect token contains the epoch, a fresh nonce, and an HMAC under `K_resume(e)`. The broker accepts only an epoch greater than its highest accepted epoch. Each message contains an epoch, strictly increasing counter, topic, nonce, and AES-GCM ciphertext. Epoch, counter, and topic are authenticated as associated data.

The local broker simulation routes validated messages to subscribed simulated clients. It intentionally does not claim MQTT wire compatibility or Mosquitto interoperability.
