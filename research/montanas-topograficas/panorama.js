// panorama.js — el paisaje de la portada: varios terrenos de la edición cosidos en una sola
// tierra y trazados con horizonte flotante, cada sierra tapando a la de detrás.
// Tres al frente y tres atrás (los más altos atrás, para que se asomen). Devuelve sólo
// geometría (en las unidades de w × h): la usan el atlas (en vivo) y herramientas/panorama.js
// (og.png y el GIF del proceso).
(function (g) {
  const MT = g.MT;
  const KX = 3, KY = 2, BW = 0.035, SC = 0.8;
  const sst = (a, b, x) => { const u = Math.min(1, Math.max(0, (x - a) / (b - a))); return u * u * (3 - 2 * u); };
  const muestra = (T, lu, lv) => {
    const G = T.G, x = Math.min(1, Math.max(0, lu)) * (G - 1), y = Math.min(1, Math.max(0, lv)) * (G - 1);
    const xi = Math.min(G - 2, Math.floor(x)), yi = Math.min(G - 2, Math.floor(y)), fx = x - xi, fy = y - yi, k = yi * G + xi, h = T.h;
    return h[k] * (1 - fx) * (1 - fy) + h[k + 1] * fx * (1 - fy) + h[k + G] * (1 - fx) * fy + h[k + G + 1] * fx * fy;
  };

  // ter: [{h, G, relieve, base, rios, nombres}] — lo que devuelve obrero.js con tipo 'terreno'
  function cose(ter) {
    const orden = ter.map((x, i) => i).sort((a, b) => (ter[a].base + ter[a].relieve) - (ter[b].base + ter[b].relieve));
    const celdas = orden.map((ti, k) => ({ T: ter[ti], i: k % KX, j: Math.floor(k / KX) }));
    const altMax = Math.max(...ter.map((x) => x.base + x.relieve));
    // cada terreno con presencia: la altura real pesa, pero comprimida (un llano de 100 m
    // junto a una cordillera de 4 000 sigue teniendo forma). Atrás, un poco más alto.
    for (const c of celdas) {
      c.cu = (c.i + 0.5) / KX; c.cv = (c.j + 0.5) / KY;
      c.f = (0.3 + 0.7 * Math.sqrt((c.T.base + c.T.relieve) / altMax)) * (c.j ? 1 : 0.7);
    }
    const peso = (c, u, v) => sst(-BW, BW, 0.5 / KX - Math.abs(u - c.cu)) * sst(-BW, BW, 0.5 / KY - Math.abs(v - c.cv));
    const alt = (u, v) => {
      let a = 0, w = 0;
      for (const c of celdas) {
        const p = peso(c, u, v); if (p <= 0) continue;
        a += p * Math.max(0, muestra(c.T, 0.5 + (u - c.cu) * KX * SC, 0.5 + (v - c.cv) * KY * SC)) * c.f; w += p;
      }
      return w ? a / w : 0;
    };
    const T = { sample: alt, relieve: altMax, base: 0, alt: (hn) => hn * altMax, anchoKm: 40, exagMax: Infinity, mar: false };
    return { T, celdas, peso };
  }

  MT.panorama = function (ter, w, h, o = {}) {
    const lang = o.lang === 'en' ? 'en' : 'es', esc = o.esc || 1; // esc: tamaño de letra y separaciones
    const { T, celdas, peso } = cose(ter);
    const p = 0.5, W = w / p * 1.04, n = o.filas || Math.round(Math.min(150, Math.max(70, h / 6.5)));
    const V = MT.vistas.crestas(T, { L: w / 2 - W / 2, W, Y0: h * 1.3, D: h * 0.9, p, n, step: 1.6 * esc, rot: 0, top: h * 0.3, H: h * 0.55 });
    const aGlobal = (ce, lu, lv) => [ce.cu + (lu - 0.5) / (KX * SC), ce.cv + (lv - 0.5) / (KY * SC)];
    // ríos: de cada terreno, donde manda ese terreno, y sólo lo que se ve
    const rios = [];
    for (const ce of celdas) for (const rio of ce.T.rios || []) {
      let seg = [];
      for (const [lu, lv] of rio) {
        const [u, v] = aGlobal(ce, lu, lv);
        const q = u > 0 && u < 1 && v > 0 && v < 1 && peso(ce, u, v) > 0.6 ? V.proyecta(u, v) : null;
        if (q && q.vis) seg.push([q.x, q.y]); else { if (seg.length > 1) rios.push(Object.assign(seg, { fila: q ? q.r : 0 })); seg = []; }
      }
      if (seg.length > 1) rios.push(seg);
    }
    for (const sg of rios) if (sg.fila == null) sg.fila = 0;
    // cimas con nombre que se ven, sin encimarse
    const cand = [];
    for (const ce of celdas) for (const nm of (ce.T.nombres || []).slice(0, 1)) {
      const [u, v] = aGlobal(ce, nm.u, nm.v);
      if (u < 0.03 || u > 0.97 || v < 0.02 || v > 0.98) continue;
      const q = V.proyecta(u, v);
      if (!q.vis || q.x < 40 * esc || q.x > w - 40 * esc || q.y < h * 0.3) continue;
      cand.push({ ...q, nombre: nm.nombre, glosa: nm.glosa, alt: Math.round(ce.T.base + muestra(ce.T, nm.u, nm.v) * ce.T.relieve) });
    }
    cand.sort((a, b) => a.y - b.y);
    const puestas = [];
    for (const r of cand) if (puestas.every((q) => Math.abs(q.x - r.x) > 170 * esc)) puestas.push(r);
    // la letra, ya en trazos: marca, guía, nombre, altitud (y glosa en inglés)
    const letras = [], E = esc;
    const escribe = (txt, x, y, size, op) => { for (const l of MT.letra.trazos(txt, x, y, size * E, { crudo: true, ...op }).lineas) letras.push(l); };
    for (const r of puestas) {
      const yb = Math.max(h * 0.24, r.y - 46 * E);
      letras.push([[r.x - 3 * E, r.y - 2 * E], [r.x, r.y - 7 * E], [r.x + 3 * E, r.y - 2 * E], [r.x - 3 * E, r.y - 2 * E]]);
      letras.push([[r.x, r.y - 9 * E], [r.x, yb + 6 * E]]);
      escribe(r.nombre, r.x, yb - 9 * E, 9, { align: 'center', track: 1.5 * E, slant: 0.18 });
      escribe(r.alt.toLocaleString('es-MX').replace(/,/g, ' ') + ' M', r.x, yb + 3 * E, 7, { align: 'center' });
      if (lang === 'en' && r.glosa) escribe(r.glosa.toUpperCase(), r.x, yb + 13 * E, 5.5, { align: 'center' });
    }
    return { strokes: V.strokes, rios, letras, puestas, n };
  };
  MT.panorama.N = KX * KY;
  // la tinta del agua: siempre fría, y lejos del tono de la tierra (si la tierra ya es cian,
  // el agua se va al azul, y al revés)
  MT.panorama.agua = function (tinta, oscuro, azar) {
    const [r, g2, b] = [1, 3, 5].map((i) => parseInt(tinta.slice(i, i + 2), 16) / 255);
    const mx = Math.max(r, g2, b), mn = Math.min(r, g2, b), d = mx - mn;
    let hu = d === 0 ? 0 : mx === r ? 60 * (((g2 - b) / d) % 6) : mx === g2 ? 60 * ((b - r) / d + 2) : 60 * ((r - g2) / d + 4);
    hu = (hu + 375) % 360; // de HSL a un tono OKLCh aproximado
    let h = 185 + azar * 70;
    if (Math.abs(hu - h) < 50) h = hu < 222 ? 268 : 178;
    return oscuro ? MT.neon(h) : MT.oklch(0.55, 0.14, h);
  };
})(typeof globalThis !== 'undefined' ? globalThis : window);
