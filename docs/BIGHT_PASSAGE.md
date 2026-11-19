# Passing a folded strand through a ring

A bight is a bend made in the middle of a strand. Pushing it through an opening can put two material passages in the opening while both free ends stay on the starting side. The return path matters when a tool must pick up a particular strand of yarn.

The example follows two straight legs of length ℓ joined by a semicircle of radius a. The ring lies in the horizontal plane. Let h be the signed height of the center of the semicircle, with its tip at h + a. When −a < h < 0, the intersections lie at horizontal offsets ±√((a + h)(a − h)). Following the yarn from its left leg, the first passage points up and the second points down. The material length beyond the plane is 2a arccos(−h/a). Once the whole bend emerges, the length is πa + 2h until the free ends reach the plane.

The ring has centerline radius R and wire radius b. The yarn radius is r. If the bend is offset in the ring plane by (x, y), every point on its centerline has radial distance at most ρ = √((|x| + a)² + y²). The lower bound R − ρ − b − r therefore certifies surface clearance whenever it is positive, throughout the stroke. It is attained when the farther leg intersects the plane inside the ring. Each reported crossing is strictly inside the ring centerline, so a crossing at the rim requires a separate contact check.

With a 2 mm bend, 15 mm legs, a centered 6 mm ring, 0.60 mm wire and 0.25 mm yarn radius, the surfaces clear by at least 3.15 mm. At h = −1 mm, 4.189 mm of yarn has passed through the plane. These illustrative dimensions define an analytical geometry benchmark. A freely deforming strand requires its own contact, gripping and load model.

```sh
python3 examples/bight_passage.py
python3 -m unittest benchmarks.test_bight_passage
```
