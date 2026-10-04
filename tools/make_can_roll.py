"""Genera assets/sprites/can_roll.png: lata roja (como la de pie, pero mas larga) TUMBADA en el suelo, con el eje
HORIZONTAL, y 8 frames de rodar (la etiqueta da la vuelta al cilindro y la anilla de la tapa gira).
Hoja de 8 frames de 24x24 en horizontal. Para scripts/rolling_can.gd.
Uso: python tools/make_can_roll.py [salida.png]"""
import sys, os, math
from PIL import Image

FR = 8
SW, SH = 13, 6
A = (2.0, 3.0)               # extremo de la base (izquierda); eje HORIZONTAL
LEN, R, E = 7.0, 1.9, 1.6    # largo del cuerpo (mas larga que la lata de pie), radio, semieje de la tapa
S2 = math.sqrt(2)
OUT = (0x2a, 0x1c, 0x24)
RED = (0xa8, 0x14, 0x14); RED_L = (0xd0, 0x2c, 0x2a); RED_D = (0x78, 0x0c, 0x10)
LIME = (0xb0, 0xc8, 0x28); CREAM = (0xf0, 0xe8, 0xb0); CREAM_D = (0xc8, 0xc0, 0x80)
G1 = (0xb4, 0xb4, 0xb4); G2 = (0x8c, 0x8c, 0x8c); G3 = (0x64, 0x64, 0x64); SLOT = (0x10, 0x10, 0x14)


def coords(x, y):
    return x + 0.5 - A[0], y + 0.5 - A[1]   # t a lo largo del eje (horizontal), s perpendicular (+s = abajo)


def inside(x, y):
    t, s = coords(x, y)
    if abs(s) > R:
        return False
    if ((t - LEN) / E) ** 2 + (s / R) ** 2 <= 1.0:
        return True
    if (t / E) ** 2 + (s / R) ** 2 <= 1.0:   # el extremo trasero tambien es redondo (misma elipse)
        return True
    if 0 <= t <= LEN:
        return True
    k = math.sqrt(max(0.0, 1 - (s / R) ** 2))
    return LEN < t <= LEN + E * k   # solo se ve la tapa (la base queda oculta, recta)


def angdist(a, b):
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return abs(d)


def shade(c, s):
    if c is RED:
        return RED_L if s < -0.6 else (RED_D if s > 0.9 else RED)
    return c


mask = [[inside(x, y) for x in range(SW)] for y in range(SH)]
sheet = Image.new('RGBA', (SW * FR, SH), (0, 0, 0, 0))
for k in range(FR):
    th = k * 2 * math.pi / FR
    img = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))
    for y in range(SH):
        for x in range(SW):
            if not mask[y][x]:
                continue
            t, s = coords(x, y)
            edge = any(not (0 <= x + dx < SW and 0 <= y + dy < SH and mask[y + dy][x + dx])
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            u, v = (t - LEN) / E, s / R
            q = u * u + v * v
            if edge:
                c = OUT
            elif q <= 1.0:                     # tapa metalica (elipse) con la anilla/ranura que gira
                if q > 0.8:
                    c = G3 if s > 0 else G1     # borde de la tapa
                else:
                    c = G1 if q > 0.4 else G2
                    along = (u * math.cos(th) + v * math.sin(th))
                    across = abs(-u * math.sin(th) + v * math.cos(th))
                    if across < 0.3 and -0.1 < along < 0.8:
                        c = SLOT
            else:
                psi = math.asin(max(-1.0, min(1.0, s / R))) - th   # angulo sobre la lata (rueda hacia +s, abajo)
                c = RED
                if angdist(psi, 0.0) < 0.7 and 0.0 < t < 6.0:      # franja verde
                    c = LIME
                if angdist(psi, 2.5) < 0.85 and 0.5 < t < 5.2:      # etiqueta crema
                    c = CREAM if angdist(psi, 2.5) < 0.6 else CREAM_D
                c = shade(c, s) if c is RED else c
                if c in (LIME, CREAM) and s > 1.9:
                    c = CREAM_D if c is CREAM else (0x80, 0x98, 0x20)
            img.putpixel((x, y), c + (255,))
    sheet.paste(img, (k * SW, 0))

out = sys.argv[1] if len(sys.argv) > 1 else 'assets/sprites/can_roll.png'
os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
sheet.save(out)
print('ok', out, sheet.size)
