"""Genera los efectos de sonido en assets/sfx/ (sintetizados): swing, hit, hit_heavy, grunt_enemy, grunt_player,
ko y thunder (rayo que retumba). Uso: python tools/make_sfx.py"""
import os, wave
import numpy as np

SR = 32000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'sfx')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(5)


def tt(n):
    return np.arange(n) / SR


def lowpass(x, a):
    """Filtro de un polo; a puede ser escalar o array (coeficiente por muestra, 0..1)."""
    y = np.zeros_like(x)
    acc = 0.0
    av = np.broadcast_to(a, x.shape)
    for i in range(len(x)):
        acc += av[i] * (x[i] - acc)
        y[i] = acc
    return y


def write(name, sig, db=-2.0):
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * 10 ** (db / 20)
    pcm = (np.clip(sig, -1, 1) * 32767).astype(np.int16)
    p = os.path.join(OUT, name + '.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print('ok', name, round(len(pcm) / SR, 2), 's')


def swing():
    n = int(0.085 * SR)                                    # silbido muy corto y seco
    t = tt(n)
    noise = rng.uniform(-1, 1, n)
    a = 0.1 + 0.45 * np.sin(np.pi * t / t[-1]) ** 2
    band = noise - lowpass(noise, 0.03)
    return lowpass(band, a) * np.sin(np.pi * t / t[-1]) ** 1.2


def thump(f0, f1, dur, decay):
    n = int(dur * SR)
    t = tt(n)
    f = f1 + (f0 - f1) * np.exp(-t / (decay * 0.35))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay)


def hit(heavy=False):
    n = int((0.17 if heavy else 0.1) * SR)                 # golpes secos: ataque inmediato, cola cortisima
    sig = np.zeros(n)
    th = thump(190 if not heavy else 150, 70 if not heavy else 50, 0.15 if heavy else 0.08, 0.045 if heavy else 0.022)
    sig[:len(th)] += th * 1.0
    m = int((0.05 if heavy else 0.03) * SR)
    t = tt(m)
    crack = rng.uniform(-1, 1, m)
    crack = crack - lowpass(crack, 0.2)
    sig[:m] += crack * np.exp(-t / (0.012 if heavy else 0.007)) * 1.1
    if heavy:
        d = int(0.03 * SR)
        sig[d:d + len(th) // 2] += th[:len(th) // 2] * 0.45
    return lowpass(np.tanh(sig * 1.8), 0.7)


def grunt(f_start, f_end, dur=0.12, rough=1.0):
    n = int(dur * SR)
    t = tt(n)
    f = f_start + (f_end - f_start) * (t / t[-1])
    ph = np.cumsum(f) / SR
    src = 2 * (ph % 1.0) - 1                               # diente de sierra = voz
    src += rough * 0.25 * rng.uniform(-1, 1, n)
    # dos formantes aproximados (vocal "uh") con filtros paso-bajo en cascada y paso-alto
    v = lowpass(src, 0.28)
    v = v - lowpass(v, 0.04)
    v = np.tanh(v * 2.0)
    return v * np.minimum(1, t / 0.01) * np.exp(-t / (dur * 0.4))


def ko():
    n = int(0.35 * SR)
    t = tt(n)
    f = 330 * np.exp(-t / 0.15) + 50
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 * np.exp(-t / 0.15)
    noise = rng.uniform(-1, 1, n) * np.exp(-t / 0.05) * 0.5
    th = np.zeros(n); th[:int(0.3 * SR)] = thump(120, 40, 0.3, 0.1)
    return np.tanh((tone + noise + th) * 1.3)


def thunder():
    dur = 4.2
    n = int(dur * SR)
    t = tt(n)
    sig = np.zeros(n)
    # chasquido inicial (rayo): ruido blanco muy corto y brillante
    c = int(0.09 * SR)
    sig[:c] += (rng.uniform(-1, 1, c) * np.exp(-tt(c) / 0.025)) * 1.2
    # retumbar: ruido marron filtrado con rafagas de amplitud que decaen (ecos del trueno)
    white = rng.uniform(-1, 1, n)
    brown = lowpass(white, 0.015)
    brown = brown - lowpass(brown, 0.0006)
    brown = brown / (np.abs(brown).max() + 1e-9)
    mod = np.zeros(n)
    for start, amp, width in ((0.04, 1.0, 0.7), (0.5, 0.8, 0.6), (1.1, 0.7, 0.8), (1.9, 0.5, 0.9), (2.7, 0.35, 0.8)):
        i = int(start * SR)
        seg = np.exp(-tt(n - i) / width) * np.minimum(1, tt(n - i) / 0.05)
        mod[i:] += seg * amp
    mod *= np.exp(-t / 2.0)
    sig += brown * mod * 2.2
    # subgrave que se estremece
    sig += np.sin(2 * np.pi * (42 + 10 * np.exp(-t / 0.8)) * t) * np.exp(-t / 1.4) * 0.5
    out = np.tanh(sig * 1.2)
    out = lowpass(out, 0.22)                              # el trueno es grave
    out[:c] = lowpass(sig[:c], 0.6) * 0.9 + out[:c]       # el chasquido conserva algo de brillo
    return out


def slot_tick():
    """Clic mecanico de rodillo de tragaperras: golpecito seco + pitido corto."""
    n = int(0.04 * SR)
    t = tt(n)
    click = rng.uniform(-1, 1, n)
    click = click - lowpass(click, 0.15)
    sig = click * np.exp(-t / 0.004) * 0.9
    sig += np.sin(2 * np.pi * 1900 * t) * np.exp(-t / 0.012) * 0.55
    sig += np.sin(2 * np.pi * 320 * t) * np.exp(-t / 0.01) * 0.5
    return sig


def slot_win():
    """Premio de tragaperras: arpegio de campanitas que acaba en un acorde brillante."""
    n = int(1.1 * SR)
    sig = np.zeros(n)
    for k, f in enumerate((880, 1109, 1319, 1760, 2093)):
        i = int(k * 0.07 * SR)
        m = n - i
        t = tt(m)
        bell = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.1)) * np.exp(-t / 0.35)
        sig[i:] += bell * (0.5 + 0.1 * k)
    return np.tanh(sig * 0.9)


if __name__ == '__main__':
    write('swing', swing(), -6)
    write('hit', hit(False), -2)
    write('hit_heavy', hit(True), -1)
    write('grunt_enemy', grunt(130, 85, 0.13), -5)
    write('grunt_player', grunt(210, 140, 0.12), -5)
    write('ko', ko(), -3)
    write('thunder', thunder(), -1)
    write('slot_tick', slot_tick(), -6)
    write('slot_win', slot_win(), -4)
