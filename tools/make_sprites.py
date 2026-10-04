"""Genera las hojas de sprites (pixel art 8 bits) del jugador y del enemigo.
Uso:  python tools/make_sprites.py [carpeta_salida]

Estilo Master System / Streets of Rage 1: personaje de ~45 px, paleta reducida,
sombreado plano de 2 tonos y contorno oscuro.
Cada frame es de 64x64 con los pies en (32, 60). Filas = animaciones (ver ORDER).
Las poses se definen con objetivos de manos y pies; brazos y piernas se resuelven con
cinemática inversa (2 huesos), así que las articulaciones se doblan de forma natural.
Para cambiar colores o rasgos edita PAL_PLAYER / PAL_ENEMY o las poses y vuelve a ejecutar.
"""
import math, random, sys, os
from PIL import Image, ImageDraw

W = H = 64
COLS = 8
CX, GROUND = 32, 60
OUT = (16, 12, 22, 255)
THIGH, SHIN = 9.0, 9.0
UARM, FARM = 7.5, 7.0
ANKLE = 3
TORSO = 12


def rgba(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def duo(base, dark):
    return (rgba(dark), rgba(base))


PAL_PLAYER = dict(
    skin=duo('e8b48c', 'b97c58'),
    hair=duo('5a3e2c', '34231a'), hair_tip=rgba('b89a78'),
    shirt=duo('34343e', '1a1a22'),
    jeans=duo('8fb4de', '5f86b8'),
    shoe=duo('f0f0f0', 'a0a0b0'),
    glasses=True, chain=True, graphic=True)

PAL_ENEMY = dict(
    skin=duo('d9a07c', 'a96f4e'),
    hair=duo('e0c040', 'a88a20'), hair_tip=rgba('fff2a8'),
    shirt=duo('c03030', '7a1a1a'),
    jeans=duo('46466a', '2a2a46'),
    shoe=duo('5a3e2c', '34231a'),
    glasses=False, chain=False, graphic=False)


# ---------------------------------------------------------------- geometría
def ik(A, T, l1, l2, prefer):
    dx, dy = T[0] - A[0], T[1] - A[1]
    dist = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / dist, dy / dist
    d = max(min(dist, l1 + l2 - 0.05), abs(l1 - l2) + 0.05)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    mx, my = A[0] + ux * a, A[1] + uy * a
    c1 = (mx - uy * h, my + ux * h)
    c2 = (mx + uy * h, my - ux * h)
    return (c1 if prefer(c1) > prefer(c2) else c2), (A[0] + ux * d, A[1] + uy * d)


def capsule(d, p0, p1, r0, r1, col):
    for p, r in ((p0, r0), (p1, r1)):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    d.polygon([(p0[0] + nx * r0, p0[1] + ny * r0), (p1[0] + nx * r1, p1[1] + ny * r1),
               (p1[0] - nx * r1, p1[1] - ny * r1), (p0[0] - nx * r0, p0[1] - ny * r0)], fill=col)


def limb(d, p0, p1, w0, w1, cols):
    """Miembro con 2 tonos planos: sombra y base (luz desde arriba-delante)."""
    dark, base = cols
    capsule(d, p0, p1, w0 / 2, w1 / 2, dark)
    capsule(d, (p0[0] + .6, p0[1] - .5), (p1[0] + .6, p1[1] - .5), max(w0 / 2 - 1, .4), max(w1 / 2 - 1, .4), base)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def shade(cols, k):
    return tuple(tuple(int(c * k) if i < 3 else c for i, c in enumerate(col)) for col in cols)


# ---------------------------------------------------------------- partes
def draw_shoe(d, foot, P, back):
    x, y = foot
    dark, base = shade(P['shoe'], 0.8) if back else P['shoe']
    d.polygon([(x - 3, y - 4), (x, y - 4), (x + 2, y - 2), (x + 5, y - 2), (x + 6, y - 1), (x + 6, y), (x - 3, y)], fill=base)
    d.line([(x - 3, y), (x + 6, y)], fill=dark)
    d.point((x - 3, y - 3), fill=dark)


def draw_leg(d, hip, foot, P, back):
    cols = shade(P['jeans'], 0.82) if back else P['jeans']
    knee, ankle = ik(hip, (foot[0], foot[1] - ANKLE), THIGH, SHIN, lambda p: p[0])
    limb(d, hip, knee, 6, 5, cols)
    limb(d, knee, ankle, 5, 4.5, cols)
    p = lerp(knee, ankle, 0.5)
    d.point((p[0] - 1, p[1]), fill=cols[0])
    draw_shoe(d, foot, P, back)


def draw_arm(d, shoulder, hand, P, back):
    skin = shade(P['skin'], 0.88) if back else P['skin']
    elbow, hand = ik(shoulder, hand, UARM, FARM, lambda p: p[1] - 0.3 * p[0])
    limb(d, elbow, hand, 3.6, 3.2, skin)
    limb(d, shoulder, elbow, 4.2, 3.8, skin)
    limb(d, shoulder, lerp(shoulder, elbow, 0.7), 5.4, 5.0, shade(P['shirt'], 0.75) if back else P['shirt'])      # manga
    d.ellipse([hand[0] - 1.8, hand[1] - 1.8, hand[0] + 1.8, hand[1] + 1.8], fill=skin[1])
    d.point((hand[0] + 1, hand[1] + 1), fill=skin[0])


def draw_head(d, c, P, rnd):
    hx, hy = int(round(c[0])), int(round(c[1]))
    skin, hair = P['skin'], P['hair']
    d.rectangle([hx - 1, hy + 3, hx + 1, hy + 6], fill=skin[0])                   # cuello
    d.rectangle([hx - 4, hy - 4, hx + 4, hy + 4], fill=skin[1])                   # cara
    for p in ((hx - 4, hy + 4), (hx + 4, hy + 4)):
        d.point(p, fill=(0, 0, 0, 0))
    d.rectangle([hx - 4, hy + 1, hx - 3, hy + 3], fill=skin[0])                   # sombra trasera
    d.point((hx + 5, hy + 1), fill=skin[1])                                       # nariz
    d.point((hx + 5, hy + 2), fill=skin[1])
    if P['glasses']:
        fr = rgba('101018')
        d.rectangle([hx - 1, hy - 2, hx + 5, hy + 1], fill=fr)                    # montura gruesa
        d.rectangle([hx, hy - 1, hx + 1, hy], fill=rgba('b9dcf0'))
        d.rectangle([hx + 3, hy - 1, hx + 4, hy], fill=rgba('b9dcf0'))
        d.point((hx + 1, hy), fill=fr)
        d.point((hx + 4, hy), fill=fr)
        d.line([(hx - 1, hy - 2), (hx - 3, hy - 2)], fill=fr)
        d.line([(hx + 2, hy + 3), (hx + 4, hy + 3)], fill=rgba('f6f6f6'))         # sonrisa
        d.point((hx + 1, hy + 3), fill=rgba('7a2e2e'))
        d.point((hx + 5, hy + 3), fill=rgba('7a2e2e'))
    else:
        ink = rgba('101018')
        d.point((hx + 1, hy), fill=ink)
        d.point((hx + 4, hy), fill=ink)
        d.line([(hx, hy - 2), (hx + 2, hy - 1)], fill=ink)
        d.line([(hx + 3, hy - 1), (hx + 5, hy - 2)], fill=ink)
        d.line([(hx + 1, hy + 3), (hx + 4, hy + 3)], fill=rgba('7a2e2e'))
    # pelo rizado
    d.ellipse([hx - 5, hy - 7, hx + 5, hy - 2], fill=hair[1])
    d.rectangle([hx - 5, hy - 5, hx - 3, hy + 2], fill=hair[1])
    for k in range(7):
        ang = math.pi * (1.0 + k / 6.0 * 1.15)
        px, py = hx + math.cos(ang) * 4.8, hy - 2 + math.sin(ang) * 4.6
        d.ellipse([px - 1.4, py - 1.4, px + 1.4, py + 1.4], fill=hair[1] if k % 2 else hair[0])
    for k in range(5):
        d.point((hx - 4 + k * 2, hy - 7 + rnd.randint(0, 1)), fill=P['hair_tip'])
    d.point((hx - 5, hy - 1), fill=hair[0])
    d.point((hx - 5, hy + 1), fill=hair[0])


def draw_torso(d, S, Pv, P, wide):
    sh = P['shirt']
    hs = 4.0 + 2.5 * wide          # semiancho en los hombros
    hw = 3.5 + 2.0 * wide          # semiancho en la cintura
    pts = [(S[0] - hs, S[1] + 1), (S[0] - hs * 0.45, S[1] - 1), (S[0] + hs * 0.6, S[1] - 1), (S[0] + hs, S[1] + 1),
           (Pv[0] + hw, Pv[1]), (Pv[0] + hw, Pv[1] + 2), (Pv[0] - hw, Pv[1] + 2), (Pv[0] - hw - 0.5, Pv[1])]
    d.polygon(pts, fill=sh[1])
    d.polygon([(S[0] - hs, S[1] + 1), (S[0] - hs * 0.45, S[1] - 1), (S[0] - hs * 0.2, S[1]), (Pv[0] - hw * 0.3, Pv[1] + 2),
               (Pv[0] - hw, Pv[1] + 2), (Pv[0] - hw - 0.5, Pv[1])], fill=sh[0])
    d.polygon([(S[0] - 2, S[1] - 1), (S[0] + 3, S[1] - 1), (S[0] + 1, S[1] + 1), (S[0] - 1, S[1] + 1)], fill=P['skin'][0])
    if wide > 0.5:                                                   # el pecho solo se ve de tres cuartos
        if P['graphic']:
            gx, gy = S[0] + 1, S[1] + 4
            d.rectangle([gx - 2, gy - 1, gx + 2, gy + 2], fill=rgba('24448a'))
            d.rectangle([gx - 1, gy, gx + 2, gy + 1], fill=rgba('f0a830'))
            d.point((gx - 2, gy - 1), fill=rgba('a9cbe2'))
        if P['chain']:
            c = rgba('dde1ea')
            for p in ((-2, 1), (-1, 2), (3, 1), (2, 2), (0, 3), (1, 3)):
                d.point((S[0] + p[0], S[1] + p[1]), fill=c)
    elif P['chain']:                                                 # de perfil: solo un destello de la cadena
        d.point((S[0] + hs - 1, S[1] + 2), fill=rgba('dde1ea'))
    return hw


def draw_pelvis(d, Pv, P, wide):
    j = P['jeans']
    hw = 3.5 + 2.0 * wide
    x0, x1 = int(round(Pv[0] - hw)), int(round(Pv[0] + hw - 0.5))
    d.rectangle([x0, Pv[1] - 1, x1, Pv[1] + 3], fill=j[1])
    d.rectangle([x0, Pv[1] - 1, x0 + 1, Pv[1] + 3], fill=j[0])
    d.line([(x0, Pv[1] - 1), (x1, Pv[1] - 1)], fill=rgba('26262e'))      # cinturón


def draw_char(P, pose, seed=7):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    wide = pose['wide']
    Pv = (CX + pose['px'], GROUND - ANKLE - THIGH - SHIN - 2 + pose['bob'])
    S = (Pv[0] + pose['lean'], Pv[1] - TORSO)
    head = (S[0] + 1 + pose['head'][0], S[1] - 6 + pose['head'][1])
    sF = (S[0] + 1.5 + 2.5 * wide, S[1] + 2)
    sB = (S[0] - 1 - 1.0 * wide, S[1] + 3)
    off = 1 + wide
    hipF, hipB = (Pv[0] + off, Pv[1] + 2), (Pv[0] - off, Pv[1] + 2)
    foot = lambda f: (CX + f[0], GROUND - f[1])

    draw_leg(d, hipB, foot(pose['fB']), P, True)
    draw_leg(d, hipF, foot(pose['fF']), P, False)
    draw_pelvis(d, Pv, P, wide)
    draw_arm(d, sB, (S[0] + pose['hB'][0], S[1] + pose['hB'][1]), P, True)   # detras del torso
    draw_torso(d, S, Pv, P, wide)
    draw_head(d, head, P, rnd)
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
    px = im.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= 128 else 0)
    return im


# ---------------------------------------------------------------- poses
def pose(**k):
    base = dict(bob=0, px=0, lean=0, wide=1.0, head=(0, 0),
                hF=(11, -2), hB=(9, 4), fF=(5, 0), fB=(-4, 0))
    base.update(k)
    return base


GUARD = dict(lean=1, head=(1, 0), bob=2, hF=(11, -2), hB=(9, 4), fF=(6, 0), fB=(-4, 0))


def walk_poses():
    """Caminar de perfil (estrecho): zancada completa y brazos que se balancean."""
    res = []
    for i in range(6):
        a = i * 2 * math.pi / 6
        s, c = math.sin(a), math.cos(a)
        res.append(pose(wide=0.0, lean=1, head=(1, 0), bob=1 + round(abs(s)),
                        fF=(round(s * 6), round(max(0, c) * 3)),
                        fB=(round(-s * 6), round(max(0, -c) * 3)),
                        hF=(5 - round(s * 5), 7 - round(abs(c))),
                        hB=(2 + round(s * 5), 7 - round(abs(c)))))
    return res


HURT0 = pose(lean=-3, bob=1, head=(-3, 1), hF=(-2, 2), hB=(-4, -1), fF=(3, 0), fB=(-5, 0))

ANIMS = {
    'idle': [pose(**GUARD),
             pose(**{**GUARD, 'bob': 3, 'hF': (11, -1)}),
             pose(**{**GUARD, 'bob': 3, 'hF': (11, -1), 'hB': (9, 5)}),
             pose(**{**GUARD, 'hB': (9, 5)})],
    'walk': walk_poses(),
    'jump': [pose(wide=0.5, lean=1, bob=-1, fF=(7, 9), fB=(-3, 6), hF=(8, -9), hB=(4, -4)),
             pose(wide=0.5, lean=0, bob=-1, fF=(8, 3), fB=(-5, 2), hF=(9, -2), hB=(1, 1))],
    'attack1': [pose(lean=-1, bob=2, hF=(2, 3), hB=(9, 3), fF=(6, 0), fB=(-5, 0)),
                pose(lean=3, bob=2, hF=(20, -2), hB=(9, 5), fF=(7, 0), fB=(-6, 0)),
                pose(lean=2, bob=2, hF=(12, -1), hB=(9, 5), fF=(7, 0), fB=(-5, 0))],
    'attack2': [pose(lean=-1, bob=3, hF=(4, 7), hB=(9, 4), fF=(6, 0), fB=(-5, 0)),
                pose(lean=2, bob=1, hF=(13, -14), hB=(9, 4), fF=(6, 0), fB=(-5, 0)),
                pose(lean=1, bob=2, hF=(10, -5), hB=(9, 4), fF=(6, 0), fB=(-4, 0))],
    'attack3': [pose(lean=-2, hF=(10, -2), hB=(8, 4), fF=(7, 5), fB=(-3, 0)),
                pose(lean=-4, bob=1, hF=(5, 4), hB=(-3, 1), fF=(20, 13), fB=(-3, 0)),
                pose(lean=-2, hF=(10, -2), hB=(8, 4), fF=(9, 5), fB=(-3, 0))],
    'hurt': [HURT0,
             pose(lean=-4, bob=2, head=(-4, 2), hF=(-3, 3), hB=(-5, 0), fF=(2, 0), fB=(-6, 0)),
             pose(lean=-2, bob=2, head=(-2, 1), hF=(5, 1), hB=(5, 3), fF=(4, 0), fB=(-5, 0))],
    'dead': 'rotate',
}
ORDER = ['idle', 'walk', 'jump', 'attack1', 'attack2', 'attack3', 'hurt', 'dead']


def build(P):
    sheet = Image.new('RGBA', (W * COLS, H * len(ORDER)), (0, 0, 0, 0))
    for row, name in enumerate(ORDER):
        if ANIMS[name] == 'rotate':
            base = hard_alpha(draw_char(P, HURT0))
            frames = []
            for ang, dy, dx in ((30, 0, 6), (65, 3, 14), (90, 12, 24)):
                big = Image.new('RGBA', (W * 3, H + 20), (0, 0, 0, 0))
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
