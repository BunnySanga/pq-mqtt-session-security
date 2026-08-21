"""Summarize Sem 1 CSV results and optionally create a plot."""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    with args.csv_file.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("CSV contains no benchmark rows")
    print(f"rows: {len(rows)}")
    for column in rows[0]:
        if column == "trial":
            continue
        values = [float(row[column]) for row in rows]
        deviation = statistics.stdev(values) if len(values) > 1 else 0.0
        print(
            f"{column}: mean={statistics.mean(values):.2f}, "
            f"median={statistics.median(values):.2f}, stdev={deviation:.2f}, "
            f"min={min(values):.2f}, max={max(values):.2f}"
        )


if __name__ == "__main__":
    main()
