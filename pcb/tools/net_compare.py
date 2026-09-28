"""İki netlistin bağlantı olarak aynı olduğunu doğrular (parça, değer, footprint, net üyeleri)."""
import sys
import sch_gen as S


def load(p):
    tree = S.parse(open(p, encoding="utf8").read())
    comps = {S.kid(c, "ref")[1]: (S.kid(c, "value")[1], S.kid(c, "footprint")[1])
             for c in S.kids(S.kid(tree, "components"), "comp")}
    nets = {}
    for n in S.kids(S.kid(tree, "nets"), "net"):
        nodes = frozenset((S.kid(d, "ref")[1], S.kid(d, "pin")[1]) for d in S.kids(n, "node"))
        name = S.kid(n, "name")[1].lstrip("/")
        if len(nodes) > 1 or not name.startswith("unconnected-"):
            nets[name] = nodes
    return comps, nets


a, b = load(sys.argv[1]), load(sys.argv[2])
ok = True
if a[0] != b[0]:
    ok = False
    for r in sorted(set(a[0]) | set(b[0])):
        if a[0].get(r) != b[0].get(r):
            print("parça farkı:", r, a[0].get(r), "<>", b[0].get(r))
if a[1] != b[1]:
    ok = False
    for n in sorted(set(a[1]) | set(b[1])):
        if a[1].get(n) != b[1].get(n):
            print("net farkı:", n, sorted(a[1].get(n, ())), "<>", sorted(b[1].get(n, ())))
print("AYNI: %d parça, %d net" % (len(a[0]), len(a[1])) if ok else "FARKLI")
sys.exit(0 if ok else 1)
