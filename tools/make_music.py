"""Genera la musica del juego (sintetizada, sin samples) en assets/music/:
menu_theme.wav y street_theme.wav (bucles de rock/metal ochentero cañero), stage_clear.wav (fanfarria final) y
game_over.wav. Uso: python tools/make_music.py"""
import os, wave
import numpy as np

SR = 32000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'music')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def tt(n):
    return np.arange(n) / SR


def env(n, a=0.005, d=0.12, s=0.6, r=0.05):
    t = tt(n)
    e = np.minimum(1.0, t / max(a, 1e-4))
    e = e * (s + (1 - s) * np.exp(-t / max(d, 1e-4)))
    rel = int(r * SR)
    if n > rel:
        e[-rel:] *= np.linspace(1, 0, rel)
    return e


def pulse(f, n, duty=0.25, vib=0.0):
    t = tt(n)
    ph = f * t + (vib * np.sin(2 * np.pi * 5.5 * t) * 0.01 * np.minimum(1, t * 2) * f / 440.0 * 40 if vib else 0)
    return np.where((ph % 1.0) < duty, 1.0, -1.0)


def saw(f, n, detune=0.0, vib=0.0):
    t = tt(n)
    ph = f * (1 + detune) * t
    if vib:
        ph = ph + vib * 0.004 * f * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t * 2) / 5.5
    return 2 * (ph % 1.0) - 1


def tri(f, n):
    t = tt(n)
    return 2 * np.abs(2 * ((f * t) % 1.0) - 1) - 1


def smooth(x, k=3):
    return np.convolve(x, np.ones(k) / k, mode='same')


def kick():
    n = int(0.2 * SR)
    t = tt(n)
    f = 48 + 120 * np.exp(-t / 0.025)
    click = np.exp(-t / 0.004) * rng.uniform(-1, 1, n) * 0.25
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08) + click


def snare():
    n = int(0.22 * SR)
    t = tt(n)
    noise = rng.uniform(-1, 1, n)
    return noise * np.exp(-t / 0.07) * 0.85 + np.sin(2 * np.pi * 200 * t) * np.exp(-t / 0.05) * 0.5


def hat(open_=False):
    n = int((0.18 if open_ else 0.045) * SR)
    t = tt(n)
    noise = np.diff(rng.uniform(-1, 1, n + 1))
    return noise * np.exp(-t / (0.08 if open_ else 0.014)) * 0.5


def crash():
    n = int(1.2 * SR)
    t = tt(n)
    noise = np.diff(rng.uniform(-1, 1, n + 1))
    return noise * np.exp(-t / 0.45) * 0.6


def tom(f0):
    n = int(0.25 * SR)
    t = tt(n)
    f = f0 * (1 + 0.6 * np.exp(-t / 0.05))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)


class Track:
    def __init__(self, bpm, bars, tail=2.0):
        self.spb = 60.0 / bpm
        self.n = int(bars * 4 * self.spb * SR)
        self.tail = int(tail * SR)
        self.buf = np.zeros(self.n + self.tail)

    def add(self, beat, sig, gain=1.0):
        i = int(beat * self.spb * SR)
        if i >= self.n:
            return
        j = min(len(self.buf), i + len(sig))
        self.buf[i:j] += sig[:j - i] * gain

    def loop(self):
        b = self.buf[:self.n].copy()
        b += np.pad(self.buf[self.n:], (0, self.n - self.tail))[:self.n] if self.n >= self.tail else 0
        return b

    def raw(self):
        return self.buf.copy()

    def nl(self, beats):
        return int(beats * self.spb * SR)


def bass(t, beat, beats, m, g=0.55):
    n = t.nl(beats)
    sig = (pulse(hz(m), n, 0.5) * 0.45 + saw(hz(m), n) * 0.45 + np.sin(2 * np.pi * hz(m - 12) * tt(n)) * 0.5) * env(n, 0.003, 0.12, 0.6, 0.02)
    t.add(beat, sig, g)


def guitar(t, beat, beats, root, g=0.3, mute=True):
    n = t.nl(beats)
    sig = np.zeros(n)
    for iv, dt in ((0, 0.0), (7, 0.003), (12, -0.003), (19, 0.002)):
        sig += saw(hz(root + iv), n, dt)
    sig = smooth(np.tanh(sig * 1.6), 3)
    sig *= env(n, 0.002, 0.07 if mute else 0.6, 0.3 if mute else 0.85, 0.015)
    t.add(beat, sig, g)


def lead(t, beat, beats, m, g=0.2, duty=0.25, vib=1.0):
    n = t.nl(beats)
    sig = (np.tanh((saw(hz(m), n, 0.0, vib) * 0.7 + pulse(hz(m), n, duty, vib) * 0.5) * 1.8)) * env(n, 0.01, 0.5, 0.75, 0.05)
    t.add(beat, sig, g)


def pad(t, beat, beats, ms, g=0.1):
    n = t.nl(beats)
    sig = np.zeros(n)
    for m in ms:
        sig += saw(hz(m), n, 0.004) + saw(hz(m), n, -0.004)
    t.add(beat, sig / len(ms) * env(n, 0.25, 1.0, 0.8, 0.3), g)


GALLOP = [(0.0, 0.4), (0.5, 0.2), (0.75, 0.2)]


def metal_bar(t, o, root, last_run, accent=True):
    """Compas de riff al galope (palm-mute) con carrera de semicorcheas opcional en el ultimo tiempo."""
    for beat in range(4):
        if beat == 3 and last_run:
            for k, iv in enumerate((0, 3, 5, 6)):
                guitar(t, o + 3 + k * 0.25, 0.22, root + 12 + iv, 0.3)
                bass(t, o + 3 + k * 0.25, 0.22, root + iv, 0.5)
            continue
        for off, d in GALLOP:
            guitar(t, o + beat + off, d, root + 12, 0.34 if (beat == 0 and off == 0 and accent) else 0.27)
            bass(t, o + beat + off, d, root, 0.5)


def drums_metal(t, bars, double_kick_bars=(0, 1, 2)):
    for b in range(bars):
        o = b * 4
        grp = b % 4
        if grp == 0:
            t.add(o, crash(), 0.55)
        if grp in double_kick_bars:
            for beat in range(4):
                for off, _ in GALLOP:
                    t.add(o + beat + off, kick(), 0.55)
        else:
            for beat in (0, 1, 2, 3):
                t.add(o + beat, kick(), 0.8)
        for beat in (1, 3):
            t.add(o + beat, snare(), 0.55)
        for k in range(8):
            t.add(o + k * 0.5, hat(k == 7), 0.3 if k % 2 == 0 else 0.2)
        if grp == 3:
            for k, f in enumerate((230, 190, 150, 120)):
                t.add(o + 3 + k * 0.25, tom(f), 0.55)


def write(name, sig, gain_db=-3.0):
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * 10 ** (gain_db / 20)
    pcm = (np.clip(sig, -1, 1) * 32767).astype(np.int16)
    p = os.path.join(OUT, name)
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print('ok', name, round(len(pcm) / SR, 1), 's', os.path.getsize(p) // 1024, 'KB')


def melody(t, notes, off, g=0.2, octave=0, duty=0.25):
    for (b0, d, m) in notes:
        lead(t, off + b0, d, m + octave, g, duty)


# ---------------- calle Tajo: thrash 170 bpm, Mi menor ----------------
def street():
    t = Track(170, 16)
    roots = [40, 40, 36, 38, 40, 40, 43, 38] * 2           # E E C D E E G D
    for b, r in enumerate(roots):
        metal_bar(t, b * 4, r, last_run=(b % 2 == 1))
    drums_metal(t, 16)
    A = [(0, .75, 76), (.75, .25, 79), (1, .5, 83), (1.5, .5, 81), (2, 1, 79), (3, .5, 76), (3.5, .5, 78),
         (4, .75, 79), (4.75, .25, 81), (5, .5, 83), (5.5, .5, 86), (6, 1.5, 83), (7.5, .5, 81)]
    B = [(0, 1, 88), (1, .5, 86), (1.5, .5, 83), (2, 1, 81), (3, .5, 83), (3.5, .5, 81),
         (4, .5, 79), (4.5, .5, 78), (5, 1, 76), (6, 2, 76)]
    order = [A, A, B, B, A, B, A, B]
    for i, ph in enumerate(order):
        melody(t, ph, i * 8, 0.19, 12 if i >= 4 and ph is B else 0)
    return t.loop()


# ---------------- menu: heavy 150 bpm, La menor, mas himno ----------------
def menu():
    t = Track(150, 16)
    roots = [45, 45, 41, 43, 45, 45, 48, 43] * 2          # A A F G A A C G
    for b, r in enumerate(roots):
        metal_bar(t, b * 4, r, last_run=(b % 4 == 3))
        pad(t, b * 4, 4, [r + 24, r + 27, r + 31], 0.05)
    drums_metal(t, 16, double_kick_bars=(1, 2))
    M1 = [(0, 2, 81), (2, 1, 79), (3, 1, 76), (4, 2, 77), (6, 1, 79), (7, 1, 81)]
    M2 = [(0, 1.5, 84), (1.5, .5, 81), (2, 2, 79), (4, 1, 77), (5, 1, 79), (6, 2, 81)]
    M3 = [(0, .5, 81), (.5, .5, 84), (1, .5, 88), (1.5, .5, 84), (2, 1, 86), (3, 1, 84),
          (4, .5, 81), (4.5, .5, 79), (5, 1, 77), (6, 2, 79)]
    order = [M1, M2, M1, M2, M3, M3, M1, M3]
    for i, ph in enumerate(order):
        melody(t, ph, i * 8, 0.19, 0, 0.25)
    return t.loop()


# ---------------- fanfarria de final (stage clear), Do mayor, una sola vez ----------------
def stage_clear():
    t = Track(124, 6, tail=3.0)
    F = [(0, .5, 67), (.5, .5, 72), (1, .5, 76), (1.5, 1.5, 79), (3, .5, 76), (3.5, .5, 79), (4, 4, 84),
         (8, .5, 65), (8.5, .5, 69), (9, .5, 72), (9.5, 1.5, 77), (11, .5, 74), (11.5, .5, 77), (12, 4, 83),
         (16, .5, 67), (16.5, .5, 72), (17, .5, 76), (17.5, .5, 79), (18, .5, 84), (18.5, .5, 79), (19, .5, 84),
         (20, 1, 88), (21, .5, 86), (21.5, .5, 84), (22, 6, 88)]
    for (b0, d, m) in F:
        lead(t, b0, d, m, 0.2, 0.25, 0.6)
        lead(t, b0, d, m - 12, 0.1, 0.5, 0.6)
    chords = [(0, 8, 48), (8, 8, 53), (16, 4, 55), (20, 4, 48)]
    for (b0, d, r) in chords:
        for k in range(int(d)):
            guitar(t, b0 + k, 0.9, r, 0.28, mute=False)
            bass(t, b0 + k, 0.9, r - 12, 0.5)
    for b in range(0, 24, 1):
        t.add(b, kick(), 0.8 if b % 2 == 0 else 0.0)
        if b % 2 == 1:
            t.add(b, snare(), 0.55)
    for k in range(8):
        t.add(14 + k * 0.25, snare(), 0.3 + 0.08 * k)   # redoble
    t.add(20, crash(), 0.8)
    t.add(0, crash(), 0.6)
    return t.raw()


# ---------------- game over: lento y sombrio, Do menor ----------------
def game_over():
    t = Track(72, 5, tail=4.0)
    for (b0, d, m) in [(0, 2, 72), (2, 2, 70), (4, 2, 68), (6, 4, 67), (10, 3, 65), (13, 7, 60)]:
        lead(t, b0, d, m, 0.2, 0.5, 1.0)
    for (b0, d, ms) in [(0, 6, [48, 51, 55]), (6, 6, [44, 48, 51]), (12, 8, [43, 46, 50])]:
        pad(t, b0, d, ms, 0.16)
    for k in range(0, 18, 2):
        t.add(k, tom(90), 0.7 * (1 - k / 28))
        t.add(k + 0.5, tom(80), 0.4 * (1 - k / 28))
    bass(t, 0, 6, 36, 0.5); bass(t, 6, 6, 32, 0.5); bass(t, 12, 8, 31, 0.5)
    return t.raw()


if __name__ == '__main__':
    write('street_theme.wav', street())
    write('menu_theme.wav', menu())
    write('stage_clear.wav', stage_clear())
    write('game_over.wav', game_over())
