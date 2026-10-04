"""Pasada nocturna ochentera sobre la calle ya dibujada de día (ver make_background.py):
suciedad (goteras, grafitis, carteles, grietas), basura, contenedores, charcos, cables,
y luego la iluminación: ambiente azul-violeta oscuro + farolas de sodio encendidas, ventanas con luz,
neones y rótulos emisivos, cielo con estrellas y luna.
Las farolas están en LAMPS (misma lista en scripts/background.gd, que ilumina también a los luchadores)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import trash_sprites as TS

LAMPS = [90, 330, 580, 820, 1020, 1240]
WARM = np.array([1.0, 0.72, 0.36])
HEAD_Y = 24   # altura de la bombilla de las farolas (el poste mide unos 106 px)


def apply(img, W, H, SY, CY, sky_colors, glass, protect, emissive, manholes):
    rnd = random.Random(1984)
    d = ImageDraw.Draw(img)
    px = img.load()

    arr0 = np.array(img)
    sky = np.zeros((H, W), bool)
    for c in sky_colors:
        sky |= (arr0 == np.array(c)).all(axis=2)

    def solid(x, y):
        return 0 <= x < W and 0 <= y < H and not sky[y, x]

    def mul(x, y, k):
        if solid(x, y):
            r, g, b = px[x, y]
            px[x, y] = (int(r * k), int(g * k), int(b * k))

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = c

    def prot(x):
        return any(a <= x < b for a, b in protect)

    # ---------- suciedad en fachadas ----------
    for _ in range(380):                                    # goteras / regueros
        x = rnd.randint(0, W - 1)
        y0 = rnd.randint(24, SY - 30)
        for k in range(rnd.randint(6, 30)):
            mul(x, y0 + k, 0.88 - 0.06 * (k < 4))
    for _ in range(260):                                    # manchas de humedad
        x, y = rnd.randint(0, W - 8), rnd.randint(30, SY - 10)
        for dx in range(rnd.randint(3, 8)):
            for dy in range(rnd.randint(2, 5)):
                mul(x + dx, y + dy, 0.86)
    for x in range(W):                                      # mugre en la base de los muros
        for k in range(14):
            mul(x, SY - 1 - k, 0.78 + 0.016 * k)
    for _ in range(W * 14 // 10):                           # grano de suciedad
        mul(rnd.randint(0, W - 1), rnd.randint(24, SY - 1), rnd.choice((0.8, 0.88)))

    for _ in range(36):                                      # carteles pegados (conciertos, fiestas)
        x, y = rnd.randint(4, W - 12), rnd.randint(SY - 64, SY - 22)
        if prot(x) or prot(x + 8) or not solid(x, y) or not solid(x + 6, y + 9):
            continue
        c = rnd.choice(((0xf0, 0xe8, 0xc8), (0xf0, 0xd0, 0x40), (0xe8, 0x70, 0xa8), (0x70, 0xc0, 0xe0)))
        d.rectangle([x, y, x + 6, y + 9], fill=c)
        for yy in (y + 2, y + 5, y + 7):
            d.line([x + 1, yy, x + rnd.randint(3, 5), yy], fill=(0x30, 0x2a, 0x34))
        put(x + 6, y + 9, (0x80, 0x78, 0x70))
    # ---------- acera y calzada sucias ----------
    for _ in range(90):                                       # grietas en la acera
        x, y = rnd.randint(0, W - 1), rnd.randint(SY + 1, CY - 1)
        for _ in range(rnd.randint(4, 12)):
            mul(x, y, 0.62)
            x += rnd.choice((-1, 0, 1, 1))
            y = min(max(y + rnd.choice((-1, 0, 0, 1)), SY + 1), CY - 1)
    for _ in range(70):                                       # manchas (grasa, chicles, humedad)
        x, y = rnd.randint(0, W - 8), rnd.randint(SY + 1, CY - 2)
        for dx in range(rnd.randint(2, 7)):
            for dy in range(rnd.randint(1, 3)):
                mul(x + dx, y + dy, 0.72)
    for _ in range(1400):                                     # grano oscuro en el asfalto
        mul(rnd.randint(0, W - 1), rnd.randint(CY + 3, H - 1), rnd.choice((0.72, 0.8)))
    for _ in range(26):                                       # manchas de aceite
        x, y = rnd.randint(0, W - 14), rnd.randint(CY + 12, H - 6)
        for dx in range(rnd.randint(5, 13)):
            for dy in range(rnd.randint(2, 4)):
                mul(x + dx, y + dy, 0.62)
    for _ in range(46):                                       # grietas en el asfalto
        x, y = rnd.randint(0, W - 1), rnd.randint(CY + 6, H - 2)
        for _ in range(rnd.randint(8, 26)):
            mul(x, y, 0.55)
            x += rnd.choice((1, 1, 2, 0))
            y = min(max(y + rnd.choice((-1, 0, 0, 1)), CY + 4), H - 1)
    for _ in range(8):                                        # rodadas de neumáticos
        x, y = rnd.randint(0, W - 80), rnd.randint(CY + 14, H - 6)
        for k in range(rnd.randint(40, 90)):
            mul(x + k, y + (k // 30), 0.85)

    # ---------- basura y mobiliario sucio ----------
    def sprite(name, x, y, flip=False):
        """Dibuja un sprite de trash_sprites con su esquina inferior izquierda en (x, y)."""
        rows, pal = TS.SPR[name]
        w, h = len(rows[0]), len(rows)
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch != '.':
                    cc = (w - 1 - c) if flip else c
                    put(x + cc, y - h + 1 + r, pal[ch])

    def bin_(x):
        """Contenedor pequeño, verde apagado."""
        yb = SY + 15
        body, dark, mid, lite = (0x30, 0x4e, 0x3c), (0x22, 0x38, 0x2c), (0x28, 0x44, 0x34), (0x44, 0x6a, 0x52)
        d.rectangle([x, yb - 12, x + 17, yb], fill=body)
        d.rectangle([x - 1, yb - 14, x + 18, yb - 12], fill=mid)
        d.rectangle([x, yb - 12, x + 17, yb - 11], fill=dark)
        d.line([x + 2, yb - 9, x + 2, yb - 2], fill=lite)
        d.line([x + 15, yb - 9, x + 15, yb - 2], fill=dark)
        d.rectangle([x + 7, yb - 8, x + 10, yb - 5], fill=(0x98, 0x9c, 0x90))              # etiqueta
        d.rectangle([x + 1, yb, x + 3, yb + 1], fill=(0x18, 0x18, 0x20))
        d.rectangle([x + 14, yb, x + 16, yb + 1], fill=(0x18, 0x18, 0x20))
        sprite('bag_black', x + 1, yb - 14)
        sprite('bag_black', x + 10, yb - 14, True)
    for x in (270, 905, 1105):
        if min(abs(x - l) for l in LAMPS) > 25:
            bin_(x)
    for x in (270, 455, 905, 1105):                           # bolsas sueltas junto a los contenedores
        sprite('bag_black', x - 8, SY + 15)
        sprite('crumple', x + 22, SY + 15)
    for _ in range(230):                                      # papeles y basura en el suelo (planos, a 45 grados)
        zone = rnd.random()
        x = rnd.randint(2, W - 12)
        if zone < 0.5:                                         # acera
            y = rnd.randint(SY + 4, CY - 2)
        elif zone < 0.7:                                       # junto al bordillo
            y = rnd.randint(CY + 4, CY + 9)
        else:                                                  # calzada
            y = rnd.randint(CY + 10, H - 4)
        sprite(rnd.choice(TS.FLAT), x, y, rnd.random() < 0.5)

    # ---------- charcos irregulares (albedo azulado) ----------
    def blob(cx, cy, rx, ry):
        """Mancha irregular: contorno con armónicos aleatorios y cierta inclinación; devuelve un set de píxeles."""
        amps = [rnd.uniform(0.12, 0.28), rnd.uniform(0.08, 0.22), rnd.uniform(0.04, 0.14)]
        phs = [rnd.uniform(0, 6.28) for _ in amps]
        shear = rnd.uniform(-0.9, 0.9)
        pix = set()
        for y in range(cy - ry - 3, cy + ry + 4):
            for x in range(cx - rx - 8, cx + rx + 9):
                dx = (x - cx - shear * (y - cy)) / rx
                dy = (y - cy) / ry
                r = math.hypot(dx, dy)
                th = math.atan2(dy, dx)
                lim = 1 + sum(a * math.cos((k + 1) * th + ph) for k, (a, ph) in enumerate(zip(amps, phs)))
                if r <= lim * 0.92 and 0 <= x < W and CY + 4 <= y < H:
                    pix.add((x, y))
        return pix

    puddles = []
    taken = set()                                          # píxeles ocupados (+margen) para que no se solapen
    for k in range(120):
        if len(puddles) >= 17:
            break
        if len(puddles) < 14:
            cx, cy = rnd.randint(24, W - 24), rnd.randint(CY + 14, H - 10)
            rx, ry = rnd.randint(8, 24), rnd.randint(3, 7)
        else:                                                  # charcos alargados junto al bordillo
            cx, cy = rnd.randint(24, W - 24), CY + rnd.randint(6, 9)
            rx, ry = rnd.randint(12, 28), rnd.randint(2, 3)
        pix = blob(cx, cy, rx, ry)
        if len(pix) < 18 or any(q in taken for q in pix):
            continue
        for (x, y) in pix:
            for ddx in range(-3, 4):
                for ddy in range(-3, 4):
                    taken.add((x + ddx, y + ddy))
        for (x, y) in pix:
            edge = any((x + dx, y + dy) not in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            px[x, y] = (0x16, 0x1c, 0x2e) if edge else (0x28, 0x32, 0x4c)
        puddles.append((cx, cy, pix))

    # ---------- gradación nocturna ----------
    albedo = np.array(img).astype(np.float32) / 255.0
    lum = (albedo * np.array([0.3, 0.59, 0.11])).sum(axis=2, keepdims=True)
    night = (lum + (albedo - lum) * 0.8) * np.array([0.30, 0.34, 0.58]) + np.array([0.012, 0.014, 0.045])
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

    def light(cx, cy, color, rx, ry, k, power=1.6):
        r = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2)
        return (np.clip(1 - r, 0, 1) ** power * k)[..., None] * np.array(color, dtype=np.float32)[None, None, :]

    L = np.zeros((H, W, 3), np.float32)
    for lx in LAMPS:                                          # farolas de sodio: luz solo hacia abajo (cono)
        dx_, dy_ = XX - lx, YY - (HEAD_Y + 2)
        dist = np.sqrt(dx_ ** 2 + dy_ ** 2) + 1e-3
        cos_ = np.clip(dy_ / dist, 0, 1)                      # 1 = justo debajo, 0 = horizontal o por encima
        cone = np.clip((cos_ - 0.5) / 0.5, 0, 1) ** 0.7       # semiángulo de ~60 grados
        fall = 1.0 / (1.0 + (dist / 85.0) ** 2) * np.clip(1 - dist / 290.0, 0, 1)
        L += (cone * fall * 3.4)[..., None] * WARM[None, None, :]
        pool = np.clip(1 - np.sqrt(((XX - lx) / 120.0) ** 2 + ((YY - 158) / 46.0) ** 2), 0, 1) ** 1.1
        pool[YY < SY] = 0
        L += (pool * 0.8)[..., None] * WARM[None, None, :]
    # ventanas encendidas
    gmask = (np.array(img) == np.array(glass)).all(axis=2)
    lab, n = ndimage.label(gmask)
    lit_windows = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) < 25:
            continue
        if rnd.random() < 0.4:
            lit_windows.append((xs.min(), xs.max(), ys.min(), ys.max(), xs, ys))
            L += light(xs.mean(), ys.mean(), (1.0, 0.8, 0.45), 26, 26, 0.45)
    for (x0, y0, x1, y1, col, rad, k) in emissive:             # luces de neones / rótulos
        L += light((x0 + x1) / 2, (y0 + y1) / 2, col, rad, rad * 0.8, k)
    L[sky] = 0
    out = night + albedo * np.clip(L, 0, 1.4) * 0.95
    out = np.clip(out, 0, 1)

    # los rótulos y ventanas con luz propia (emisivos) conservan su brillo
    for (x0, y0, x1, y1, col, rad, k) in emissive:
        out[y0:y1, x0:x1] = np.maximum(out[y0:y1, x0:x1], np.clip(albedo[y0:y1, x0:x1] * 1.05, 0, 1))
    for (xa, xb, ya, yb, xs, ys) in lit_windows:
        for x_, y_ in zip(xs, ys):
            t = (y_ - ya) / max(1, yb - ya)
            out[y_, x_] = np.array([1.0, 0.82 - 0.2 * t, 0.42 - 0.12 * t])

    # ---------- cielo nocturno ----------
    skyc = [(0.04, 0.05, 0.19), (0.08, 0.07, 0.26), (0.16, 0.09, 0.32), (0.30, 0.12, 0.40), (0.52, 0.18, 0.46), (0.74, 0.30, 0.46)]
    for y in range(0, SY):
        t = y / (SY - 1) * (len(skyc) - 1)
        i = min(int(t), len(skyc) - 2)
        f = t - i
        c = np.array(skyc[i]) * (1 - f) + np.array(skyc[i + 1]) * f
        band = np.floor(y / 6)                                 # bandas de color (pixel art)
        c = np.array(skyc[min(int(band / ((SY - 1) / 6.0 / 1.0 / 6.0 * 6) ), len(skyc) - 1)]) if False else c
        row = sky[y]
        out[y][row] = np.round(c * 8) / 8                      # cuantizado = degradado en bandas
    # estrellas
    for _ in range(190):
        x, y = rnd.randint(0, W - 1), rnd.randint(0, 80)
        if sky[y, x]:
            b = rnd.choice((0.55, 0.75, 1.0))
            out[y, x] = np.array([b, b, min(1.0, b + 0.1)])
            if b == 1.0 and rnd.random() < 0.3:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if sky[y + dy, x + dx]:
                        out[y + dy, x + dx] = np.array([0.6, 0.6, 0.75])
    # luna con halo
    mx, my = 300, 36
    halo = np.clip(1 - np.sqrt(((XX - mx) / 34) ** 2 + ((YY - my) / 34) ** 2), 0, 1) ** 2
    out += (halo * 0.28)[..., None] * np.array([0.9, 0.85, 1.0]) * sky[..., None]
    for dy in range(-11, 12):
        for dx in range(-11, 12):
            if dx * dx + dy * dy <= 121 and sky[my + dy, mx + dx]:
                shade = 0.94 if dx + dy < 6 else 0.8
                out[my + dy, mx + dx] = np.array([0.96, 0.94, 0.82]) * shade
    for (dx, dy, r) in ((-3, -4, 2), (4, 2, 3), (-5, 5, 1), (2, -7, 1)):   # cráteres
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r and sky[my + dy + yy, mx + dx + xx]:
                    out[my + dy + yy, mx + dx + xx] = np.array([0.74, 0.72, 0.66])
    # nubes oscuras con borde rosado
    for _ in range(9):
        cx, cy = rnd.randint(0, W), rnd.randint(40, 90)
        for k in range(rnd.randint(3, 5)):
            rx0, ry0 = rnd.randint(14, 26), rnd.randint(2, 4)
            for yy in range(-ry0, ry0 + 1):
                for xx in range(-rx0, rx0 + 1):
                    x_, y_ = cx + k * 12 + xx, cy + yy
                    if 0 <= x_ < W and 0 <= y_ < H and sky[y_, x_] and (xx / rx0) ** 2 + (yy / ry0) ** 2 <= 1:
                        out[y_, x_] = np.array([0.30, 0.15, 0.40]) if yy < ry0 - 1 else np.array([0.62, 0.28, 0.50])

    img2 = Image.fromarray((out * 255).astype(np.uint8))
    d2 = ImageDraw.Draw(img2)
    p2 = img2.load()

    def glow(cx, cy, col, r, k):
        arr = np.array(img2).astype(np.float32) / 255.0
        g = np.clip(1 - np.sqrt(((XX - cx) / r) ** 2 + ((YY - cy) / r) ** 2), 0, 1) ** 2 * k
        arr += g[..., None] * np.array(col)[None, None, :]
        return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))

    # ---------- reflejos en los charcos (siempre dentro de la mancha) ----------
    p2 = img2.load()
    for (cx, cy, pix) in puddles:
        ys_ = [y for _, y in pix]
        xs_ = [x for x, _ in pix]
        y_top, y_bot, x_left, x_right = min(ys_), max(ys_), min(xs_), max(xs_)
        hgt = max(1, y_bot - y_top)
        # reflejo difuso del cielo: parte superior más clara, con ligera textura por bandas
        for (x, y) in pix:
            t = (y - y_top) / hgt
            interior = all((x + dx, y + dy) in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if not interior:
                continue
            f = max(0.0, 0.85 - t * 1.3)
            if f > 0:
                r, g, b = p2[x, y]
                p2[x, y] = (min(255, r + int(22 * f)), min(255, g + int(30 * f)), min(255, b + int(52 * f)))
        # destellos pequeños (brillos de agua)
        for _ in range(max(1, len(pix) // 40)):
            x, y = rnd.choice(list(pix))
            if all((x + dx, y + dy) in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p2[x, y] = (0x8a, 0xa0, 0xcc)
                if (x + 1, y) in pix and rnd.random() < 0.6:
                    p2[x + 1, y] = (0x6a, 0x80, 0xb0)
        # reflejo de la farola más cercana: columna ondulada, solo sobre píxeles del charco
        near = min(LAMPS, key=lambda l: abs(l - cx))
        dist = abs(near - cx)
        if dist < 120:
            kk = (1 - dist / 120) ** 1.2
            cxl = int(cx + (near - cx) * 0.3)
            for (x, y) in pix:
                wob = int(round(math.sin((y - y_top) * 1.7 + cx) * 1.2))
                w = 1 + (hgt >= 5)
                if abs(x - (cxl + wob)) <= w:
                    t = (y - y_top) / hgt
                    f = kk * (1 - 0.5 * abs(t - 0.45) * 2) * (0.55 if abs(x - (cxl + wob)) == w else 1.0)
                    r, g, b = p2[x, y]
                    p2[x, y] = (min(255, r + int(0xd0 * f)), min(255, g + int(0x80 * f)), min(255, b + int(0x30 * f)))
    # ---------- neones "BAR" colgados ----------
    neons = []
    for nx_, ny_ in ((372, 62), (958, 70)):
        d2.line([nx_ - 12, ny_ + 4, nx_, ny_ + 4], fill=(0x14, 0x14, 0x1c))                        # soporte
        d2.rectangle([nx_, ny_, nx_ + 22, ny_ + 10], fill=(0x18, 0x0c, 0x24))
        d2.rectangle([nx_, ny_, nx_ + 22, ny_ + 10], outline=(0xff, 0x40, 0xc0))
        for i, ch in enumerate("BAR"):
            glyph = {"B": ["110", "101", "110", "101", "110"], "A": ["010", "101", "111", "101", "101"],
                     "R": ["110", "101", "110", "101", "101"]}[ch]
            for r_, row in enumerate(glyph):
                for k_, v in enumerate(row):
                    if v == '1':
                        d2.point((nx_ + 3 + i * 7 + k_ * 2, ny_ + 2 + r_ * 1 + (r_ > 2)), fill=(0x40, 0xf0, 0xff))
        neons.append((nx_ + 11, ny_ + 5))
    for (gx, gy_) in neons:
        img2 = glow(gx, gy_, (1.0, 0.25, 0.75), 36, 0.65)
    # ---------- farolas (altas, con la bombilla mirando al suelo) ----------
    d2 = ImageDraw.Draw(img2)
    for lx in LAMPS:
        d2.rectangle([lx, HEAD_Y + 2, lx + 1, SY + 12], fill=(0x12, 0x12, 0x1a))            # poste
        d2.rectangle([lx - 3, SY + 8, lx + 4, SY + 12], fill=(0x1c, 0x1c, 0x26))            # base
        d2.rectangle([lx - 1, SY - 8, lx + 2, SY - 6], fill=(0x1c, 0x1c, 0x26))             # anillo decorativo
        d2.rectangle([lx - 6, HEAD_Y - 2, lx + 7, HEAD_Y], fill=(0x12, 0x12, 0x1a))         # pantalla superior
        d2.rectangle([lx - 5, HEAD_Y, lx + 6, HEAD_Y + 2], fill=(0x1c, 0x1c, 0x26))         # carcasa
        d2.rectangle([lx - 3, HEAD_Y + 2, lx + 4, HEAD_Y + 3], fill=(0xff, 0xf0, 0xb8))     # bombilla (hacia abajo)
    for lx in LAMPS:
        arr = np.array(img2).astype(np.float32) / 255.0
        g = np.clip(1 - np.sqrt(((XX - lx - 0.5) / 20.0) ** 2 + ((YY - HEAD_Y - 6) / 14.0) ** 2), 0, 1) ** 2 * 0.8
        g[YY < HEAD_Y + 2] = 0                                                              # nada de brillo hacia arriba
        arr += g[..., None] * np.array([1.0, 0.7, 0.3])[None, None, :]
        img2 = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    # ---------- cables eléctricos ----------
    d2 = ImageDraw.Draw(img2)
    for _ in range(14):
        xa = rnd.randint(-20, W - 80)
        xb = xa + rnd.randint(90, 240)
        ya = rnd.randint(14, 34)
        yb = ya + rnd.randint(-4, 6)
        sag = rnd.randint(4, 9)
        prev = None
        for x in range(xa, xb + 1):
            t = (x - xa) / (xb - xa)
            y = int(ya + (yb - ya) * t + sag * 4 * t * (1 - t))
            if 0 <= x < W:
                d2.point((x, y), fill=(0x0c, 0x0c, 0x14))
    return img2
