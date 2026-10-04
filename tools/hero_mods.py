"""Retoques de píxel-art para convertir el punk del pack en nuestro héroe:
pelo rizado y alborotado, gafas de pasta, más grueso/barrigón, menos musculado y algo más alto.
Se aplica frame a frame (solo a los frames de pie; los de caída se dejan como están)."""
import random
from PIL import Image

SKIN = {(0xd7, 0x7e, 0x4b), (0x9c, 0x5c, 0x37), (0xff, 0xb1, 0x64), (0xff, 0xb6, 0x6b)}
HAIR = [(0x34, 0x30, 0x38), (0x5a, 0x40, 0x30), (0x20, 0x1e, 0x28)]
HAIR_SET = set(HAIR)
GLASS, LENS = (0x0c, 0x0c, 0x10, 255), (0xb8, 0xd0, 0xe8, 255)
H, W = 63, 96
TALL = 1.10


def _bbox_top(px):
    for y in range(H):
        for x in range(W):
            if px[x, y][3]:
                return y
    return 0


def curly_hair_and_glasses(img, seed):
    rnd = random.Random(seed)
    px = img.load()
    y0 = _bbox_top(px)
    # 1) quitar la cresta (pelo oscuro en la zona de la cabeza)
    for y in range(y0, y0 + 14):
        for x in range(W):
            if px[x, y][3] and px[x, y][:3] in HAIR_SET:
                px[x, y] = (0, 0, 0, 0)
    # 2) localizar la cara
    pts = [(x, y) for y in range(y0, y0 + 13) for x in range(W) if px[x, y][3] and px[x, y][:3] in SKIN]
    if not pts:
        return
    xs = sorted(p[0] for p in pts)
    mx = xs[len(xs) // 2]
    pts = [p for p in pts if abs(p[0] - mx) <= 5]
    fl, fr = min(p[0] for p in pts), max(p[0] for p in pts)
    ft = min(p[1] for p in pts)
    # ojo original (pixel oscuro rodeado de piel): referencia para las gafas
    eye = None
    for y in range(ft + 1, ft + 8):
        for x in range(fl, fr + 1):
            if px[x, y][3] and px[x, y][:3] == (0x16, 0x14, 0x1c) and px[x, y + 1][3] and px[x, y + 1][:3] in SKIN:
                eye = (x, y)
                break
        if eye:
            break
    ex, ey = eye if eye else (fl + 1, ft + 3)
    cx = (fl + fr) / 2 + 1.5
    rx, ry = (fr - fl) / 2 + 3.5, 3.6
    cy = ft - 0.5
    # 3) melena rizada: elipse ancha con rizos (bultos) y volumen hacia la nuca
    for y in range(ft - 6, ft + 8):
        for x in range(fl - 5, fr + 7):
            if not (0 <= x < W and 0 <= y < H):
                continue
            dx, dy = (x - cx) / rx, (y - cy) / ry
            bump = rnd.choice((0.0, 0.0, 0.15, 0.3)) if y < ft + 1 else 0.0
            inside = dx * dx + dy * dy <= 1.0 + bump
            behind = x >= cx - 0.5 and y < ft + 7 and dx * dx + (dy * 0.5) ** 2 <= 1.2
            if not (inside or behind):
                continue
            cur = px[x, y]
            if cur[3] and cur[:3] in SKIN and (y > ey - 2 or x < cx - 3):
                continue                  # la cara (frente incluida hasta las gafas) queda visible
            r = rnd.random()
            col = HAIR[2] if dy > 0.3 else (HAIR[1] if r < 0.25 else (HAIR[2] if r < 0.5 else HAIR[0]))
            px[x, y] = col + (255,)
    # 4) gafas de pasta (montura gruesa)
    gx = ex - 1
    for x in range(gx, gx + 4):
        px[x, ey - 1] = GLASS
    for x, c in zip(range(gx, gx + 4), (GLASS, LENS, LENS, GLASS)):
        px[x, ey] = c
    for x in range(gx, gx + 4):
        if px[x, ey + 1][3]:
            px[x, ey + 1] = GLASS if x in (gx, gx + 3) else px[x, ey + 1]
    for x in range(gx + 4, gx + 7):      # patilla
        if px[x, ey][3] and px[x, ey][:3] in SKIN:
            px[x, ey] = GLASS


def flatten_muscle(img):
    px = img.load()
    y0 = _bbox_top(px)
    for y in range(y0 + 12, y0 + 34):
        for x in range(W):
            p = px[x, y]
            if p[3] and p[:3] == (0x9c, 0x5c, 0x37):
                px[x, y] = (0xd7, 0x7e, 0x4b, 255)
            elif p[3] and p[:3] in ((0xff, 0xb6, 0x6b), (0xff, 0xb1, 0x64)):
                px[x, y] = (0xe6, 0x92, 0x58, 255)   # sin brillos de músculo


def fatten(img):
    """Barriga y torso más anchos (escala horizontal por filas, anclada a la espalda)."""
    px = img.load()
    y0 = _bbox_top(px)
    top = y0 + 12
    rows = range(y0 + 12, 63)
    pts = [x for y in range(top + 2, top + 16) for x in range(W) if px[x, y][3]]
    if not pts:
        return img
    pivot = sum(pts) / len(pts) + 4
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    po = out.load()
    for y in range(H):
        t = y - top
        if y < top:
            s = 1.0
        elif t < 22:
            s = 1.0 + 0.38 * (1 - abs(t - 10) / 12.0) if t < 22 else 1.0
            s = max(1.12, s)
        else:
            s = 1.12 if y < 54 else 1.05
        for x in range(W):
            sx = int(round(pivot + (x - pivot) / s))
            if 0 <= sx < W:
                po[x, y] = px[sx, y]
    return out


def taller(img):
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    px, po = img.load(), out.load()
    for y in range(H):
        sy = int(round(62 - (62 - y) / TALL))
        if 0 <= sy < H:
            for x in range(W):
                po[x, y] = px[x, sy]
    return out


def hero_frame(img, seed):
    img = img.copy()
    flatten_muscle(img)
    curly_hair_and_glasses(img, seed)
    img = fatten(img)
    return taller(img)
