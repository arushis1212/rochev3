"""Solve the static printed-knob and metal-gate setting at the parked capture station."""
import argparse
import json
import math
from pathlib import Path

try:
    from .two_contact_section import Compliance
except ImportError:  # direct invocation from the repository root
    from two_contact_section import Compliance

def predict(left_gap_mm, right_gap_mm, tangent_ratio=0., carried_spring_g=.370):
    values=(left_gap_mm,right_gap_mm,tangent_ratio,carried_spring_g)
    if any(not math.isfinite(x) for x in values):
        raise ValueError("Inputs must be finite")
    if min(left_gap_mm,right_gap_mm)<0 or max(left_gap_mm,right_gap_mm)>.014:
        raise ValueError("Use a lower journal gap from 0 to 0.014 mm")
    if not -.20<=tangent_ratio<=.20 or not 0<=carried_spring_g<=.370:
        raise ValueError("Use a tangential ratio within ±0.20 and a carried mass from 0 to 0.370 g")
    model=json.loads(Path(__file__).with_name("gate_setting_coefficients.json").read_bytes())
    normal_load=(model["spring_force_N"]+(model["translating_mass_g"]+carried_spring_g)*model["axial_weight_N_g"])/(
        model["normal_axial"]-tangent_ratio*model["tangent_axial"])
    free=[bias+per_gram*carried_spring_g+per_newton*normal_load
          for bias,per_gram,per_newton in model["affine_free_gap_and_free_bias"]]
    matrix=model["rail_mm_N"]
    contact=Compliance(matrix[0][0],(matrix[0][1]+matrix[1][0])/2,matrix[1][1])
    reactions,gaps,_=contact.contact(free[0]+left_gap_mm,free[1]+right_gap_mm)
    loss=free[2]+sum(r*k for r,k in zip(reactions,model["gate_response_mm_N"]))
    return dict(upper_normal_N=normal_load,lower_normal_reactions_N=reactions,
                remaining_lower_gaps_mm=gaps,gate_bias_mm=loss,predicted_gate_opening_mm=.202-loss)

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--left-gap",type=float,default=0.,help="unloaded clearance under left roller, mm")
    ap.add_argument("--right-gap",type=float,default=0.,help="unloaded clearance under right roller, mm")
    ap.add_argument("--tangent-ratio",type=float,default=0.,help="signed upper tangential/normal force")
    ap.add_argument("--spring-mass",type=float,default=.370,help="spring mass carried by the moving eye, grams")
    args=ap.parse_args()
    print(json.dumps(predict(args.left_gap,args.right_gap,args.tangent_ratio,args.spring_mass),indent=2))
