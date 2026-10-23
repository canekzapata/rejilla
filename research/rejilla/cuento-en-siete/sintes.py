"""Cuento en siete — lo que se sintetiza en Python: el espectro (Grisey), el sinte del dúo, el sinte del coro, el sub 808 y los
vocoders. Lo usa mezcla.py; no escribe nada por su cuenta.

  espectro(P)          los parciales de Mi1 como resonadores: entran del grave al agudo, se estiran (f_k = f1·k^(1+σ)), laten en
                       2+2+3 al final del I y en la coda se recogen (σ → 0) hasta la fundamental
  sinte_lead(notas)    monofónico: dos sierras (±6 cents) por un pasabajos resonante de dos polos calculado armónico por armónico
                       (sin aliasing), portamento de 14 ms en lo ligado, el filtro abre más en los acentos
  sinte_coro(voces)    el coral en sierras apiladas (tres por voz, ±9 cents, y la soprano doblada a la octava): la portadora del
                       vocoder de hyperpop
  sub808(eventos)      seno que cae una octava en 35 ms y se satura
  vocoder(mod, car)    vocoder de canales por STFT: la envolvente de la moduladora (Sabina) en 30 bandas sobre la portadora
                       blanqueada; las consonantes (arriba de 5 kHz) pasan de la voz
"""
import math
import numpy as np
from scipy.signal import stft, istft, butter, sosfiltfilt

SR = 48000
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def espectro(P, N):
    E = P['espectro']; f1 = hz(E['fund'] + 12 * 0)            # E1: 41.2 Hz
    t = np.arange(N) / SR; y = np.zeros(N); rng = np.random.default_rng(P['semilla'])
    est = np.array(E['estira']); sig = np.interp(t, est[:, 0], est[:, 1])
    c = E['coda']; ce = np.array(c['estira']); en_coda = t >= c['t0']; sig[en_coda] = np.interp(t[en_coda], ce[:, 0], ce[:, 1])
    S = P['semicorchea']; r0, r1 = E['ritmo']['desde'], E['ritmo']['hasta']
    fin_I = P['compases'][10][0] * S
    for pa in E['parciales']:
        k, t0, v = pa['k'], pa['t'], pa['v']
        f = f1 * k ** (1 + sig)
        # envolvente: entra lento (como un resonador que se llena), se sostiene, se apaga al entrar la invención
        a = np.clip((t - t0) / (1.2 + 3 / k), 0, 1) ** 2 * np.clip(1 - (t - fin_I) / .5, 0, 1)
        # en la coda vuelve, del agudo al grave se va apagando: el último en irse es el 2
        tc0 = c['t0'] + .25 * (24 - k) * 0 + rng.uniform(0, .6); tc1 = c['t1'] - 1.2 * (k - 2) ** .8
        a += np.clip((t - tc0) / 2.0, 0, 1) * np.clip((tc1 - t) / 2.5, 0, 1) * .8
        # al final del I late: cada parcial en su propio periodo (múltiplos de la semicorchea según k) → el espectro se vuelve pulso
        per = S * [4, 4, 6][k % 3] * (1 + (k % 4 == 0)); fase = ((t - r0 + k * S) % per) / per
        pulso = np.where((t > r0) & (t < r1 + .2), np.clip(1.4 - 2.2 * fase, .15, 1), 1.0)
        mov = 1 + .12 * np.sin(2 * np.pi * (.13 + .05 * k) * t + rng.uniform(0, 6))      # el resonador respira
        ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 6)
        x = np.sin(ph) + .35 * np.sin(ph * 1.0007 + 1.3)                                    # dos modos casi juntos: baten
        act = a > 1e-4
        y[act] += (v * a * pulso * mov * x)[act]
    # el soplo del resonador: ruido en banda estrecha alrededor de cada parcial del 8 al 16, apenas
    ruido = rng.standard_normal(N)
    for k in range(8, 17):
        fk = f1 * k * 1.02
        b = sosfiltfilt(butter(2, [fk * .985, fk * 1.015], 'band', fs=SR, output='sos'), ruido)
        y += b * .25 / k * np.clip(t / 3, 0, 1) * (t < fin_I)
    # la fundamental sola al final
    tf = c['t1'] - 6; af = np.clip((t - tf) / 2, 0, 1) * np.clip((c['t1'] + 1 - t) / 3, 0, 1)
    y += .6 * af * np.sin(2 * np.pi * f1 * t)
    return y / (np.abs(y).max() + 1e-12)


def _lpf_mag(f, fc, q):
    x = f / fc; return 1 / np.sqrt((1 - x * x) ** 2 + (x / q) ** 2)


def sinte_lead(notas, N, semilla=0):
    """notas: [{t, dur, m, v}] monofónicas. Se rinde por frases (tramos sin silencio de más de 80 ms)."""
    y = np.zeros(N); rng = np.random.default_rng(semilla)
    if not notas: return y
    frases, cur = [], [notas[0]]
    for a, b in zip(notas, notas[1:]):
        if b['t'] - (a['t'] + a['dur']) > .08: frases.append(cur); cur = [b]
        else: cur.append(b)
    frases.append(cur)
    for fr in frases:
        i0 = max(0, int((fr[0]['t'] - .01) * SR)); i1 = min(N, int((fr[-1]['t'] + fr[-1]['dur'] + .25) * SR)); n = i1 - i0
        t = i0 / SR + np.arange(n) / SR
        m = np.full(n, fr[0]['m'], float); amp = np.zeros(n); fc = np.zeros(n)
        for j, nt in enumerate(fr):
            a = int((nt['t'] - i0 / SR) * SR); z = int((nt['t'] + nt['dur'] - i0 / SR) * SR)
            m[a:] = nt['m']
            if j:                                                  # portamento: 14 ms desde la nota anterior
                p = fr[j - 1]['m']; L = int(.014 * SR); u = np.linspace(0, 1, max(1, min(L, n - a)))
                m[a:a + len(u)] = p + (nt['m'] - p) * u
            u = (np.arange(n) - a) / SR
            env = np.where((u >= 0) & (u <= nt['dur']), np.minimum(1, u / .004), 0)
            rel = np.where(u > nt['dur'], np.exp(-(u - nt['dur']) / .05), 0) * (u > nt['dur'])
            amp = np.maximum(amp, nt['v'] * np.maximum(env, rel))
            # el filtro: abre al golpe (más en el acento) y se cierra en 90 ms hacia 2.2× la fundamental
            f0 = float(hz(nt['m']))
            fe = np.where(u >= 0, f0 * (2.2 + (6 + 6 * (nt['v'] >= 1)) * np.exp(-np.clip(u, 0, None) / .09)), 0)
            fc = np.where(u >= 0, fe, fc)
        f = hz(m) * (1 + .004 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - fr[0]['t']) / .4, 0, 1))
        fc = np.clip(fc, 200, 14000)
        x = np.zeros(n)
        for det in (-6, 6):
            fd = f * 2 ** (det / 1200); ph = 2 * np.pi * np.cumsum(fd) / SR + rng.uniform(0, 6)
            for k in range(1, 60):
                fk = k * fd
                if fk.min() > 15000: break
                g = (1 / k) * _lpf_mag(fk, fc, 2.6) * (fk < 15000)
                x += g * np.sin(k * ph)
        x += .25 * np.sign(np.sin(2 * np.pi * np.cumsum(f / 2) / SR)) * _lpf_mag(f, fc, 1)  # sub-oscilador cuadrado una octava abajo
        y[i0:i1] += np.tanh(1.6 * x * amp) / np.tanh(1.6)
    return y / (np.abs(y).max() + 1e-12)


def sinte_coro(voces, N, semilla=0):
    """voces: {'S': [{t, dur, nota}], 'A': …}. Sierras apiladas por sílaba; la soprano también a la octava."""
    y = np.zeros(N); rng = np.random.default_rng(semilla)
    for v, lst in voces.items():
        for e in lst:
            i0 = int(e['t'] * SR); n = min(N - i0, int((e['dur'] + .12) * SR))
            if n <= 0: continue
            t = np.arange(n) / SR; env = np.minimum(1, t / .01) * np.where(t < e['dur'], 1, np.exp(-(t - e['dur']) / .04))
            notas = [e['nota']] + ([e['nota'] + 12] if v == 'S' else []) + ([e['nota'] - 12] if v == 'B' else [])
            for m in notas:
                for det in (-9, 0, 9):
                    f = float(hz(m)) * 2 ** (det / 1200); ph = 2 * np.pi * f * t + rng.uniform(0, 6); x = np.zeros(n)
                    for k in range(1, int(9000 / f)): x += np.sin(k * ph) / k
                    y[i0:i0 + n] += x * env * (.5 if v == 'B' else .35)
    return y / (np.abs(y).max() + 1e-12)


def sub808(eventos, N):
    y = np.zeros(N)
    for e in eventos:
        i0 = int(e['t'] * SR); n = min(N - i0, int((e['dur'] + .15) * SR)); t = np.arange(n) / SR
        f = float(hz(e['midi'])) * (1 + 1.0 * np.exp(-t / .035))
        env = np.minimum(1, t / .003) * np.where(t < e['dur'], np.exp(-t / 1.2), np.exp(-e['dur'] / 1.2) * np.exp(-(t - e['dur']) / .05))
        y[i0:i0 + n] += np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env) * e['vel']
    return y / (np.abs(y).max() + 1e-12)


def _banco(f, bandas, lo, hi):
    """filtros triangulares en escala logarítmica (bandas × bins), normalizados por banda"""
    c = np.geomspace(lo, hi, bandas + 2); B = np.zeros((bandas, len(f)))
    for i in range(bandas):
        a, m, z = c[i], c[i + 1], c[i + 2]
        B[i] = np.clip(np.minimum((f - a) / (m - a), (z - f) / (z - m)), 0, None)
    return B


def vocoder(mod, car, bandas=30, lo=90, hi=7500, suaviza=3, consonantes=.35, piso_db=-55, graves=260):
    """mod, car: mono. La portadora se blanquea (se divide entre su propia envolvente) y toma la de la moduladora.
    Abajo de `graves` Hz la voz casi no tiene energía (Sabina canta arriba de 250 Hz) y el vocoder borraba el grave de toda
    portadora (v1–v3: hueco de −19 dB en 120–250 Hz en los coros): ahí las bandas siguen el volumen total de la voz y conservan
    la forma del espectro de la portadora."""
    n = max(len(mod), len(car)); mod = np.pad(mod, (0, n - len(mod))); car = np.pad(car, (0, n - len(car)))
    nper, hop = 1024, 256
    f, _, M = stft(mod, SR, nperseg=nper, noverlap=nper - hop); _, _, C = stft(car, SR, nperseg=nper, noverlap=nper - hop)
    B = _banco(f, bandas, lo, hi)
    Em = B @ np.abs(M); Ec = B @ np.abs(C)
    if suaviza > 1:                                            # ~16 ms de suavizado en el tiempo: ligado, sin perder las consonantes
        k = np.ones(suaviza) / suaviza; Em = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, Em)
    piso = Em.max() * 10 ** (piso_db / 20)
    G = Em / (Ec + Ec.max() * 1e-4) * (Em > piso)
    cen = np.geomspace(lo, hi, bandas + 2)[1:-1]; bajo = cen < graves
    if bajo.any():
        em, ec = Em[~bajo].sum(0), Ec[~bajo].sum(0)
        G[bajo] = (em / (ec + ec.max() * 1e-4) * (em > Em.max() * 10 ** (piso_db / 20)))[None, :]
    W = B / (B.sum(0, keepdims=True) + 1e-9)                   # de bandas a bins
    Y = C * (W.T @ G)
    _, y = istft(Y, SR, nperseg=nper, noverlap=nper - hop); y = y[:n]
    sib = sosfiltfilt(butter(4, 5000, 'high', fs=SR, output='sos'), mod)   # las consonantes de Sabina, tal cual
    y = y / (np.abs(y).max() + 1e-12) + consonantes * sib / (np.abs(sib).max() + 1e-12)
    return y / (np.abs(y).max() + 1e-12)
