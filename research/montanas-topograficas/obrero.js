// obrero.js — levanta láminas fuera del hilo de la página, para las miniaturas del atlas.
// Recibe {s, lang} y devuelve los trazos en un solo arreglo plano (rápido de pasar):
// por trazo, [pluma, n, x0, y0, x1, y1, …].
self.window = self;
importScripts('nucleo.js?v=38', 'terreno.js?v=38', 'idioma.js?v=38', 'letra.js?v=38', 'vistas.js?v=38',
  'toponimia/glosario.js?v=38', 'toponimia/nombrar.js?v=38', 'edicion/variantes.js?v=38', 'lamina.js?v=38');

self.onmessage = (e) => {
  const { s, lang, id, tipo } = e.data;
  if (tipo === 'terreno') { // sólo el relieve, para coserlo al panorama de la portada
    try {
      const MT = self.MT, T = MT.terreno(String(s), {});
      const nom = MT.nombra(T, String(s), (MT.VARIANTES && MT.VARIANTES[s]) || 0).filter((n) => n.clase === 'cumbre' || n.clase === 'atolon').slice(0, 3)
        .map((n) => ({ u: n.u, v: n.v, nombre: n.nombre, glosa: n.glosa }));
      const rios = T.hidro ? (T.hidro.rios || []).slice().sort((a, b) => b.clase - a.clase).slice(0, 10).map((r) => r.pts.map(([u, v]) => [u, v])) : [];
      const h = new Float32Array(T.h);
      self.postMessage({ id, s, terreno: { h, G: T.G, relieve: T.relieve, base: T.base, anchoKm: T.anchoKm, arq: T.arq, tipo: T.nombre, mar: T.mar, nombres: nom, rios } }, [h.buffer]);
    } catch (err) { self.postMessage({ id, s, error: String(err) }); }
    return;
  }
  try {
    const L = self.MT.lamina(String(s), { lang });
    let n = 0;
    for (const t of L.trazos) n += 2 + t.pts.length * 2;
    const plano = new Float32Array(n);
    let k = 0;
    for (const t of L.trazos) {
      plano[k++] = t.pluma; plano[k++] = t.pts.length;
      for (const [x, y] of t.pts) { plano[k++] = x; plano[k++] = y; }
    }
    self.postMessage({ id, s, page: L.page, papel: L.papel, plumas: L.plumas, plano, meta: { toponimo: L.meta.toponimo, nombre: L.meta.nombre } }, [plano.buffer]);
  } catch (err) {
    self.postMessage({ id, s, error: String(err) });
  }
};
