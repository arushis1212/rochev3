"""Assemble the common vertical allowance from the actual source-shape contact thresholds."""
import csv
from pathlib import Path

DATA = Path(__file__).with_name("gate_register_measurements.csv")


def intervals(path=DATA):
    grouped = {}
    with Path(path).open(newline="") as source:
        for row in csv.DictReader(source):
            key = float(row["head_mm"])
            lower = float(row["startup_threshold_mm"])
            upper = [float(row[k]) for k in ("peak1_threshold_mm", "peak2_threshold_mm") if row[k]]
            grouped.setdefault(key, []).append((lower, min(upper) if upper else None))
    return {
        head: (max(row[0] for row in corners),
               min(row[1] for row in corners) if all(row[1] is not None for row in corners) else None)
        for head, corners in grouped.items()
    }


if __name__ == "__main__":
    for head, (low, high) in sorted(intervals().items()):
        limit = f"{high*1000:+.3f} µm" if high is not None else "startup data only"
        print(f"Head {head:+.3f} mm, lower {low*1000:+.3f} µm, upper {limit}")
