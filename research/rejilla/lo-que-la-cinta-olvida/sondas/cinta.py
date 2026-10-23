"""sonda de la cinta: (1) un la 440 en tiempo de cinta tocado a v constante 0.64 debe salir a 281.6 Hz y durar 1/0.64 veces más;
(2) con v que cambia, la duración real es ∫dτ/v; (3) el lago: cada pasada pierde nivel y óxido.   python sondas/cinta.py"""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'motor')); import cinta as C
SR = 48000; T = 4.0; t = np.arange(int(T * SR)) / SR; x = np.stack([np.sin(2 * math.pi * 440 * t)] * 2, 1) * .5
mp = C.mapa(lambda s: .64, T); N = int(mp[1][-1] * SR); y, vt = C.tocar(x, mp, N, None, 1)
seg = y[SR:SR + 32768, 0]; F = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); f = np.fft.rfftfreq(len(seg), 1 / SR); k = F.argmax()
fp = f[k] + .5 * (F[k - 1] - F[k + 1]) / (F[k - 1] - 2 * F[k] + F[k + 1]) * (f[1] - f[0])
print(f'v=0.64: duración {N / SR:.3f} s (esperada {T / .64:.3f}) · altura {fp:.1f} Hz (esperada {440 * .64:.1f}, con wow y flutter encima)')
mp2 = C.mapa(lambda s: .57 if s < 2 else .82, T); print(f'v que cambia (.57 → .82): duración {mp2[1][-1]:.3f} s (esperada {2 / .57 + 2 / .82:.3f})')
ruido = np.random.default_rng(0).standard_normal((60 * SR, 2)) * .3
out, med = C.lago(ruido, 1, 3, 59, 2)
print('lago: pasadas', len(med)); [print('  ', m) for m in med[::5]]
