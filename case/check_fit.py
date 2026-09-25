"""freecadcmd check_fit.py : KiCad'den gelen parcali kart STEP'i ile kutuyu karsilastirir (cakisma, yukseklik payi)."""
import os, FreeCAD as App, Part
HERE = r"C:\Users\yavuz\Desktop\hava-istasyonu\case"
out = os.path.join(HERE, "out")
def load(n):
    s = Part.Shape(); s.read(os.path.join(out, n)); return s
board = load("board_with_parts.step")
base, lid = load("base.step"), load("lid.step")
bb = board.BoundBox
print("KiCad STEP sinirlari: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f" % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
# KiCad STEP: kart alt yuzu z=0. Kutuda kart tabani z=5.0 (FLOOR+POST_H)
board.translate(App.Vector(0, 0, 5.0))
board.exportStl(os.path.join(out, "board_with_parts.stl"))
bb = board.BoundBox
print("kutu icinde: Z %.2f..%.2f  (kapak alti z=16.0) -> en yuksek parca ile kapak arasi %.2f mm" % (bb.ZMin, bb.ZMax, 16.0 - bb.ZMax))
for name, sh in (("base", base), ("lid", lid)):
    v = board.common(sh).Volume
    print("kart+parcalar / %s cakisma hacmi: %.3f mm3 %s" % (name, v, "(TEMIZ)" if v < 0.01 else "(CAKISMA!)"))
    if v >= 0.01:
        c = board.common(sh); cb = c.BoundBox
        print("   cakisma bolgesi: X %.1f..%.1f Y %.1f..%.1f Z %.1f..%.1f" % (cb.XMin, cb.XMax, cb.YMin, cb.YMax, cb.ZMin, cb.ZMax))
