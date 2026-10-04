"""Genera las hojas de sprites (pixel art) del jugador y del enemigo.
Uso:  python tools/make_sprites.py [carpeta_salida]

Cada frame es de 96x96 con los pies en (48, 90). Filas = animaciones (ver ORDER).
Las poses se definen con objetivos de manos y pies; brazos y piernas se resuelven con
cinemática inversa (2 huesos), así que las articulaciones se doblan de forma natural.
Para cambiar colores o rasgos edita PAL_PLAYER / PAL_ENEMY o las poses y vuelve a ejecutar.
"""
import math, random, sys, os
from PIL import Image, ImageDraw

W = H = 96
COLS = 8
CX, GROUND = 48, 90
OUT = (18, 14, 26, 255)
THIGH, SHIN = 15.5, 15.5
UARM, FARM = 14, 13
ANKLE = 5         # altura del tobillo sobre el suelo
TORSO = 23


def rgba(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def tri(base, dark, light):
    return (rgba(dark), rgba(base), rgba(light))


PAL_PLAYER = dict(
    skin=tri('e8b48c', 'b97c58', 'f7d3b2'),
    hair=tri('4a3426', '2a1c14', '6a5040'), hair_tip=rgba('b89a78'),
    shirt=tri('2c2c34', '16161c', '44444f'),
    jeans=tri('8fb4de', '5f86b8', 'b9d3ee'),
    shoe=tri('eeeeee', '9a9aa8', 'ffffff'), sole=rgba('55556a'),
    glasses=True, chain=True, graphic=True)

PAL_ENEMY = dict(
    skin=tri('d9a07c', 'a96f4e', 'eec19f'),
    hair=tri('d8b838', 'a88a20', 'f4e07a'), hair_tip=rgba('fff2a8'),
    shirt=tri('b02a2a', '7a1a1a', 'd85050'),
    jeans=tri('3c3c5c', '25253e', '56567a'),
    shoe=tri('4a3426', '2a1c14', '6a5040'), sole=rgba('15100c'),
    glasses=False, chain=False, graphic=False)


# ---------------------------------------------------------------- geometría
def ik(A, T, l1, l2, prefer):
    """Cinemática inversa de 2 huesos. Devuelve (articulación, punto final alcanzado)."""
    dx, dy = T[0] - A[0], T[1] - A[1]
    dist = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / dist, dy / dist
    d = max(min(dist, l1 + l2 - 0.05), abs(l1 - l2) + 0.05)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    mx, my = A[0] + ux * a, A[1] + uy * a
    c1 = (mx - uy * h, my + ux * h)
    c2 = (mx + uy * h, my - ux * h)
    joint = c1 if prefer(c1) > prefer(c2) else c2
    return joint, (A[0] + ux * d, A[1] + uy * d)


def capsule(d, p0, p1, r0, r1, col):
    for p, r in ((p0, r0), (p1, r1)):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    d.polygon([(p0[0] + nx * r0, p0[1] + ny * r0), (p1[0] + nx * r1, p1[1] + ny * r1),
               (p1[0] - nx * r1, p1[1] - ny * r1), (p0[0] - nx * r0, p0[1] - ny * r0)], fill=col)


def limb(d, p0, p1, w0, w1, cols):
    """Miembro cónico con 3 tonos: sombra, base y luz (luz desde arriba-delante)."""
    dark, base, light = cols
    capsule(d, p0, p1, w0 / 2, w1 / 2, dark)
    capsule(d, (p0[0] + .8, p0[1] - .6), (p1[0] + .8, p1[1] - .6), max(w0 / 2 - 1.2, .5), max(w1 / 2 - 1.2, .5), base)
    if min(w0, w1) >= 6:
        capsule(d, (p0[0] + 1.5, p0[1] - 1.0), (p1[0] + 1.5, p1[1] - 1.0), max(w0 / 2 - 2.8, .4), max(w1 / 2 - 2.8, .4), light)
        capsule(d, (p0[0] + .6, p0[1] - .3), (p1[0] + .6, p1[1] - .3), max(w0 / 2 - 2.2, .4), max(w1 / 2 - 2.2, .4), base)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ---------------------------------------------------------------- partes
def draw_shoe(d, foot, P, back):
    x, y = foot
    dark, base, light = P['shoe']
    col = dark if back else base
    sole = P['sole']
    d.polygon([(x - 5, y - 6), (x + 1, y - 6), (x + 3, y - 4), (x + 8, y - 3), (x + 10, y - 1),
               (x + 10, y), (x - 5, y)], fill=col)
    d.rectangle([x - 5, y - 1, x + 10, y], fill=sole)               # suela
    d.line([(x - 5, y - 6), (x - 5, y - 2)], fill=dark)             # talón
    if not back:
        d.line([(x + 1, y - 5), (x + 4, y - 3)], fill=light)        # brillo del empeine
    d.line([(x + 3, y - 5), (x + 6, y - 3)], fill=dark)             # cordones
    d.point((x + 9, y - 2), fill=light if not back else base)


def draw_leg(d, hip, foot, P, back):
    cols = P['jeans']
    cols = tuple(tuple(int(c * 0.82) if i < 3 else c for i, c in enumerate(col)) for col in cols) if back else cols
    knee, ankle = ik(hip, (foot[0], foot[1] - ANKLE), THIGH, SHIN, lambda p: p[0])
    limb(d, hip, knee, 11, 9, cols)
    limb(d, knee, ankle, 9, 8, cols)
    dark = cols[0]
    for t in (0.35, 0.65):                                          # pliegues del vaquero
        p = lerp(knee, ankle, t)
        d.line([(p[0] - 3, p[1]), (p[0] + 1, p[1] + 1)], fill=dark)
    d.line([(ankle[0] - 4, ankle[1] + 1), (ankle[0] + 3, ankle[1] + 1)], fill=dark)   # dobladillo
    draw_shoe(d, foot, P, back)


def draw_arm(d, shoulder, hand, P, back):
    skin = P['skin']
    if back:
        skin = tuple(tuple(int(c * 0.86) if i < 3 else c for i, c in enumerate(col)) for col in skin)
    elbow, hand = ik(shoulder, hand, UARM, FARM, lambda p: p[1] - 0.3 * p[0])
    limb(d, elbow, hand, 7, 6, skin)                                # antebrazo
    limb(d, shoulder, elbow, 8, 7, skin)                            # brazo
    sl_end = lerp(shoulder, elbow, 0.68)
    limb(d, shoulder, sl_end, 10, 9, P['shirt'])                    # manga
    d.ellipse([hand[0] - 3, hand[1] - 3, hand[0] + 3, hand[1] + 3], fill=skin[1])  # puño
    d.ellipse([hand[0] - 2, hand[1] - 3, hand[0] + 2, hand[1] + 1], fill=skin[2])
    d.line([(hand[0] - 1, hand[1] + 1), (hand[0] + 3, hand[1] + 1)], fill=skin[0])


def draw_head(d, c, P, rnd, enemy_angry):
    hx, hy = c
    skin = P['skin']
    d.rectangle([hx - 3, hy + 5, hx + 3, hy + 11], fill=skin[0])                 # cuello
    d.ellipse([hx - 7, hy - 8, hx + 7, hy + 7], fill=skin[1])                    # cráneo/cara
    d.rectangle([hx - 5, hy + 1, hx + 6, hy + 7], fill=skin[1])                  # mandíbula
    d.rectangle([hx - 6, hy + 3, hx - 4, hy + 6], fill=skin[0])                  # sombra mejilla trasera
    d.rectangle([hx + 3, hy - 3, hx + 6, hy + 2], fill=skin[2])                  # luz frente/pómulo
    d.rectangle([hx + 7, hy, hx + 8, hy + 2], fill=skin[1])                      # nariz
    d.point((hx + 8, hy + 1), fill=skin[2])
    d.rectangle([hx - 4, hy - 1, hx - 3, hy + 3], fill=skin[0])                  # oreja
    # cara
    if P['glasses']:
        fr = rgba('121218')
        d.rectangle([hx - 1, hy - 3, hx + 9, hy + 2], fill=fr)                       # montura gruesa
        for lx in (hx + 1, hx + 6):
            d.rectangle([lx, hy - 2, lx + 2, hy + 1], fill=rgba('b9dcf0'))
            d.point((lx + 2, hy), fill=rgba('121218'))                           # pupila
            d.point((lx + 2, hy + 1), fill=rgba('121218'))
            d.point((lx, hy - 2), fill=rgba('ffffff'))                           # brillo
        d.line([(hx, hy - 3), (hx - 4, hy - 3)], fill=fr)                        # patilla
        d.line([(hx + 1, hy - 5), (hx + 7, hy - 5)], fill=rgba('2a1c14'))        # cejas
    my = hy + 4
    d.line([(hx + 2, my), (hx + 7, my)], fill=rgba('7a2e2e'))
    d.point((hx + 1, my - 1), fill=rgba('7a2e2e'))
    d.point((hx + 8, my - 1), fill=rgba('7a2e2e'))
    if P['glasses']:
        d.line([(hx + 3, my), (hx + 6, my)], fill=rgba('f6f6f6'))                # sonrisa con dientes
    # pelo rizado: masa + rizos en 3 tonos, puntas aclaradas
    hair = P['hair']
    d.ellipse([hx - 9, hy - 12, hx + 7, hy - 3], fill=hair[1])
    d.rectangle([hx - 9, hy - 8, hx - 4, hy + 5], fill=hair[1])
    for k in range(10):
        ang = math.pi * (1.0 + k / 9.0 * 1.15)
        px, py = hx - 1 + math.cos(ang) * 8.5, hy - 2 + math.sin(ang) * 8.5
        col = hair[2] if k % 3 == 0 else hair[1]
        d.ellipse([px - 2.8, py - 2.8, px + 2.8, py + 2.8], fill=col)
    for k in range(8):
        px = hx - 7 + k * 2 + rnd.randint(-1, 1)
        py = hy - 11 + rnd.randint(0, 2)
        d.ellipse([px - 1, py - 1, px + 1, py + 1], fill=P['hair_tip'])
    for _ in range(6):
        d.point((hx - 9 + rnd.randint(0, 5), hy - 6 + rnd.randint(0, 9)), fill=hair[0])
    d.ellipse([hx + 3, hy - 9, hx + 8, hy - 5], fill=hair[1])                    # rizo frontal
    d.point((hx + 6, hy - 8), fill=P['hair_tip'])
    if not P['glasses']:                                                         # ojos y cejas (sobre el pelo)
        ink = rgba('121218')
        d.rectangle([hx + 2, hy - 2, hx + 3, hy], fill=rgba('f6f6f6'))
        d.rectangle([hx + 6, hy - 2, hx + 7, hy], fill=rgba('f6f6f6'))
        d.point((hx + 3, hy - 1), fill=ink)
        d.point((hx + 7, hy - 1), fill=ink)
        d.line([(hx + 1, hy - 4), (hx + 4, hy - 3)], fill=ink)
        d.line([(hx + 6, hy - 3), (hx + 8, hy - 4)], fill=ink)


def draw_torso(d, S, Pv, P):
    sh = P['shirt']
    pts = [(S[0] - 9, S[1] + 1), (S[0] - 4, S[1] - 2), (S[0] + 5, S[1] - 2), (S[0] + 9, S[1] + 1),
           (Pv[0] + 8, Pv[1] - 1), (Pv[0] + 7, Pv[1] + 3), (Pv[0] - 7, Pv[1] + 3), (Pv[0] - 8, Pv[1] - 1)]
    d.polygon(pts, fill=sh[1])
    d.polygon([(S[0] - 10, S[1] + 1), (S[0] - 5, S[1] - 1), (S[0] - 4, Pv[1] + 3), (Pv[0] - 8, Pv[1] + 3), (Pv[0] - 9, Pv[1] - 1)], fill=sh[0])
    d.polygon([(S[0] + 5, S[1] - 2), (S[0] + 10, S[1] + 1), (Pv[0] + 9, Pv[1] - 1), (Pv[0] + 7, Pv[1] - 1)], fill=sh[2])
    for t in (0.55, 0.8):                                                         # pliegues
        a = lerp((S[0] - 8, S[1]), (Pv[0] - 7, Pv[1]), t)
        d.line([(a[0], a[1]), (a[0] + 7, a[1] + 2)], fill=sh[0])
    # cuello de la camiseta
    d.polygon([(S[0] - 3, S[1] - 2), (S[0] + 4, S[1] - 2), (S[0] + 2, S[1] + 2), (S[0] - 1, S[1] + 2)], fill=P['skin'][0])
    if P['graphic']:
        gx, gy = S[0] + 1, S[1] + 8
        d.ellipse([gx - 5, gy - 4, gx + 5, gy + 4], fill=rgba('1e3f7a'))
        d.ellipse([gx - 2, gy - 3, gx + 4, gy + 3], fill=rgba('f0a830'))
        d.ellipse([gx, gy - 2, gx + 3, gy + 1], fill=rgba('ffe27a'))
        d.point((gx - 4, gy - 1), fill=rgba('a9cbe2'))
        d.point((gx + 4, gy + 3), fill=rgba('e84830'))
    if P['chain']:
        c = rgba('dde1ea')
        cy = S[1] + 1
        for i in range(8):
            d.point((S[0] - 4 + i, cy + i // 2 + (i if i < 4 else 0) // 2), fill=c)
        for i in range(5):
            d.point((S[0] - 3 + i, cy + 1 + i), fill=c)
            d.point((S[0] + 5 - i, cy + 1 + i), fill=c)
        d.rectangle([S[0], cy + 6, S[0] + 2, cy + 8], fill=rgba('4a4e5a'))
        d.point((S[0] + 1, cy + 6), fill=rgba('ffffff'))


def draw_pelvis(d, Pv, P):
    j = P['jeans']
    d.polygon([(Pv[0] - 9, Pv[1] - 2), (Pv[0] + 9, Pv[1] - 2), (Pv[0] + 9, Pv[1] + 6), (Pv[0] - 9, Pv[1] + 6)], fill=j[1])
    d.rectangle([Pv[0] - 9, Pv[1] - 2, Pv[0] - 5, Pv[1] + 6], fill=j[0])
    d.rectangle([Pv[0] + 5, Pv[1] - 2, Pv[0] + 9, Pv[1] + 5], fill=j[2])
    d.line([(Pv[0] - 9, Pv[1] - 1), (Pv[0] + 9, Pv[1] - 1)], fill=rgba('2a2a34'))      # cinturón
    d.rectangle([Pv[0] + 1, Pv[1] - 2, Pv[0] + 3, Pv[1]], fill=rgba('b8b8c4'))        # hebilla


def draw_char(P, pose, seed=7):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    Pv = (CX + pose['px'], GROUND - ANKLE - THIGH - SHIN - 4 + pose['bob'])
    S = (Pv[0] + pose['lean'], Pv[1] - TORSO)
    head = (S[0] + 2 + pose['head'][0], S[1] - 10 + pose['head'][1])
    sF, sB = (S[0] + 7, S[1] + 2), (S[0] - 7, S[1] + 3)
    hipF, hipB = (Pv[0] + 4, Pv[1] + 4), (Pv[0] - 4, Pv[1] + 4)
    foot = lambda f: (CX + f[0], GROUND - f[1])

    draw_leg(d, hipB, foot(pose['fB']), P, True)
    draw_leg(d, hipF, foot(pose['fF']), P, False)
    draw_pelvis(d, Pv, P)
    draw_torso(d, S, Pv, P)
    draw_head(d, head, P, rnd, False)
    draw_arm(d, sB, (S[0] + pose['hB'][0], S[1] + pose['hB'][1]), P, True)
    draw_arm(d, sF, (S[0] + pose['hF'][0], S[1] + pose['hF'][1]), P, False)
    return im


def outline(im):
    src = im.load()
    out = im.copy()
    o = out.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and src[nx, ny][3] > 0:
                        o[x, y] = OUT
                        break
    return out


def hard_alpha(im):
    """Quita el semitransparente que deja el dibujado para mantener pixel art limpio."""
    px = im.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= 128 else 0)
    return im


# ---------------------------------------------------------------- poses
def pose(**k):
    base = dict(bob=0, px=0, lean=0, head=(0, 0),
                hF=(18, -10), hB=(10, 9), fF=(9, 0), fB=(-7, 0))
    base.update(k)
    return base


GUARD = dict(lean=2, head=(1, 0), bob=3, hF=(20, -3), hB=(10, 7), fF=(10, 0), fB=(-8, 0))


def walk_poses():
    res = []
    for i in range(6):
        a = i * 2 * math.pi / 6
        s, c = math.sin(a), math.cos(a)
        res.append(pose(**{**GUARD, 'bob': 1 + round(abs(s) * 2),
                           'fF': (2 + round(s * 9), round(max(0, c) * 6)),
                           'fB': (-2 - round(s * 9), round(max(0, -c) * 6)),
                           'hF': (20, -3 + (1 if i % 3 == 0 else 0)),
                           'hB': (10, 7 + (1 if i % 3 == 0 else 0))}))
    return res


HURT0 = pose(lean=-5, bob=1, head=(-5, 2), hF=(-4, 4), hB=(-8, -2), fF=(5, 0), fB=(-9, 0))

ANIMS = {
    'idle': [pose(**GUARD),
             pose(**{**GUARD, 'bob': 4, 'hF': (20, -2)}),
             pose(**{**GUARD, 'bob': 4, 'hF': (20, -2), 'hB': (10, 8)}),
             pose(**{**GUARD, 'hB': (10, 8)})],
    'walk': walk_poses(),
    'jump': [pose(lean=1, bob=-2, fF=(12, 16), fB=(-6, 10), hF=(14, -16), hB=(8, -8)),
             pose(lean=0, bob=-2, fF=(14, 5), fB=(-9, 3), hF=(16, -4), hB=(2, 2))],
    'attack1': [pose(lean=-2, bob=2, hF=(4, 6), hB=(12, 5), fF=(11, 0), fB=(-9, 0)),
                pose(lean=5, bob=2, hF=(36, -4), hB=(10, 8), fF=(13, 0), fB=(-10, 0)),
                pose(lean=3, bob=2, hF=(22, -2), hB=(10, 8), fF=(12, 0), fB=(-8, 0))],
    'attack2': [pose(lean=-1, bob=5, hF=(8, 12), hB=(10, 7), fF=(11, 0), fB=(-9, 0)),
                pose(lean=4, bob=1, hF=(24, -26), hB=(10, 7), fF=(11, 0), fB=(-9, 0)),
                pose(lean=2, bob=2, hF=(18, -8), hB=(10, 7), fF=(10, 0), fB=(-8, 0))],
    'attack3': [pose(lean=-3, hF=(16, -3), hB=(8, 7), fF=(12, 8), fB=(-5, 0)),
                pose(lean=-8, bob=2, hF=(8, 8), hB=(-6, 2), fF=(36, 24), fB=(-5, 0)),
                pose(lean=-4, hF=(16, -3), hB=(8, 7), fF=(17, 8), fB=(-5, 0))],
    'hurt': [HURT0,
             pose(lean=-4, bob=4, head=(-3, 3), hF=(0, 12), hB=(4, 12), fF=(7, 0), fB=(-8, 0))],
    'dead': 'rotate',
}
ORDER = ['idle', 'walk', 'jump', 'attack1', 'attack2', 'attack3', 'hurt', 'dead']


def build(P):
    sheet = Image.new('RGBA', (W * COLS, H * len(ORDER)), (0, 0, 0, 0))
    for row, name in enumerate(ORDER):
        if ANIMS[name] == 'rotate':
            base = hard_alpha(draw_char(P, HURT0))
            frames = []
            for ang, dy, dx in ((30, 0, 9), (65, 6, 21), (90, 20, 34)):
                big = Image.new('RGBA', (W * 3, H + 30), (0, 0, 0, 0))
                big.paste(base, (W, 0))
                rot = big.rotate(ang, resample=Image.NEAREST, center=(W + CX, GROUND))
                frames.append(outline(rot.crop((W - dx, dy, 2 * W - dx, H + dy))))
        else:
            frames = [outline(hard_alpha(draw_char(P, p))) for p in ANIMS[name]]
        for col, f in enumerate(frames):
            sheet.paste(f, (col * W, row * H))
    return sheet


if __name__ == '__main__':
    outdir = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(outdir, exist_ok=True)
    build(PAL_PLAYER).save(os.path.join(outdir, 'player.png'))
    build(PAL_ENEMY).save(os.path.join(outdir, 'enemy.png'))
    print('ok')
