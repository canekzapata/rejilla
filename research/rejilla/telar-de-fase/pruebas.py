"""Independent checks for the continuous Gaussian metaplectic motor."""
import json
import numpy as np
from motor import Paquete, aplicar, evaluar, inversa, fuente, nota, coeficientes_rejilla


def comprobar():
    x = np.linspace(-65, 65, 65537)
    packets = [Paquete(.7+.31j, .8+.2j, .3, .9), Paquete(1.2-.2j, .3-.1j, -.8, -.6)]
    y = evaluar(packets, x)
    rel = lambda a,b: float(np.linalg.norm(a-b)/np.linalg.norm(b))
    ops = [('dilatar',1.4),('chirp',.7),('girar',1.1),('dispersar',.6)]
    chain = evaluar(aplicar(packets, ops), x)
    inverse_error = rel(evaluar(aplicar(packets, ops+inversa(ops)), x), y)
    energy_error = abs(float(np.trapezoid(abs(chain)**2,x)/np.trapezoid(abs(y)**2,x))-1)
    turn_error = rel(evaluar(aplicar(packets,[('girar',2*np.pi)]), x), -y)
    two_turn_error = rel(evaluar(aplicar(packets,[('girar',4*np.pi)]), x), y)
    chirp_error = rel(evaluar(aplicar(packets,[('chirp',.6)]),x), y*np.exp(.6j*np.pi*x*x))
    dilation_error = rel(evaluar(aplicar(packets,[('dilatar',1.3)]),x), evaluar(packets,x/1.3)/np.sqrt(1.3))
    # Quadrature definition of Fourier, independent of Gaussian parameter rules.
    t = np.linspace(-18,18,16385)
    u = np.linspace(-3,3,193)
    numeric = np.trapezoid(evaluar(packets,t)[None,:]*np.exp(-2j*np.pi*u[:,None]*t), t, axis=1)
    fourier_error = rel(evaluar(aplicar(packets,[('girar',np.pi/2)]),u), np.exp(-1j*np.pi/4)*numeric)
    first = evaluar(aplicar(packets,[('chirp',.8),('girar',.9)]),x)
    second = evaluar(aplicar(packets,[('girar',.9),('chirp',.8)]),x)
    order_difference = rel(first,second)
    clean,_ = nota()
    cancelled,_ = nota(giro=2*np.pi,referencia=1)
    restored,_ = nota(giro=4*np.pi,referencia=1)
    cancellation_db = 20*np.log10(max(1e-16,np.linalg.norm(cancelled)/np.linalg.norm(clean)))
    restored_error = rel(restored,clean)
    Z = coeficientes_rejilla(clean)
    bins = np.pad(Z[0],((0,0),(0,1)))
    decoded = np.fft.irfft(bins*32768, n=32768, axis=1).ravel()[:len(clean)]
    grid_error = rel(decoded, clean)
    # Entire admitted UI range: finite, safe fixed gain, including low notes.
    maximum = 0.
    for midi in (48,57,72):
        for theta in (0,np.pi/2,np.pi,2*np.pi,4*np.pi):
            for a in (.5,2.):
                v,_=nota(midi=midi,giro=theta,inclinacion=.8,estirar=a,dispersion=.6)
                assert np.isfinite(v).all()
                maximum=max(maximum,float(abs(v).max()))
    result = dict(inversa_error_rel=inverse_error, energia_compleja_error_rel=energy_error,
        giro_2pi_error_rel=turn_error, giro_4pi_error_rel=two_turn_error,
        chirp_error_rel=chirp_error, dilatacion_error_rel=dilation_error,
        fourier_cuadratura_error_rel=fourier_error, orden_diferencia_rel=order_difference,
        cancelacion_2pi_db=cancellation_db, retorno_4pi_error_rel=restored_error,
        rejilla_dft_error_rel=grid_error,pico_extremos_interfaz=maximum)
    for k in ('inversa_error_rel','energia_compleja_error_rel','giro_2pi_error_rel',
              'giro_4pi_error_rel','chirp_error_rel','dilatacion_error_rel','fourier_cuadratura_error_rel',
              'retorno_4pi_error_rel'):
        assert result[k]<1e-9, (k,result[k])
    assert order_difference>.05 and cancellation_db < -180
    assert grid_error<1e-5 and maximum < .98
    return result


if __name__ == '__main__':
    print(json.dumps(comprobar(), indent=2))
