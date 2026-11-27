"""Follow the same marked yarn through five transverse sections of a translating hook."""
import json
from pathlib import Path
import numpy as np


def trace(path=None):
    with np.load(path or Path(__file__).with_suffix(".npz"),allow_pickle=False) as z:
        s=z["material_mm"]; R=z["basis"]; p=(z["world_mm"]-z["pocket_origin_mm"])@R
        lo,hi,bottom,top=z["window_mm"];travel=float(z["entry_travel_mm"]); fresh=float(z["fresh_after_mm"])
        if not np.all(np.diff(s)>0) or not np.allclose(R.T@R,np.eye(3)) or np.linalg.det(R)<0:
            raise ValueError("Invalid material register or head frame")
        curves=[]
        for plane in z["section_mm"]:
            side=p[:,2]-plane
            ix=np.flatnonzero(((side[:-1]<=0)&(side[1:]>0))|((side[1:]<=0)&(side[:-1]>0)))
            crossings=[]
            for i in ix:
                u=-side[i]/(side[i+1]-side[i])
                x,y=(p[i]+u*(p[i+1]-p[i]))[:2]
                if lo<=x<=hi:
                    # Holder advances along its local second axis. The frozen yarn
                    # is therefore at y+travel initially and at y after the stroke.
                    a=max(0.,float(y+travel-top));b=min(travel,float(y+travel-bottom))
                    if a<=b:
                        crossings.append(dict(begin_mm=a,end_mm=b,s_mm=float(s[i]+u*(s[i+1]-s[i])),
                                              sign=int(np.sign(side[i+1]-side[i]))))
            curves.append(crossings)
        start=[sum(row["begin_mm"]==0 for row in section) for section in curves]
        end=[[row for row in section if row["end_mm"]==travel] for section in curves]
        valid=all(len(section)==1 and section[0]["s_mm"]>fresh and section[0]["sign"]==1 for section in end)
        only_target=all(len(section)==1 for section in curves)
        entry=max(section[0]["begin_mm"] for section in end) if valid else None
        return dict(initial_counts=start,terminal_counts=[len(section) for section in end],
                    terminal_material_mm=[[r["s_mm"] for r in section] for section in end],
                    all_five_fresh_and_positive=valid,only_one_label_per_section_during_entry=only_target,
                    all_sections_occupied_after_mm=entry,entry_travel_mm=travel)


if __name__=="__main__":
    print(json.dumps(trace(),indent=2))
