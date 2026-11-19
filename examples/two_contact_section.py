"""Frictionless two-direction compression of one linear elastic section."""
from dataclasses import dataclass
import json
import math


@dataclass(frozen=True)
class Compliance:
    first: float
    cross: float
    second: float

    def contact(self, gap1, gap2):
        """Return compressive reactions in N, final gaps in mm, stored potential in N mm."""
        a,c,b=self.first,self.cross,self.second
        if not all(math.isfinite(v) for v in (a,b,c,gap1,gap2)):
            raise ValueError("Use finite gaps and coefficients")
        determinant=a*b-c*c
        if a<=0 or b<=0 or determinant<=0 or not math.isfinite(determinant):
            raise ValueError("The reciprocal compliance must be positive definite")
        if gap1>=0 and gap2>=0:
            p,q=0.,0.
        elif gap1<=0 and gap2-c*gap1/a>=0:
            p,q=-gap1/a,0.
        elif gap2<=0 and gap1-c*gap2/b>=0:
            p,q=0.,-gap2/b
        else:
            p,q=(c*gap2-b*gap1)/determinant,(c*gap1-a*gap2)/determinant
        compressed=(gap1+a*p+c*q,gap2+c*p+b*q)
        energy=-.5*(p*gap1+q*gap2)
        return (p,q),compressed,energy


if __name__=='__main__':
    model=Compliance(.40,.12,.30)  # mm/N in the two normal directions
    reactions,gaps,energy=model.contact(-.12,-.09)
    print(json.dumps(dict(reactions_N=reactions,remaining_gaps_mm=gaps,
                          elastic_potential_Nmm=energy),indent=2))
