"""SIMULATED timing model; this is not an AVR hardware measurement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimingEstimate:
    operation: str
    cycles: int
    clock_hz: int = 7_370_000

    @property
    def seconds(self) -> float:
        return self.cycles / self.clock_hz


def estimate_sem1(full_handshake_cycles: int = 31_833_391, resume_cycles: int = 80_000) -> list[TimingEstimate]:
    return [
        TimingEstimate("full_kem_mqtt_handshake_simulated", full_handshake_cycles),
        TimingEstimate("epoch_resume_simulated", resume_cycles),
    ]


if __name__ == "__main__":
    for estimate in estimate_sem1():
        print(f"{estimate.operation}: {estimate.seconds:.6f}s (SIMULATED)")
