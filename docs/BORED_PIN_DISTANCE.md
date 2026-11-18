# Finite bored-pin distance

`physics/bored_pin_contact.py` evaluates Euclidean signed distance and a nearest-surface normal for a finite cylinder along Y containing an upward capsule channel along Z. The supported geometry has pin radiusR,half-lengthL,channel radiusr and lower-hemisphere centrez with0<r<z,z+r<R,r<L. All points use the same solid.

The closest-point candidates include the retained outer cylindrical wall, complete end disks, inner channel wall, lower hemisphere and upper intersection rim. The rim in one symmetry quadrant is `(t,sqrt(r²−t²),sqrt(R²−t²))`,0<=t<=r. Its squared-distance stationarity equation is reduced to a scalar angular search; endpoint cases are handled explicitly. Geometric membership supplies the sign. At differentiable points the normalized closest-point vector supplies the signed-distance gradient; nonunique closest points require the documented chosen normal.

Tests compare318 native-CAD queries covering inside/outside, rim and end features, check analytical gradients against finite differences, and verify translation, symmetry and distance continuity bounds. These are floating-point geometry checks. Contact forces additionally require a constitutive law, a complete scene and applicable boundary conditions.
