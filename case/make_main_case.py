"""freecadcmd make_main_case.py : ana kart kutusu. Kart 2 vida ile tabana sabitlenir (M2 montaj delikleri).
Sag duvardan sensor kablosu (dik acili header), alt duvardan USB-C. Kapakta 2 buton ve 1 LED deligi."""
import json, os
import FreeCAD as App, Part
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\yavuz\Desktop\hava-istasyonu\case"
D = json.load(open(os.path.join(HERE, "dims_main.json")))
bx0, by0, bx1, by1 = D["board"]; P = D["parts"]

WALL, FLOOR, LID, GAP = 2.0, 2.0, 2.0, 0.6
POST_H, PCB_T = 3.0, 1.6
INNER_H = 11.0            # taban ustu -> kapak alti; 10 mm iken kapak citasi USB-C ustune 0.4 mm carpti
ANT_CLEAR = 2.0           # anten ucu ustunde plastik boslugu (metal yok)
TOL = 0.2

def box(x0, y0, x1, y1, z0, z1):
    xa, xb = sorted((x0, x1)); ya, yb = sorted((-y0, -y1))
    return Part.makeBox(xb - xa, yb - ya, z1 - z0, App.Vector(xa, ya, z0))
def cyl(x, y, r, z0, z1):
    return Part.makeCylinder(r, z1 - z0, App.Vector(x, -y, z0))

ant_top = P["U1"]["fab"][1]
cx0, cx1 = bx0 - GAP, bx1 + GAP
cy0, cy1 = ant_top - ANT_CLEAR, by1 + GAP
ox0, ox1, oy0, oy1 = cx0 - WALL, cx1 + WALL, cy0 - WALL, cy1 + WALL
ZB = FLOOR + POST_H; ZT = ZB + PCB_T; ZI = FLOOR + INNER_H

base = box(ox0, oy0, ox1, oy1, 0, ZI).cut(box(cx0, cy0, cx1, cy1, FLOOR, ZI + 1))
# vidali direkler (montaj delikleri): M2 kilavuz deligi 1.6 mm
for ref in ("H1", "H2"):
    x, y = P[ref]["pos"]
    base = base.fuse(cyl(x, y, 3.0, FLOOR, ZB)).cut(cyl(x, y, 0.8, FLOOR + 0.5, ZB + 0.1))
# ust kose dayanaklari (sadece kartin altina oturur)
for (x, y) in ((2.5, 1.5), (bx1 - 2.5, 1.5)):
    base = base.fuse(cyl(x, y, 1.5, FLOOR, ZB))
# USB-C acikligi (alt duvar)
uc = P["J1"]["fab"]; ux = (uc[0] + uc[2]) / 2; uw = (uc[2] - uc[0]) + 1.2
base = base.cut(box(ux - uw / 2, cy1 - 0.5, ux + uw / 2, oy1 + 0.5, ZT - 0.4, ZT + 3.2 + 1.0))
# sensor kablosu acikligi (sag duvar): header pinleri boyunca
pads = P["J2"]["pads"]; py0, py1 = min(p[1] for p in pads) - 2.0, max(p[1] for p in pads) + 2.0
base = base.cut(box(cx1 - 0.5, py0, ox1 + 0.5, py1, ZT - 0.5, ZT + 7.0))

# kapak
lid = box(ox0, oy0, ox1, oy1, ZI, ZI + LID)
lip = box(cx0 + TOL, cy0 + TOL, cx1 - TOL, cy1 - TOL, ZI - 2.5, ZI)
lip = lip.cut(box(cx0 + TOL + 1.5, cy0 + TOL + 1.5, cx1 - TOL - 1.5, cy1 - TOL - 1.5, ZI - 3, ZI + 1))
lid = lid.fuse(lip)
for ref in ("SW1", "SW2"):
    x, y = P[ref]["pos"]; lid = lid.cut(cyl(x, y, 1.4, ZI - 3, ZI + LID + 1))
x, y = P["D1"]["pos"]; lid = lid.cut(cyl(x, y, 1.0, ZI - 3, ZI + LID + 1))

out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
for name, sh in (("main_base", base), ("main_lid", lid)):
    sh.exportStep(os.path.join(out, name + ".step")); sh.exportStl(os.path.join(out, name + ".stl"))
print("ANA KUTU DIS OLCU mm: %.1f x %.1f x %.1f" % (ox1 - ox0, oy1 - oy0, ZI + LID))
print("gecerli: base=%s lid=%s | kart tabani z=%.1f ustu z=%.1f kapak alti z=%.1f" % (base.isValid(), lid.isValid(), ZB, ZT, ZI))
