# Transferring a carriage between two stops

An indexed screw carries a carriage on a rear shoe while the operator changes a gauge rod. Moving the housing forward transfers load to the end stop before the rear shoe separates. Two positive normal reactions can coexist during the transfer. The example calculates the carriage position and both reactions from the housing position.

Let `h` be the rear shoe’s unloaded position, `b` the end stop’s unloaded position, and `F` the total forward force. With linear compliances `Cᵣ` and `Cₚ` in mm/N, simultaneous contact requires `q = h + CᵣR = b + CₚP` and `R + P = F`. Solving gives `P = (h − b + CᵣF)/(Cᵣ + Cₚ)` within the overlap interval. Clamping this result to the range from zero to F supplies the single-contact branches. The code also evaluates both remaining gaps. [Runnable example](../examples/indexed_load_transfer.py)

For example, take an 8 N forward load, a 0.0005 mm/N rear compliance, a 0.0001 mm/N end compliance and a stop at zero. Load transfer begins at a housing position of −0.0040 mm and finishes at +0.0008 mm. At zero, the rear shoe carries 1.333 N and the end stop carries 6.667 N. These compliance values illustrate the calculation.

For a positive clearance window of width W, load-dependent compression reduces the common acceptable housing interval to `W − (maximum compression − minimum compression)`. A measured monotone index map spanning that entire interval contains an eligible index whenever its maximum adjacent spacing fits the interval width. The program also accepts individual measured positions and returns the exact qualifying index numbers, including endpoints. [Force balance, continuity and variable-load checks](../benchmarks/test_indexed_load_transfer.py)

```sh
python3 examples/indexed_load_transfer.py
python3 -m unittest benchmarks.test_indexed_load_transfer
```
