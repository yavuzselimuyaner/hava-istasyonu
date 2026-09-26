"""freecadcmd make_shield.py : sensor karti icin radyasyon siperi (Stevenson tarzi, 3 semsiye plaka + cati).
Sensor karti UST (bilesen) yuzu ASAGI bakacak sekilde catinin altina 2 direge asili; header asagi bakar,
Dupont fisi ve kablo alttan cikar. Olculer dims_sensor.json'dan (montaj deligi konumu)."""
import json, os, math
import FreeCAD as App, Part
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
D = json.load(open(os.path.join(HERE, "dims_sensor.json")))
bx0, by0, bx1, by1 = D["board"]
cxb, cyb = (bx0 + bx1) / 2, (by0 + by1) / 2          # kart merkezi

# ---- parametreler ----
R_OUT, R_HOLE = 27.0, 10.0      # plaka dis yaricapi, merkez delik yaricapi
PL_H, PL_T = 8.0, 1.5           # plaka yuksekligi, dikey kalinlik
PITCH = 10.0                    # plaka araligi
N_PLATES = 3
ROOF_Z, ROOF_H, ROOF_R0, ROOF_R1 = 40.0, 12.0, 30.0, 8.0
ROD_R, ROD_AT = 2.5, 22.0       # ayirici cubuk yaricapi ve konum yaricapi
POST_R, POST_L = 2.5, 4.0       # kart direkleri (catinin altindan asagi)
BOARD_BACK_Z = ROOF_Z - POST_L  # kartin arka yuzu (montaj yuzu)

def cone_shell(z0):
    outer = Part.makeCone(R_OUT, R_HOLE, PL_H, App.Vector(0, 0, z0))
    inner = Part.makeCone(R_OUT, R_HOLE, PL_H, App.Vector(0, 0, z0 - PL_T))
    plate = outer.cut(inner)
    return plate.cut(Part.makeCylinder(R_HOLE, PL_H + 4, App.Vector(0, 0, z0 - 1)))

shield = None
for k in range(N_PLATES):
    p = cone_shell(k * PITCH)
    shield = p if shield is None else shield.fuse(p)
for a in (90, 210, 330):
    x, y = ROD_AT * math.cos(math.radians(a)), ROD_AT * math.sin(math.radians(a))
    shield = shield.fuse(Part.makeCylinder(ROD_R, ROOF_Z - 0.0, App.Vector(x, y, 0)))
shield = shield.fuse(Part.makeCone(ROOF_R0, ROOF_R1, ROOF_H, App.Vector(0, 0, ROOF_Z)))
# kart direkleri: montaj deliklerinin kart merkezine gore konumu (kart XY duzleminde, merkez ekseninde)
posts = []
for ref in ("H1", "H2"):
    hx, hy = D["parts"][ref]["pos"]
    px, py = hx - cxb, -(hy - cyb)          # FreeCAD Y = -y
    posts.append((px, py))
    shield = shield.fuse(Part.makeCylinder(POST_R, POST_L + 0.5, App.Vector(px, py, BOARD_BACK_Z), App.Vector(0, 0, 1)))

out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
shield.exportStep(os.path.join(out, "shield.step")); shield.exportStl(os.path.join(out, "shield.stl"))
# kesit (yarisi) gorsel icin
half = shield.cut(Part.makeBox(200, 100, 200, App.Vector(-100, 0, -50)))
half.exportStl(os.path.join(out, "shield_section.stl"))
bb = shield.BoundBox
print("SIPER: cap %.0f mm, yukseklik %.0f mm, valid=%s, hacim %.0f mm3" % (bb.XLength, bb.ZLength, shield.isValid(), shield.Volume))
print("kart arka yuzu z=%.1f; direk konumlari:" % BOARD_BACK_Z, [(round(x, 2), round(y, 2)) for x, y in posts])
