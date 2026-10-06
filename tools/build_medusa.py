"""Construye el sprite sheet del boss (Medusa) a partir de la hoja original tools/boss_medusa_src.jpg:
quita el fondo gris y las etiquetas, pasa la hoja (que viene a escala x2) a pixel nativo, limpia el ruido del JPG
con una paleta reducida y apila los frames en una cuadricula: una fila por animacion.
Salida: assets/sprites/boss_medusa.png y por pantalla el bloque de scripts/anim_sets.gd.
Uso: python tools/build_medusa.py"""
import os, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'boss_medusa_src.jpg')
OUT = os.path.join(HERE, '..', 'assets', 'sprites', 'boss_medusa.png')
BG = np.array([162, 162, 162])
SCALE = 2          # la hoja original esta ampliada x2
LABEL_X = 232      # a la izquierda de esto solo hay texto ("IDLE", "WALK"...)

# (nombre de fila en la hoja original, y inicial, y final) -> animacion
BANDS = [("idle", 33, 208), ("idle2", 272, 440), ("walk", 480, 656), ("run", 700, 872), ("attack1", 896, 1080)]

img = np.asarray(Image.open(SRC).convert('RGB')).astype(int)
H, W, _ = img.shape
# a pixel nativo: cada bloque 2x2 toma el color de sus pixeles que NO son fondo (asi el borde negro no se mezcla con el gris)
nh, nw = (H - 1) // SCALE, (W - 1) // SCALE
blocks = img[1:1 + nh * SCALE, 1:1 + nw * SCALE].reshape(nh, SCALE, nw, SCALE, 3).transpose(0, 2, 1, 3, 4).reshape(nh, nw, SCALE * SCALE, 3)
fg = np.abs(blocks - BG).sum(-1) > 60                      # (nh, nw, 4) pixeles de primer plano
cnt = fg.sum(-1)
dark4 = np.where(fg, blocks.sum(-1), 9999)
# color = el pixel de primer plano mas oscuro si hay negro de contorno, si no la media de los de primer plano
mean_fg = (blocks * fg[..., None]).sum(2) / np.maximum(cnt, 1)[..., None]
nat = mean_fg.astype(int)
opaque = cnt >= 2
opaque[:, :LABEL_X // SCALE] = False
black = (nat.max(-1) < 70) & opaque                         # contorno: negro puro, sin grises
OUTLINE = np.array([8, 5, 4])

# paleta reducida (k-means pequeno) para quitar el ruido del JPG
pix = nat[opaque & ~black]
rng = np.random.default_rng(3)
K = 44
cent = pix[rng.choice(len(pix), K, replace=False)].astype(float)
for _ in range(20):
    d = ((pix[:, None, :] - cent[None]) ** 2).sum(-1)
    lab = d.argmin(1)
    for k in range(K):
        sel = pix[lab == k]
        if len(sel):
            cent[k] = sel.mean(0)
cent = cent.round().astype(int)
d = ((nat.reshape(-1, 1, 3) - cent[None]) ** 2).sum(-1)
quant = cent[d.argmin(1)].reshape(nh, nw, 3)
quant[black] = OUTLINE

# quita el halo gris del fondo (pixeles casi grises pegados al borde de la silueta)
sat = nat.max(-1) - nat.min(-1)
halo = opaque & (sat < 28) & (nat.sum(-1) > 3 * 70) & ~ndi.binary_erosion(opaque, iterations=2)
opaque &= ~halo

# quita pixeles sueltos (ruido)
lab_all, n_all = ndi.label(opaque, structure=np.ones((3, 3)))
sizes = ndi.sum(opaque, lab_all, range(1, n_all + 1))
for i, s in enumerate(sizes):
    if s < 4:
        opaque[lab_all == i + 1] = False

frames = {}   # anim -> lista de (imagen RGBA recortada, ancla_x_relativa)
for name, y0, y1 in BANDS:
    ny0, ny1 = y0 // SCALE - 3, y1 // SCALE + 3
    sub = opaque[ny0:ny1]
    dil = ndi.binary_dilation(sub, iterations=3)
    lab, n = ndi.label(dil)
    boxes = []
    for i, sl in enumerate(ndi.find_objects(lab)):
        m = sub[sl] & (lab[sl] == i + 1)
        if m.sum() < 60:
            continue
        yy, xx = np.where(m)
        boxes.append((sl[1].start + xx.min(), ny0 + sl[0].start + yy.min(), sl[1].start + xx.max() + 1, ny0 + sl[0].start + yy.max() + 1, lab, i + 1))
    boxes.sort(key=lambda b: b[0])
    fl = []
    for (x0, y0b, x1, y1b, labm, li) in boxes:
        a = np.zeros((y1b - y0b, x1 - x0, 4), dtype=np.uint8)
        m = opaque[y0b:y1b, x0:x1] & (labm[y0b - ny0:y1b - ny0, x0:x1] == li)   # solo los pixeles de ESTE frame
        a[..., :3] = quant[y0b:y1b, x0:x1]
        a[..., 3] = np.where(m, 255, 0)
        # ancla horizontal = centro de masa del 40% superior (cabeza y torso): no se mueve entre poses
        ys, xs = np.where(m)
        top = ys < ys.min() + max(1, int(0.4 * (ys.max() - ys.min() + 1)))
        ax = int(round(xs[top].mean()))
        fl.append((Image.fromarray(a, 'RGBA'), ax))
    frames[name] = fl
    print(name, [(f[0].width, f[0].height, f[1]) for f in fl])

# celda comun: alineada por el ancla (x) y por la base (y)
left = max(ax for fl in frames.values() for (_, ax) in fl) + 1
right = max(im.width - ax for fl in frames.values() for (im, ax) in fl) + 1
cell_h = max(im.height for fl in frames.values() for (im, _) in fl) + 1
cell_w = left + right
cols = max(len(fl) for fl in frames.values())
rows = len(frames)
sheet = Image.new('RGBA', (cols * cell_w, rows * cell_h), (0, 0, 0, 0))
cfg = {}
for r, (name, fl) in enumerate(frames.items()):
    for c, (im, ax) in enumerate(fl):
        ox = c * cell_w + left - ax
        oy = r * cell_h + cell_h - 1 - im.height   # pies (base) en la penultima fila de la celda
        sheet.alpha_composite(im, (ox, oy))
    cfg[name] = {"row": r, "n": len(fl)}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sheet.save(OUT)
print("cols", cols, "rows", rows, "cell", cell_w, cell_h, "feet", (left, cell_h - 1))
print(json.dumps({"cols": cols, "rows": rows, "frame": [cell_w, cell_h], "feet": [left, cell_h - 1], "anims": cfg}))
