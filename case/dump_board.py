"""KiCad python: kart ve parca olculerini json'a yazar. Kullanim: python dump_board.py <kart.kicad_pcb> <cikti.json> REF1 REF2 ..."""
import json, sys, pcbnew
path, outp, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
b = pcbnew.LoadBoard(path)
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
for ref in refs:
    fp = b.FindFootprintByReference(ref)
    pads = [[mm(p.GetPosition().x), mm(p.GetPosition().y)] for p in fp.Pads()]
    out["parts"][ref] = {"pos": [mm(fp.GetPosition().x), mm(fp.GetPosition().y)], "fab": bbox(fp, "F.Fab"),
                         "courtyard": bbox(fp, "F.CrtYd"), "pads": pads}
json.dump(out, open(outp, "w"), indent=1)
print("yazildi", outp)
