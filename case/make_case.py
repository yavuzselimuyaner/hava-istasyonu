"""FreeCAD ile calistir:  freecadcmd.exe make_case.py
board_dims.json (dump_board.py) -> kutu alti + kapak + PCB yer tutucu (STEP/STL).
Koordinat: FreeCAD X = kart x, FreeCAD Y = -(kart y) (KiCad STEP ile ayni), Z yukari, kutu tabani z=0.
"""
import json, os
import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\yavuz\Desktop\hava-istasyonu\case"
D = json.load(open(os.path.join(HERE, "board_dims.json")))
bx0, by0, bx1, by1 = D["board"]
P = D["parts"]

# ---- parametreler (mm) ----
WALL = 2.0          # duvar
FLOOR = 2.0         # taban kalinligi
LID = 2.0           # kapak kalinligi
GAP = 0.6           # kart ile duvar arasi bosluk
POST_H = 3.0        # kart alti destek yuksekligi (alt taraftaki header/pin uclari icin)
PCB_T = 1.6
INNER_H = 14.0      # taban ustunden kapak alt yuzeyine
ANT_CLEAR = 2.0     # anten ucunun ustunde plastik boslugu (metal yok)
TOL = 0.2

# ---- yardimci ----
def box(x0, y0, x1, y1, z0, z1):
    """x,y KiCad koordinati (y asagi); FreeCAD'de Y = -y."""
    xa, xb = sorted((x0, x1)); ya, yb = sorted((-y0, -y1))
    return Part.makeBox(xb - xa, yb - ya, z1 - z0, App.Vector(xa, ya, z0))

def cyl(x, y, r, z0, z1):
    return Part.makeCylinder(r, z1 - z0, App.Vector(x, -y, z0))

# ---- ic bosluk (kart + anten bolgesi) ----
ant_top = P["U1"]["fab"][1]                     # modul ust ucu (anten), kartin ustunden disari
cx0, cx1 = bx0 - GAP, bx1 + GAP
cy0 = ant_top - ANT_CLEAR                       # ust (anten tarafi)
cy1 = by1 + GAP                                 # alt (USB tarafi)
ox0, ox1, oy0, oy1 = cx0 - WALL, cx1 + WALL, cy0 - WALL, cy1 + WALL
Z_BOARD_BOT = FLOOR + POST_H
Z_BOARD_TOP = Z_BOARD_BOT + PCB_T
Z_INNER_TOP = FLOOR + INNER_H

# ---- kutu alti ----
base = box(ox0, oy0, ox1, oy1, 0, Z_INNER_TOP)
base = base.cut(box(cx0, cy0, cx1, cy1, FLOOR, Z_INNER_TOP + 1))
# kart destek direkleri (kose, kart alt yuzune oturur)
posts = [(3.0, 2.0), (47.0, 1.8), (3.0, 53.5), (47.0, 53.5)]
for (px, py) in posts:
    base = base.fuse(cyl(px, py, 2.0, FLOOR, Z_BOARD_BOT))
# USB-C acikligi (alt duvar)
uc = P["J1"]["fab"]; ux = (uc[0] + uc[2]) / 2; uw = (uc[2] - uc[0]) + 1.2
base = base.cut(box(ux - uw / 2, cy1 - 0.5, ux + uw / 2, oy1 + 0.5, Z_BOARD_TOP - 0.4, Z_BOARD_TOP + 3.2 + 1.0))
# BME280 havalandirma yuvalari (sag duvar, sensorun hizasinda)
u3y = P["U3"]["pos"][1]
for k in (-3.0, 0.0, 3.0):
    base = base.cut(box(cx1 - 0.5, u3y + k - 0.6, ox1 + 0.5, u3y + k + 0.6, Z_BOARD_TOP + 0.5, Z_BOARD_TOP + 6.0))

# ---- kapak ----
lid = box(ox0, oy0, ox1, oy1, Z_INNER_TOP, Z_INNER_TOP + LID)
lip = box(cx0 + TOL, cy0 + TOL, cx1 - TOL, cy1 - TOL, Z_INNER_TOP - 2.5, Z_INNER_TOP)
lip = lip.cut(box(cx0 + TOL + 1.5, cy0 + TOL + 1.5, cx1 - TOL - 1.5, cy1 - TOL - 1.5, Z_INNER_TOP - 3, Z_INNER_TOP + 1))
lid = lid.fuse(lip)
# kart bastirma direkleri
for (px, py) in posts:
    lid = lid.fuse(cyl(px, py, 2.0, Z_BOARD_TOP, Z_INNER_TOP))
# ekran penceresi (harici modul kapagin altina yapistirilir): kartin ortasinda 27x27
wx, wy, ws = 25.0, 31.0, 27.0
lid = lid.cut(box(wx - ws / 2, wy - ws / 2, wx + ws / 2, wy + ws / 2, Z_INNER_TOP - 4, Z_INNER_TOP + LID + 1))
# buton delikleri (SW1..SW3) ve LED
for ref in ("SW1", "SW2", "SW3"):
    x, y = P[ref]["pos"]
    lid = lid.cut(cyl(x, y, 1.4, Z_INNER_TOP - 3, Z_INNER_TOP + LID + 1))
x, y = P["D1"]["pos"]
lid = lid.cut(cyl(x, y, 1.0, Z_INNER_TOP - 3, Z_INNER_TOP + LID + 1))
# kapagin ekran penceresi altindaki direkleri kes (pencere ile cakisan direk yok; kontrol asagida)

# ---- PCB yer tutucusu (gorsel + cakisma kontrolu) ----
pcb = box(bx0, by0, bx1, by1, Z_BOARD_BOT, Z_BOARD_TOP)

out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
for name, sh in (("base", base), ("lid", lid)):
    sh.exportStep(os.path.join(out, name + ".step"))
    sh.exportStl(os.path.join(out, name + ".stl"))

print("DIS OLCU mm: %.1f x %.1f x %.1f (kapak dahil)" % (ox1 - ox0, oy1 - oy0, Z_INNER_TOP + LID))
print("IC BOSLUK mm: %.1f x %.1f, ic yukseklik %.1f" % (cx1 - cx0, cy1 - cy0, INNER_H))
print("kart tabani z=%.1f, ustu z=%.1f, kapak alti z=%.1f" % (Z_BOARD_BOT, Z_BOARD_TOP, Z_INNER_TOP))
print("base hacim %.0f mm3 gecerli=%s | lid hacim %.0f mm3 gecerli=%s" % (base.Volume, base.isValid(), lid.Volume, lid.isValid()))
# temel kontroller
print("kart/base cakisma hacmi (0 olmali): %.3f" % pcb.common(base).Volume)
print("kart/lid cakisma hacmi (0 olmali): %.3f" % pcb.common(lid).Volume)
