"""freecadcmd check_fit.py : parcali 3D kart modelleri ile kutu/siper cakisma kontrolu (Dupont fis yer tutucusu dahil)."""
import json, os, FreeCAD as App, Part
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd(); out = os.path.join(HERE, "out")
def load(n):
    s = Part.Shape(); s.read(os.path.join(out, n)); return s
def report(name, board, solids):
    bb = board.BoundBox
    print("[%s] parcali kart sinirlari Z %.2f..%.2f" % (name, bb.ZMin, bb.ZMax))
    for sname, sh in solids:
        v = board.common(sh).Volume
        print("[%s] cakisma / %s: %.3f mm3 %s" % (name, sname, v, "(TEMIZ)" if v < 0.01 else "(CAKISMA!)"))
        if v >= 0.01:
            c = board.common(sh).BoundBox
            print("     bolge X %.1f..%.1f Y %.1f..%.1f Z %.1f..%.1f" % (c.XMin, c.XMax, c.YMin, c.YMax, c.ZMin, c.ZMax))

# ---- ANA KUTU ----
D = json.load(open(os.path.join(HERE, "dims_main.json"))); P = D["parts"]
board = load("main_with_parts.step"); board.translate(App.Vector(0, 0, 5.0))       # kart tabani z=5.0
pads = P["J2"]["pads"]; y0 = min(p[1] for p in pads) - 1.4; y1 = max(p[1] for p in pads) + 1.4
px = pads[0][0] + 2.5
plug = Part.makeBox(30, y1 - y0, 2.7, App.Vector(px, -y1, 5.0 + 1.6))             # Dupont 1x4 fis + kablo (yatay)
base, lid = load("main_base.step"), load("main_lid.step")
report("ANA", board, [("taban", base), ("kapak", lid)])
report("ANA fis", plug, [("taban", base), ("kapak", lid)])
print("[ANA] en yuksek parca z=%.2f, kapak alti z=13.0 -> pay %.2f mm" % (board.BoundBox.ZMax, 13.0 - board.BoundBox.ZMax))
board.exportStl(os.path.join(out, "main_with_parts.stl"))

# ---- SIPER ----
S = json.load(open(os.path.join(HERE, "dims_sensor.json")))
cxb, cyb = (S["board"][0] + S["board"][2]) / 2, (S["board"][1] + S["board"][3]) / 2
sb = load("sensor_with_parts.step")
sb.translate(App.Vector(-cxb, cyb, 0))                                            # kart merkezini eksene tasi (STEP Y = -y)
sb.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 180)                          # bilesen yuzu asagi
sb.translate(App.Vector(0, 0, 36.0))                                              # arka yuz z=36 (direk uclari)
shield = load("shield.step")
report("SIPER", sb, [("siper", shield)])
jp = S["parts"]["J1"]["pads"]; jx = (min(p[0] for p in jp) + max(p[0] for p in jp)) / 2 - cxb; jy = -(jp[0][1] - cyb)
plug2 = Part.makeBox(10.6, 3.2, 10.0, App.Vector(-jx - 5.3, jy - 1.6, 23.0))     # Dupont fisi (header uzerinde)
wire = Part.makeCylinder(3.0, 23.0, App.Vector(-jx, jy, 0))                       # kablo demeti alttan cikar
report("SIPER fis+kablo", plug2.fuse(wire), [("siper", shield)])
sb.exportStl(os.path.join(out, "sensor_with_parts.stl"))

# ---- NEGATIF KONTROL: kart bilerek 3 mm saga kaydirilinca cakisma CIKMALI (kontrol calisiyor mu?) ----
b2 = load("main_with_parts.step"); b2.translate(App.Vector(3.0 + 0.6 + 2.0, 0, 5.0))
v = b2.common(base).Volume
print("[KONTROL] karti duvara 5.6 mm kaydirinca cakisma hacmi: %.1f mm3 -> %s" % (v, "kontrol CALISIYOR" if v > 0.5 else "KONTROL ISE YARAMIYOR"))
