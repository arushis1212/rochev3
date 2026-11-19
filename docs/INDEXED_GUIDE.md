# The path between indexed guide positions

Two screw wheels move a planar guide 1 mm per notch in this example. The guide must move 3 mm horizontally and 4 mm vertically. Turning the nearest wheel when the ideal position crosses a half-notch gives seven separate moves. Both axes reach the intended endpoint exactly. During the stroke the largest perpendicular distance to the intended line is **0.600 mm**. The largest distance to the ideal position at the same command progress is **0.625 mm**.

For a line displacement `(a, b)` and guide position `(x, y)`, the perpendicular distance is `|a y − b x| / hypot(a, b)`. A wheel crosses its next half-notch at a rational fraction of the commanded stroke. The example sorts those fractions exactly. When both wheels reach a threshold together it turns the horizontal wheel first. Each turn traverses a straight line. Between turns the ideal position advances while the physical guide stays put. The maximum error on either interval occurs at an endpoint because the norm of an affine displacement is convex. This also gives a general synchronized error bound of one half-notch per axis.

On a rail aligned with the command line, each notch lies on that line. A rail set at an angle error ε introduces a transverse offset of `L sin(ε)` over travel L. Both constructions quantify the geometric input to a yarn-contact calculation. A yarn tension or slip prediction additionally needs the material and guide contact model.

Run the example and its six tests from the repository root.

```sh
python3 examples/indexed_guide.py
python3 -m unittest benchmarks.test_indexed_guide
```

[Example source](../examples/indexed_guide.py) · [Repeatable checks](../benchmarks/test_indexed_guide.py)
