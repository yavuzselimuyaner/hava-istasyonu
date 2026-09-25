"""STL -> PNG (ortografik, duz golgeleme, ressam algoritmasi). Blender yoksa kullanilir."""
import numpy as np, re, math, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")

def load(name):
    t = open(os.path.join(OUT, name + ".stl"), encoding="utf8", errors="ignore").read()
    v = np.array(re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", t), dtype=np.float64)
    return v.reshape(-1, 3, 3)

def render(parts, fname, az=35, el=32, size=(1500, 1050), lid_lift=0.0, screen=None, screen_z=17.0):
    tris, cols = [], []
    for name, col, dz in parts:
        T = load(name).copy(); T[:, :, 2] += dz
        tris.append(T); cols.append(np.tile(np.array(col, float), (len(T), 1)))
    T = np.concatenate(tris); C = np.concatenate(cols)
    a, e = math.radians(az), math.radians(el)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    R = Rx @ Rz
    P = T @ R.T                                   # x sag, y derinlik (+ uzak), z yukari
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
    L = np.array([-0.4, -0.6, 0.7]); L /= np.linalg.norm(L)
    inten = 0.35 + 0.65 * np.abs(n @ L)
    depth = P[:, :, 1].mean(axis=1)
    order = np.argsort(-depth)                    # uzaktan yakina
    xs, ys = P[:, :, 0], P[:, :, 2]
    pad = 40
    sx = (size[0] - 2 * pad) / (xs.max() - xs.min()); sy = (size[1] - 2 * pad) / (ys.max() - ys.min())
    s = min(sx, sy)
    px = (xs - xs.min()) * s + pad + ((size[0] - 2 * pad) - (xs.max() - xs.min()) * s) / 2
    py = size[1] - ((ys - ys.min()) * s + pad + ((size[1] - 2 * pad) - (ys.max() - ys.min()) * s) / 2)
    W, H = size
    zbuf = np.full((H, W), np.inf); rgb = np.full((H, W, 3), 245, dtype=np.uint8)
    dep = P[:, :, 1]
    for i in range(len(T)):
        x0, x1, x2 = px[i]; y0, y1, y2 = py[i]
        minx = max(int(math.floor(min(x0, x1, x2))), 0); maxx = min(int(math.ceil(max(x0, x1, x2))), W - 1)
        miny = max(int(math.floor(min(y0, y1, y2))), 0); maxy = min(int(math.ceil(max(y0, y1, y2))), H - 1)
        if minx > maxx or miny > maxy: continue
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(minx, maxx + 1) + 0.5, np.arange(miny, maxy + 1) + 0.5)
        l0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
        l1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not m.any(): continue
        z = l0 * dep[i, 0] + l1 * dep[i, 1] + l2 * dep[i, 2]
        sub = zbuf[miny:maxy + 1, minx:maxx + 1]
        upd = m & (z < sub)
        sub[upd] = z[upd]
        rgb[miny:maxy + 1, minx:maxx + 1][upd] = np.clip(C[i] * inten[i], 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb)
    if screen is not None:
        cx, cy, hf = 25.0, -31.0, 12.5
        world = np.array([[cx - hf, cy + hf, screen_z], [cx + hf, cy + hf, screen_z], [cx + hf, cy - hf, screen_z], [cx - hf, cy - hf, screen_z]])
        pr = world @ R.T
        offx = pad + ((size[0] - 2 * pad) - (xs.max() - xs.min()) * s) / 2
        offy = pad + ((size[1] - 2 * pad) - (ys.max() - ys.min()) * s) / 2
        dst = [((p[0] - xs.min()) * s + offx, size[1] - ((p[2] - ys.min()) * s + offy)) for p in pr]
        sw, sh = screen.size; src = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
        A = []; B = []
        for (x, y), (u, v) in zip(dst, src):            # hedef -> kaynak perspektif katsayilari
            A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
            A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
        coef = np.linalg.solve(np.array(A, float), np.array(B, float))
        warped = screen.convert("RGB").transform(size, Image.PERSPECTIVE, tuple(coef), Image.BILINEAR)
        mask = Image.new("L", size, 0); ImageDraw.Draw(mask).polygon(dst, fill=255)
        img = Image.composite(warped, img, mask)
    img.save(os.path.join(HERE, fname)); print("yazildi", fname, len(T), "ucgen")

BASE = (220, 220, 225); LIDC = (95, 115, 150); BRD = (30, 130, 70)
if __name__ == "__main__":
    import sys
    scr = None
    sp = os.path.join(HERE, "..", "firmware", "pc_demo", "screen.png")
    if os.path.exists(sp): scr = Image.open(sp)
    render([("base", BASE, 0), ("board_with_parts", BRD, 0), ("lid", LIDC, 0)], "kutu_kapali.png")
    render([("base", BASE, 0), ("board_with_parts", BRD, 0), ("lid", LIDC, 30)], "kutu_acik.png", az=30, el=38)
    render([("base", BASE, 0), ("board_with_parts", BRD, 0)], "kutu_ustten.png", az=0, el=89)
    if scr is not None:
        render([("base", BASE, 0), ("board_with_parts", BRD, 0), ("lid", LIDC, 0)], "gosterim_iso.png", az=25, el=48, screen=scr)
        render([("base", BASE, 0), ("board_with_parts", BRD, 0), ("lid", LIDC, 0)], "gosterim_ustten.png", az=0, el=89.5, screen=scr, size=(1100, 1300))
