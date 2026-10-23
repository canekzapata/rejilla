// Saca del país que se calcula las dos ventanas que se van a oír, en JSON.
// Izquierdo: la tinta fina (×1), una generación por segundo.
// Derecho: la tinta ×7 en sus propias celdas: la misma ley, siete veces más lenta.
import { crearMundo, ventanaNativa, FUERA, MOTOR } from '../../netart/pais-que-se-calcula/motor.js';
import { TEXTO_FUNDADOR, SEMILLA } from '../../netart/pais-que-se-calcula/fundador.js';

const [voces = 24, segundos = 98] = process.argv.slice(2).map(Number);
const m = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
const [fina, lenta] = m.capas;
const leer = (capa, gens) => {
  const v = ventanaNativa(capa, capa.xMin, 0, voces, gens);
  return Array.from({ length: gens }, (_, t) =>
    Array.from(v.subarray(t * voces, (t + 1) * voces), (q) => (q === FUERA ? 0 : q)));
};
const gLenta = Math.ceil(segundos / lenta.escala);
console.log(JSON.stringify({
  motor: MOTOR, semilla: SEMILLA, voces, segundos,
  izq: { p: fina.p, escala: fina.escala, x0: fina.xMin, regla: [fina.cl, fina.cc, fina.cr], filas: leer(fina, segundos) },
  der: { p: lenta.p, escala: lenta.escala, x0: lenta.xMin, regla: [lenta.cl, lenta.cc, lenta.cr], filas: leer(lenta, gLenta) },
}));
