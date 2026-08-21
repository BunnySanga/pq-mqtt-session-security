from attacks.interrupted_handshake_attack import run as interrupted_run
from attacks.replay_transcript_attack import run as replay_run


def test_replay_attack_is_rejected():
    assert replay_run()["replay_rejected"] is True


def test_interrupted_message_is_rejected():
    assert interrupted_run()["interrupted_message_rejected"] is True
