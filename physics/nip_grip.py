"""Finite, conditional reduced boundary for the physically closed inlet nip.

This does not predict compressed yarn stiffness or establish holding force.
It enforces only material already registered in the specified physical clamp.
"""
import numpy as np
from physics.fixture_contact import BoxUnion,subtract_box

class NipGrip:
    def __init__(self,feeder,section,node_count):
        cfg=feeder['inlet_grip']
        if any(type(i)is not int for i in section['indices']):raise ValueError('Nip material IDs must be integers')
        self.indices=np.asarray(section['indices'],dtype=int)
        self.xyz=np.asarray(section['world_xyz_mm'],dtype=float)
        if (len(self.indices)<2 or self.xyz.shape!=(len(self.indices),3)
                or not np.all(np.isfinite(self.xyz))
                or not np.array_equal(self.indices,np.arange(self.indices[0],node_count))
                or self.indices[0]<1):raise ValueError('Nip must hold a finite contiguous supply-end material interval')
        tol=cfg['material_position_tolerance_mm'];xmax=22.+cfg['exit_transition_mm']
        if (np.any(self.xyz[:,0]<10.)or np.any(self.xyz[:,0]>xmax)
                or self.xyz[0,0]<22.-cfg['exit_transition_mm']
                or np.max(abs(self.xyz[:,1]-cfg['center_y_mm']))>tol
                or np.max(abs(self.xyz[:,2]-cfg['closed_center_z_mm']))>tol):
            raise ValueError('Nip material outside physical pad/exit domain')
        self.edge_ids=set(range(int(self.indices[0])-1,node_count-1))
        hw=cfg['reduced_envelope_halfwidth_y_mm'];y=cfg['center_y_mm']
        self.cut=(np.array([10.,y-hw,237.9]),np.array([xmax,y+hw,239.+feeder['nip_closed_gap_mm']+.1]))
        self.exit_edge=int(self.indices[0])-1
        self.exit_cut=(self.cut[0].copy(),self.cut[1].copy());self.exit_cut[0][0]=22.-cfg['exit_transition_mm']
        self.scope='Closed-nip conditional no-slip boundary; only named own-pad material and bounded exit transition reduced. Retention/compression unmeasured.'

    def cut_for_edge(self,edge):
        if edge not in self.edge_ids:raise ValueError('Unregistered nip material edge')
        return self.exit_cut if edge==self.exit_edge else self.cut

    def reduce(self,boxes,edge):
        return BoxUnion([p for box in boxes for p in subtract_box(box,self.cut_for_edge(edge))])

    def metadata(self):
        return {'indices':self.indices.tolist(),'material_edges':sorted(self.edge_ids),
                'cut_box_mm':[v.tolist()for v in self.cut],
                'free_exit_edge':self.exit_edge,'exit_cut_box_mm':[v.tolist()for v in self.exit_cut],
                'qualified_retention':False,'scope':self.scope}
