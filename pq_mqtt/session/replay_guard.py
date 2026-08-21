"""Replay and monotonic-epoch enforcement."""

from __future__ import annotations

from dataclasses import dataclass


class ReplayError(ValueError):
    """Raised when a token or message is stale or already used."""


@dataclass
class ReplayGuard:
    highest_epoch: int = -1
    highest_counter: int = -1

    def accept_epoch(self, epoch: int) -> None:
        if epoch <= self.highest_epoch:
            raise ReplayError(f"epoch {epoch} is not newer than {self.highest_epoch}")
        self.highest_epoch = epoch
        self.highest_counter = -1

    def accept_message(self, epoch: int, counter: int) -> None:
        self.validate_message(epoch, counter)
        self.highest_counter = counter

    def validate_message(self, epoch: int, counter: int) -> None:
        """Check a message without mutating state.

        Call ``accept_message`` only after authenticating the ciphertext.
        """
        if epoch != self.highest_epoch:
            raise ReplayError("message belongs to an inactive epoch")
        if counter <= self.highest_counter:
            raise ReplayError("message counter was replayed or reordered")
