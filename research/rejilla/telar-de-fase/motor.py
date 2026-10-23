"""Telar de fase 1.0. Gaussian wavepackets; continuous metaplectic lift.

Convention: F(f)(p) = integral f(x) exp(-2 pi i p x) dx.
R(pi/2) = exp(-i pi/4) F. No Hermite phases assigned to audio partials.
Only numpy is needed to use this motor. See README for the carrier and sampling.
"""
from dataclasses import dataclass, replace
import math
import numpy as np

VERSION = '1.0.0'
SEMILLA = 20261021
SR = 32768
TAU = .018


@dataclass(frozen=True)
class Paquete:
    """B exp[-pi A (x-q)^2 + 2 pi i p (x-q/2)], Re(A)>0."""
    A: complex
    B: complex
    q: float = 0.
    p: float = 0.

    def __post_init__(self):
        if not all(np.isfinite(v) for v in (self.A, self.B, self.q, self.p)) or self.A.real <= 0:
            raise ValueError('Paquete no finito o con anchura no positiva')

    def evaluar(self, x):
        return self.B * np.exp(-np.pi*self.A*(x-self.q)**2 + 2j*np.pi*self.p*(x-self.q/2))

    def chirp(self, c):
        return replace(self, A=self.A-1j*c, p=self.p+c*self.q)

    def dilatar(self, a):
        if not np.isfinite(a) or a <= 0:
            raise ValueError('La dilatación debe ser positiva y finita')
        return Paquete(self.A/a**2, self.B/math.sqrt(a), self.q*a, self.p/a)

    def girar(self, theta):
        if not np.isfinite(theta) or abs(theta) > 64*np.pi:
            raise ValueError('Giro fuera del intervalo admitido: ±32 vueltas')
        # Follow the path, never reduce theta modulo 2pi. Each denominator stays
        # in one open half-plane, so its principal square root is the local lift.
        pasos = max(1, math.ceil(abs(theta)/(np.pi/4)))
        c, s = math.cos(theta/pasos), math.sin(theta/pasos)
        z = self
        for _ in range(pasos):
            den = c+1j*z.A*s
            z = Paquete((z.A*c+1j*s)/den, z.B/np.sqrt(den),
                        c*z.q+s*z.p, -s*z.q+c*z.p)
        return z

    def dispersar(self, b):
        # R(pi/2) C(-b) R(-pi/2): Fourier multiplier exp(-i pi b p^2).
        return self.girar(-np.pi/2).chirp(-b).girar(np.pi/2)


def aplicar(paquetes, operaciones):
    z = list(paquetes)
    for nombre, valor in operaciones:
        if nombre not in ('girar', 'chirp', 'dilatar', 'dispersar') or not np.isfinite(valor):
            raise ValueError('Operación desconocida o parámetro no finito')
        z = [getattr(p, nombre)(float(valor)) for p in z]
    return z


def inversa(operaciones):
    return [(n, 1/v if n == 'dilatar' else -v) for n, v in reversed(operaciones)]


def evaluar(paquetes, x):
    return sum((p.evaluar(np.asarray(x)) for p in paquetes), np.zeros_like(x, dtype=complex))


def hz(midi):
    return 440*2**((midi-69)/12)


def fuente(midi=57, cuerpo='cobre', semilla=SEMILLA):
    """A sum of real continuous Gaussians in complex baseband; no audio assets.

    Carrier hz(midi) is applied AFTER the metaplectic core. Higher partials are
    displacements of Gaussian packets, not eigenmodes of the harmonic oscillator.
    """
    if cuerpo not in ('cobre', 'vidrio', 'boca'):
        raise ValueError('Cuerpo desconocido')
    f = hz(midi)
    z = []
    for h in range(1, 8):
        ratio = h if cuerpo != 'vidrio' else h*(1+.014*(h-1)**2)
        weight = h**-1.15
        if cuerpo == 'boca':
            weight *= .25+1.7*np.exp(-((h*f-750)/260)**2)+np.exp(-((h*f-1250)/350)**2)
        A = (.08+.012*h) + 1j*(.025*h)
        if cuerpo == 'vidrio':
            A = (.16+.02*h) + .01j*h
        q = -.2+.07*h
        p = (ratio-1)*f*TAU
        phase = .25*math.sin((semilla % 65521)*.13+h*2.17)
        # Correct Weyl phase so all partials share their physical onset phase.
        B = .18*weight*np.exp(1j*phase-1j*np.pi*p*q)
        z.append(Paquete(A, B, q, p))
    return z


def operaciones(giro=0., inclinacion=0., estirar=1., dispersion=0., orden='inclinar-girar'):
    if orden not in ('inclinar-girar', 'girar-inclinar'):
        raise ValueError('Orden desconocido')
    middle = [('chirp', inclinacion), ('girar', giro)]
    if orden == 'girar-inclinar':
        middle.reverse()
    return [('dilatar', estirar), *middle, ('dispersar', dispersion)]


def nota(midi=57, cuerpo='cobre', giro=0., inclinacion=0., estirar=1., dispersion=0.,
         referencia=0., orden='inclinar-girar', sr=SR, duracion=1.5, semilla=SEMILLA):
    """Return real audio and metadata. Same fixed gain across all gestures.

    Note center = 0.6 s. The metaplectic envelope may precede its center.
    The finite output window and the real carrier are outside the unitary core.
    """
    if not 24 <= midi <= 96 or not 8000 <= sr <= 192000 or not .05 <= duracion <= 30:
        raise ValueError('Nota, frecuencia de muestreo o duración fuera de rango')
    if not 0 <= referencia <= 1:
        raise ValueError('Referencia fuera de 0..1')
    t = np.arange(round(sr*duracion))/sr
    x = (t-.6)/TAU
    original = fuente(midi, cuerpo, semilla)
    ops = operaciones(giro, inclinacion, estirar, dispersion, orden)
    viajera = aplicar(original, ops)
    z = evaluar(viajera, x)
    if referencia:
        z = (z+referencia*evaluar(original, x))/(1+referencia)
    y = np.real(z*np.exp(2j*np.pi*hz(midi)*(t-.6)))
    # Fixed 6ms boundary fade; never normalize a cancellation into full volume.
    fade = max(1, round(.006*sr))
    y[:fade] *= np.linspace(0, 1, fade)
    y[-fade:] *= np.linspace(1, 0, fade)
    return y, {'midi': midi, 'cuerpo': cuerpo, 'operaciones': ops, 'referencia': referencia,
               'semilla': semilla, 'tau_s': TAU, 'centro_s': .6,
               'pico': float(np.max(np.abs(y))), 'rms': float(np.sqrt(np.mean(y*y)))}


def render(partitura, duracion, sr=SR, semilla=SEMILLA):
    """Rejilla-compatible event score. e['t'] is the packet center in seconds.

    Each event may carry midi, vel, pan, cuerpo, giro, inclinacion, estirar,
    dispersion, referencia, orden. All durations are seconds, angles radians.
    """
    audio = np.zeros((round(duracion*sr), 2))
    allowed = {'midi','cuerpo','giro','inclinacion','estirar','dispersion','referencia','orden'}
    recibos = []
    for e in partitura.get('notas', []):
        params = {k:v for k,v in e.items() if k in allowed}
        y, meta = nota(**params, sr=sr, semilla=semilla)
        i = round((e['t']-.6)*sr)
        off = max(0, -i)
        i = max(0, i)
        n = min(len(y)-off, len(audio)-i)
        pan = float(e.get('pan', 0))
        vel = float(e.get('vel', .8))
        if not -1 <= pan <= 1 or not 0 <= vel <= 1:
            raise ValueError('Pan o velocidad fuera de rango')
        angle = (pan+1)*np.pi/4
        if n > 0:
            audio[i:i+n] += y[off:off+n, None]*vel*np.array([np.cos(angle), np.sin(angle)])
        recibos.append({'t':e['t'], **meta})
    if not np.isfinite(audio).all():
        raise ValueError('Audio no finito')
    return audio, recibos


def coeficientes_rejilla(audio, sr=SR):
    """Exact sampled DFT columns: one column = one second at even sr.

    Shape (channels, columns, sr/2). Complex coefficients normalized by sr.
    DC and Nyquist are zeroed, as spectrumsynth's real sinusoidal rows require.
    This is an adapter from this temporal motor, not closed-form modal writing.
    """
    if sr % 2:
        raise ValueError('La rejilla requiere sample_rate par')
    y = np.asarray(audio)
    if y.ndim == 1:
        y = y[:, None]
    columns = math.ceil(len(y)/sr)
    padded = np.pad(y, ((0, columns*sr-len(y)), (0,0)))
    blocks = padded.reshape(columns, sr, y.shape[1])
    Z = np.fft.rfft(blocks, axis=1)/sr
    Z[:,0,:] = 0
    return Z[:,:sr//2,:].transpose(2,0,1)
