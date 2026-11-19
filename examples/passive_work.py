"""Check a passive energy budget along a piecewise-affine command, with exact bounds."""
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Interval:
    low: Fraction
    high: Fraction

    def __post_init__(self):
        object.__setattr__(self, "low", Fraction(self.low))
        object.__setattr__(self, "high", Fraction(self.high))
        if self.high < self.low:
            raise ValueError("Interval ends must be ordered")

    @classmethod
    def exact(cls, value):
        return cls(value, value)

    def __add__(self, other):
        return Interval(self.low + other.low, self.high + other.high)

    def __sub__(self, other):
        return Interval(self.low - other.high, self.high - other.low)


@dataclass(frozen=True)
class Budget:
    available: tuple
    required_extra: Interval

    @property
    def outcome(self):
        if self.required_extra.low > 0:
            return "deficit"
        if self.required_extra.high > 0:
            return "uncertain"
        return "within available energy"


def passive_budget(steps, initial_kinetic=Interval.exact(0)):
    """Each (external work increment, potential change from start) uses one energy unit."""
    if initial_kinetic.low < 0:
        raise ValueError("Initial kinetic energy must be nonnegative")
    supplied = initial_kinetic
    available = [initial_kinetic]
    for work_increment, potential_change in steps:
        supplied = supplied + work_increment
        available.append(supplied - potential_change)
    # At each command the balance funds kinetic energy and cumulative dissipation.
    # Extremal negative balances bound the minimum additional initial energy.
    minimum_extra = max(Fraction(0), -min(point.high for point in available))
    sufficient_extra = max(Fraction(0), -min(point.low for point in available))
    return Budget(tuple(available), Interval(minimum_extra, sufficient_extra))


if __name__ == "__main__":
    exact = Interval.exact
    example = [(exact(4), exact(3)), (exact(-5), exact(1)), (exact(1), exact(0))]
    report = passive_budget(example)
    print("Available energy at each command (mJ):", [str(p.low) for p in report.available])
    print("Minimum extra initial energy (mJ):", report.required_extra.low)
