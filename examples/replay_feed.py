"""Re-evaluate a saved synthetic equilibrium using the published geometry and energy."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from physics.feed_equilibrium import FeedEquilibrium
from physics.feeder_domain import FeederContact,ScrewCover
from physics.guide_contact import GuidedContact
from physics.transfer_holding import WorldTransfer
from physics.loop_holding import head_frame

def main():
 cp=json.loads((ROOT/'docs/FEED_REFINED_CHECKPOINT.json').read_text());cfg=json.loads((ROOT/'spec/transfer_holding.json').read_text());cfg.update(yarn_linear_density_g_per_m=.1786,contact_reference_spacing_mm=.0125,penalty_N_per_mm2=8000);full=json.loads((ROOT/'spec/r5_m2_fixture.json').read_text());ins=json.loads((ROOT/'spec/transfer_installation.json').read_text());conn=json.loads((ROOT/'spec/connected_yarn.json').read_text());profiles=json.loads((ROOT/'cad/transfer/generated/contact_profiles.json').read_text());base=json.loads((ROOT/'cad/r5m2/generated/contact_profiles.json').read_text())['profiles'];o,M=head_frame(cfg['head_tip_xyz_mm']);guide=o+M@np.array(conn['guide_local_mm']);fast=full['fasteners']['M3'];screw=ScrewCover(ins['fairlead_mount_screw_underhead_xyz_mm'],ins['fairlead_mount_screw_length_mm'],3,fast['head_d_max'],fast['head_height_max']);ob=FeederContact(GuidedContact(WorldTransfer(profiles,base,cfg['head_tip_xyz_mm'],*cp['state']),guide,full['guide']),cp['feeder_z'],[screw]);model=FeedEquilibrium(cp['q'],cp['rest'],cp['split'],cp['center'],cp['angles'],cp['feeder_z'],cfg,ob,full['feeder'],'LOW');E,g=model.energy(model.x0);res=max(float(abs(g).max()),float(np.linalg.norm(model.last_info['clamp_torque_residual_Nmm'])/44));result={'scope':'Re-evaluation of one declared synthetic quasistatic endpoint','nodes':len(cp['q']),'state_mm':cp['state'],'reference_material_length_mm':float(sum(cp['rest'])),'energy_Nmm':float(E),'force_residual_N':res,'feeder_z_mm':cp['feeder_z']};print(json.dumps(result,indent=2));return 0 if res<=1e-7 else 1
if __name__=='__main__':sys.exit(main())
