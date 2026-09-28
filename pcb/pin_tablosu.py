"""Sematikten alinan netlistten (pcb/*/hava.net) pin -> net tablosu uretir: docs/tasarim/03-pin-tablosu.md
Datasheet'lerle karsilastirmak icin. Pin isimleri KiCad sembol dosyalarindan okunur."""
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYM = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"


def sexpr(text):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    pos = 0

    def read():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == "(":
            lst = []
            while toks[pos] != ")":
                lst.append(read())
            pos += 1
            return lst
        return t[1:-1] if t.startswith('"') else t
    return read()


def find_all(n, name):
    return [c for c in n if isinstance(c, list) and c and c[0] == name]


def find(n, name):
    r = find_all(n, name)
    return r[0] if r else None


def load_net(path):
    tree = sexpr(open(path, encoding="utf8").read())
    comps = {}
    for c in find_all(find(tree, "components"), "comp"):
        comps[find(c, "ref")[1]] = find(c, "value")[1]
    pin_net = {}
    for n in find_all(find(tree, "nets"), "net"):
        name = find(n, "name")[1].lstrip("/")      # KiCad yerel etiketleri "/AD" diye yazar
        if name.startswith("unconnected-"):
            continue                                  # boş bacak (şematikte "bağlantı yok" işareti)
        for nd in find_all(n, "node"):
            pin_net[(find(nd, "ref")[1], find(nd, "pin")[1])] = name
    return comps, pin_net


def sym_pins(lib, name):
    t = open(os.path.join(SYM, lib + ".kicad_sym"), encoding="utf8").read()
    i = t.index('(symbol "%s"' % name)
    j = t.find('\n\t(symbol "', i + 10)
    blk = t[i:j if j > 0 else len(t)]
    d = {}
    for nm, num in re.findall(r'\(name "([^"]*)".*?\(number "([^"]*)"', blk, re.S):
        d[num] = nm
    return d


def table(ref, comps, pin_net, names, only_used=False):
    pins = sorted({p for (r, p) in pin_net if r == ref}, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x))
    rows = []
    for p in pins:
        rows.append("| %s | %s | %s |" % (p, names.get(p, ""), pin_net[(ref, p)]))
    return "| Pin | Adı (sembol) | Bağlı olduğu net |\n|---|---|---|\n" + "\n".join(rows)


out = ["# Pin tablosu (karttan otomatik üretildi)",
       "",
       "Bu tablo, şematikten (`pcb/*/hava.kicad_sch`) alınan `pcb/*/hava.net` dosyasından üretildi (`pcb/pin_tablosu.py`). Datasheet'lerdeki pin tablolarıyla karşılaştırma için: pin numarası, ad ve bağlı olduğu net. Karşılaştırma sonuçları `02-datasheet-denetimi.md` içinde.",
       "Net adları: `+3V3`, `+5V`, `GND` güç hatları; `I2C_SDA/SCL` sensör; `USB_DP/DM` USB; `EN`, `BOOT` reset ve boot.",
       ""]
comps, pn = load_net(os.path.join(ROOT, "pcb", "main", "hava.net"))
out += ["## Ana kart", ""]
out += ["### U1 — ESP32-C3-WROOM-02 (karşılaştır: modül datasheet'i pin tablosu; çip datasheet'i Tablo 3-3 boot)", "", table("U1", comps, pn, sym_pins("RF_Module", "ESP32-C3-WROOM-02")), ""]
out += ["Strapping kontrolü: **IO2 (pin 16)** ve **IO8 (pin 7)** birer 10 kΩ ile +3V3'e, **IO9 (pin 8)** BOOT hattına (10 kΩ pull-up + buton) bağlı olmalı. Tablodaki `IO2_PU` ve `IO8_PU` netleri R8 ve R9 dirençlerinin diğer ucudur; aşağıdaki direnç tablosunda R8/R9 satırlarında pin 1 = +3V3 görmelisin.", ""]
u2 = {"1": "VIN", "2": "GND", "3": "EN", "5": "VOUT"}
out += ["### U2 — AP2112K-3.3 (karşılaştır: AP2112 datasheet 'Pin Descriptions', SOT25)", "", table("U2", comps, pn, u2), ""]
out += ["### U4 — USBLC6-2SC6 (USB koruması)", "", table("U4", comps, pn, {"1": "I/O1", "2": "GND", "3": "I/O2", "4": "I/O2", "5": "VBUS", "6": "I/O1"}), ""]
out += ["### J2 — sensör konnektörü (4 pin)", "", table("J2", comps, pn, {"1": "1", "2": "2", "3": "3", "4": "4"}), ""]
out += ["### J1 — USB-C (CC1/CC2 pinleri her biri 5,1 kΩ ile GND'ye bağlı olmalı)", "", table("J1", comps, pn, {}), ""]
out += ["### Dirençler ve kondansatörler (değer → bağlı net çiftleri)", "", "| Ref | Değer | Pin 1 | Pin 2 |", "|---|---|---|---|"]
for ref in sorted((r for r in comps if re.match(r"[RC]\d+$", r)), key=lambda r: (r[0], int(r[1:]))):
    out.append("| %s | %s | %s | %s |" % (ref, comps[ref], pn.get((ref, "1"), ""), pn.get((ref, "2"), "")))
out.append("")

comps2, pn2 = load_net(os.path.join(ROOT, "pcb", "sensor", "hava.net"))
out += ["## Sensör kartı", ""]
out += ["### U1 — BME280 (karşılaştır: Bosch datasheet Bölüm 7, Tablo 35 ve Şekil 17)", "", table("U1", comps2, pn2, sym_pins("Sensor", "BME280")), ""]
out += ["Beklenen (I2C): **CSB → +3V3**, **SDO → GND** (adres 0x76), VDD ve VDDIO ikisi de +3V3, iki pin GND.", ""]
out += ["### J1 — sensör konnektörü (ana kartın J2'si ile aynı sırada olmalı)", "", table("J1", comps2, pn2, {"1": "1", "2": "2", "3": "3", "4": "4"}), ""]
out += ["### Kondansatörler", "", "| Ref | Değer | Pin 1 | Pin 2 |", "|---|---|---|---|"]
for ref in sorted((r for r in comps2 if re.match(r"C\d+$", r)), key=lambda r: int(r[1:])):
    out.append("| %s | %s | %s | %s |" % (ref, comps2[ref], pn2.get((ref, "1"), ""), pn2.get((ref, "2"), "")))
out.append("")
open(os.path.join(ROOT, "docs", "tasarim", "03-pin-tablosu.md"), "w", encoding="utf8").write("\n".join(out))
print("yazildi, satir:", len(out))
