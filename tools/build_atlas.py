"""Empaqueta los frames sueltos del pack CC0 "Streets of Fight" (ansimuz) en hojas de sprites
para el juego y genera scripts/anim_sets.gd con la configuración de cada animación.

Uso:
    python tools/build_atlas.py "<carpeta Streets of Fight files>/Assets/Sprites" [salida_proyecto]

Cada animación ocupa UNA FILA de la hoja; cada frame mide 96x63 con los pies en (48, 62).
Si tu artista cambia/añade frames, solo hay que editar las tablas GIRL / PUNK de abajo.
La animación "dead" (caída) no viene en el pack: se genera girando el último frame de "hurt".
"""
import glob, os, re, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_mods

FW, FH = 96, 63
FEET = (48, 62)

# nombre_en_juego: (carpeta_del_pack | "ROTATE:<anim>", fps, loop, impact[, (inicio, fin)])
#   impact = índice del frame en el que el golpe "conecta" (solo ataques).
#   (inicio, fin) = usa solo esos frames de la carpeta (por ejemplo, Hurt del punk trae
#   2 frames de golpe + 2 de caída).
GIRL = {
    'idle':      ('Idle',      6, True,  None),
    'walk':      ('Walk',     14, True,  None),
    'jump':      ('Jump',      8, False, None),
    'attack1':   ('Jab',       0, False, 1),
    'attack2':   ('Punch',     0, False, 1),
    'attack3':   ('Kick',      0, False, 3),
    'hurt':      ('Hurt',      0, False, None),
    'dead':      ('ROTATE:hurt', 0, False, None),
    'jump_kick': ('Jump_kick', 0, False, 1),   # extra: aún sin usar
    'dive_kick': ('Dive_kick', 0, False, 3),   # extra: aún sin usar
}
PUNK = {
    'idle':    ('Idle',  6, True,  None),
    'walk':    ('Walk',  8, True,  None),
    'attack1': ('Punch', 0, False, 1),
    'hurt':    ('Hurt',  0, False, None, (0, 2)),   # encogerse al recibir el golpe
    'dead':    ('Hurt',  0, False, None, (2, 4)),   # salir despedido + quedarse tumbado
}
# animaciones que no existen para un personaje y reutilizan otra
PUNK_ALIAS = {'attack2': 'attack1', 'attack3': 'attack1', 'jump': 'idle'}


# Héroe masculino = el punk del pack con la paleta cambiada (el pack es CC0: se puede modificar).
# pelo/camiseta oscuros, vaqueros claros; así no se confunde con los enemigos (pelo rojo, vaqueros azules).
HERO_PALETTE = {
    (0xed, 0x49, 0x24): (0x5a, 0x40, 0x30),   # pelo (luz)
    (0xce, 0x20, 0x38): (0x34, 0x30, 0x38),   # pelo/camiseta
    (0x8a, 0x0b, 0x41): (0x20, 0x1e, 0x28),   # pelo/camiseta (sombra)
    (0x58, 0x2d, 0x39): (0x16, 0x14, 0x1c),   # sombra oscura
    (0x40, 0x60, 0xa0): (0x78, 0x98, 0xc8),   # vaqueros
    (0x60, 0x80, 0xe0): (0xa8, 0xc4, 0xf0),   # vaqueros (luz)
}


def recolor(img, palette):
    img = img.copy()
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in palette:
                px[x, y] = palette[(r, g, b)] + (a,)
    return img


def load_frames(src, who, folder, palette=None):
    files = sorted(glob.glob(os.path.join(src, who, folder, '*.png')),
                   key=lambda f: int(re.findall(r'(\d+)\.png', f)[0]))
    frames = [Image.open(f).convert('RGBA') for f in files]
    if not palette:
        return frames
    frames = [recolor(f, palette) for f in frames]
    return frames


def fall_frames(last):
    """3 frames de caída hacia atrás girando el último frame de daño alrededor de los pies."""
    out = []
    for ang, dy in ((30, 0), (65, 6), (90, 11)):
        big = Image.new('RGBA', (FW * 3, FH + 30), (0, 0, 0, 0))
        big.paste(last, (FW, 0))
        rot = big.rotate(ang, resample=Image.NEAREST, center=(FW + FEET[0], FEET[1] + 1))
        out.append(rot.crop((FW, dy, 2 * FW, FH + dy)))
    return out


def build(src, who, table, alias, out_png, set_name, faces_right=True, palette=None):
    rows, frames_by = [], {}
    for name, spec in table.items():
        folder = spec[0]
        if folder.startswith('ROTATE:'):
            continue
        frames = load_frames(src, who, folder, palette)
        if len(spec) > 4:
            frames = frames[spec[4][0]:spec[4][1]]
        if palette and name != 'dead':
            n_keep = len(frames)
            if name == 'hurt':
                n_keep = 2
            frames = [hero_mods.hero_frame(f, 7 + i) for i, f in enumerate(frames[:n_keep])] + frames[n_keep:]
        frames_by[name] = frames
    for name, spec in table.items():
        folder = spec[0]
        if folder.startswith('ROTATE:'):
            frames_by[name] = fall_frames(frames_by[folder.split(':')[1]][-1])
    names = list(table.keys())
    cols = max(len(frames_by[n]) for n in names)
    sheet = Image.new('RGBA', (cols * FW, len(names) * FH), (0, 0, 0, 0))
    for r, n in enumerate(names):
        for c, f in enumerate(frames_by[n]):
            sheet.paste(f, (c * FW, r * FH))
    sheet.save(out_png)

    lines = [f'\t"{set_name}": {{', f'\t\t"cols": {cols}, "rows": {len(names)},',
             f'\t\t"faces_right": {str(faces_right).lower()},',
             f'\t\t"frame": Vector2i({FW}, {FH}), "feet": Vector2({FEET[0]}, {FEET[1]}),', '\t\t"anims": {']
    for r, n in enumerate(names):
        folder, fps, loop, impact = table[n][:4]
        extra = f', "impact": {impact}' if impact is not None else ''
        lines.append(f'\t\t\t"{n}": {{"row": {r}, "n": {len(frames_by[n])}, "fps": {float(fps)}, "loop": {str(loop).lower()}{extra}}},')
    for a, b in alias.items():
        lines.append(f'\t\t\t"{a}": {{"alias": "{b}"}},')
    lines += ['\t\t},', '\t},']
    return '\n'.join(lines), cols, len(names)


# --- Protagonista "mage": hoja entregada por el usuario (idle 10 frames de 46x55, walk 24 de 45x58) ---
MW, MH = 64, 60
MFEET = (32, 59)


def _cut(path, fw, fh, cols, n):
    im = Image.open(path).convert('RGBA')
    return [im.crop(((i % cols) * fw, (i // cols) * fh, (i % cols) * fw + fw, (i // cols) * fh + fh)) for i in range(n)]


def _place(f):
    """Centra el frame (por los pies) en el recuadro MWxMH, apoyado abajo."""
    bb = f.getbbox()
    out = Image.new('RGBA', (MW, MH), (0, 0, 0, 0))
    if not bb:
        return out
    feet = f.crop((0, max(bb[3] - 10, 0), f.width, bb[3])).getbbox()
    cx = (feet[0] + feet[2]) / 2 if feet else (bb[0] + bb[2]) / 2
    ox = int(round(MFEET[0] - cx))
    oy = MFEET[1] + 1 - bb[3]
    out.paste(f, (ox, oy), f)
    return out


def build_mage(proj, out_png):
    src = os.path.join(proj, 'assets/sprites/src')
    idle = _cut(os.path.join(src, 'mage_idle.png'), 46, 55, 10, 10)
    walk = _cut(os.path.join(src, 'mage_walk.png'), 45, 58, 4, 24)
    idle = [_place(f) for f in idle]
    walk = [_place(f) for f in walk]
    cols = 24
    sheet = Image.new('RGBA', (cols * MW, 2 * MH), (0, 0, 0, 0))
    for i, f in enumerate(idle):
        sheet.paste(f, (i * MW, 0))
    for i, f in enumerate(walk):
        sheet.paste(f, (i * MW, MH))
    sheet.save(out_png)
    # No hay frames de ataque/daño/caída: se usan poses simples con movimiento por código ("fx" en fighter.gd).
    return "\t\"mage\": {\n" + "\n".join([
        f'\t\t"cols": {cols}, "rows": 2,',
        '\t\t"faces_right": false,',
        f'\t\t"frame": Vector2i({MW}, {MH}), "feet": Vector2({MFEET[0]}, {MFEET[1]}),',
        '\t\t"anims": {',
        '\t\t\t"idle": {"row": 0, "n": 10, "fps": 8.0, "loop": true},',
        '\t\t\t"walk": {"row": 1, "n": 24, "fps": 20.0, "loop": true},',
        '\t\t\t"jump": {"row": 0, "n": 1, "fps": 0.0, "loop": false},',
        '\t\t\t"attack1": {"row": 0, "n": 2, "fps": 0.0, "loop": false, "impact": 1, "fx": "punch"},',
        '\t\t\t"attack2": {"row": 0, "n": 2, "fps": 0.0, "loop": false, "impact": 1, "fx": "punch"},',
        '\t\t\t"attack3": {"row": 0, "n": 2, "fps": 0.0, "loop": false, "impact": 1, "fx": "kick"},',
        '\t\t\t"hurt": {"row": 0, "n": 1, "fps": 0.0, "loop": false, "fx": "hurt"},',
        '\t\t\t"dead": {"row": 0, "n": 1, "fps": 0.0, "loop": false, "fx": "dead"},',
        '\t\t},', '\t},'])


if __name__ == '__main__':
    src = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(os.path.join(proj, 'assets', 'sprites'), exist_ok=True)
    os.makedirs(os.path.join(proj, 'scripts'), exist_ok=True)
    sp = os.path.join(proj, 'assets/sprites')
    # El punk dibuja mirando a la IZQUIERDA (faces_right=False); la chica, a la derecha.
    h, hc, hr = build(src, 'Enemy-Punk', PUNK, PUNK_ALIAS, os.path.join(sp, 'player_hero.png'), 'hero', False, HERO_PALETTE)
    g, gc, gr = build(src, 'Brawler-Girl', GIRL, {}, os.path.join(sp, 'player.png'), 'brawler')
    p, pc, pr = build(src, 'Enemy-Punk', PUNK, PUNK_ALIAS, os.path.join(sp, 'enemy.png'), 'punk', False)
    m = build_mage(proj, os.path.join(sp, 'player_mage.png'))
    gd = ('# GENERADO por tools/build_atlas.py: no editar a mano (vuelve a ejecutar el script).\n'
          '# Configuración de las hojas de sprites: una fila por animación.\n'
          'class_name AnimSets\n\nconst SETS := {\n' + m + '\n' + h + '\n' + g + '\n' + p + '\n}\n')
    open(os.path.join(proj, 'scripts/anim_sets.gd'), 'w', encoding='utf-8').write(gd)
    print('girl', gc, 'x', gr, ' punk', pc, 'x', pr)
