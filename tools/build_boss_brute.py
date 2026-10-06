"""Genera el sprite del boss 'BRUTO' a partir de la hoja del punk (assets/sprites/enemy.png).
El punk solo usa 14 colores, asi que se cambia la paleta color a color (sin degradados ni borrosidad) y se
amplia x1.33 (nearest x4 + moda 3x3) para que sea algo mayor que un enemigo normal sin perder detalle.
Salida: assets/sprites/boss_brute.png (mismas filas/columnas que el set 'punk', celda 128x85)."""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'assets', 'sprites', 'enemy.png')
OUT = os.path.join(HERE, '..', 'assets', 'sprites', 'boss_brute.png')
CW, CH, COLS, ROWS = 96, 63, 4, 5
UP, DOWN = 4, 3   # ampliacion x(4/3): nearest x4 y reduccion por moda 3x3 (conserva el detalle)
from collections import Counter
OW, OH = CW * UP // DOWN, (CH + 1) * UP // DOWN   # celda de salida 128x85

# cresta (pelo) -> blanco hielo
HAIR = {(237, 73, 36): (240, 244, 255), (206, 32, 56): (186, 198, 228), (138, 11, 65): (104, 116, 164)}
# chaleco de cuero negro
VEST = {(237, 73, 36): (96, 96, 116), (206, 32, 56): (54, 54, 68), (138, 11, 65): (26, 26, 36)}
OTHER = {
    (64, 96, 160): (74, 82, 54), (96, 128, 224): (118, 128, 84), (0, 64, 64): (30, 38, 28),
    (181, 182, 255): (160, 170, 120),                       # vaqueros -> pantalon militar
    (128, 96, 96): (196, 36, 40),                           # camiseta gris -> roja
    (69, 60, 60): (18, 14, 14), (88, 45, 57): (46, 32, 36), # contornos y botas
    (156, 92, 55): (116, 62, 38), (215, 126, 75): (172, 96, 56),
    (255, 177, 100): (216, 138, 80), (255, 182, 107): (222, 146, 88),   # piel mas oscura y curtida
}

sheet = np.asarray(Image.open(SRC).convert('RGBA')).copy()
out = np.zeros((ROWS * OH, COLS * OW, 4), np.uint8)
for r in range(ROWS):
    for c in range(COLS):
        cell = sheet[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW].copy()
        ys, xs = np.where(cell[..., 3] > 0)
        if len(ys) == 0:
            continue
        top, bot = ys.min(), ys.max()
        upright = r < 4 and (bot - top) > 40
        for y, x in zip(ys, xs):
            col = tuple(int(v) for v in cell[y, x, :3])
            if col in HAIR:
                hair = upright and (y - top) < 0.24 * (bot - top + 1) or (r == 2 and c == 2 and x > 55)
                if r == 4:
                    hair = (x - xs.min()) > 0.65 * (xs.max() - xs.min())   # caidos: la cabeza esta a la derecha
                col = (HAIR if hair else VEST)[col]
            else:
                col = OTHER.get(col, col)
            cell[y, x, :3] = col
        pad = np.zeros((CH + 1, CW, 4), np.uint8)
        pad[1:] = cell
        big = np.kron(pad, np.ones((UP, UP, 1), np.uint8))
        o = np.zeros((OH, OW, 4), np.uint8)
        for y in range(OH):
            for x in range(OW):
                blk = big[y * DOWN:(y + 1) * DOWN, x * DOWN:(x + 1) * DOWN].reshape(-1, 4)
                vis = [tuple(p) for p in blk if p[3] > 0]
                if len(vis) * 2 > len(blk):
                    o[y, x] = Counter(vis).most_common(1)[0][0]
        out[r * OH:(r + 1) * OH, c * OW:(c + 1) * OW] = o
Image.fromarray(out, 'RGBA').save(OUT)
print('ok', out.shape, 'cell', OW, OH, 'feet', (48 * UP // DOWN, 63 * UP // DOWN - 1))
