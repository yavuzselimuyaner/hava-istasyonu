"""SKiDL netlistinden KiCad şematiği (.kicad_sch) üretir.

Sembolleri KiCad'in kendi kütüphanelerinden alır, her bacağa kısa bir tel ve net
etiketi koyar (güç netlerine güç sembolü), boş bacaklara "bağlantı yok" işareti koyar.
Parçaların yeri her kartın gen_schematic.py dosyasındaki GROUPS listesinden gelir.

Çıkan şematik KiCad'de açılır, ERC'den geçer ve PCB bu şematikten alınan
netlistten kurulur (akış: SKiDL -> şematik -> netlist -> PCB).
"""
import os
import re
import uuid

SYM_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
GRID = 1.27
STUB = 2.54
POWER_NETS = {"GND": "power:GND", "+3V3": "power:+3V3", "+5V": "power:+5V"}
CHAR_W = 1.0   # etiket metni için yaklaşık karakter genişliği (mm)


# ---------------------------------------------------------------- s-ifade
class Q(str):
    """Tırnaklı dize (yazarken tekrar tırnaklanır)."""


def parse(text):
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
        if tok.startswith('"'):
            return Q(tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        return tok

    return read()


def dump(node, ind=0):
    if not isinstance(node, list):
        if isinstance(node, Q):
            return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return str(node)
    if not any(isinstance(c, list) for c in node):
        return "(" + " ".join(dump(c) for c in node) + ")"
    pad = "\t" * (ind + 1)
    out = "(" + dump(node[0])
    for c in node[1:]:
        out += "\n" + pad + dump(c, ind + 1) if isinstance(c, list) else " " + dump(c)
    return out + "\n" + "\t" * ind + ")"


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    r = kids(node, name)
    return r[0] if r else None


_NS = uuid.UUID("5b1c6f0e-8a3d-4c55-9a51-6e2f3d8b7a10")
_uid_state = {"key": "", "n": 0}


def uid(name=None):
    """Tekrar üretimde aynı kalan UUID (şematik her üretildiğinde git farkı küçük kalsın,
    PCB'deki footprint -> sembol bağları değişmesin)."""
    if name is None:
        _uid_state["n"] += 1
        name = "#%d" % _uid_state["n"]
    return Q(str(uuid.uuid5(_NS, _uid_state["key"] + "/" + name)))


def num(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else repr(v)


def snap(v):
    return round(v / GRID) * GRID


# ---------------------------------------------------------------- kütüphane
_lib_text = {}


def _block(lib, name):
    """Kütüphane dosyasından tek bir sembol bloğunun metnini çıkarır."""
    if lib not in _lib_text:
        with open(os.path.join(SYM_DIR, lib + ".kicad_sym"), encoding="utf8") as f:
            _lib_text[lib] = f.read()
    text = _lib_text[lib]
    m = re.search(r'\n\t\(symbol "%s"\s' % re.escape(name), text)
    if not m:
        raise SystemExit("sembol yok: %s:%s" % (lib, name))
    i, depth, in_str = m.start() + 1, 0, False
    j = i
    while True:
        ch = text[j]
        if in_str:
            if ch == "\\":
                j += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
        j += 1


def load_symbol(lib, name):
    """'extends' zincirini açarak düz bir sembol döndürür (adı: ad, alt birimler ad_u_s)."""
    sym = parse(_block(lib, name))
    ext = kid(sym, "extends")
    if not ext:
        return sym
    parent = load_symbol(lib, ext[1])
    pname = parent[1]
    own = {p[1]: p for p in kids(sym, "property")}
    out = [sym[0], Q(name)]
    for c in parent[2:]:
        if isinstance(c, list) and c[0] == "property" and c[1] in own:
            continue
        if isinstance(c, list) and c[0] == "symbol":
            c = [c[0], Q(name + c[1][len(pname):])] + c[2:]
        out.append(c)
    # alt birimlerden önce çocuğun kendi özellikleri
    first_sub = next(i for i, c in enumerate(out) if isinstance(c, list) and c[0] == "symbol")
    for p in reversed(list(own.values())):
        out.insert(first_sub, p)
    return out


def pins_of(sym):
    """[(numara, ad, tip, x, y, açı)] — sembol koordinatında (Y yukarı)."""
    res = []
    for sub in kids(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", sub[1])
        if m and m.group(2) not in ("0", "1"):
            continue                      # De Morgan gövdesi
        for p in kids(sub, "pin"):
            at = kid(p, "at")
            res.append((kid(p, "number")[1], kid(p, "name")[1], p[1],
                        float(at[1]), float(at[2]), int(float(at[3]))))
    return res


def body_box(sym):
    xs, ys = [], []
    for sub in kids(sym, "symbol"):
        for g in sub:
            if not isinstance(g, list):
                continue
            if g[0] == "rectangle":
                for k in ("start", "end"):
                    xs.append(float(kid(g, k)[1])); ys.append(float(kid(g, k)[2]))
            elif g[0] == "polyline":
                for xy in kids(kid(g, "pts"), "xy"):
                    xs.append(float(xy[1])); ys.append(float(xy[2]))
            elif g[0] == "circle":
                c, r = kid(g, "center"), float(kid(g, "radius")[1])
                xs += [float(c[1]) - r, float(c[1]) + r]; ys += [float(c[2]) - r, float(c[2]) + r]
            elif g[0] == "pin":
                at = kid(g, "at")
                xs.append(float(at[1])); ys.append(float(at[2]))
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (-1, -1, 1, 1)


# Bacak açısı -> bacak ucundan dışarı yön (ekran koordinatı, Y aşağı)
OUT_DIR = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}


# ---------------------------------------------------------------- netlist
def read_netlist(path):
    tree = parse(open(path, encoding="utf8").read())
    comps = {}
    for c in kids(kid(tree, "components"), "comp"):
        ls = kid(c, "libsource")
        comps[kid(c, "ref")[1]] = dict(
            value=kid(c, "value")[1], footprint=kid(c, "footprint")[1],
            lib=kid(ls, "lib")[1], part=kid(ls, "part")[1])
    pin_net = {}
    for n in kids(kid(tree, "nets"), "net"):
        for nd in kids(n, "node"):
            pin_net[(kid(nd, "ref")[1], kid(nd, "pin")[1])] = kid(n, "name")[1]
    return comps, pin_net


# ---------------------------------------------------------------- şematik
class Sheet:
    def __init__(self, project, title, paper="A3", board_key=""):
        self.project, self.title, self.paper = project, title, paper
        # UUID'ler başlığa değil kart klasörüne bağlı: başlık değişince PCB bağları kopmasın
        _uid_state.update(key=project + "/" + board_key, n=0)
        self.root = uid("root")
        self.lib = {}
        self.items = []
        self.pwr_n = 0

    def _lib_id(self, lib, name):
        lid = "%s:%s" % (lib, name)
        if lid not in self.lib:
            s = load_symbol(lib, name)
            s[1] = Q(lid)
            self.lib[lid] = s
        return lid

    def symbol(self, lib, name, ref, value, x, y, rot=0, footprint="", fields=None):
        lid = self._lib_id(lib, name)
        sym = self.lib[lid]
        props = []
        for p in kids(sym, "property"):
            key = p[1]
            val = {"Reference": ref, "Value": value, "Footprint": footprint}.get(key, p[2])
            at = kid(p, "at")
            px, py = float(at[1]), float(at[2])
            if fields and key in fields:
                px, py = fields[key]
            np = [p[0], Q(key), Q(val), ["at", num(x + px), num(y - py), at[3] if len(at) > 3 else "0"]]
            np += [c for c in p[3:] if isinstance(c, list) and c[0] in ("hide", "effects")]
            props.append(np)
        pins = sorted({pn[0] for pn in pins_of(sym)})
        self.items.append(
            ["symbol", ["lib_id", Q(lid)], ["at", num(x), num(y), str(rot)], ["unit", "1"],
             ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"],
             ["uuid", uid("sym/" + ref)]] + props +
            [["pin", Q(p), ["uuid", uid("pin/%s/%s" % (ref, p))]] for p in pins] +
            [["instances", ["project", Q(self.project),
                            ["path", Q("/" + self.root), ["reference", Q(ref)], ["unit", "1"]]]]])
        return sym

    def power(self, net, x, y, out):
        """Güç sembolü; gövdesi bacaktan dışarı doğru bakar."""
        lib, name = POWER_NETS[net].split(":") if net in POWER_NETS else ("power", "PWR_FLAG")
        down = name in ("GND",)
        rot = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[out] if down else \
              {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[out]
        self.pwr_n += 1
        ref = "#PWR%02d" % self.pwr_n if name != "PWR_FLAG" else "#FLG%02d" % self.pwr_n
        lid = self._lib_id(lib, name)
        sym = self.lib[lid]
        props = []
        # Değer metnini sembolün gövdesinin ötesine koy
        d = 5.08 if down else 3.81
        tx, ty = x + out[0] * d, y + out[1] * d
        for p in kids(sym, "property"):
            key = p[1]
            val = {"Reference": ref}.get(key, p[2])
            np = [p[0], Q(key), Q(val), ["at", num(tx), num(ty), "0"]]
            hide = key != "Value"
            if hide:
                np.append(["hide", "yes"])
            np.append(["effects", ["font", ["size", "1.27", "1.27"]]])
            props.append(np)
        self.items.append(
            ["symbol", ["lib_id", Q(lid)], ["at", num(x), num(y), str(rot)], ["unit", "1"],
             ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"],
             ["uuid", uid()]] + props + [["pin", Q("1"), ["uuid", uid()]]] +
            [["instances", ["project", Q(self.project),
                            ["path", Q("/" + self.root), ["reference", Q(ref)], ["unit", "1"]]]]])

    def wire(self, x1, y1, x2, y2):
        self.items.append(["wire", ["pts", ["xy", num(x1), num(y1)], ["xy", num(x2), num(y2)]],
                           ["stroke", ["width", "0"], ["type", "default"]], ["uuid", uid()]])

    def label(self, net, x, y, out):
        ang, just = {(-1, 0): (180, "right"), (1, 0): (0, "left"),
                     (0, -1): (90, "left"), (0, 1): (270, "right")}[out]
        self.items.append(["label", Q(net), ["at", num(x), num(y), str(ang)],
                           ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", just, "bottom"]],
                           ["uuid", uid()]])

    def junction(self, x, y):
        self.items.append(["junction", ["at", num(x), num(y)], ["diameter", "0"],
                           ["color", "0", "0", "0", "0"], ["uuid", uid()]])

    def no_connect(self, x, y):
        self.items.append(["no_connect", ["at", num(x), num(y)], ["uuid", uid()]])

    def text(self, s, x, y, size=2.0, bold=True):
        font = ["font", ["size", num(size), num(size)]] + ([["bold", "yes"]] if bold else [])
        self.items.append(["text", Q(s), ["exclude_from_sim", "no"], ["at", num(x), num(y), "0"],
                           ["effects", font, ["justify", "left", "bottom"]], ["uuid", uid()]])

    def frame(self, x1, y1, x2, y2):
        self.items.append(["rectangle", ["start", num(x1), num(y1)], ["end", num(x2), num(y2)],
                           ["stroke", ["width", "0"], ["type", "dash"]], ["fill", ["type", "none"]],
                           ["uuid", uid()]])

    def save(self, path, date="", rev="", comments=()):
        tb = ["title_block", ["title", Q(self.title)], ["date", Q(date)], ["rev", Q(rev)]]
        for i, c in enumerate(comments, 1):
            tb.append(["comment", str(i), Q(c)])
        doc = (["kicad_sch", ["version", "20250610"], ["generator", Q("eeschema")],
                ["generator_version", Q("9.99")], ["uuid", self.root], ["paper", Q(self.paper)], tb,
                ["lib_symbols"] + list(self.lib.values())] + self.items +
               [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]])
        with open(path, "w", encoding="utf8", newline="\n") as f:
            f.write(dump(doc) + "\n")


UP_POWER = {"+3V3", "+5V"}          # gövdesi yukarı bakan güç sembolleri (GND aşağı bakar)


def plan_pins(sym, ref, pin_net, texts=()):
    """Bir parçanın bacakları için çizim listesi (sembol merkezine göre, ekran koordinatı).
    Güç netleri mümkünse dik duran güç sembolüyle, sığmazsa net etiketiyle gösterilir;
    aynı taraftaki komşu bacaklar aynı güç netindeyse tek sembolde birleştirilir."""
    pins = {}
    for pnum, _, _, px, py, a in pins_of(sym):
        key = (px, -py)
        net = pin_net.get((ref, pnum))
        if key in pins:               # üst üste binmiş bacaklar (USB-C GND/VBUS)
            if net and pins[key][1] and net != pins[key][1]:
                raise SystemExit("ayni noktada farkli net: %s %s" % (ref, pnum))
            if net:
                pins[key] = (pins[key][0], net)
            continue
        pins[key] = (OUT_DIR[a], net)

    acts, done = [], set()
    for (x, y), (out, net) in sorted(pins.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if (x, y) in done:
            continue
        done.add((x, y))
        if not net:
            acts.append(("nc", x, y))
            continue
        ex, ey = x + out[0] * STUB, y + out[1] * STUB
        acts.append(("wire", x, y, ex, ey))
        if net not in POWER_NETS:
            acts.append(("label", net, ex, ey, out))
            continue
        up = net in UP_POWER
        want = (0, -1) if up else (0, 1)
        if out[0] == 0 and out != want:   # dikey ama sembol ters dönerdi: etiket
            acts.append(("label", net, ex, ey, out))
            continue
        # Aynı taraftaki en yakın komşu (en fazla 5,08 mm) aynı netteyse tek sembolde birleşir
        ax = 1 if out[0] else 0           # yatay bacaklar y boyunca, dikeyler x boyunca dizilir
        run = [(x, y)]
        while True:
            cur = run[-1]
            cand = [k for k, v in pins.items() if v[0] == out and abs(k[ax ^ 1] - cur[ax ^ 1]) < 1e-6
                    and 1e-6 < k[ax] - cur[ax] <= 5.08 + 1e-6]
            nb = min(cand, key=lambda k: k[ax]) if cand else None
            if not nb or pins[nb][1] != net:
                break
            run.append(nb); done.add(nb)
        acts.pop()                        # ilk bacağın kısa teli aşağıda yeniden çizilir
        if out[0] == 0:                   # dikey: sembol zaten dışarı bakıyor
            ends = [(rx + out[0] * STUB, ry + out[1] * STUB) for rx, ry in run]
            for (rx, ry), (qx, qy) in zip(run, ends):
                acts.append(("wire", rx, ry, qx, qy))
            for p1, p2 in zip(ends, ends[1:]):
                acts.append(("wire", p1[0], p1[1], p2[0], p2[1]))
            acts.append(("power", net, ends[0][0], ends[0][1], want))
            continue
        # yatay: sembol yukarı (+V) ya da aşağı (GND) bakar; o yönde 7,62 mm içinde aynı
        # tarafta başka bacak varsa sembol onun yazısına çarpar -> etiket
        end_y = run[0][1] if up else run[-1][1]
        sgn = -1 if up else 1
        blocked = any(abs(k[0] - x) < 1e-6 and v[0] == out and 0 < (k[1] - end_y) * sgn <= 7.62
                      for k, v in pins.items())
        if blocked:
            for (rx, ry) in run:
                acts.append(("wire", rx, ry, rx + out[0] * STUB, ry))
                acts.append(("label", net, rx + out[0] * STUB, ry, out))
            continue
        # tel en az iki kat uzun; sembol bir yazıya çarpıyorsa çarpmayana kadar uzat
        k = 2
        while k < 8:
            fx = x + out[0] * k * STUB
            sb = (fx - 2.5, end_y - 6.5, fx + 2.5, end_y) if up else (fx - 2.5, end_y, fx + 2.5, end_y + 6.5)
            if not any(sb[0] < t[2] and t[0] < sb[2] and sb[1] < t[3] and t[1] < sb[3] for t in texts):
                break
            k += 1
        for (rx, ry) in run:
            acts.append(("wire", rx, ry, fx, ry))
        for (_, y1), (_, y2) in zip(run, run[1:]):
            acts.append(("wire", fx, y1, fx, y2))
        acts.append(("power", net, fx, end_y, want))
    # 3 ya da daha fazla bağlantının buluştuğu tel uçlarına kavşak noktası
    ends = {}
    for w in acts:
        if w[0] == "wire":
            for pt in (w[1:3], w[3:5]):
                k = (round(pt[0], 3), round(pt[1], 3))
                ends[k] = ends.get(k, 0) + 1
    for w in acts:
        if w[0] == "power":
            k = (round(w[2], 3), round(w[3], 3))
            if k in ends:
                ends[k] += 1
    acts += [("junction", x, y) for (x, y), n in ends.items() if n >= 3]
    return acts


def _text_box(x, y, s, ang, just, size=1.27):
    w, h = len(s) * CHAR_W * size / 1.27, size
    if ang in (90, 270):
        return (x - h, y - w / 2 if just == "center" else y - w, x + h, y + (w / 2 if just == "center" else w))
    if just == "left":
        return (x, y - h, x + w, y + h / 2)
    if just == "right":
        return (x - w, y - h, x, y + h / 2)
    return (x - w / 2, y - h, x + w / 2, y + h / 2)


def part_extent(sym, acts, props):
    """Parçanın gövde, yazı, tel, etiket ve güç sembolleriyle kapladığı alan (ekran, merkeze göre)."""
    x0, y0, x1, y1 = body_box(sym)
    boxes = [(x0, -y1, x1, -y0)]
    for px, py, ang, just, hidden, text in props.values():
        if not hidden:
            boxes.append(_text_box(px, -py, text, ang, just))
    for a in acts:
        if a[0] == "wire":
            boxes.append((min(a[1], a[3]), min(a[2], a[4]), max(a[1], a[3]), max(a[2], a[4])))
        elif a[0] == "nc":
            boxes.append((a[1] - 1, a[2] - 1, a[1] + 1, a[2] + 1))
        elif a[0] == "label":
            _, net, x, y, out = a
            w = len(net) * CHAR_W + 1
            ex, ey = x + out[0] * w, y + out[1] * w
            boxes.append((min(x, ex) - 1.3, min(y, ey) - 1.3, max(x, ex) + 1.3, max(y, ey) + 1.3))
        elif a[0] == "power":
            _, net, x, y, out = a
            ex, ey = x + out[0] * 6.5, y + out[1] * 6.5
            boxes.append((min(x, ex) - 2.5, min(y, ey), max(x, ex) + 2.5, max(y, ey)))
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _props(sym, ref, value):
    res = {}
    for p in kids(sym, "property"):
        at = kid(p, "at")
        eff = kid(p, "effects") or []
        j = kid(eff, "justify") or []
        just = "left" if "left" in j else "right" if "right" in j else "center"
        hidden = kid(p, "hide") is not None or "hide" in eff
        text = {"Reference": ref, "Value": value}.get(p[1], p[2])
        res[p[1]] = (float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0,
                     just, hidden, text)
    return res


def _group(sh, comps, pin_net, gtitle, gx, gy, rows, placed, used_pins):
    cy = gy + 8
    gw = 0
    for row in rows:
        info = {}
        for ref in row:
            c = comps[ref]
            sym = load_symbol(c["lib"], c["part"])
            props = _props(sym, ref, c["value"])
            texts = [_text_box(px, -py, t, ang, j) for px, py, ang, j, hid, t in props.values() if not hid]
            acts = plan_pins(sym, ref, pin_net, texts)
            info[ref] = (sym, acts, part_extent(sym, acts, props))
        row_h = max(e[3] - e[1] for _, _, e in info.values())
        cx = gx + 5
        for ref in row:
            c = comps[ref]
            sym, acts, (l, t, r, b) = info[ref]
            sx, sy = snap(cx - l), snap(cy - t + (row_h - (b - t)) / 2)
            sh.symbol(c["lib"], c["part"], ref, c["value"], sx, sy, footprint=c["footprint"])
            for pnum, *_ in pins_of(sym):
                if (ref, pnum) in pin_net:
                    used_pins.add((ref, pnum))
            for a in acts:
                k = a[0]
                if k == "nc":
                    sh.no_connect(sx + a[1], sy + a[2])
                elif k == "wire":
                    sh.wire(sx + a[1], sy + a[2], sx + a[3], sy + a[4])
                elif k == "junction":
                    sh.junction(sx + a[1], sy + a[2])
                elif k == "label":
                    sh.label(a[1], sx + a[2], sy + a[3], a[4])
                elif k == "power":
                    sh.power(a[1], sx + a[2], sy + a[3], a[4])
            placed.add(ref)
            cx = sx + r + 7
        gw = max(gw, cx - gx)
        cy += row_h + 5
    gw = max(gw, len(gtitle) * 1.6 + 8)
    sh.text(gtitle, gx + 2, gy + 5)
    sh.frame(gx, gy, snap(gx + gw), snap(cy))
    return snap(gw), snap(cy - gy)


def build(net_path, out_path, project, title, columns, paper="A4", flags=(), flags_col=0,
          comments=(), date=""):
    """columns: [[(başlık, [[ref, ...], ...]), ...], ...] — sütunlar, her sütunda alt alta
    gruplar, her grupta satırlar. flags: PWR_FLAG konacak netler (ERC için: güç pasif bir
    bacaktan, örn. USB konnektöründen giriyorsa)."""
    comps, pin_net = read_netlist(net_path)
    sh = Sheet(project, title, paper, board_key=os.path.basename(os.path.dirname(os.path.abspath(out_path))))
    placed, used_pins = set(), set()
    x = 15.24
    for ci, col in enumerate(columns):
        y, colw = 15.24, 0
        for gtitle, rows in col:
            w, h = _group(sh, comps, pin_net, gtitle, x, y, rows, placed, used_pins)
            colw = max(colw, w)
            y += h + 7.62
        if flags and ci == flags_col:
            # PWR_FLAG: "bu net bir kaynaktan besleniyor" işareti (güç USB'nin pasif
            # bacağından girdiği için ERC bunu ister); elektriksel olarak bir şey eklemez
            fx, top = x + 10.16, snap(y + 12)
            for net in flags:
                bot = top + STUB
                sh.wire(fx, top, fx, bot)
                if net == "GND":
                    sh.power("__FLAG__", fx, top, (0, -1)); sh.power(net, fx, bot, (0, 1))
                else:
                    sh.power(net, fx, top, (0, -1)); sh.power("__FLAG__", fx, bot, (0, 1))
                fx += 17.78
            gw = max(fx - x, 45)
            sh.text("ERC power flags", x + 2, y + 5)
            sh.frame(x, y, snap(x + gw), snap(bot + 10))
        x = snap(x + colw + 7.62)
    missing = set(comps) - placed
    if missing:
        raise SystemExit("yerleşmeyen parça: %s" % sorted(missing))
    lost = set(pin_net) - used_pins
    if lost:
        raise SystemExit("şematikte karşılığı olmayan bacak: %s" % sorted(lost))
    sh.save(out_path, date=date, comments=comments)
    return sh
