"""Rigid clamp pose and analytical rotation derivatives, angles scaled in mm."""
import numpy as np

def rotation(angles,scale=44.):
    a,b,c=np.asarray(angles,dtype=float)/scale
    ca,sa,cb,sb,cc,sc=np.cos(a),np.sin(a),np.cos(b),np.sin(b),np.cos(c),np.sin(c)
    Z=np.array([[ca,-sa,0],[sa,ca,0],[0,0,1.]])
    Y=np.array([[cb,0,-sb],[0,1.,0],[sb,0,cb]])
    X=np.array([[1.,0,0],[0,cc,-sc],[0,sc,cc]])
    dZ=np.array([[-sa,-ca,0],[ca,-sa,0],[0,0,0.]])
    dY=np.array([[-sb,0,-cb],[0,0,0.],[cb,0,-sb]])
    dX=np.array([[0.,0,0],[0,-sc,-cc],[0,cc,-sc]])
    return Z@Y@X,np.array([dZ@Y@X,Z@dY@X,Z@Y@dX])/scale

def migrate_line_clamp(center,angles,height=5.,scale=44.):
    angles=np.r_[angles,0.];R,_=rotation(angles,scale)
    return np.asarray(center)-R@np.array([0.,0.,height]),angles
