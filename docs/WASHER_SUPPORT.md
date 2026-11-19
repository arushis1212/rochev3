# Bearing area near a plate edge

A washer beside a straight plate edge can overhang the plate. Part of its flat underside can also lie over the plate’s screw hole. This example calculates how much area is guaranteed to have solid backing as the washer shifts during assembly.

Let the flat outer radius be *R*, the washer bore radius *a*, the support bore radius *b* and the maximum relative center offset *e*. Any point more than *b + e* from the washer center is outside the plate bore by the triangle inequality. The usable inner radius for this bound is therefore the larger of *a* and *b + e*. If the nominal center is distance *d* inside the plate edge, the least supported position lies *d − e* inside it. At that position, subtract the circular segment supported inside the inner radius from the segment supported inside *R*. Moving the center farther onto the plate only increases the supported annular area. Other edges or holes require their own geometry.

For an example with *R* = 3.00 mm, *a* = 1.55 mm, *b* = 1.50 mm, *d* = 1.80 mm and *e* = 0.18 mm, at least **14.5305 mm²** has geometric backing. At 36 N and complete contact across the backed area, the average pressure is at most **2.478 MPa**. Actual contact imprint, washer deflection, local pressure and substrate creep require separate measurements or analysis.

Run `python3 examples/washer_support.py` to reproduce the calculation. The tests check independent numerical integration, edge and full-disk cases, invalid dimensions and increasing offset. [Calculation](../examples/washer_support.py) · [Benchmarks](../benchmarks/test_washer_support.py)
