"""KiCad'in kendi Python'u ile çalıştır:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_board.py
hava.net -> hava.kicad_pcb (footprint yerleşimi + net atamaları + kart sınırı)
"""
import os
import re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
FP_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
BOARD_W, BOARD_H = 32.0, 41.0   # mm
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

# Yerlesim (mm, kart sol-ust koseye gore). Anten kartin ust kenarindan disari tasar (U1 y=7.2).
PLACE = {
    "U1": (16.0, 7.2, 0), "J1": (16.0, BOARD_H - 3.5, 0), "U4": (16.0, 30.6, 0),
    "U2": (6.5, 29.0, 0), "C1": (6.5, 33.5, 0), "C2": (10.8, 29.0, 0),
    "R1": (8.4, 36.6, 0), "R2": (5.6, 36.6, 0),
    "C3": (3.5, 3.5, 0), "C4": (3.5, 7.0, 0), "R3": (3.2, 10.5, 0), "C5": (3.2, 14.0, 0),
    "R4": (3.2, 17.5, 0), "R9": (3.2, 21.0, 0), "R8": (13.5, 17.0, 0),
    "SW1": (24.5, 29.0, 0), "SW2": (24.5, 34.5, 0),
    "D1": (13.0, 23.0, 0), "R7": (10.0, 23.0, 0),
    "J2": (22.0, 16.5, 0),       # dik acili header: pin ucu +x'e, kart kenarina kadar (x~32.1)
    "R5": (18.5, 16.5, 0), "R6": (18.5, 19.0, 0),
    "H1": (2.5, BOARD_H - 2.5, 0), "H2": (BOARD_W - 2.5, BOARD_H - 2.5, 0),
}
EXPECT = {"U1": "ESP32-C3", "J1": "USB", "U2": "AP2112", "U4": "USBLC6", "J2": "Conn",
          "R1": "5.1k", "R2": "5.1k", "R3": "10k", "R4": "10k", "R5": "4.7k", "R6": "4.7k",
          "R7": "1k", "R8": "10k", "R9": "10k", "C1": "10uF", "C2": "10uF", "C3": "10uF",
          "C4": "100nF", "C5": "1uF", "D1": "LED", "SW1": "SW", "SW2": "SW", "H1": "Mounting", "H2": "Mounting"}
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
