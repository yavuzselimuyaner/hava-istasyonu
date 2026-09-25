"""KiCad'in kendi Python'u ile çalıştır:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_board.py
v1 hava.net -> hava.kicad_pcb (footprint yerleşimi + net atamaları + kart sınırı)
"""
import os
import re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
FP_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
BOARD_W, BOARD_H = 50.0, 56.0   # mm
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

# Yerleşim: ref -> (x, y, açı derece, katman). Koordinatlar kart sol-üst köşesine göre mm.
# Ref'ler gen_netlist.py'de açıkça verilir; aşağıda değer kontrolü var.
PLACE = {
    "U1": (25.0, 13.0, 0),      # ESP32-C3-WROOM-02, anten kart üst kenarında
    "U4": (25.0, 51.0, 0),      # USB ESD koruması, J1'e yakın
    "J1": (25.0, BOARD_H - 3.5, 0),
    "U2": (13.0, 47.0, 0),      # LDO
    "C1": (13.0, 52.0, 0),      # LDO girişi
    "C2": (18.0, 47.0, 0),      # LDO çıkışı
    "R1": (32.0, 55.0, 0),      # CC dirençleri
    "R2": (35.0, 55.0, 0),
    "U3": (42.0, 47.0, 0),      # BME280, ısı kaynaklarından uzak
    "C6": (42.0, 51.0, 0),
    "R5": (46.0, 44.0, 0),
    "R6": (46.0, 46.5, 0),
    "C3": (10.0, 33.0, 0),      # ESP 3V3 bypass
    "C4": (13.0, 33.0, 0),
    "R3": (10.0, 29.0, 0),      # EN pull-up
    "C5": (13.0, 29.0, 0),      # EN kondansatörü
    "R4": (10.0, 25.0, 0),      # BOOT pull-up
    "SW1": (5.0, 36.0, 0),
    "SW2": (5.0, 42.0, 0),
    "SW3": (5.0, 48.0, 0),
    "R7": (40.0, 33.0, 0),
    "D1": (44.0, 33.0, 0),
    "J2": (46.0, 12.0, 0),      # ekran header'ı (dikey 1x8)
}
EXPECT = {"U1": "ESP32-C3", "U4": "USBLC6", "J1": "USB", "U2": "AP2112", "U3": "BME280", "J2": "Conn",
          "R1": "5.1k", "R2": "5.1k", "R3": "10k", "R4": "10k", "R5": "4.7k",
          "R6": "4.7k", "R7": "1k", "C1": "10uF", "C2": "10uF", "C3": "10uF",
          "C4": "100nF", "C5": "1uF", "C6": "100nF", "D1": "LED", "SW1": "SW",
          "SW2": "SW", "SW3": "SW"}
for ref, key in EXPECT.items():
    assert key in comps[ref]["value"] or key in comps[ref]["footprint"], (ref, comps[ref])
# Anten kartin ust kenarindan disari tasar (Espressif onerisi): modul ve diger parcalar yukari kaydirilir
SHIFT = 5.8
PLACE = {k: (x, y if k == "J1" else y - SHIFT, r) for k, (x, y, r) in PLACE.items()}
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
