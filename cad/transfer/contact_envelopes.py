"""Conservative union cover of every additive carriage primitive, before cuts."""
def carriage_boxes(C,I):
 a=C['stripper_channel_mm']/2+C['stripper_plate_thickness_mm']+C['lift_carriage_plate_gap_mm'];b=a+C['lift_pin_embed_mm'];v=C['lift_park_v_mm'];t0,t1=C['lift_carriage_top_offsets_mm'];rw=C['lift_guide_w_mm'];col=C['lift_carriage_column_width_mm']/2;u=(a+b)/2+C['lift_guide_u_offset_mm'];rad=C['lift_bushing_outer_d_mm']/2;lo,hi=C['lift_bushing_v_offsets_mm'];ew=I['lift_ear_half_w_mm']
 boxes=[[a,b,v+t0,v+t1,-rw-3,rw+3],[b,I['lift_ear_u_mm'][1],v+t0,v+t1,-ew,ew],[*I['lift_ear_u_mm'],*I['lift_ear_v_mm'],-ew,ew]]
 for w in [-C['lift_pin_w_mm'],C['lift_pin_w_mm']]:boxes.append([a,b,v-col,v+t0,w-col,w+col])
 for w in [-rw,rw]:boxes.append([u-rad,u+rad,v+lo,v+hi,w-rad,w+rad])
 if not C.get('pin_shuttle'):raise ValueError('Union cover only supports the explicit pin-shuttle carriage')
 bu0,bu1=I['reset_bridge_u_mm'];bv0,bv1=I['reset_bridge_v_mm'];sw=I['pin_shuttle_half_w_mm'];boxes.append([bu0,bu1,bv0,bv1,-sw,sw])
 for w in [-C['lift_pin_w_mm'],C['lift_pin_w_mm']]:boxes.append([bu0,bu1,bv0,v+t0,w-col,w+col])
 return boxes
