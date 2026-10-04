"""Genera el arte del menu de inicio: assets/ui/portrait.png (retrato pixel-art 160x224, mitad de pantalla),
assets/ui/title.png (MYTHIC STREETS) y assets/ui/button.png (boton START, 2 frames).
Uso: python tools/make_menu_art.py   (necesita tools/menu_portrait_src.jpg)"""
import os, sys
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'ui')
os.makedirs(OUT, exist_ok=True)

# ---------------- retrato ----------------
src = Image.open(os.path.join(HERE, 'menu_portrait_src.jpg')).convert('RGB')
W, H = src.size
ch = H
cw = int(ch * 160 / 224)
cx0 = int(W * 0.08)
src = src.crop((cx0, 0, cx0 + cw, ch))
src = ImageEnhance.Contrast(src).enhance(1.25)
src = ImageEnhance.Color(src).enhance(1.15)
src = ImageEnhance.Brightness(src).enhance(1.12)
small = src.resize((160, 224), Image.LANCZOS)
small = small.filter(ImageFilter.UnsharpMask(radius=1, percent=60, threshold=2))
# paleta limitada + tramado ordenado (Bayer 4x4) para el aspecto pixel-art
pal = small.quantize(colors=22, method=Image.MEDIANCUT, dither=Image.NONE)
palette = np.array(pal.getpalette()[:22 * 3], dtype=np.float32).reshape(-1, 3)
arr = np.asarray(small, dtype=np.float32)
bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0 - 0.5
th = np.tile(bayer, (224 // 4, 160 // 4))[..., None] * 26.0
a2 = np.clip(arr + th, 0, 255)
d = ((a2[:, :, None, :] - palette[None, None, :, :]) ** 2).sum(-1)
idx = d.argmin(-1)
rgb = palette[idx].astype(np.uint8)
alpha = np.full((224, 160), 255, dtype=np.uint8)
# desvanecido del borde derecho (tramado) para fundirlo con el fondo
fade = 30
for x in range(160 - fade, 160):
    p = (x - (160 - fade)) / fade
    cut = (bayer[:, x % 4][np.arange(224) % 4] + 0.5)
    alpha[:, x] = np.where(cut >= p, 255, 0)
Image.fromarray(np.dstack([rgb, alpha]), 'RGBA').save(os.path.join(OUT, 'portrait.png'))

# ---------------- fuente 5x7 ----------------
G = {
 'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
 'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
 'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
 'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
 'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
 'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
 'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
 'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
 'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
 'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
}


def text_mask(txt, scale, gap):
    cols = []
    w = len(txt) * (5 * scale + gap) - gap
    m = np.zeros((7 * scale, w), dtype=bool)
    x = 0
    for chn in txt:
        if chn != ' ':
            for r, row in enumerate(G[chn]):
                for c, ch_ in enumerate(row):
                    if ch_ == '#':
                        m[r * scale:(r + 1) * scale, x + c * scale:x + (c + 1) * scale] = True
        x += 5 * scale + gap
    return m


def dilate(m, n=1):
    out = m.copy()
    for _ in range(n):
        o = out.copy()
        o[1:, :] |= out[:-1, :]; o[:-1, :] |= out[1:, :]; o[:, 1:] |= out[:, :-1]; o[:, :-1] |= out[:, 1:]
        o[1:, 1:] |= out[:-1, :-1]; o[:-1, :-1] |= out[1:, 1:]; o[1:, :-1] |= out[:-1, 1:]; o[:-1, 1:] |= out[1:, :-1]
        out = o
    return out


def shift(m, dx, dy):
    o = np.zeros_like(m)
    h, w = m.shape
    o[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return o


def render(txt, scale, gap, colors, pad=4, depth=3, outline=(0x10, 0x08, 0x18), extrude=(0x6a, 0x10, 0x20)):
    m = text_mask(txt, scale, gap)
    h, w = m.shape
    Wc, Hc = w + pad * 2 + depth, h + pad * 2 + depth
    big = np.zeros((Hc, Wc), dtype=bool)
    big[pad:pad + h, pad:pad + w] = m
    img = np.zeros((Hc, Wc, 4), dtype=np.uint8)
    ext = np.zeros_like(big)
    for k in range(1, depth + 1):
        ext |= shift(big, k, k)
    ol = dilate(big | ext, 1)
    img[ol] = outline + (255,)
    img[ext] = extrude + (255,)
    ys = np.where(big.any(1))[0]
    y0, y1 = ys.min(), ys.max()
    for y in range(Hc):
        t = (y - y0) / max(1, y1 - y0)
        c = colors[min(int(t * len(colors)), len(colors) - 1)]
        row = big[y]
        img[y][row] = c + (255,)
    # brillo: fila superior de cada letra mas clara
    top = big & ~shift(big, 0, 1)
    img[top] = (0xff, 0xff, 0xe8, 255)
    return Image.fromarray(img, 'RGBA')


GOLD = [(0xff, 0xf0, 0x7a), (0xff, 0xd0, 0x30), (0xff, 0xa0, 0x20), (0xe8, 0x60, 0x18), (0xc0, 0x30, 0x18)]
title = render("MYTHIC STREETS", 3, 3, GOLD)
title.save(os.path.join(OUT, 'title.png'))
print('title', title.size)

# ---------------- boton (rockero 80s: placa negra, marco cromado, neon, rayos, remaches) ----------------
from PIL import ImageDraw
BW, BH = 144, 40


def lerp(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


def bolt_icon(flip):
    ic = Image.new('RGBA', (16, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(ic)
    pts = [(10, 0), (2, 14), (7, 14), (4, 27), (14, 10), (8, 10), (12, 0)]
    if flip:
        pts = [(15 - x, y) for x, y in pts]
    d.polygon(pts, fill=(0x10, 0x08, 0x18, 255))
    inner = [(10, 2), (4, 13), (9, 13), (5, 24), (12, 11), (7, 11), (11, 2)]
    if flip:
        inner = [(15 - x, y) for x, y in inner]
    d.polygon(inner, fill=(0xff, 0xe8, 0x40, 255))
    return ic


def button(hover):
    img = np.zeros((BH, BW, 4), dtype=np.uint8)
    cham = 5
    yy, xx = np.mgrid[0:BH, 0:BW]
    inside = np.ones((BH, BW), dtype=bool)
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (BW - 1, 0, -1, 1), (0, BH - 1, 1, -1), (BW - 1, BH - 1, -1, -1)):
        d = (np.abs(xx - cx) + np.abs(yy - cy))
        inside &= ~(d < cham)
    img[inside] = (0x10, 0x08, 0x18, 255)               # contorno negro
    # marco cromado (2..5 px) con degradado vertical
    frame = inside & (xx >= 1) & (xx < BW - 1) & (yy >= 1) & (yy < BH - 1)
    chrome = [(0xf4, 0xf4, 0xff), (0xa8, 0xa8, 0xc0), (0x58, 0x58, 0x70), (0xb8, 0xb8, 0xd0), (0x38, 0x38, 0x50)]
    for y in range(BH):
        t = y / (BH - 1) * (len(chrome) - 1)
        i = min(int(t), len(chrome) - 2)
        c = lerp(chrome[i], chrome[i + 1], t - i)
        row = frame[y]
        img[y][row] = c + (255,)
    # placa interior negra
    pl = inside & (xx >= 5) & (xx < BW - 5) & (yy >= 5) & (yy < BH - 5)
    top = (0x20, 0x10, 0x30); bot = (0x08, 0x04, 0x10) if not hover else (0x80, 0x10, 0x30)
    for y in range(BH):
        c = lerp(top, bot, max(0.0, (y - 5) / (BH - 10)))
        img[y][pl[y]] = c + (255,)
    # rayas diagonales brillantes (efecto metal pulido)
    stripes = pl & (((xx + yy) % 14) < 2) & (xx < BW // 2)
    img[stripes] = (0x38, 0x24, 0x50, 255) if not hover else (0xa0, 0x30, 0x48, 255)
    # borde de neon
    neon = (0xff, 0x30, 0xa0) if not hover else (0x50, 0xf4, 0xff)
    glow = (0x80, 0x10, 0x50) if not hover else (0x20, 0x80, 0xa0)
    ring = pl & ((xx == 7) | (xx == BW - 8) | (yy == 7) | (yy == BH - 8)) & (xx >= 7) & (xx <= BW - 8) & (yy >= 7) & (yy <= BH - 8)
    ring_g = pl & ((xx == 6) | (xx == BW - 7) | (yy == 6) | (yy == BH - 7))
    img[ring_g & ~ring] = glow + (255,)
    img[ring] = neon + (255,)
    # remaches en las esquinas
    for (cx, cy) in ((10, 10), (BW - 11, 10), (10, BH - 11), (BW - 11, BH - 11)):
        img[cy:cy + 2, cx:cx + 2] = (0xe8, 0xe8, 0xf8, 255)
        img[cy + 1, cx + 1] = (0x70, 0x70, 0x88, 255)
    base = Image.fromarray(img, 'RGBA')
    base.alpha_composite(bolt_icon(False), (12, (BH - 28) // 2))
    base.alpha_composite(bolt_icon(True), (BW - 12 - 16, (BH - 28) // 2))
    cols = [(0xff, 0xff, 0xff), (0xff, 0xf0, 0x70), (0xff, 0xa0, 0x20), (0xe8, 0x38, 0x30)]
    t = render("START", 3, 2, cols, pad=2, depth=2, outline=(0x30, 0x08, 0x20), extrude=(0x60, 0x10, 0x60))
    base.alpha_composite(t, ((BW - t.width) // 2, (BH - t.height) // 2))
    return base


sheet = Image.new('RGBA', (BW * 2, BH), (0, 0, 0, 0))
sheet.paste(button(False), (0, 0)); sheet.paste(button(True), (BW, 0))
sheet.save(os.path.join(OUT, 'button.png'))
print('ok')
