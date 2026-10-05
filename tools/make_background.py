"""Genera assets/backgrounds/calle_tajo.png (1280x224): calle andaluza en pixel art, 1 px del fondo = 1 px del juego.
Es una escena ORIGINAL inspirada en la arquitectura de un barrio sevillano (fachadas encaladas, zócalo almagre,
balcones de forja, rejas, tejados de teja, naranjos). No usa imágenes de Google Street View.
Uso: python tools/make_background.py [salida.png]"""
import random, sys
from PIL import Image, ImageDraw

W, H = 1280, 224
SIDEWALK_Y = 118
CURB_Y = 138
rnd = random.Random(2024)
img = Image.new('RGB', (W, H))
d = ImageDraw.Draw(img)


def rect(x0, y0, x1, y1, c):
    """Rectángulo incluyendo los bordes, como en un editor de píxel-art (x1,y1 exclusivos)."""
    if x1 > x0 and y1 > y0:
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=c)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((x, y), c)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# ---------- paleta ----------
SKY = [(0x6f, 0xb5, 0xe8), (0x7d, 0xc0, 0xee), (0x8c, 0xca, 0xf0), (0x9b, 0xd3, 0xf2),
       (0xaa, 0xdb, 0xf4), (0xb9, 0xe2, 0xf5), (0xc8, 0xe9, 0xf6), (0xd6, 0xef, 0xf7)]
WALLS = [(0xf2, 0xee, 0xe2), (0xf0, 0xe4, 0xbc), (0xe8, 0xc4, 0x7a), (0xec, 0xc0, 0xa4),
         (0xc9, 0xdc, 0xe6), (0xf4, 0xf0, 0xdc), (0xe6, 0xd2, 0x9a)]
ZOCALO = [(0xa6, 0x45, 0x30), (0x4d, 0x5d, 0x7f), (0x8a, 0x3a, 0x2c), (0x5c, 0x6e, 0x58)]
TILE = (0xc4, 0x55, 0x2f)
TILE_D = (0x8e, 0x33, 0x20)
IRON = (0x1d, 0x1b, 0x24)
WOOD = (0x6b, 0x42, 0x26)
GLASS = (0x2a, 0x36, 0x50)
GREEN = (0x3f, 0x6e, 0x3c)

# ---------- cielo + lejanía ----------
for i, c in enumerate(SKY):
    rect(0, i * 16, W, i * 16 + 16, c)
for _ in range(14):                      # nubes
    cx, cy = rnd.randint(0, W), rnd.randint(8, 50)
    for k in range(rnd.randint(3, 5)):
        rw, rh = rnd.randint(16, 30), rnd.randint(4, 7)
        rect(cx + k * 12 - 6, cy - rh // 2 + (k % 2) * 2, cx + k * 12 - 6 + rw, cy + rh // 2 + 3 + (k % 2) * 2, (0xf6, 0xfb, 0xff))
    rect(cx - 6, cy + 3, cx + 40, cy + 5, (0xdd, 0xee, 0xf8))

FAR = (0xa6, 0xbe, 0xd2)
FAR_D = (0x93, 0xac, 0xc4)
x = 0
while x < W:                              # casas lejanas
    bw, bh = rnd.randint(30, 60), rnd.randint(40, 80)
    rect(x, SIDEWALK_Y - bh, x + bw, SIDEWALK_Y, FAR)
    rect(x + bw - 2, SIDEWALK_Y - bh, x + bw, SIDEWALK_Y, FAR_D)
    x += bw + rnd.randint(-4, 6)
# torre de iglesia con campanario (hacia 1/3 y 5/6 del nivel)
for tx in (410, 1040):
    rect(tx, 22, tx + 26, SIDEWALK_Y, (0xe4, 0xd6, 0xb2))
    rect(tx + 22, 22, tx + 26, SIDEWALK_Y, (0xc9, 0xb8, 0x90))
    rect(tx - 2, 20, tx + 28, 24, (0xb8, 0xa2, 0x78))
    rect(tx + 4, 30, tx + 12, 52, (0x5a, 0x4a, 0x3a))      # hueco campanas
    rect(tx + 5, 28, tx + 11, 30, (0x5a, 0x4a, 0x3a))
    rect(tx + 6, 38, tx + 10, 44, (0xc8, 0x9a, 0x3a))      # campana
    rect(tx + 2, 8, tx + 24, 20, (0xe4, 0xd6, 0xb2))        # cuerpo superior
    rect(tx + 9, 11, tx + 17, 18, (0x5a, 0x4a, 0x3a))
    rect(tx + 8, 0, tx + 18, 8, TILE)                       # chapitel
    rect(tx + 12, -2, tx + 14, 0, IRON)

sky_snapshot = img.copy()   # cielo + lejanía, para poder 'borrar' casas bajo un enclave

def paint_sidewalk(xa, xb, base=(0xc8, 0xbd, 0xa4), joint=(0xa4, 0x98, 0x7e), hi=(0xe0, 0xd6, 0xbe), y1=None, curb=True):
    """Acera en perspectiva a 45 grados (como en Streets of Rage): las juntas perpendiculares a la fachada
    se ven en diagonal, las paralelas en horizontal, y el bordillo muestra su arista y su cara frontal."""
    y1 = CURB_Y if y1 is None else y1
    rect(xa, SIDEWALK_Y, xb, y1, base)
    rect(xa, SIDEWALK_Y, xb, SIDEWALK_Y + 1, hi)                       # arista junto a la fachada
    for yy in (SIDEWALK_Y + 7, SIDEWALK_Y + 14):                        # juntas paralelas a la fachada
        if yy < y1:
            rect(xa, yy, xb, yy + 1, joint)
    depth = y1 - SIDEWALK_Y
    for x0 in range(xa - xa % 20 - 20, xb + 40, 20):                    # juntas en diagonal (45 grados)
        for k in range(depth - 1):
            x, y = x0 + k, y1 - 1 - k
            if xa <= x < xb:
                px(x, y, joint)
    if curb:
        rect(xa, CURB_Y, xb, CURB_Y + 1, (0xb8, 0xb0, 0xa0))           # arista superior del bordillo
        rect(xa, CURB_Y + 1, xb, CURB_Y + 2, (0x9a, 0x92, 0x84))        # cara frontal
        rect(xa, CURB_Y + 2, xb, CURB_Y + 3, (0x6a, 0x64, 0x5c))        # sombra


# ---------- acera y calle (se dibujan antes que los edificios para que la base los tape) ----------
paint_sidewalk(0, W)
ASPH = (0x5b, 0x59, 0x63)
rect(0, CURB_Y + 3, W, H, ASPH)
for yy in range(CURB_Y + 3, H):                         # asfalto con degradado y grano
    t = (yy - CURB_Y) / (H - CURB_Y)
    base = shade(ASPH, 0.92 + 0.22 * t)
    rect(0, yy, W, yy + 1, base)
for _ in range(5200):
    xx, yy = rnd.randint(0, W - 1), rnd.randint(CURB_Y + 3, H - 1)
    px(xx, yy, shade(ASPH, rnd.choice((0.8, 0.85, 1.15, 1.25))))
rect(0, CURB_Y + 3, W, CURB_Y + 5, (0x4a, 0x48, 0x52))   # sombra junto al bordillo
for xx in range(8, W, 48):                               # línea discontinua
    rect(xx, 184, xx + 22, 186, (0xd8, 0xd2, 0xb8))
for xx in range(0, W, 32):                               # pasos de cebra cada tanto en x=300
    pass
for k in range(7):                                       # paso de peatones
    rect(300 + k * 8, 140, 300 + k * 8 + 5, 214, (0xcf, 0xca, 0xb8)) if False else None


# ---------- casas ----------
FONT = {  # fuente 3x5 para el azulejo con el nombre de la calle
    'C': ["111", "100", "100", "100", "111"], 'T': ["111", "010", "010", "010", "010"],
    'A': ["010", "101", "111", "101", "101"], 'J': ["001", "001", "001", "101", "010"],
    'O': ["010", "101", "101", "101", "010"], '/': ["001", "001", "010", "100", "100"],
    ' ': ["000"] * 5,
}


def text(x0, y0, s, c):
    for ch in s:
        for r, row in enumerate(FONT[ch]):
            for k, v in enumerate(row):
                if v == '1':
                    px(x0 + k, y0 + r, c)
        x0 += 4


def window(x0, y0, w, h, shutters=None):
    rect(x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1, (0xf8, 0xf6, 0xee))
    rect(x0, y0, x0 + w, y0 + h, GLASS)
    rect(x0 + 1, y0 + 1, x0 + 3, y0 + h - 1, (0x4a, 0x5a, 0x7a))  # reflejo
    rect(x0 + w // 2, y0, x0 + w // 2 + 1, y0 + h, (0xf8, 0xf6, 0xee))
    rect(x0 - 2, y0 + h + 1, x0 + w + 2, y0 + h + 2, (0xb8, 0xae, 0x98))  # alféizar
    if shutters:
        rect(x0 - 4, y0 - 1, x0 - 1, y0 + h + 1, shutters)
        rect(x0 + w + 1, y0 - 1, x0 + w + 4, y0 + h + 1, shutters)
        for yy in range(y0, y0 + h, 2):
            rect(x0 - 4, yy, x0 - 1, yy + 1, shade(shutters, 0.75))
            rect(x0 + w + 1, yy, x0 + w + 4, yy + 1, shade(shutters, 0.75))


def reja(x0, y0, w, h):
    window(x0, y0, w, h)
    for xx in range(x0 + 1, x0 + w, 3):
        rect(xx, y0, xx + 1, y0 + h, IRON)
    rect(x0, y0 + h // 2, x0 + w, y0 + h // 2 + 1, IRON)
    rect(x0 - 1, y0 + h - 1, x0 + w + 1, y0 + h, IRON)


def door(x0, y0, w, h, c=WOOD):
    rect(x0 - 1, y0 - 2, x0 + w + 1, y0 + h, (0xf8, 0xf6, 0xee))
    rect(x0, y0 - 1, x0 + w, y0 + h, c)
    rect(x0 + 2, y0 + 2, x0 + w // 2 - 1, y0 + h // 2 - 1, shade(c, 0.78))
    rect(x0 + w // 2 + 1, y0 + 2, x0 + w - 2, y0 + h // 2 - 1, shade(c, 0.78))
    rect(x0 + 2, y0 + h // 2 + 2, x0 + w - 2, y0 + h - 2, shade(c, 0.85))
    px(x0 + w - 3, y0 + h // 2, (0xe8, 0xc0, 0x50))      # picaporte


def balcony(cx, y_floor, w=20, door_c=GREEN):
    """Balcón de forja con puerta de contraventanas verdes. y_floor = suelo del balcón."""
    x0 = cx - w // 2
    rect(x0 + 3, y_floor - 24, x0 + w - 3, y_floor, (0xf8, 0xf6, 0xee))
    rect(x0 + 4, y_floor - 23, x0 + w - 4, y_floor, GLASS)
    rect(x0 + 4, y_floor - 23, x0 + w // 2, y_floor, door_c)             # hoja izquierda
    rect(x0 + w // 2 + 1, y_floor - 23, x0 + w - 4, y_floor, shade(door_c, 0.9))
    for yy in range(y_floor - 22, y_floor, 2):
        rect(x0 + 4, yy, x0 + w - 4, yy + 1, shade(door_c, 0.72))
    rect(x0, y_floor, x0 + w, y_floor + 2, (0xd8, 0xd0, 0xbc))            # losa
    rect(x0, y_floor + 2, x0 + w, y_floor + 3, (0x9a, 0x90, 0x7c))
    rect(x0, y_floor - 7, x0 + w, y_floor - 6, IRON)                      # barandilla
    for xx in range(x0, x0 + w, 2):
        rect(xx, y_floor - 7, xx + 1, y_floor, IRON)
    for xx in range(x0 + 3, x0 + w - 2, 6):                              # macetas
        rect(xx, y_floor - 11, xx + 3, y_floor - 7, (0x9c, 0x4a, 0x2a))
        rect(xx, y_floor - 13, xx + 3, y_floor - 11, (0x3a, 0x7a, 0x3a))
        px(xx + 1, y_floor - 14, (0xd8, 0x2a, 0x3a))
        px(xx + 2, y_floor - 13, (0xe8, 0x4a, 0x5a))


def house(x0, w, n_floors, wall, zoc, roof_kind, shop=False):
    h = 38 + 34 * (n_floors - 1) + 10
    top = SIDEWALK_Y - h
    right = x0 + w
    rect(x0, top, right, SIDEWALK_Y, wall)
    for _ in range(w * h // 70):                      # textura de cal
        px(rnd.randint(x0, right - 1), rnd.randint(top, SIDEWALK_Y - 9), shade(wall, rnd.choice((0.95, 0.93, 1.03))))
    rect(right - 3, top, right, SIDEWALK_Y, shade(wall, 0.84))
    rect(x0, top, x0 + 1, SIDEWALK_Y, shade(wall, 1.05))
    # cornisa / tejado
    if roof_kind == 'tile':
        rect(x0 - 3, top - 7, right + 3, top, TILE)
        for xx in range(x0 - 3, right + 3, 3):
            rect(xx, top - 7, xx + 1, top, TILE_D)
        rect(x0 - 3, top - 2, right + 3, top, TILE_D)
        rect(x0 - 3, top, right + 3, top + 2, (0xf8, 0xf4, 0xe8))
        rect(x0 - 3, top + 2, right + 3, top + 3, shade(wall, 0.7))
    else:  # azotea con pretil
        rect(x0 - 1, top - 6, right + 1, top, (0xf8, 0xf4, 0xe8))
        rect(x0 - 1, top - 6, right + 1, top - 5, (0xd8, 0xd0, 0xbc))
        rect(x0 - 1, top, right + 1, top + 2, shade(wall, 0.85))
        if rnd.random() < 0.6:                          # depósito / chimenea
            cx = rnd.randint(x0 + 6, right - 14)
            rect(cx, top - 14, cx + 8, top - 6, (0xb8, 0xa8, 0x90))
            rect(cx, top - 14, cx + 8, top - 13, (0x8a, 0x7a, 0x62))
    # zócalo
    rect(x0, SIDEWALK_Y - 9, right, SIDEWALK_Y, zoc)
    rect(x0, SIDEWALK_Y - 10, right, SIDEWALK_Y - 9, shade(zoc, 0.7))
    rect(x0, SIDEWALK_Y - 9, right, SIDEWALK_Y - 8, shade(zoc, 1.2))
    # plantas
    slots = max(1, (w - 8) // 28)
    gap = w / slots
    gy = SIDEWALK_Y - 9      # suelo planta baja
    kinds = []
    for s in range(slots):
        cx = int(x0 + gap * (s + 0.5))
        k = rnd.choice(['door', 'reja', 'reja', 'garage']) if not shop else 'shop'
        if s == 0 and not shop and slots > 1:
            k = 'door'
        kinds.append(k)
        if k == 'door':
            door(cx - 7, gy - 29, 14, 29, rnd.choice((WOOD, (0x3a, 0x5a, 0x3a), (0x7a, 0x2a, 0x2a))))
        elif k == 'reja':
            reja(cx - 8, gy - 26, 16, 18)
        elif k == 'garage':
            rect(cx - 10, gy - 30, cx + 10, gy, (0xf8, 0xf6, 0xee))
            rect(cx - 9, gy - 29, cx + 9, gy, (0x6e, 0x72, 0x7a))
            for yy in range(gy - 28, gy, 3):
                rect(cx - 9, yy, cx + 9, yy + 1, (0x5a, 0x5e, 0x66))
        elif k == 'shop':
            rect(cx - 12, gy - 28, cx + 12, gy, (0xf8, 0xf6, 0xee))
            rect(cx - 11, gy - 24, cx + 11, gy, GLASS)
            rect(cx - 10, gy - 22, cx - 4, gy - 8, (0x5a, 0x7a, 0x9a))
            for k2 in range(5):                           # toldo a rayas
                c = (0xc8, 0x30, 0x30) if k2 % 2 == 0 else (0xf4, 0xf0, 0xe0)
                rect(cx - 14 + k2 * 6, gy - 32, cx - 14 + k2 * 6 + 6, gy - 25, c)
            rect(cx - 14, gy - 25, cx + 16, gy - 24, (0x8a, 0x20, 0x20))
    for f in range(1, n_floors):
        fy = gy - 38 * 0 - 34 * f - 4       # suelo de la planta f
        for s in range(slots):
            cx = int(x0 + gap * (s + 0.5))
            if rnd.random() < 0.65:
                balcony(cx, fy + 2, 20 if gap > 24 else 16, rnd.choice((GREEN, (0x5a, 0x3a, 0x22), (0x2a, 0x4a, 0x6a))))
            else:
                window(cx - 6, fy - 20, 12, 16, rnd.choice((GREEN, (0x5a, 0x3a, 0x22), None)))
    # cables eléctricos sueltos / aire acondicionado
    if rnd.random() < 0.5:
        ax = rnd.randint(x0 + 4, right - 16)
        rect(ax, top + 8, ax + 10, top + 14, (0xe8, 0xe8, 0xe8))
        rect(ax, top + 12, ax + 10, top + 14, (0xb0, 0xb0, 0xb0))
    return top


x = -8
specs = []
while x < W:
    w = rnd.choice((84, 96, 112, 126))
    n = rnd.choice((1, 2, 2, 2))
    wall = rnd.choice(WALLS)
    zoc = rnd.choice(ZOCALO)
    kind = rnd.choice(('tile', 'tile', 'flat'))
    specs.append((x, w, n, wall, zoc, kind))
    x += w
for i, (x0, w, n, wall, zoc, kind) in enumerate(specs):
    # nunca dos casas contiguas del mismo color
    if i and specs[i - 1][3] == wall:
        wall = WALLS[(WALLS.index(wall) + 1) % len(WALLS)]
    house(x0, w, n, wall, zoc, kind, shop=(i % 7 == 3))

# azulejo con el nombre de la calle en una esquina
for ax in (22, 700):
    rect(ax, 44, ax + 34, 56, (0xf8, 0xf8, 0xf8))
    rect(ax + 1, 45, ax + 33, 55, (0x2a, 0x4f, 0xa8))
    rect(ax + 2, 46, ax + 32, 54, (0xf2, 0xf4, 0xf8))
    text(ax + 5, 48, "C/ TAJO", (0x1c, 0x3c, 0x8a))

# ---------- mobiliario urbano ----------
def orange_tree(cx):
    rect(cx - 1, SIDEWALK_Y + 2, cx + 2, SIDEWALK_Y + 12, (0x5a, 0x38, 0x22))
    rect(cx - 5, SIDEWALK_Y + 10, cx + 6, SIDEWALK_Y + 14, (0x8a, 0x6a, 0x4a))  # alcorque
    for dy in range(-22, 6):
        rw = int(((1 - ((dy + 8) / 15.0) ** 2) ** 0.5) * 13) if abs(dy + 8) < 15 else 0
        rect(cx - rw, SIDEWALK_Y + dy - 6, cx + rw + 1, SIDEWALK_Y + dy - 5, (0x2f, 0x6a, 0x34))
    for _ in range(60):
        xx, yy = cx + rnd.randint(-12, 12), SIDEWALK_Y + rnd.randint(-26, -2)
        if img.getpixel((xx, yy)) in ((0x2f, 0x6a, 0x34),):
            px(xx, yy, rnd.choice(((0x4c, 0x92, 0x44), (0x22, 0x52, 0x2a))))
    for _ in range(9):
        xx, yy = cx + rnd.randint(-10, 10), SIDEWALK_Y + rnd.randint(-24, -6)
        if img.getpixel((xx, yy))[1] > 0x40 and img.getpixel((xx, yy))[0] < 0x70:
            rect(xx, yy, xx + 2, yy + 2, (0xf2, 0x90, 0x1c))


def farola(cx):
    rect(cx, SIDEWALK_Y - 52, cx + 2, SIDEWALK_Y + 12, IRON)
    rect(cx - 2, SIDEWALK_Y + 8, cx + 4, SIDEWALK_Y + 12, (0x2c, 0x2a, 0x34))
    rect(cx - 3, SIDEWALK_Y - 60, cx + 5, SIDEWALK_Y - 52, (0xf6, 0xe8, 0xa8))
    rect(cx - 4, SIDEWALK_Y - 62, cx + 6, SIDEWALK_Y - 60, IRON)
    rect(cx - 3, SIDEWALK_Y - 52, cx + 5, SIDEWALK_Y - 50, IRON)


def bolardo(cx):
    rect(cx, SIDEWALK_Y + 8, cx + 4, SIDEWALK_Y + 14, (0x88, 0x84, 0x7c))
    rect(cx, SIDEWALK_Y + 8, cx + 4, SIDEWALK_Y + 9, (0xb4, 0xb0, 0xa4))
    rect(cx + 3, SIDEWALK_Y + 9, cx + 4, SIDEWALK_Y + 14, (0x6a, 0x66, 0x5e))


_real_img, _real_d = img, d          # los naranjos se quitaron: se "dibujan" en una imagen vacía
img = Image.new('RGB', (W, H))       # solo para no alterar la secuencia aleatoria del resto de la escena
d = ImageDraw.Draw(img)
for tx in range(130, W, 215):
    orange_tree(tx + rnd.randint(-10, 10))
img, d = _real_img, _real_d
if '--day' in sys.argv:
    for fx in range(60, W, 330):
        farola(fx + 40)
for bx in range(40, W, 90):
    if all(abs(bx - t) > 30 for t in range(130, W, 215)):
        bolardo(bx)

# ---------- enclave: "La Cueva Roja" (tienda de cómics y juegos), al final de la calle ----------
FONT.update({
    'L': ["100", "100", "100", "100", "111"], 'U': ["101", "101", "101", "101", "111"],
    'E': ["111", "100", "110", "100", "111"], 'V': ["101", "101", "101", "101", "010"],
    'R': ["110", "101", "110", "101", "101"], 'J': ["001", "001", "001", "101", "010"],
    'O': ["010", "101", "101", "101", "010"], 'A': ["010", "101", "111", "101", "101"],
})


def cueva_roja(x0):
    w = W - x0
    top = SIDEWALK_Y - 86
    CREAM = (0xea, 0xd8, 0xac)
    BRICK = (0xc0, 0x52, 0x30)
    BRICK_D = (0x96, 0x3a, 0x24)
    RED = (0xd8, 0x20, 0x2a)
    # acera de baldosa clara delante
    paint_sidewalk(x0 - 6, W)
    paint_sidewalk(x0 + 24, x0 + 112, base=(0xe6, 0xe2, 0xda), joint=(0xcf, 0xca, 0xc0), hi=(0xf2, 0xee, 0xe6), y1=CURB_Y - 2, curb=False)   # solado blanco de la entrada
    # fachada
    rect(x0, top, W, SIDEWALK_Y, CREAM)
    rect(x0, top, x0 + 2, SIDEWALK_Y, (0x20, 0x1c, 0x18))                   # medianera con la casa vecina
    rect(x0 + 2, top, x0 + 4, SIDEWALK_Y, shade(CREAM, 0.8))
    for _ in range(w * 86 // 60):
        px(rnd.randint(x0, W - 1), rnd.randint(top, SIDEWALK_Y - 12), shade(CREAM, rnd.choice((0.95, 0.93, 1.03))))
    # tejado
    rect(x0, top - 7, W, top, TILE)
    for xx in range(x0, W, 3):
        rect(xx, top - 7, xx + 1, top, TILE_D)
    rect(x0, top - 2, W, top, TILE_D)
    rect(x0, top, W, top + 2, (0xf8, 0xf4, 0xe8))
    # planta alta: ventana con balcón y contraventanas
    window(x0 + 56, top + 8, 14, 18, GREEN)
    window(x0 + 96, top + 8, 14, 18, (0x5a, 0x3a, 0x22))
    # pilares y base de ladrillo
    def brick(xa, xb, ya, yb):
        rect(xa, ya, xb, yb, BRICK)
        for yy in range(ya, yb, 4):
            rect(xa, yy, xb, yy + 1, BRICK_D)
            off = 0 if ((yy - ya) // 4) % 2 == 0 else 3
            for xx in range(xa + off, xb, 6):
                rect(xx, yy, xx + 1, yy + 4, BRICK_D)
    brick(x0 + 16, x0 + 24, top + 30, SIDEWALK_Y)       # pilar junto a la reja
    brick(x0 + 112, x0 + 120, top + 30, SIDEWALK_Y)     # pilar derecho de la puerta
    brick(x0 + 120, W, top + 14, SIDEWALK_Y)            # gran pilar/lateral de ladrillo
    brick(x0 + 2, x0 + 16, SIDEWALK_Y - 24, SIDEWALK_Y)  # zócalo de ladrillo izquierdo
    rect(x0 + 2, SIDEWALK_Y - 25, x0 + 16, SIDEWALK_Y - 24, (0xd8, 0xb0, 0x90))
    rect(x0 + 120, top + 14, W, top + 16, (0xe0, 0xa0, 0x70))
    # reja negra de la puerta de la izquierda
    rect(x0 + 2, SIDEWALK_Y - 48, x0 + 15, SIDEWALK_Y - 25, IRON)
    for yy in range(SIDEWALK_Y - 46, SIDEWALK_Y - 25, 4):
        rect(x0 + 3, yy, x0 + 14, yy + 1, (0x3a, 0x38, 0x44))
    for xx in range(x0 + 4, x0 + 14, 3):
        rect(xx, SIDEWALK_Y - 48, xx + 1, SIDEWALK_Y - 25, (0x3a, 0x38, 0x44))
    # cartel redondo rojo en la pared (esquina izquierda)
    cx, cy = x0 + 28, top + 23
    for dy in range(-9, 10):
        rw = int((81 - dy * dy) ** 0.5)
        rect(cx - rw, cy + dy, cx + rw + 1, cy + dy + 1, RED)
    text(cx - 6, cy - 3, "LA", (0xff, 0xff, 0xff))
    # gran rótulo rojo con el nombre
    rect(x0 + 24, top + 32, x0 + 112, top + 50, RED)
    rect(x0 + 24, top + 32, x0 + 112, top + 33, (0xf0, 0x50, 0x50))
    rect(x0 + 24, top + 49, x0 + 112, top + 50, (0x9a, 0x14, 0x1c))
    rect(x0 + 112, top + 32, x0 + 114, top + 52, shade(RED, 0.7))   # canto lateral
    # nube de diálogo blanca con "LA CUEVA ROJA" (en su estilo, texto en dos líneas)
    rect(x0 + 50, top + 29, x0 + 88, top + 49, (0xff, 0xff, 0xff))
    rect(x0 + 52, top + 27, x0 + 86, top + 29, (0xff, 0xff, 0xff))
    rect(x0 + 48, top + 33, x0 + 50, top + 45, (0xff, 0xff, 0xff))
    rect(x0 + 88, top + 33, x0 + 90, top + 45, (0xff, 0xff, 0xff))
    rect(x0 + 66, top + 49, x0 + 70, top + 52, (0xff, 0xff, 0xff))   # pico de la nube
    text(x0 + 55, top + 33, "LA CUEVA", RED)
    text(x0 + 59, top + 40, "ROJA", RED)
    rect(x0 + 96, top + 42, x0 + 110, top + 43, (0xff, 0xff, 0xff))  # texto de la web (borroso)
    rect(x0 + 26, top + 42, x0 + 38, top + 43, (0xff, 0xff, 0xff))
    # escaparate y puerta abierta
    rect(x0 + 24, top + 52, x0 + 112, SIDEWALK_Y, (0xf4, 0xf2, 0xee))      # marco blanco
    rect(x0 + 26, top + 54, x0 + 80, SIDEWALK_Y, (0x55, 0x62, 0x72))       # cristal
    rect(x0 + 26, top + 54, x0 + 30, SIDEWALK_Y, (0x7a, 0x88, 0x98))
    rect(x0 + 82, top + 54, x0 + 110, SIDEWALK_Y, (0x20, 0x20, 0x28))      # interior de la tienda
    rect(x0 + 80, top + 54, x0 + 82, SIDEWALK_Y, (0xf4, 0xf2, 0xee))
    rect(x0 + 110, top + 54, x0 + 112, SIDEWALK_Y, (0xf4, 0xf2, 0xee))
    rect(x0 + 24, top + 52, x0 + 112, top + 54, (0xf4, 0xf2, 0xee))
    # interior: estanterías con cómics y figuras
    for yy in (top + 60, top + 70, top + 80):
        rect(x0 + 84, yy + 6, x0 + 108, yy + 7, (0xc8, 0xc4, 0xbc))
        for xx in range(x0 + 85, x0 + 108, 3):
            rect(xx, yy, xx + 2, yy + 6, rnd.choice(((0xd8, 0x30, 0x30), (0x30, 0x60, 0xc8), (0xe8, 0xc0, 0x30),
                                                    (0x40, 0xa0, 0x50), (0xe8, 0xe8, 0xe8), (0x90, 0x40, 0xa8))))
    rect(x0 + 30, top + 72, x0 + 52, top + 82, (0xe8, 0xe4, 0xe0))          # expositor blanco
    for xx in range(x0 + 32, x0 + 51, 5):
        rect(xx, top + 66, xx + 3, top + 72, rnd.choice(((0xd8, 0x30, 0x30), (0x30, 0x60, 0xc8), (0xe8, 0xc0, 0x30))))
    rect(x0 + 56, top + 60, x0 + 76, top + 64, (0x66, 0x74, 0x84))          # reflejo en el cristal
    rect(x0 + 55, SIDEWALK_Y - 8, x0 + 78, SIDEWALK_Y, (0x44, 0x50, 0x60))
    # focos del techo
    px(x0 + 96, top + 57, (0xff, 0xff, 0xe0))
    # caja eléctrica y placa
    rect(x0 + 5, SIDEWALK_Y - 21, x0 + 13, SIDEWALK_Y - 4, (0xd8, 0xd8, 0xdc))
    rect(x0 + 5, SIDEWALK_Y - 21, x0 + 13, SIDEWALK_Y - 20, (0xa8, 0xa8, 0xb0))
    rect(x0 + 124, top + 56, x0 + 130, top + 66, (0xc8, 0x28, 0x38))        # placa roja en el ladrillo
    rect(x0 + 125, top + 57, x0 + 129, top + 58, (0xf0, 0xa0, 0xa0))
    # roll-up publicitario delante de la tienda (colores amarillo/rojo/blanco, collage de portadas)
    bx, by = x0 + 40, SIDEWALK_Y - 28
    rect(bx - 1, by - 1, bx + 21, by + 35, (0x30, 0x30, 0x38))
    rect(bx, by, bx + 20, by + 34, (0xf6, 0xf4, 0xee))
    for yy in range(by + 1, by + 30, 3):                                   # collage de portadas
        for xx in range(bx + 1, bx + 8, 2):
            rect(xx, yy, xx + 2, yy + 3, rnd.choice(((0xd8, 0x30, 0x30), (0x30, 0x60, 0xc8), (0xe8, 0xc0, 0x30),
                                                    (0x40, 0xa0, 0x50), (0xe0, 0x80, 0xb0), (0x30, 0x30, 0x40))))
    for k, yy in enumerate(range(by + 2, by + 22, 3)):                     # lista de productos
        rect(bx + 10, yy, bx + 10 + rnd.randint(5, 9), yy + 1, (0xd8, 0x30, 0x30) if k % 2 == 0 else (0x44, 0x44, 0x4c))
    rect(bx + 1, by + 22, bx + 19, by + 28, (0xf0, 0xc8, 0x28))              # franja amarilla
    rect(bx + 1, by + 28, bx + 19, by + 33, (0xd8, 0x20, 0x2a))              # franja roja
    rect(bx + 8, by + 28, bx + 12, by + 32, (0xff, 0xff, 0xff))
    rect(bx - 2, by + 35, bx + 22, by + 37, (0x30, 0x30, 0x38))              # pie
    # alféizar de sombra bajo el toldo
    rect(x0 + 24, top + 54, x0 + 112, top + 56, (0x3a, 0x44, 0x54))


cueva_roja(1146)

# ---------- enclaves de la mitad de la calle ----------
FONT.update({
    'S': ["011", "100", "010", "001", "110"], 'P': ["110", "101", "110", "100", "100"], '_': ["000", "000", "000", "000", "111"],
})


def text_s(x0, y0, s, c, k=2):
    for ch in s:
        for r, row in enumerate(FONT[ch]):
            for i, v in enumerate(row):
                if v == '1':
                    rect(x0 + i * k, y0 + r * k, x0 + i * k + k, y0 + r * k + k, c)
        x0 += 4 * k


def clear_zone(xa, xb):
    """Quita las casas genéricas de esa franja (restaura cielo+lejanía) y rehace acera lisa."""
    img.paste(sky_snapshot.crop((xa, 0, xb, SIDEWALK_Y + 14)), (xa, 0))
    paint_sidewalk(xa, xb)


# ---------- enclaves de la mitad: Casa El Cateto y tienda APP ----------
def casa_el_cateto(x0, w=150):
    xb = x0 + w
    top = SIDEWALK_Y - 92
    gy = SIDEWALK_Y
    BR = (0xb0, 0x8e, 0x62)
    BRJ = (0x98, 0x76, 0x50)
    MAR = (0x7c, 0x1c, 0x2a)
    PLAS = (0xe8, 0xe2, 0xd2)
    clear_zone(x0 - 4, xb + 4)
    rect(x0, top, xb, gy, BR)
    for yy in range(top, gy, 3):                             # ladrillo cara vista
        rect(x0, yy, xb, yy + 1, BRJ)
        off = 0 if ((yy - top) // 3) % 2 == 0 else 4
        for xx in range(x0 + off, xb, 8):
            rect(xx, yy, xx + 1, yy + 3, BRJ)
    for _ in range(w * 92 // 40):
        px(rnd.randint(x0, xb - 1), rnd.randint(top, gy - 10), shade(BR, rnd.choice((0.9, 1.08, 1.12))))
    rect(xb - 4, top, xb, gy, shade(BR, 0.8))
    rect(x0, top, x0 + 1, gy, (0x20, 0x1c, 0x18))
    # cornisa granate superior
    rect(x0 - 1, top + 6, xb + 1, top + 12, MAR)
    rect(x0 - 1, top + 6, xb + 1, top + 7, shade(MAR, 1.4))
    rect(x0 - 1, top + 11, xb + 1, top + 12, shade(MAR, 0.7))
    rect(x0 - 1, top, xb + 1, top + 1, shade(BR, 1.15))
    # planta alta: paños blancos con ventanas enrejadas
    for px0 in range(x0 + 6, xb - 24, 36):
        rect(px0, top + 14, px0 + 24, top + 37, PLAS)
        rect(px0 + 22, top + 14, px0 + 24, top + 37, shade(PLAS, 0.82))
        rect(px0 + 7, top + 16, px0 + 17, top + 34, (0xf2, 0xf0, 0xe8))
        rect(px0 + 8, top + 17, px0 + 16, top + 33, GLASS)
        for xx in range(px0 + 9, px0 + 16, 2):
            rect(xx, top + 17, xx + 1, top + 33, IRON)
        rect(px0 + 8, top + 25, px0 + 16, top + 26, IRON)
    # rótulo "CASA EL CATETO" sobre el ladrillo y cornisa granate inferior
    text_s(x0 + 20, top + 40, "CASA EL CATETO", MAR, 2)
    rect(x0 - 1, top + 53, xb + 1, top + 58, MAR)
    rect(x0 - 1, top + 53, xb + 1, top + 54, shade(MAR, 1.4))
    rect(x0 - 1, top + 57, xb + 1, top + 58, shade(MAR, 0.7))
    # planta baja: ventanas con reja
    for wx in (x0 + 12, x0 + 44, xb - 26):
        window(wx, gy - 32, 14, 20)
        for xx in range(wx + 1, wx + 14, 3):
            rect(xx, gy - 32, xx + 1, gy - 12, IRON)
        rect(wx, gy - 22, wx + 14, gy - 21, IRON)
    # zócalo de piedra clara
    rect(x0, gy - 8, xb, gy, (0xc4, 0xb4, 0x94))
    rect(x0, gy - 9, xb, gy - 8, (0x9a, 0x88, 0x68))
    # entrada: reja negra con cristal y toldo blanco
    ex = x0 + 92
    rect(ex - 1, gy - 29, ex + 27, gy, (0x2a, 0x28, 0x30))
    rect(ex + 1, gy - 27, ex + 25, gy, (0x4a, 0x56, 0x66))
    for xx in range(ex + 2, ex + 25, 3):
        rect(xx, gy - 27, xx + 1, gy, IRON)
    rect(ex, gy - 16, ex + 26, gy - 15, IRON)
    rect(ex - 4, gy - 36, ex + 34, gy - 29, (0xf4, 0xf2, 0xee))              # toldo
    for xx in range(ex - 4, ex + 34, 4):
        rect(xx, gy - 36, xx + 1, gy - 29, (0xc8, 0xc6, 0xc0))
    rect(ex - 4, gy - 30, ex + 34, gy - 28, (0xa8, 0xa4, 0x9c))
    # señal azul de dirección obligatoria con poste
    rect(x0 + 77, gy - 30, x0 + 79, gy + 10, (0x7a, 0x7a, 0x82))
    rect(x0 + 70, gy - 43, x0 + 86, gy - 28, (0x2a, 0x68, 0xc0))
    rect(x0 + 71, gy - 42, x0 + 85, gy - 29, (0x3a, 0x78, 0xd0))
    rect(x0 + 77, gy - 40, x0 + 79, gy - 31, (0xf8, 0xf8, 0xf8))
    rect(x0 + 75, gy - 38, x0 + 81, gy - 37, (0xf8, 0xf8, 0xf8))
    rect(x0 + 76, gy - 39, x0 + 80, gy - 38, (0xf8, 0xf8, 0xf8))


def tienda_app(x0, w=100):
    xb = x0 + w
    top = SIDEWALK_Y - 100
    gy = SIDEWALK_Y
    PINK = (0xd8, 0x96, 0x8c)
    clear_zone(x0 - 4, xb + 4)
    rect(x0, top, xb, gy, PINK)
    for _ in range(w * 100 // 60):
        px(rnd.randint(x0, xb - 1), rnd.randint(top, gy - 9), shade(PINK, rnd.choice((0.92, 0.95, 1.05))))
    rect(xb - 3, top, xb, gy, shade(PINK, 0.84))
    rect(x0, top, x0 + 1, gy, shade(PINK, 0.7))
    # tejado y cornisa
    rect(x0 - 2, top - 7, xb + 2, top, TILE)
    for xx in range(x0 - 2, xb + 2, 3):
        rect(xx, top - 7, xx + 1, top, TILE_D)
    rect(x0 - 2, top, xb + 2, top + 3, (0xf2, 0xe2, 0xd8))
    # balcones de forja en la planta alta
    for cx in (x0 + 24, x0 + 70):
        balcony(cx, top + 38, 24, (0x5a, 0x3a, 0x22))
    # cartel "APP_" con panel azul
    rect(x0 + 6, top + 46, x0 + 82, top + 62, (0xf4, 0xf6, 0xf6))
    rect(x0 + 6, top + 46, x0 + 82, top + 47, (0xc8, 0xcc, 0xcc))
    rect(x0 + 52, top + 46, x0 + 82, top + 62, (0x18, 0x4c, 0xb4))
    text_s(x0 + 12, top + 50, "APP_", (0x1e, 0x8f, 0x96), 2)
    rect(x0 + 60, top + 51, x0 + 76, top + 52, (0xd8, 0xe4, 0xf8))
    rect(x0 + 60, top + 55, x0 + 72, top + 56, (0xd8, 0xe4, 0xf8))
    cx, cy = x0 + 3, top + 54                                             # círculo azul de la esquina
    for dy in range(-6, 7):
        rw = int((36 - dy * dy) ** 0.5)
        rect(cx - rw, cy + dy, cx + rw + 1, cy + dy + 1, (0x18, 0x4c, 0xb4))
    # escaparate con toldo turquesa y carteles
    rect(x0 + 8, top + 62, x0 + 52, top + 66, (0x2a, 0x8f, 0x8a))
    rect(x0 + 8, top + 66, x0 + 52, gy, (0xf4, 0xf2, 0xee))
    rect(x0 + 10, top + 66, x0 + 50, gy, (0x20, 0x20, 0x2a))
    rect(x0 + 12, top + 70, x0 + 22, top + 94, (0x2a, 0x5a, 0xb8))        # póster azul
    rect(x0 + 14, top + 74, x0 + 20, top + 76, (0xf8, 0xf8, 0xf8))
    rect(x0 + 14, top + 79, x0 + 20, top + 80, (0xf8, 0xf8, 0xf8))
    rect(x0 + 24, top + 70, x0 + 32, top + 90, (0xe8, 0x50, 0x30))        # póster naranja
    rect(x0 + 34, top + 70, x0 + 48, top + 92, (0xe8, 0xe8, 0xf0))        # póster blanco
    rect(x0 + 36, top + 74, x0 + 46, top + 75, (0x20, 0x4c, 0xb0))
    # panel informativo blanco
    rect(x0 + 56, top + 66, x0 + 84, top + 96, (0xf6, 0xf6, 0xf6))
    rect(x0 + 56, top + 66, x0 + 84, top + 67, (0xc0, 0xc0, 0xc8))
    text_s(x0 + 60, top + 69, "APP", (0x1e, 0x8f, 0x96), 2)
    for k, yy in enumerate(range(top + 79, top + 94, 3)):
        rect(x0 + 59, yy, x0 + 59 + (20 if k % 2 == 0 else 15), yy + 1, (0x7a, 0x7e, 0x88))
    # puerta marrón a la derecha y caja de la acometida
    rect(x0 + 88, top + 62, xb, gy, (0xf0, 0xe0, 0xd8))
    rect(x0 + 90, top + 64, xb - 1, gy, (0x6a, 0x40, 0x2a))
    rect(x0 + 90, top + 78, x0 + 98, top + 82, shade((0x6a, 0x40, 0x2a), 0.8))
    rect(x0 + 85, top + 78, x0 + 87, top + 90, (0xe8, 0xe8, 0xe8))
    rect(x0, gy - 6, x0 + 8, gy, shade(PINK, 0.8))                         # zócalo


casa_el_cateto(496)
tienda_app(650)
rect(646, 20, 650, SIDEWALK_Y, (0x58, 0x44, 0x40))   # medianera entre ambos edificios


# ---------- enclave del principio: plaza de entrada ----------
def plaza_quiosco(xa, xb):
    gy = SIDEWALK_Y
    clear_zone(xa, xb)
    # solado claro de plaza con parches de ladrillo rosado
    paint_sidewalk(xa, xb, base=(0xd6, 0xcc, 0xb6), joint=(0xc2, 0xb8, 0xa0), hi=(0xea, 0xe2, 0xcc))
    for (px0, pw) in ((90, 44), (176, 26)):
        for yy in range(gy + 3, gy + 10):                                    # parches de ladrillo rosado (siguen la diagonal)
            rect(px0 + (gy + 9 - yy), yy, px0 + (gy + 9 - yy) + pw, yy + 1, (0xd0, 0xa4, 0x94))
    # edificio blanco al fondo a la derecha, con balcones y bajos de color teja
    bx0, bx1 = 118, xb
    btop = gy - 86
    rect(bx0, btop, bx1, gy, (0xf2, 0xf0, 0xe8))
    rect(bx1 - 4, btop, bx1, gy, (0xdc, 0xd8, 0xcc))
    rect(bx0, btop, bx0 + 1, gy, (0xc8, 0xc4, 0xb8))
    rect(bx0 + 10, btop - 8, bx1, btop, (0xf8, 0xf6, 0xf0))                 # azotea con balaustrada
    for xx in range(bx0 + 10, bx1, 4):
        rect(xx, btop - 6, xx + 2, btop, (0xdc, 0xd8, 0xcc))
    rect(bx0 + 14, btop - 16, bx0 + 56, btop - 14, (0x7a, 0x52, 0x34))      # pérgola de madera
    rect(bx0 + 14, btop - 16, bx0 + 16, btop - 8, (0x7a, 0x52, 0x34))
    rect(bx0 + 54, btop - 16, bx0 + 56, btop - 8, (0x7a, 0x52, 0x34))
    for wx in (bx0 + 14, bx0 + 44):                                         # ventanas planta alta con arcos
        rect(wx, btop + 10, wx + 12, btop + 22, (0xe6, 0xe2, 0xd8))
        rect(wx + 2, btop + 13, wx + 10, btop + 21, GLASS)
        rect(wx + 3, btop + 11, wx + 9, btop + 13, GLASS)
    rect(bx0 + 64, btop + 6, bx1 - 6, btop + 40, (0x2a, 0x2a, 0x36))        # ventanal oscuro con balcón
    rect(bx0 + 62, btop + 38, bx1 - 4, btop + 41, (0xe6, 0xe2, 0xd8))
    for xx in range(bx0 + 62, bx1 - 4, 3):
        rect(xx, btop + 31, xx + 1, btop + 38, (0xe6, 0xe2, 0xd8))
    rect(bx0, btop + 52, bx1, gy, (0xe4, 0xe0, 0xd4))
    rect(bx0, gy - 16, bx1, gy, (0xb8, 0x6a, 0x4a))                         # zócalo teja
    rect(bx0, gy - 17, bx1, gy - 16, (0xd4, 0x90, 0x6c))
    for dx in (12, 34):                                                     # soportales / puertas al fondo
        rect(bx0 + dx, gy - 38, bx0 + dx + 14, gy - 16, (0x4a, 0x3a, 0x34))
        rect(bx0 + dx + 2, gy - 36, bx0 + dx + 12, gy - 16, (0x6a, 0x54, 0x48))
    # casa baja amarilla y ciprés a la izquierda
    rect(xa, gy - 56, xa + 52, gy, (0xe6, 0xb0, 0x50))
    rect(xa + 48, gy - 56, xa + 52, gy, (0xc4, 0x90, 0x38))
    rect(xa, gy - 62, xa + 54, gy - 56, (0x8a, 0x8a, 0x94))
    rect(xa + 6, gy - 44, xa + 18, gy - 30, GLASS)
    # casa encalada en el hueco central (el quiosco se quitó)
    house(54, 64, 2, WALLS[1], ZOCALO[0], 'tile')
    # ciprés alto + árboles jóvenes con alcorque
    def cypress(cx, h):
        for dy in range(h):
            t = dy / h
            rw = int(2 + 7 * (1 - abs(t * 2 - 1.1) ** 1.5)) if t < 0.95 else 1
            rect(cx - rw, gy - 10 - h + dy, cx + rw + 1, gy - 10 - h + dy + 1, (0x1f, 0x44, 0x2a) if dy % 3 else (0x2c, 0x5a, 0x36))
    cypress(xa + 22, 80)
    def young_tree(cx):
        rect(cx - 6, gy + 8, cx + 7, gy + 13, (0xb8, 0x72, 0x4c))                    # alcorque
        rect(cx - 4, gy + 9, cx + 5, gy + 12, (0x9a, 0x5c, 0x3c))
        rect(cx, gy - 40, cx + 2, gy + 10, (0x5a, 0x40, 0x30))                        # tronco fino
        for dy in range(-40, -8):
            rw = int(((1 - ((dy + 24) / 17.0) ** 2) ** 0.5) * 8) if abs(dy + 24) < 17 else 0
            if rw:
                for xx in range(cx - rw, cx + rw + 1):
                    if rnd.random() < 0.75:
                        px(xx + 1, gy + dy, rnd.choice(((0x3a, 0x84, 0x3c), (0x2a, 0x62, 0x34), (0x52, 0xa0, 0x48))))
    # señal de paso de peatones con poste
    rect(xa + 6, gy - 52, xa + 8, gy + 12, (0x8a, 0x8a, 0x92))
    rect(xa + 0, gy - 68, xa + 16, gy - 52, (0x2a, 0x68, 0xc0))
    rect(xa + 1, gy - 67, xa + 15, gy - 53, (0x3a, 0x78, 0xd0))
    for dy in range(0, 10):                                                         # triángulo blanco
        rect(xa + 8 - dy // 2 - 1, gy - 65 + dy, xa + 8 + dy // 2 + 1, gy - 64 + dy, (0xf8, 0xf8, 0xf8))
    rect(xa + 7, gy - 63, xa + 9, gy - 57, (0x1a, 0x3a, 0x80))
    # bolardos grises
    for bx in (30, 112, 150, 206):
        rect(bx, gy + 6, bx + 3, gy + 16, (0x7a, 0x7a, 0x82))
        rect(bx, gy + 6, bx + 3, gy + 7, (0xa8, 0xa8, 0xb0))
    # paso de cebra en la calzada, junto al final de la plaza
    for yy in range(140, 214, 7):
        rect(xb - 28, yy, xb - 6, yy + 3, (0xd8, 0xd4, 0xc0))
        rect(xb - 28, yy + 3, xb - 6, yy + 4, (0xb0, 0xac, 0x9c))


plaza_quiosco(0, 202)

args = [a for a in sys.argv[1:] if not a.startswith('--')]
out = args[0] if args else 'assets/backgrounds/calle_tajo.png'
import os
os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
if '--day' not in sys.argv:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import night_pass
    protect = [(0, 202), (496, 750), (1146, 1280)]       # enclaves: sin grafitis encima
    emissive = [  # (x0, y0, x1, y1, color_luz, radio, fuerza)
        (1170, 59, 1262, 84, (1.0, 0.18, 0.18), 70, 0.9),
        (1164, 45, 1184, 65, (1.0, 0.18, 0.18), 30, 0.6),
        (656, 64, 732, 80, (0.2, 0.9, 0.9), 60, 0.8),
        (706, 84, 734, 114, (0.7, 0.9, 1.0), 30, 0.5),
        (660, 84, 700, 118, (0.8, 0.9, 1.0), 40, 0.6),
    ]
    glass = (0x2a, 0x36, 0x50)
    sky_cols = list(SKY) + [(0xf6, 0xfb, 0xff), (0xdd, 0xee, 0xf8)]
    img = night_pass.apply(img, W, H, SIDEWALK_Y, CURB_Y, sky_cols, glass, protect, emissive, ())
img.save(out)
print('ok', out, img.size)
