# The sliding crochet gate

The hook holds the mouth of the yarn passage closed while its gate advances. A shallow cam on the gate brings its metal face into contact with the working strand. A narrow channel in the hook heel gives the cam room when the gate opens for service. The two brass parts use the existing slide. [Hook STEP](../cad/capture_gate/hook_with_heel_relief.step) · [Gate STEP](../cad/capture_gate/gate_with_cam.step) · [Part coordinate bounds and file hashes](../cad/capture_gate/geometry.json)

| Feature | Dimension |
|---|---:|
| Cam rise and flat width | 0.140 mm × 1.05 mm |
| Rise, plateau and descent lengths along the gate | 0.40, 0.47 and 0.40 mm |
| Heel channel width and maximum depth | 1.25 mm × 0.170 mm |
| Working advance from the closed position | 0.85 mm |
| Full service travel | 16.5 mm |

The complete service sweep gives a conservative lower bound of 0.07139 mm between the cam and hook on the nominal rigid solids. Allowing 0.020 mm for their relative alignment and 0.010 mm on each profile leaves 0.03139 mm. These are proposed inspection limits. The included STEP files are individual parts in their own coordinates.

For the modeled 0.550–0.600 mm yarn, a ±0.030 mm centerline allowance, ±0.010 mm cam profile and ±0.030 mm working command give 0.04285 to 0.17185 mm geometric overlap at engagement. That overlap calls for local yarn or hardware displacement. At 0.600 mm diameter a single freely moving normal coordinate settles 0.11879 mm away from its starting position under a 5.447 mN cam reaction, with the neighboring positions held. This result describes local capture mechanics. A yarn sample, profile inspection and a loaded full-cycle test establish the behavior of a fabricated pair.
