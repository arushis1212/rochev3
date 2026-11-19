# Measuring section compliance in two directions

A single-direction compression test measures only part of the response when a yarn section touches two supports. At fixed axial pretension, apply two independent normal load increments to a preloaded section. Record both displacements for each load and subtract the fixture response. Keep a third combined load and a separate specimen for validation. Each displacement and force error bound must include the baseline subtraction, fixture response and instrument uncertainty. This example covers a local, elastic response in one contact regime.

Write the measured load columns as a matrix P and the corrected displacements as Y. The measured compliance is C = YP⁻¹ in mm/N. If each load entry has absolute error at most f and each displacement entry has error at most d, the corresponding 2 × 2 matrix errors have spectral norms at most 2f and 2d. Let s be the smallest singular value of P. Provided s > 2f, the largest possible spectral discrepancy between the estimated and true compliance is at most (2d + 2f ‖C‖₂)/(s − 2f). This follows by subtracting the two systems Y = CP and bounding the inverse of the perturbed load matrix. Nearly parallel load columns make the estimate less informative.

A reciprocal elastic material has a symmetric compliance matrix. The program checks whether the observed cross terms agree within the measurement bounds. It also tests whether the smallest eigenvalue of the symmetric fit exceeds the spectral uncertainty. These are consistency and stability checks for the assumed model. A third load probes prediction error independently of the two fitted cases.

The numerical example applies independent 0.4 N increments with illustrative per-entry errors of 0.001 N and 0.001 mm. Its input displacements are synthetic. For a line load in N/mm, the same calculation yields compliance in mm²/N. The contact length and its uncertainty enter the conversion.

```sh
python3 examples/section_calibration.py
python3 -m unittest benchmarks.test_section_calibration
```

[Compliance identification](../examples/section_calibration.py) · [Two-support response](TWO_CONTACT_SECTION.md)
