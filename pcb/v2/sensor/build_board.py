"""KiCad'in kendi Python'u ile çalıştır:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_board.py
v1 hava.net -> hava.kicad_pcb (footprint yerleşimi + net atamaları + kart sınırı)
"""
import os
import re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
FP_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
BOARD_W, BOARD_H = 14.0, 16.0   # mm
ORG_X, ORG_Y = 100.0, 100.0     # kartın sol-üst köşesi (sayfa koordinatı)


def parse_sexpr(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    pos = 0

    def read():
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        if tok == "(":
            lst = []
            while tokens[pos] != ")":
                lst.append(read())
            pos += 1
            return lst
        return tok[1:-1] if tok.startswith('"') else tok

    return read()


def find_all(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def find(node, name):
    r = find_all(node, name)
    return r[0] if r else None


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(ORG_X + x), mm(ORG_Y + y))


tree = parse_sexpr(open(os.path.join(HERE, "hava.net"), encoding="utf8").read())
comps = {}
for c in find_all(find(tree, "components"), "comp"):
    ref = find(c, "ref")[1]
    comps[ref] = dict(value=find(c, "value")[1], footprint=find(c, "footprint")[1])
nets = {}
for n in find_all(find(tree, "nets"), "net"):
    name = find(n, "name")[1]
    nets[name] = [(find(nd, "ref")[1], find(nd, "pin")[1]) for nd in find_all(n, "node")]

# Yerlesim (mm). J1 90 derece dondurulmus: pinler x yonunde, kartin alt kenarinda.
PLACE = {
    "U1": (7.0, 4.5, 0), "C1": (4.0, 7.7, 0), "C2": (10.0, 7.7, 0),
    "J1": (2.95, 12.8, 90),
    "H1": (2.0, 2.0, 0), "H2": (BOARD_W - 2.0, 2.0, 0),
}
EXPECT = {"U1": "BME280", "C1": "100nF", "C2": "100nF", "J1": "Conn", "H1": "Mounting", "H2": "Mounting"}
for ref, key in EXPECT.items():
    assert key in comps[ref]["value"] or key in comps[ref]["footprint"], (ref, comps[ref])
assert set(comps) == set(PLACE), set(comps) ^ set(PLACE)

board = pcbnew.BOARD()
netinfo = {}
for name in nets:
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    netinfo[name] = ni

pin_net = {}
for name, nodes in nets.items():
    for ref, pin in nodes:
        pin_net[(ref, pin)] = name

for ref, info in comps.items():
    lib, fpname = info["footprint"].split(":")
    fp = pcbnew.FootprintLoad(os.path.join(FP_DIR, lib + ".pretty"), fpname)
    if fp is None:
        raise SystemExit("footprint yok: " + info["footprint"])
    fp.SetReference(ref)
    fp.SetValue(info["value"])
    x, y, rot = PLACE[ref]
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(rot)
    board.Add(fp)
    for pad in fp.Pads():
        n = pin_net.get((ref, pad.GetNumber()))
        if n:
            pad.SetNet(netinfo[n])

edge = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(mm(0.1))
    seg.SetStart(vec(*edge[i]))
    seg.SetEnd(vec(*edge[(i + 1) % 4]))
    board.Add(seg)

out = os.path.join(HERE, "hava.kicad_pcb")
pcbnew.SaveBoard(out, board)
print("yazildi:", out, "| parca:", len(comps), "| net:", len(nets))
