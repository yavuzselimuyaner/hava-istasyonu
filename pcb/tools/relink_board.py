"""KiCad python ile çalıştır: relink_board.py <kart klasörü>
Şematik yeniden üretildiğinde, yolları çizilmiş kartı yeniden yönlendirmeden footprint'leri
şematikteki sembollere (hava.net içindeki kimliklere) yeniden bağlar."""
import os
import sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sch_gen as S

d = os.path.abspath(sys.argv[1])
tree = S.parse(open(os.path.join(d, "hava.net"), encoding="utf8").read())
ids = {S.kid(c, "ref")[1]: S.kid(c, "tstamps")[1] for c in S.kids(S.kid(tree, "components"), "comp")}
for name in ("hava.kicad_pcb", "hava_routed.kicad_pcb"):
    path = os.path.join(d, name)
    board = pcbnew.LoadBoard(path)
    n = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in ids:
            raise SystemExit("şematikte yok: " + ref)
        fp.SetPath(pcbnew.KIID_PATH("/" + ids[ref]))
        n += 1
    if n != len(ids):
        raise SystemExit("footprint sayısı şematikle uyuşmuyor")
    pcbnew.SaveBoard(path, board)
    print(name, "yeniden bağlandı:", n)
