"""hava.net -> fab/hava_bom.csv (JLCPCB BOM sutunlari). LCSC kodu bos = dogrulanmadi."""
import re, csv, os
from collections import defaultdict
t = open('hava.net', encoding='utf8').read()
blocks = re.findall(r'\(comp\s*\(ref "(\w+)"\)\s*\(value "([^"]*)"\).*?\(footprint "([^"]*)"\)', t, re.S)
groups = defaultdict(list)
for ref, val, fp in blocks:
    groups[(val, fp)].append(ref)
KNOWN = {  # web aramasinda katalogda gorulen, STOK/uygunluk dogrulanmadi
    'ESP32-C3-WROOM-02': 'C2934560 (N4 surumu; dogrulanmadi)',
    'AP2112K-3.3': 'C51118 (AP2112K-3.3TRG1; dogrulanmadi)',
}
def key(r): return (re.match(r'[A-Z]+', r).group(), int(re.search(r'\d+', r).group()))
os.makedirs('fab', exist_ok=True)
with open('fab/hava_bom.csv', 'w', newline='', encoding='utf8') as f:
    w = csv.writer(f)
    w.writerow(['Comment', 'Designator', 'Footprint', 'Quantity', 'LCSC Part #'])
    for (val, fp), refs in sorted(groups.items(), key=lambda kv: key(sorted(kv[1], key=key)[0])):
        refs = sorted(refs, key=key)
        w.writerow([val, ','.join(refs), fp.split(':')[-1], len(refs), KNOWN.get(val, '')])
print(open('fab/hava_bom.csv', encoding='utf8').read())
