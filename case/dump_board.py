"""KiCad python ile calistir: karttan kutu icin gereken olculeri board_dims.json'a yazar (mm, kart sol-ust koseye gore)."""
import json, pcbnew
b = pcbnew.LoadBoard(r"C:\Users\yavuz\Desktop\hava-istasyonu\pcb\v1\hava_routed.kicad_pcb")
O = pcbnew.FromMM(100)
mm = lambda v: round(pcbnew.ToMM(v - O), 3)
e = b.GetBoardEdgesBoundingBox()
out = {"board": [mm(e.GetLeft()), mm(e.GetTop()), mm(e.GetRight()), mm(e.GetBottom())], "parts": {}}
def bbox(fp, layer):
    ids = b.GetLayerID(layer); xs = []; ys = []
    for g in fp.GraphicalItems():
        if g.GetLayer() == ids:
            r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    return [mm(min(xs)), mm(min(ys)), mm(max(xs)), mm(max(ys))] if xs else None
for ref in ("U1", "J1", "J2", "U2", "U3", "SW1", "SW2", "SW3", "D1"):
    fp = b.FindFootprintByReference(ref)
    out["parts"][ref] = {"pos": [mm(fp.GetPosition().x), mm(fp.GetPosition().y)],
                         "fab": bbox(fp, "F.Fab"), "courtyard": bbox(fp, "F.CrtYd")}
json.dump(out, open("board_dims.json", "w"), indent=1)
print(json.dumps(out))
