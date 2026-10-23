// lamina.js — compone la hoja: terreno + vistas + rótulos, todo en mm y en orden de trazado.
// Pluma 0 = relieve. Pluma 1 = letra, guías, escalas y marcos.
(function (G) {
  const MT = G.MT;
  MT.REGISTROS = ['carto', 'lamina', 'obra'];
  MT.NOMBRE_REGISTRO = { carto: 'cartográfico', lamina: 'lámina', obra: 'obra' };
  MT.HOJAS = ['crestas', 'curvas', 'lado', 'torre', 'bloque', 'proyeccion', 'secuencia', 'corte'];
  MT.NOMBRE_HOJA = { crestas: 'perfiles', curvas: 'curvas de nivel', lado: 'díptico', torre: 'lámina con proyecciones', bloque: 'bloque diagrama', proyeccion: 'bloque y planta proyectada', secuencia: 'historia en cuatro tiempos', corte: 'corte A–A′' };
  const DIR = ['SUR', 'ESTE', 'NORTE', 'OESTE'];
  const FLECHA_N = [[0, -1], [1, 0], [0, 1], [-1, 0]]; // hacia dónde queda el norte en la hoja
  const AL_OBSERVADOR = [[0, 1], [1, 0], [0, -1], [-1, 0]]; // dónde está quien mira, en una planta con el norte arriba

  const fmt = (n) => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const dec = (x) => { const v = Math.round(x * 10) / 10; return v.toFixed(Number.isInteger(v) ? 0 : 1); };
  const nice = (x) => {
    const e = Math.pow(10, Math.floor(Math.log10(x))), m = x / e;
    return (m < 1.5 ? 1 : m < 2.25 ? 2 : m < 3.5 ? 2.5 : m < 7.5 ? 5 : 10) * e;
  };
  const escalaNum = (n) => { const e = Math.pow(10, Math.floor(Math.log10(n)) - 1); return '1 : ' + fmt(Math.round(n / e) * e); };
  const circulo = (cx, cy, r, k = 14) => Array.from({ length: k + 1 }, (_, i) => {
    const a = (i / k) * Math.PI * 2; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r];
  });
  const S1 = 1.9, S2 = 2.3, SL = 0.22;
  const R8 = ['NORTE', 'NORESTE', 'ESTE', 'SURESTE', 'SUR', 'SUROESTE', 'OESTE', 'NOROESTE'];
  // un vector en (a, b) de la vista → (este, norte) del terreno
  const abUV = [(a, b) => [a, b], (a, b) => [-b, a], (a, b) => [-a, -b], (a, b) => [b, -a]];
  const uvAB = [(u, v) => [u, v], (u, v) => [v, -u], (u, v) => [-u, -v], (u, v) => [-v, u]];
  const rumbo = (rot, da, db) => { const [du, dv] = abUV[rot](da, db); const g = (Math.atan2(du, dv) * 180 / Math.PI + 360) % 360; return R8[Math.round(g / 45) % 8]; };
  // plano de planta derecho: la esquina (0,0) abajo a la izquierda
  const plano = (x0, y0, S, rot) => ({ O: [x0, y0 + S], U: [S, 0], V: [0, -S], S, rot, x0, y0 });
  // niveles de curva compartidos por la planta y el bloque
  function nivelesDe(T, eq, cada) {
    const out = [];
    if (T.mar) out.push({ m: T.nivelMar ? 0 : T.base, costa: true, maestra: true, hn: T.umbralMar });
    for (let m = Math.floor(T.base / eq) * eq + eq; m < T.base + T.relieve; m += eq) if (!(T.nivelMar && m === 0))
      out.push({ m, maestra: Math.round(m / eq) % cada === 0, hn: (m - T.base) / T.relieve });
    return out;
  }  function trazaRio(K, pts, clase) {
    if (pts.length < 2) return;
    const p = MT.simplifica(pts, 0.03);
    K.add(p, 1);
    if (clase >= 2) K.add(desfasa(p, 0.17).reverse(), 1);
    if (clase >= 3) K.add(desfasa(p, -0.17), 1);
  }
  const rioEnVista = (K, T, V) => { if (T.hidro && V.drape) for (const rv of T.hidro.rios) for (const t of V.drape(rv.pts)) trazaRio(K, t, rv.clase); };
  const desfasa = (p, d) => p.map((q, i) => {
    const a = p[Math.max(0, i - 1)], b = p[Math.min(p.length - 1, i + 1)];
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    return [q[0] - (b[1] - a[1]) / L * d, q[1] + (b[0] - a[0]) / L * d];
  });

  // ── el papel: todo lo que se dibuja pasa por aquí, en orden
  function lienzo() {
    const trazos = [], etiquetas = [];
    const add = (pts, pluma) => { if (pts.length > 1) trazos.push({ pluma, pts }); };
    // cada nombre propio deja su caja: el visor la usa para abrir la ficha del nombre
    const marcaTopo = (topo, lineas) => {
      if (!topo || !lineas.length) return;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (const l of lineas) for (const [x, y] of l) { if (x < x0) x0 = x; if (y < y0) y0 = y; if (x > x1) x1 = x; if (y > y1) y1 = y; }
      etiquetas.push({ topo, caja: [x0 - 0.6, y0 - 0.6, x1 + 0.6, y1 + 0.6] });
    };
    const escribe = (s, x, y, size, op = {}) => {
      const t = MT.letra.trazos(s, x, y, size, op); t.lineas.forEach((l) => add(l, 1)); marcaTopo(op.topo, t.lineas); return t.ancho;
    };
    const escribeRot = (s, cx, cy, size, th, op = {}) => {
      const t = MT.letra.trazos(s, 0, size / 2, size, { ...op, align: 'center' });
      const c = Math.cos(th), sn = Math.sin(th);
      const ls = t.lineas.map((l) => l.map(([x, y]) => [cx + x * c - y * sn, cy + x * sn + y * c]));
      ls.forEach((l) => add(l, 1)); marcaTopo(op.topo, ls);
    };
    const discontinua = (a, b, on = 1.2, off = 1) => {
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 0.5) return;
      const ux = (b[0] - a[0]) / L, uy = (b[1] - a[1]) / L;
      for (let s = 0; s < L; s += on + off) {
        const e = Math.min(L, s + on); add([[a[0] + ux * s, a[1] + uy * s], [a[0] + ux * e, a[1] + uy * e]], 1);
      }
    };
    const flecha = (x, y, dx, dy, L, rotulo) => {
      const tx = x + dx * L / 2, ty = y + dy * L / 2;
      add([[x - dx * L / 2, y - dy * L / 2], [tx, ty]], 1);
      add([[tx - dx * 2 - dy * 1.2, ty - dy * 2 + dx * 1.2], [tx, ty], [tx - dx * 2 + dy * 1.2, ty - dy * 2 - dx * 1.2]], 1);
      if (rotulo) escribe(rotulo, tx + dx * 3, ty + dy * 3 + 1.1, 2.2, { align: 'center' });
    };
    const marco = (x0, y0, x1, y1) => add([[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]], 1);
    return { trazos, etiquetas, marcaTopo, add, escribe, escribeRot, discontinua, flecha, marco };
  }

  // escala gráfica de doble filete, segmentos alternos rellenos con una segunda pasada
  function escalaGrafica(K, x0, y, mmKm, maxLen, titulo) {
    const paso = nice(maxLen * 0.8 / mmKm / 4);
    const div = Math.max(2, Math.min(5, Math.floor(maxLen / (paso * mmKm)))), w = paso * mmKm;
    K.add([[x0, y], [x0 + div * w, y]], 1);
    K.add([[x0 + div * w, y + 1.2], [x0, y + 1.2]], 1);
    for (let k = 0; k <= div; k++) {
      K.add([[x0 + k * w, y - 0.6], [x0 + k * w, y + 1.8]], 1);
      K.escribe(dec(k * paso) + (k === div ? ' KM' : ''), x0 + k * w, y + 4.6, 1.7, { align: k === div ? 'left' : 'center' });
      if (k < div && k % 2 === 0) {
        K.add([[x0 + k * w, y + 0.4], [x0 + (k + 1) * w, y + 0.4]], 1);
        K.add([[x0 + (k + 1) * w, y + 0.8], [x0 + k * w, y + 0.8]], 1);
      }
    }
    if (titulo) K.escribe(titulo, x0, y - 2, 1.5, { slant: SL, track: 0.4 });
  }

  // qué rasgos del terreno merecen nombre en esta lámina
  function rasgosRotulables(T, registro, enPlanta) {
    const R = T.rasgos, nP = T.arq === 'dunas' ? 1 : { carto: 3, lamina: 2, obra: 1 }[registro]; // en el mar de arena, una cresta basta
    const interior = (q) => q.u > 0.06 && q.u < 0.94 && q.v > 0.06 && q.v < 0.94;
    const sobreAgua = (q) => !T.nivelMar || q.h > T.nivelMar + 0.005; // bajo el mar no hay cimas ni collados que nombrar
    const picos = R.picos.filter((q) => q.prom >= 0.08 && interior(q) && sobreAgua(q));
    const tt = T.terminos || {};
    const principal = tt.principal || (T.arq === 'mesa' ? 'MESA' : T.arq === 'canon' ? 'BORDE' : 'CUMBRE');
    const esp = (R.especiales || []).filter(interior).slice(0, nP);
    if (T.arq === 'impactos') return { lista: bautiza(T, esp), nP: 0 }; // en la llanura de impactos sólo cuentan los cráteres
    let L = [];
    const cerca = (q) => esp.some((e) => Math.hypot(e.u - q.u, e.v - q.v) < 0.035); // no rotular dos veces lo mismo
    if (T.arq !== 'canon' || enPlanta) L = picos.filter((q) => !cerca(q)).slice(0, nP + 2).map((q, i) => ({ ...q, tipo: 'pico', term: i === 0 ? principal : tt.otros || 'CIMA' }));
    if (T.arq === 'canon') L = L.slice(0, 1);
    if (registro !== 'obra' && T.arq !== 'canon' && T.arq !== 'dunas' && picos[1] && picos[1].col && picos[1].col.h > 0.03 && sobreAgua(picos[1].col) && interior(picos[1].col)) // un collado al nivel del mar no es collado
      L.splice(Math.min(2, L.length), 0, { ...picos[1].col, tipo: 'col', term: 'COLLADO' });
    if (T.arq === 'canon' && enPlanta && R.fondo) L.push({ ...R.fondo, tipo: 'fondo', term: 'FONDO' });
    // orden de importancia: la cima principal, lo especial, el collado, el agua, las demás cimas
    const pk = L.filter((c) => c.tipo === 'pico'), otros = L.filter((c) => c.tipo !== 'pico');
    const lista = bautiza(T, [...pk.slice(0, 1), ...esp, ...otros, ...pk.slice(1)]);
    // el agua con nombre (lagos, mar, playa; los ríos van por su cauce, en la planta): sin pasar
    // de 5 nombres por lámina, contando las cimas que se alcanzan a poner
    const N = T.toponimos || [], cupo = Math.max(0, 5 - esp.length - Math.min(L.length, nP + 1));
    const aguas = ['mar', 'lago', 'playa'].flatMap((cl) => N.filter((n) => n.clase === cl && interior(n)));
    for (const n of aguas.slice(0, cupo)) {
      // si ya hay un rasgo especial ahí (el LAGO del rift, la LAGUNA del atolón), le pone su nombre
      const ya = lista.find((c) => !c.crudo && Math.hypot(c.u - n.u, c.v - n.v) < 0.06);
      if (ya) { Object.assign(ya, { term: n.nombre, crudo: true, glosa: n.glosa, topo: n }); continue; }
      lista.splice(1 + esp.length + otros.length, 0, { u: n.u, v: n.v, h: n.h, tipo: 'agua', clase: n.clase, term: n.nombre, crudo: true, glosa: n.glosa, sinCota: n.clase !== 'lago', topo: n });
    }
    return { lista: lista.slice(0, 5), nP }; // nunca más de 5 nombres por lámina
  }

  // cada rasgo rotulado toma el nombre propio más cercano de su clase (toponimia/nombrar.js);
  // el nombre no se traduce (crudo) y en inglés lleva su glosa chiquita
  const CLASE_DE = { pico: 'cumbre', col: 'paso', crater: 'hondonada', fondo: 'hondonada' };
  const ES_LAGO = /^(LAGO|LAGUNA)/; // los rasgos especiales que son agua quieta toman el nombre del lago
  function bautiza(T, lista) {
    const N = T.toponimos || [], tomados = new Set();
    return lista.map((c) => {
      // un rasgo especial (COLADA, RIFT, FIORDO…) toma su propio nombre, del mismo término
      const esp = !CLASE_DE[c.tipo] && N.find((n) => n.clase === 'especial' && n.term === String(c.term || '').toUpperCase() && !tomados.has(n) && Math.hypot(n.u - c.u, n.v - c.v) < 0.03);
      if (esp) { tomados.add(esp); return { ...c, term: esp.nombre, crudo: true, glosa: esp.glosa, topo: esp }; }
      if (c.term === 'PASO') { const bo = N.find((n) => n.clase === 'boca' && !tomados.has(n)); if (bo) { tomados.add(bo); return { ...c, term: bo.nombre, crudo: true, glosa: bo.glosa, topo: bo }; } }
      const cl = CLASE_DE[c.tipo] || (ES_LAGO.test(c.term || '') ? 'lago' : null); if (!cl) return c;
      let b = null, dm = cl === 'lago' ? 0.09 : cl === 'paso' ? 0.12 : 0.05;
      for (const n of N) if ((n.clase === cl || (cl === 'lago' && n.clase === 'laguna')) && !tomados.has(n) && Math.hypot(n.u - c.u, n.v - c.v) < dm) { dm = Math.hypot(n.u - c.u, n.v - c.v); b = n; }
      if (!b) return c;
      tomados.add(b);
      return { ...c, term: b.nombre, crudo: true, glosa: b.glosa, topo: b };
    });
  }
  const glosaDe = (c) => (MT._lang === 'en' && c.glosa ? c.glosa.toUpperCase() : '');

  // ── B · rótulos sobre los perfiles: llamadas en un renglón, sólo lo que se ve cerca del cielo
  function rotulaCrestas(K, T, V, A, registro, techo, maxGuia = 22) {
    const { lista, nP } = rasgosRotulables(T, registro, false);
    const bh = S1 + 1.3 + S2, llamadas = [], rotulados = [];
    let puestos = 0;
    for (const c of lista) {
      if (c.tipo === 'pico' && puestos >= nP) continue;
      const pr = V.proyecta(c.u, c.v);
      if (!pr.vis) continue;
      const cielo = V.silueta(pr.x - 2, pr.x + 2);
      if (pr.y - cielo > maxGuia) continue; // la guía no debe atravesar media montaña
      const alt = c.sinCota ? '' : c.dato || fmt(T.alt(c.h)); // un cráter dice su diámetro; una colada, su largo
      const bw = Math.max(MT.letra.mide(c.term, S1, { track: 0.5, crudo: c.crudo }) + S1 * 0.3, MT.letra.mide(alt, S2), MT.letra.mide(glosaDe(c), S2 * 0.8, { crudo: true })) + 2;
      llamadas.push({ c, pr, alt, bw, x: pr.x, yb: Math.min(cielo - 4, pr.y - 8) });
      if (c.tipo === 'pico') puestos++;
    }
    if (llamadas.length) {
      llamadas.sort((a, b) => a.x - b.x);
      const yb = Math.max(techo + bh, Math.min(...llamadas.map((l) => l.yb)));
      for (let it = 0; it < 60; it++) {
        let mov = false;
        for (let k = 1; k < llamadas.length; k++) {
          const a = llamadas[k - 1], b = llamadas[k], gap = (a.bw + b.bw) / 2 + 2 - (b.x - a.x);
          if (gap > 0) { a.x -= gap / 2; b.x += gap / 2; mov = true; }
        }
        for (const l of llamadas) l.x = Math.min(V.xmax - l.bw / 2, Math.max(V.xmin + l.bw / 2, l.x));
        if (!mov) break;
      }
      for (const { c, pr, alt, x } of llamadas) {
        if (c.tipo === 'pico') K.add([[pr.x - 0.9, pr.y - 0.3], [pr.x, pr.y - 1.9], [pr.x + 0.9, pr.y - 0.3], [pr.x - 0.9, pr.y - 0.3]], 1);
        else K.add(circulo(pr.x, pr.y, 0.7), 1);
        const y0 = c.tipo === 'pico' ? pr.y - 2.6 : pr.y - 1.4, codo = yb + 3;
        if (Math.abs(x - pr.x) < 0.3) K.add([[pr.x, y0], [x, yb + 0.8]], 1);
        else K.add([[pr.x, y0], [pr.x, Math.min(y0, codo)], [x, yb + 0.8]], 1);
        K.escribe(c.term, x, yb - S2 - 1.3, S1, { slant: SL, track: 0.5, align: 'center', crudo: c.crudo, topo: c.topo });
        K.escribe(alt, x, yb, S2, { align: 'center' });
        if (glosaDe(c)) K.escribe(glosaDe(c), x, yb + S2 * 0.8 + 1, S2 * 0.8, { align: 'center', crudo: true });
        rotulados.push({ term: c.term, alt: Math.round(T.alt(c.h)) });
      }
    }
    // el cañón se rotula por su fondo, donde el primer perfil lo corta (siempre a la vista)
    if (T.arq === 'canon') {
      let my = 0, mx = 0, mh = Infinity; // el punto más hondo del filo delantero
      for (const [x, y, h] of V.frente) if (h < mh) { mh = h; mx = x; my = y; }
      const alt = fmt(T.alt(mh));
      K.add(circulo(mx, my, 0.7), 1);
      const tw = Math.max(MT.letra.mide('FONDO', S1, { track: 0.5 }), MT.letra.mide(alt, S2)) + 1;
      const frenteY = (x) => { let m = null, d = Infinity; for (const f of V.frente) { const q = Math.abs(f[0] - x); if (q < d) { d = q; m = f[1]; } } return d < 1 ? m : null; };
      const libre = (x0, x1) => {
        for (let x = x0; x <= x1; x += 0.5) { const y = frenteY(x); if (y === null || y > my - 3.5) return false; }
        return true;
      };
      const lado = libre(mx + 5, mx + 6 + tw) ? 1 : libre(mx - 6 - tw, mx - 5) ? -1 : 0;
      if (lado) {
        K.add([[mx + lado, my], [mx + lado * 5, my]], 1);
        const al = lado > 0 ? 'left' : 'right', xt = mx + lado * 6;
        K.escribe('FONDO', xt, my - 0.9, S1, { slant: SL, track: 0.5, align: al });
        K.escribe(alt, xt, my + 2.9, S2, { align: al });
      } else {
        K.add([[mx, my + 1], [mx, my + 3]], 1);
        K.escribe('FONDO', mx, my + 3.2 + S1, S1, { slant: SL, track: 0.5, align: 'center' });
        K.escribe(alt, mx, my + 4.5 + S1 + S2, S2, { align: 'center' });
      }
      rotulados.push({ term: 'FONDO', alt: Math.round(T.alt(mh)) });
    }
    return rotulados;
  }

  // ── A · planta con curvas de nivel. Las cotas rompen la curva y se leen cuesta arriba.
  function dibujaCurvas(K, T, A, cfg) {
    const toUV = MT.vistas.aUV[A.rot], toA = MT.vistas.uvA[A.rot];
    const P2 = (a, b) => [A.O[0] + a * A.U[0] + b * A.V[0], A.O[1] + a * A.U[1] + b * A.V[1]];
    const aPag = (u, v) => P2(...toA(u, v));
    const det = A.U[0] * A.V[1] - A.U[1] * A.V[0];
    const inv = (x, y) => { const dx = x - A.O[0], dy = y - A.O[1]; return [(dx * A.V[1] - dy * A.V[0]) / det, (A.U[0] * dy - A.U[1] * dx) / det]; };
    const altPag = (x, y) => { const [a, b] = inv(x, y); return T.alt(T.sample(...toUV(a, b))); };
    const { eq, cada } = cfg;

    const niveles = [];
    if (T.mar) niveles.push({ m: T.nivelMar ? 0 : T.base, costa: true });
    for (let m = Math.floor(T.base / eq) * eq + eq; m < T.base + T.relieve; m += eq) if (!(T.nivelMar && m === 0)) niveles.push({ m }); // bajo el mar: curvas batimétricas
    for (const nv of niveles) {
      nv.maestra = !!nv.costa || Math.round(nv.m / eq) % cada === 0;
      const hn = nv.costa ? T.umbralMar : (nv.m - T.base) / T.relieve;
      nv.polis = MT.vistas.isolineas(T, hn).map((pl) => pl.map(([u, v]) => aPag(u, v)));
    }

    // máscaras: cajas (giradas) donde la curva se interrumpe para dejar hablar al texto
    const mascaras = [];
    const dentro = (mk, x, y) => {
      const dx = x - mk.cx, dy = y - mk.cy;
      if (Math.abs(dx) > mk.r || Math.abs(dy) > mk.r) return false;
      return Math.abs(dx * mk.ux + dy * mk.uy) < mk.hw && Math.abs(-dx * mk.uy + dy * mk.ux) < mk.hh;
    };
    const caja = (cx, cy, ux, uy, hw, hh) => ({ cx, cy, ux, uy, hw, hh, r: Math.hypot(hw, hh) });
    const bordes = (mk) => {
      const out = [];
      for (const a of [-1, 0, 1]) for (const b of [-1, 0, 1]) out.push([mk.cx + mk.ux * a * mk.hw - mk.uy * b * mk.hh, mk.cy + mk.uy * a * mk.hw + mk.ux * b * mk.hh]);
      return out;
    };
    const solapa = (a, b) => bordes(a).some(([x, y]) => dentro(b, x, y)) || bordes(b).some(([x, y]) => dentro(a, x, y));
    const enPlanta = (mk, m) => bordes(mk).every(([x, y]) => { const [a, b] = inv(x, y), q = m / A.S; return a > q && a < 1 - q && b > q && b < 1 - q; });

    // puntos acotados
    const puntos = [];
    for (const c of cfg.rasgos) {
      const [x, y] = aPag(c.u, c.v), alt = c.dato || fmt(T.alt(c.h));
      if (c.tipo === 'agua') { // el agua no lleva punto: el nombre va centrado en ella
        const sz = c.clase === 'mar' ? 2.4 : 1.8, tw2 = MT.letra.mide(c.term, sz, { track: 0.8, crudo: true }) + 1;
        const mk = caja(x, y, 1, 0, tw2 / 2, sz * 0.9);
        if (enPlanta(mk, 1) && !mascaras.some((o) => solapa(o, mk))) { mascaras.push(mk); puntos.push({ c, x, y, alt: '', lado: 0 }); }
        continue;
      }
      const tw = Math.max(MT.letra.mide(c.term, 1.7, { track: 0.4, crudo: c.crudo }) + 0.5, MT.letra.mide(alt, 2), MT.letra.mide(glosaDe(c), 1.3, { crudo: true }));
      for (const lado of [1, -1]) {
        const x0 = lado > 0 ? x - 1.5 : x - 2.4 - tw - 0.4, x1 = lado > 0 ? x + 2.4 + tw + 0.4 : x + 1.5;
        const mk = caja((x0 + x1) / 2, y + 0.2, 1, 0, (x1 - x0) / 2, 3.4);
        if (!enPlanta(mk, 0.5) || mascaras.some((o) => solapa(o, mk))) continue;
        mascaras.push(mk); puntos.push({ c, x, y, alt, lado }); break;
      }
    }

    // cotas sobre las curvas maestras: donde la curva va derecha y ninguna otra cruza
    const SZ = 1.7, cotas = [];
    const hachuras = cfg.estilo === 'hachuras';
    let quedan = hachuras ? 0 : cfg.nCotas; // sin curvas a la vista no hay dónde escribir cotas
    // el río principal dice su largo, a un lado del cauce, en el sentido de la corriente legible
    const conNombre = (T.toponimos || []).filter((n) => n.clase === 'rio' && n.pts);
    const cauces = conNombre.length ? conNombre.map((n) => ({ pts: n.pts, txt: n.nombre, crudo: true, topo: n }))
      : T.hidro && T.hidro.principal ? [{ pts: T.hidro.principal.pts, txt: 'RÍO', km: T.hidro.principal.largoKm }] : [];
    // un río con nombre lo lleva escrito a lo largo de su cauce, siguiendo la curva, como en
    // los mapas: el cauce se suaviza, se busca el tramo menos torcido y cada trazo de la letra
    // se dobla con él (a un lado del agua, leyéndose de izquierda a derecha)
    const curvos = [];
    if (cfg.nCotas > 0) for (const cauce of cauces.filter((c) => c.crudo)) {
      const largoKm = cauce.pts.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - cauce.pts[i - 1][0], p[1] - cauce.pts[i - 1][1]) : 0), 0) * T.anchoKm;
      const txt = `${cauce.txt} · ${dec(largoKm)} KM`, sz = 1.7, tr = 0.6;
      const w = MT.letra.mide(txt, sz, { track: tr, crudo: true });
      // remuestreo cada 0.5 mm y suavizado (media móvil de ~5 mm)
      let pl = cauce.pts.map(([u, v]) => aPag(u, v));
      const rs = [pl[0]];
      for (let i = 1; i < pl.length; i++) { const a = rs[rs.length - 1], b = pl[i], d = Math.hypot(b[0] - a[0], b[1] - a[1]); if (d >= 0.5) rs.push(b); }
      if (rs.length < 20) continue;
      const k = 14, sm = rs.map((_, i) => { let x = 0, y = 0, n = 0; for (let j = Math.max(0, i - k); j <= Math.min(rs.length - 1, i + k); j++) { x += rs[j][0]; y += rs[j][1]; n++; } return [x / n, y / n]; });
      const cum = [0]; for (let i = 1; i < sm.length; i++) cum.push(cum[i - 1] + Math.hypot(sm[i][0] - sm[i - 1][0], sm[i][1] - sm[i - 1][1]));
      const tot = cum[cum.length - 1]; if (tot < w + 4) continue;
      const en = (s) => { let i = cum.findIndex((c) => c >= s); if (i < 1) i = 1; const a = sm[i - 1], b = sm[i], f = (s - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]); const L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1; return { p: [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f], t: [(b[0] - a[0]) / L, (b[1] - a[1]) / L] }; };
      let mejor = null;
      for (let s = tot * 0.12; s + w < tot * 0.92; s += 2) {
        let giro = 0, prev = en(s).t;
        for (let q = s + 2; q <= s + w; q += 2) { const t = en(q).t; giro += Math.abs(Math.atan2(prev[0] * t[1] - prev[1] * t[0], prev[0] * t[0] + prev[1] * t[1])); prev = t; }
        if (giro > 1.3) continue;
        const ini = en(s), fin = en(s + w), izqDer = fin.p[0] >= ini.p[0];
        for (const lado of [1, -1]) {
          const cajas = [];
          for (let q = s; q <= s + w; q += 4) { const { p, t } = en(q), nx = -t[1] * lado, ny = t[0] * lado; cajas.push(caja(p[0] + nx * 2, p[1] + ny * 2, t[0], t[1], 2.2, 1.3)); }
          if (!cajas.every((mk) => enPlanta(mk, 2)) || cajas.some((mk) => mascaras.some((o) => solapa(o, mk)))) continue;
          if (!mejor || giro < mejor.giro) mejor = { s, lado, giro, izqDer, cajas };
          break;
        }
        if (mejor && mejor.giro < 0.25) break;
      }
      if (!mejor) continue;
      mascaras.push(...mejor.cajas);
      const { lineas } = MT.letra.trazos(txt, 0, 0, sz, { slant: SL, track: tr, crudo: true });
      // la letra plana (x a lo largo, y hacia arriba negativa) se lleva sobre el cauce
      const desde = curvos.length;
      for (const l of lineas) curvos.push(l.map(([x, y]) => {
        const s = mejor.izqDer ? mejor.s + x : mejor.s + w - x, { p, t } = en(s);
        const dir = mejor.izqDer ? t : [-t[0], -t[1]], arriba = [dir[1], -dir[0]]; // "arriba" de la letra (y crece hacia abajo)
        const lado = [-t[1] * mejor.lado, t[0] * mejor.lado]; // el costado del río donde va el nombre
        const h = -y - sz / 2; // la altura de la letra, centrada
        return [p[0] + lado[0] * 2 + arriba[0] * h, p[1] + lado[1] * 2 + arriba[1] * h];
      }));
      K.marcaTopo(cauce.topo, curvos.slice(desde)); // el visor abre la ficha del río al tocar su nombre
    }
    if (cfg.nCotas > 0) for (const cauce of cauces.filter((c) => !c.crudo)) {
      const largoKm = cauce.km || cauce.pts.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - cauce.pts[i - 1][0], p[1] - cauce.pts[i - 1][1]) : 0), 0) * T.anchoKm;
      const pl = cauce.pts.map(([u, v]) => aPag(u, v)), txt = `${cauce.txt} · ${dec(largoKm)} KM`;
      const w = MT.letra.mide(txt, 1.7, { track: 0.5 }) + 3, cum = [0];
      for (let i = 1; i < pl.length; i++) cum.push(cum[i - 1] + Math.hypot(pl[i][0] - pl[i - 1][0], pl[i][1] - pl[i - 1][1]));
      const tot = cum[cum.length - 1];
      buscar: for (let s = tot * (cauce.crudo ? 0.12 : 0.35); s < tot * 0.95 && s + w < tot; s += 2) {
        let i0 = cum.findIndex((c) => c >= s), i1 = cum.findIndex((c) => c >= s + w);
        if (i0 < 0 || i1 < 0) break;
        const a = pl[i0], b = pl[i1], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
        if (L < w * 0.85) continue;
        const ux = dx / L, uy = dy / L;
        for (let k = i0; k <= i1; k++) if (Math.abs((pl[k][0] - a[0]) * uy - (pl[k][1] - a[1]) * ux) > (cauce.crudo ? Math.max(0.6, w * 0.035) : 0.6)) continue buscar; // un nombre largo tolera un cauce menos recto
        for (const lado of [1, -1]) {
          const ox = -uy * 2.1 * lado, oy = ux * 2.1 * lado;
          const mk = caja((a[0] + b[0]) / 2 + ox, (a[1] + b[1]) / 2 + oy, ux, uy, w / 2, 1.3);
          if (!enPlanta(mk, 2) || mascaras.some((o) => solapa(o, mk))) continue;
          let th = Math.atan2(uy, ux); if (th > Math.PI / 2) th -= Math.PI; if (th < -Math.PI / 2) th += Math.PI;
          mascaras.push(mk); cotas.push({ txt, cx: mk.cx, cy: mk.cy, th, rio: true, crudo: cauce.crudo });
          break buscar;
        }
      }
    }
    const maestras = niveles.filter((nv) => nv.maestra && !nv.costa);
    for (let i = maestras.length - 1; i > 0; i--) { const j = Math.floor(cfg.rng() * (i + 1)); [maestras[i], maestras[j]] = [maestras[j], maestras[i]]; }
    for (const nv of maestras) {
      for (const pl of nv.polis) {
        if (quedan <= 0) break;
        const txt = fmt(nv.m), w = MT.letra.mide(txt, SZ) + 1.8;
        const cum = [0];
        for (let i = 1; i < pl.length; i++) cum.push(cum[i - 1] + Math.hypot(pl[i][0] - pl[i - 1][0], pl[i][1] - pl[i - 1][1]));
        const total = cum[cum.length - 1];
        if (total < w * 4) continue;
        const enS = (s) => {
          let i = 1; while (i < cum.length - 1 && cum[i] < s) i++;
          const f = (s - cum[i - 1]) / (cum[i] - cum[i - 1] || 1);
          return { i, p: [pl[i - 1][0] + (pl[i][0] - pl[i - 1][0]) * f, pl[i - 1][1] + (pl[i][1] - pl[i - 1][1]) * f] };
        };
        const max = 1 + Math.floor(total / 120), aqui = [];
        for (let s = w / 2 + 2 + cfg.rng() * Math.min(30, total / 3); s < total - w / 2 - 2; s += 2.5) {
          if (aqui.length >= max || quedan <= 0) break;
          if (aqui.some((q) => Math.abs(q - s) < 75)) continue;
          const a = enS(s - w / 2), b = enS(s + w / 2);
          const dx = b.p[0] - a.p[0], dy = b.p[1] - a.p[1], L = Math.hypot(dx, dy);
          if (L < w * 0.85) continue;
          const ux = dx / L, uy = dy / L;
          let recta = true;
          for (let k = a.i; k < b.i && recta; k++) if (Math.abs((pl[k][0] - a.p[0]) * uy - (pl[k][1] - a.p[1]) * ux) > 0.45) recta = false;
          if (!recta) continue;
          const mk = caja((a.p[0] + b.p[0]) / 2, (a.p[1] + b.p[1]) / 2, ux, uy, w / 2, SZ / 2 + 0.55);
          if (!enPlanta(mk, 2) || mascaras.some((o) => solapa(o, mk))) continue;
          let libre = true;
          for (let ia = -1; ia <= 1 && libre; ia += 0.5) for (let ib = -1; ib <= 1; ib++) {
            const px = mk.cx + ux * ia * mk.hw - uy * ib * mk.hh, py = mk.cy + uy * ia * mk.hw + ux * ib * mk.hh;
            if (Math.abs(altPag(px, py) - nv.m) >= eq * 0.97) { libre = false; break; }
          }
          if (!libre) continue;
          let th = Math.atan2(uy, ux);
          const upx = Math.sin(th), upy = -Math.cos(th);
          if (altPag(mk.cx + upx, mk.cy + upy) < altPag(mk.cx - upx, mk.cy - upy)) th += Math.PI; // el número mira cuesta arriba
          mascaras.push(mk); cotas.push({ txt, cx: mk.cx, cy: mk.cy, th }); aqui.push(s); quedan--;
        }
      }
    }

    // recortar, ordenar (de abajo hacia arriba o al revés) y trazar
    const recorta = (pts) => {
      const out = []; let cur = [];
      for (const p of pts) {
        if (!mascaras.some((mk) => dentro(mk, p[0], p[1]))) cur.push(p);
        else { if (cur.length > 1) out.push(cur); cur = []; }
      }
      if (cur.length > 1) out.push(cur);
      return out;
    };
    const desfasa = (p, d) => p.map((q, i) => {
      const a = p[Math.max(0, i - 1)], b = p[Math.min(p.length - 1, i + 1)];
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      return [q[0] - (b[1] - a[1]) / L * d, q[1] + (b[0] - a[0]) / L * d];
    });
    let pos = [A.O[0], A.O[1]];
    // Curvas iluminadas (Tanaka, 1950): la luz llega de arriba a la izquierda de la hoja. Cada
    // tramo mira hacia donde baja su ladera; en papel claro, lo que da la espalda a la luz se
    // engruesa con una o dos pasadas más; en papel oscuro, al revés: la tinta es la luz.
    const LUZ = [-Math.SQRT1_2, -Math.SQRT1_2];
    const tono = (x, y) => {
      const e = 0.3, gx = altPag(x + e, y) - altPag(x - e, y), gy = altPag(x, y + e) - altPag(x, y - e), L = Math.hypot(gx, gy);
      if (L < 1e-9) return 0;
      const c = (-gx / L) * LUZ[0] + (-gy / L) * LUZ[1]; // hacia la luz: la ladera baja hacia donde viene
      return cfg.oscuro ? Math.max(0, c) : Math.max(0, -c);
    };
    const iluminaTramo = (p) => {
      const nivel = [];
      for (let i = 1; i < p.length; i++) { const t = tono((p[i - 1][0] + p[i][0]) / 2, (p[i - 1][1] + p[i][1]) / 2); nivel.push(t > 0.85 ? 3 : t > 0.55 ? 2 : t > 0.22 ? 1 : 0); }
      for (const umbral of [1, 2, 3]) {
        let i = 0;
        while (i < nivel.length) {
          if (nivel[i] < umbral) { i++; continue; }
          let j = i; while (j < nivel.length && nivel[j] >= umbral) j++;
          const run = p.slice(i, j + 1);
          if (run.length > 1) {
            // la pasada extra va hacia el lado de abajo de la ladera
            const m = run[Math.floor(run.length / 2)], q = desfasa(run, 0.3)[Math.floor(run.length / 2)];
            const lado = altPag(q[0], q[1]) < altPag(m[0], m[1]) ? 1 : -1;
            K.add(desfasa(run, 0.16 * umbral * lado).reverse(), 0);
          }
          i = j;
        }
      }
    };
    for (const nv of cfg.sube ? niveles : [...niveles].reverse()) {
      if (hachuras && !nv.costa && !(T.nivelMar && nv.m < 0)) continue; // en hachuras la curva no se dibuja (bajo el mar sí: batimétricas)
      const piezas = nv.polis.flatMap(recorta).map((p) => MT.simplifica(p, 0.03)).filter((p) => p.length > 1);
      while (piezas.length) {
        let mejor = 0, dm = Infinity, rev = false;
        piezas.forEach((p, k) => {
          const d0 = Math.hypot(p[0][0] - pos[0], p[0][1] - pos[1]), d1 = Math.hypot(p[p.length - 1][0] - pos[0], p[p.length - 1][1] - pos[1]);
          if (d0 < dm) { dm = d0; mejor = k; rev = false; }
          if (d1 < dm) { dm = d1; mejor = k; rev = true; }
        });
        let p = piezas.splice(mejor, 1)[0];
        if (rev) p = p.slice().reverse();
        K.add(p, 0);
        if (nv.maestra) { const q = desfasa(p, 0.2).reverse(); K.add(q, 0); pos = q[q.length - 1]; } // segunda pasada: la maestra pesa
        if (cfg.tanaka && !nv.costa) iluminaTramo(p);
        else pos = p[p.length - 1];
      }
    }

    // E · hachuras: trazos cortos que bajan por la máxima pendiente, de una curva a la siguiente.
    // Más juntos donde es más empinado; en lo plano, nada (el blanco es llano).
    if (hachuras) {
      const mPorMm = T.anchoKm * 1000 / A.S, e = 0.25;
      const grad = (x, y) => [(altPag(x + e, y) - altPag(x - e, y)) / (2 * e), (altPag(x, y + e) - altPag(x, y - e)) / (2 * e)];
      const dentroPl = (x, y) => { const [a, b] = inv(x, y); return a > 0.002 && a < 0.998 && b > 0.002 && b < 0.998; };
      const trazosH = [];
      const paso = eq < 50 ? 2 : 1; // con equidistancias chicas, bandas del doble
      for (const nv of [...niveles].reverse()) {
        if (nv.costa || Math.round(nv.m / eq) % paso || (T.nivelMar && nv.m <= 0)) continue; // bajo el agua no hay hachuras
        const piso = nv.m - eq * paso * 0.9; // la banda deja un respiro antes de la curva de abajo
        for (const pl of nv.polis) {
          let s0 = 0, sig = cfg.rng() * 1.2;
          for (let i = 1; i < pl.length; i++) {
            const L = Math.hypot(pl[i][0] - pl[i - 1][0], pl[i][1] - pl[i - 1][1]);
            while (sig <= s0 + L) {
              const f = (sig - s0) / (L || 1), x0 = pl[i - 1][0] + (pl[i][0] - pl[i - 1][0]) * f, y0 = pl[i - 1][1] + (pl[i][1] - pl[i - 1][1]) * f;
              const [gx, gy] = grad(x0, y0), pend = Math.hypot(gx, gy) / mPorMm;
              sig += Math.min(3.5, Math.max(0.5, 0.75 * Math.sqrt(0.35 / Math.max(pend, 1e-3))));
              if (pend < 0.05) continue;
              let x = x0, y = y0; const pts = [[x, y]];
              for (let k = 0; k < 13; k++) { // trazo corto: en lo llano no se vuelve cauce
                const [qx, qy] = grad(x, y), q = Math.hypot(qx, qy);
                if (q / mPorMm < 0.02) break;
                x -= qx / q * 0.3; y -= qy / q * 0.3;
                if (!dentroPl(x, y) || altPag(x, y) <= piso) break;
                pts.push([x, y]);
              }
              if (pts.length > 2) trazosH.push(...recorta(pts));
            }
            s0 += L;
          }
        }
      }
      for (const t of trazosH) if (t.length > 1) { K.add(MT.simplifica(t, 0.03), 0); pos = t[t.length - 1]; }
    }
    // ríos y orillas de lago, en la tinta del agua
    if (T.hidro) {
      for (const rv of T.hidro.rios) for (const t of recorta(rv.pts.map(([u, v]) => aPag(u, v)))) trazaRio(K, t, rv.clase);
      if (T.hidro.lagos.length) {
        const N = T.G, campo = new Float32Array(N * N);
        for (let i = 0; i < N * N; i++) campo[i] = T.hidro.agua[i] && T.h[i] > 1e-4 ? 1 : 0;
        for (const l of MT.vistas.isolineas({ G: N, h: campo }, 0.5)) {
          for (const t of recorta(l.map(([u, v]) => aPag(u, v)))) { const q = MT.simplifica(t, 0.03); K.add(q, 1); K.add(desfasa(q, 0.18).reverse(), 1); }
        }
      }
    }
    // líneas de agua alrededor de las costas (y dentro de los lagos), en la otra tinta
    if (!T.nivelMar && (T.mar || (T.hidro && T.hidro.lagos.length))) { // con fondo, las batimétricas ya dicen el agua
      const piezas = MT.vistas.lineasAgua(T, A.S).map((l) => l.map(([u, v]) => aPag(u, v)))
        .flatMap(recorta).map((p) => MT.simplifica(p, 0.03)).filter((p) => p.length > 1);
      while (piezas.length) {
        let mejor = 0, dm = Infinity, rev = false;
        piezas.forEach((p, k) => {
          const d0 = Math.hypot(p[0][0] - pos[0], p[0][1] - pos[1]), d1 = Math.hypot(p[p.length - 1][0] - pos[0], p[p.length - 1][1] - pos[1]);
          if (d0 < dm) { dm = d0; mejor = k; rev = false; }
          if (d1 < dm) { dm = d1; mejor = k; rev = true; }
        });
        let p = piezas.splice(mejor, 1)[0];
        if (rev) p = p.slice().reverse();
        K.add(p, 1); pos = p[p.length - 1];
      }
    }
    // marco y retícula kilométrica sobre los dos filos de la esquina (0,0)
    if (cfg.marco) {
      K.add([P2(0, 0), P2(1, 0), P2(1, 1), P2(0, 1), P2(0, 0)], 1);
      if (cfg.reticula) {
        const st = nice(T.anchoKm / 5), nU = [A.U[0] / A.S, A.U[1] / A.S], nV = [A.V[0] / A.S, A.V[1] / A.S];
        for (let km = 0; km <= T.anchoKm + 1e-6; km += st) {
          const t = km / T.anchoKm, txt = dec(km), w = MT.letra.mide(txt, 1.5);
          [[P2(t, 0), [-nV[0], -nV[1]]], [P2(0, t), [-nU[0], -nU[1]]]].forEach(([p, out], e) => {
            K.add([p, [p[0] + out[0] * 1.5, p[1] + out[1] * 1.5]], 1);
            const d = 2.4 + Math.abs(out[0]) * w / 2 + Math.abs(out[1]) * 1.6;
            if (km > 0 || e === 0) K.escribe(txt, p[0] + out[0] * d, p[1] + out[1] * d + 0.75, 1.5, { align: 'center' });
          });
        }
        const pk = P2(1, 0), d = 2.4 + 1.6;
        K.escribe('KM', pk[0] - nV[0] * d + nU[0] * 5, pk[1] - nV[1] * d + nU[1] * 5 + 0.75, 1.5, { align: 'center' });
      }
    }
    // puntos acotados y cotas: la letra va al final, como en el taller
    for (const { c, x, y, alt, lado } of puntos) {
      if (c.tipo === 'agua') {
        const sz = c.clase === 'mar' ? 2.4 : 1.8;
        K.escribe(c.term, x, y + sz / 2, sz, { slant: SL, track: 0.8, align: 'center', crudo: true, topo: c.topo });
        if (glosaDe(c)) K.escribe(glosaDe(c), x, y + sz / 2 + 2.2, 1.3, { align: 'center', crudo: true });
        continue;
      }
      if (c.tipo === 'pico') K.add([[x - 1, y + 0.6], [x, y - 1.2], [x + 1, y + 0.6], [x - 1, y + 0.6]], 1);
      else K.add(circulo(x, y, 0.7), 1);
      const al = lado > 0 ? 'left' : 'right', xt = x + lado * 2.4;
      K.escribe(c.term, xt, y - 0.7, 1.7, { slant: SL, track: 0.4, align: al, crudo: c.crudo, topo: c.topo });
      K.escribe(alt, xt, y + 2.9, 2, { align: al });
      if (glosaDe(c)) K.escribe(glosaDe(c), xt, y + 5, 1.3, { align: al, crudo: true });
    }
    for (const q of cotas) K.escribeRot(q.txt, q.cx, q.cy, SZ, q.th, q.rio ? { slant: SL, track: 0.5, crudo: q.crudo } : {});
    for (const l of curvos) K.add(l, 1); // los nombres de los ríos, doblados con el cauce

    // de dónde viene la luz, en rumbo del terreno (la luz es de la hoja; el terreno puede estar girado)
    const dl = 1 / det, la = (LUZ[0] * A.V[1] - LUZ[1] * A.V[0]) * dl, lb = (A.U[0] * LUZ[1] - A.U[1] * LUZ[0]) * dl;
    if (cfg.registra) cfg.registra({ inv, rot: A.rot }); // para teñir después lo que cae en esta planta
    return { aPag, puntos, niveles, cotas: cotas.length, luz: cfg.tanaka ? rumbo(A.rot, la, lb) : null };
  }

  // ── la lámina
  MT.lamina = function (seed, o = {}) {
    seed = String(seed);
    MT._lang = o.lang === 'en' ? 'en' : 'es'; // el idioma del lector: lo aplica la letra al medir y escribir
    const T = MT.terreno(seed, { arq: o.arq, edad: o.edad, forma: o.forma, etapas: o.forma != null, realismo: o.realismo, fondo: o.fondo }); // forma: la montaña a medio hacer
    // los topónimos: la lámina se llama como su cima principal (en la formación no hay letra)
    const variante = o.variante != null ? +o.variante : (MT.VARIANTES && MT.VARIANTES[seed]) || 0; // la edición reparte sus títulos
    T.toponimos = o.forma == null && MT.nombra ? MT.nombra(T, seed, variante) : [];
    const principal = T.toponimos[0];
    const kicker = 'TRASPUESTA · ' + (MT.traduce ? MT.traduce(`LÁMINA ${seed} · ${T.nombre}`, MT._lang) : `LÁMINA ${seed} · ${T.nombre}`)
      + (MT._lang === 'en' && principal && principal.glosa ? ' · ' + principal.glosa.toUpperCase() : '');
    const nombreLamina = principal ? principal.nombre : T.nombre;
    // título: el nombre propio grande y, encima, la serie, el número y el tipo de terreno
    const titula = (K, x, y, size, op = {}) => {
      if (!principal) return K.escribe(T.nombre, x, y, size, op);
      K.escribe(nombreLamina, x, y, size, { ...op, crudo: true, topo: principal });
      K.escribe(kicker, x, y - size - 1.6, Math.max(1.2, size * 0.4), { align: op.align, track: 0.35, crudo: true });
    };
    const anchoTitulo = (size, track) => principal ? Math.max(MT.letra.mide(nombreLamina, size, { track, crudo: true }), MT.letra.mide(kicker, Math.max(1.2, size * 0.4), { track: 0.35, crudo: true }))
      : MT.letra.mide(T.nombre, size, { track });
    const r = MT.rng(seed + ':lamina');
    const tiro = r();
    const registro = MT.REGISTROS.includes(o.registro) ? o.registro
      : tiro < 0.3 ? 'carto' : tiro < 0.7 ? 'lamina' : 'obra';
    const rh = MT.rng(seed + ':hoja'), th = rh();
    let hoja = MT.HOJAS.includes(o.hoja) ? o.hoja
      : th < 0.3 ? 'crestas' : th < 0.5 ? 'curvas' : th < 0.75 ? 'lado' : 'torre';
    if (!MT.HOJAS.includes(o.hoja)) { const rn = MT.rng(seed + ':hoja3')(); if (rn < 0.32) hoja = rn < 0.18 ? 'bloque' : 'proyeccion'; else if (rn < 0.42) hoja = 'secuencia'; else if (rn >= 0.5 && rn < 0.58) hoja = 'corte'; }
    if (hoja === 'secuencia' && T.arq === 'dunas') hoja = 'crestas'; // la arena no tiene esa historia: sin erosión ni agua, los cuatro tiempos saldrían iguales
    const vertical = hoja === 'torre' || hoja === 'proyeccion' || hoja === 'corte';
    const page = vertical ? { w: 210, h: 297 } : { w: 297, h: 210 };

    // paleta: papel + 2 plumas, derivada de la semilla en OKLCh
    const rc = MT.rng(seed + ':color');
    const oscuro = rc() < (o.oscuro != null && o.oscuro !== '' ? (+o.oscuro ? 1 : 0) : { carto: 0.3, lamina: 0.55, obra: 0.8 }[registro]); // ~55 % oscuras; más en obra, menos en el mapa
    const hT = rc.range(0, 360), hL = hT + rc.range(110, 250);
    const papel = oscuro ? MT.oklch(rc.range(0.1, 0.16), rc.range(0.015, 0.05), hT + 180 + rc.range(-40, 40)) // negro teñido del contrario
      : MT.oklch(rc.range(0.94, 0.975), rc.range(0.012, 0.04), rc.range(60, 110));
    // en oscuro, estilo JODI: casi negro y dos neones en tonos que chocan, al tope de croma
    const plumas = oscuro
      ? [MT.neon(hT), MT.neon(hL)]
      : [MT.oklch(rc.range(0.24, 0.42), rc.range(0.03, 0.12), hT), MT.oklch(rc.range(0.3, 0.48), rc.range(0.08, 0.16), hL)];

    // perfiles: misma secuencia de tiradas en todas las hojas
    const C = {
      crestas: {
        carto: { L: 40, W: 204, Y0: 148, top: 40, n: [48, 84], p: [0.86, 1], D: [62, 84], H: [50, 72] },
        lamina: { L: 30, W: 237, Y0: 158, top: 32, n: [64, 116], p: [0.72, 1], D: [64, 96], H: [60, 92] },
        obra: { L: 22, W: 253, Y0: 182, top: 24, n: [90, 170], p: [0.55, 0.92], D: [70, 112], H: [72, 120] },
      }[registro],
      curvas: { L: 0, W: 1, Y0: 0, top: 0, n: [2, 2], p: [1, 1], D: [1, 1], H: [1, 1] },
      lado: { L: 16, W: 140, Y0: 138, top: 52, n: registro === 'obra' ? [70, 120] : [48, 86], p: [0.82, 1], D: [38, 56], H: [36, 58] },
      torre: { L: 40, W: 130, Y0: 104, top: 24, n: registro === 'obra' ? [60, 100] : [44, 80], p: [1, 1], D: [34, 48], H: [36, 56] },
    }[hoja] || { L: 0, W: 1, Y0: 0, top: 0, n: [2, 2], p: [1, 1], D: [1, 1], H: [1, 1] };
    const rmalla = MT.rng(seed + ':malla'), tiroMalla = rmalla();
    const P = {
      L: C.L, W: C.W, Y0: C.Y0, top: C.top, step: 0.3,
      n: r.int(...C.n), p: r.range(...C.p), D: r.range(...C.D), H: r.range(...C.H),
      rot: o.rot != null && o.rot !== '' && [0, 1, 2, 3].includes(+o.rot) ? +o.rot : r.int(0, 3),
      hvFijo: o.hvFijo || null,
    };
    if (T.arq === 'dunas' || T.arq === 'poligonos') P.n = Math.max(P.n, 240); // ~8 perfiles por duna: si no, se muestrea entre crestas y salen púas

    // curvas: equidistancia "redonda" según cuántas curvas pide el registro
    const objetivo = { carto: 24, lamina: 30, obra: 44 }[registro] * rh.range(0.8, 1.25);
    const EQS = [5, 10, 20, 25, 50, 100, 200, 250, 500];
    const eq = EQS.reduce((a, b) => Math.abs(Math.log(b / (T.relieve / objetivo))) < Math.abs(Math.log(a / (T.relieve / objetivo))) ? b : a);
    const cada = eq === 25 || eq === 250 ? 4 : 5;
    const sube = rh() < 0.5;
    const nCotas = { carto: 14, lamina: 9, obra: 4 }[registro];

    const K = lienzo();
    const exagDe = (V, A) => '×' + dec(V.exag);
    const desde = 'VISTA DESDE EL ' + DIR[P.rot];
    const lAlt = T.arq === 'canon'
      ? `BORDE ${fmt(T.base + T.relieve)} M · PUNTO MÁS BAJO ${fmt(T.base)} M · DESNIVEL ${fmt(T.relieve)} M`
      : `ALTITUD ${fmt(T.base)}–${fmt(T.base + T.relieve)} M · ${dec(T.anchoKm)} KM DE LADO`;
    const curvasCfg = (extra) => ({
      eq, cada, sube, nCotas, rng: rh, marco: registro !== 'obra', reticula: registro === 'carto', oscuro,
      tanaka: o.tanaka != null && o.tanaka !== '' ? !!+o.tanaka : MT.rng(seed + ':tanaka')() < 0.5,
      rasgos: rasgosRotulables(T, registro, true).lista, registra: (inv) => planos.push(inv), ...extra,
    });
    // Tintas hipsométricas: rasgo raro (~6.5 % de las semillas), sólo donde hay planta.
    // Cada franja de altura es una pluma; se trazan de la más baja a la más alta.
    const planos = [];
    const conPlanta = ['curvas', 'lado', 'torre', 'corte', 'proyeccion'].includes(hoja);
    const rhip = MT.rng(seed + ':hipso');
    const hipso = conPlanta && (o.hipso != null && o.hipso !== '' ? !!+o.hipso : rhip() < 0.11);
    let franjas = null;
    if (hipso) {
      const nf = rhip.int(4, 6), h0 = rhip.range(0, 360), hc = 70 + rhip.range(-25, 25), giro = rhip.range(180, 230);
      const bordes = [];
      for (let k = 1; k < nf; k++) bordes.push(Math.round((T.base + T.relieve * k / nf) / eq) * eq + eq / 2);
      const tintas = Array.from({ length: nf }, (_, k) => {
        const t = k / (nf - 1);
        return oscuro ? MT.neon(h0 + t * 260) : MT.oklch(0.5 - 0.12 * t, 0.12, hc + t * giro);
      });
      franjas = { nf, bordes, tintas, de: (alt) => { let k = 0; while (k < bordes.length && alt > bordes[k]) k++; return k; } };
    }
    // con fondo: lo que está bajo el nivel del mar va en la tinta del agua, en todas las vistas
    // el mar se lee como mar: su tinta cae siempre en la gama del agua (azul, cian, turquesa),
    // sembrada; si la tinta de la tierra también cae ahí, la tierra se va a tonos cálidos
    if (T.mar) {
      // Conservar los neones sembrados. En papel claro, si una tinta es fría y la otra
      // cálida, usar la fría para el agua; intercambiar también el rojo como antes.
      const rojo = (h) => { h = ((h % 360) + 360) % 360; return h >= 330 || h <= 50; };
      const frio = (h) => { h = ((h % 360) + 360) % 360; return h >= 150 && h <= 285; };
      const cambia = rojo(hL) || (!oscuro && frio(hT) && !frio(hL));
      const [tintaMar, tintaTierra] = cambia ? [plumas[0], plumas[1]] : [plumas[1], plumas[0]];
      franjas = { nf: 2, bordes: [0], tintas: [tintaMar, tintaTierra], de: (alt) => (alt > 0 ? 1 : 0), mar: true };
    }
    let rotulados = [], V = null, Cv = null, modoBloque = null, desdeBloque = null, estiloPlanta = null, corteGeo = null, seccion = null;

    if (hoja === 'crestas') {
      const conMalla = o.malla != null ? !!+o.malla : tiroMalla < { carto: 0.15, lamina: 0.25, obra: 0.4 }[registro];
      if (conMalla) P.nC = Math.round(P.n * rmalla.range(0.55, 1.05));
      V = MT.vistas.crestas(T, P);
      for (const s of V.strokes) K.add(s, 0);
      for (const s of V.columnas) K.add(s, 0); // la otra familia: la tela se teje
      rioEnVista(K, T, V);
      rotulados = rotulaCrestas(K, T, V, P, registro, 13);
      if (registro !== 'obra') escalaGrafica(K, P.L, P.Y0 + 8, P.W / T.anchoKm, P.W * 0.36, registro === 'carto' ? 'ESCALA EN EL PRIMER PERFIL' : null);
      if (registro === 'carto') {
        // altitudes al costado del primer perfil
        const x = P.L + P.W + 4, B = T.base, Rl = T.relieve, paso = nice(Rl / 4);
        const yA = (m) => P.Y0 - (m - B) / Rl * V.hv;
        K.add([[x, P.Y0], [x, yA(B + Rl)]], 1);
        for (let m = Math.ceil(B / paso) * paso; m <= B + Rl; m += paso) {
          K.add([[x, yA(m)], [x + 1.5, yA(m)]], 1);
          K.escribe(fmt(m), x + 2.5, yA(m) + 0.8, 1.6);
        }
        K.escribe('M', x - 0.7, yA(B + Rl) - 2, 1.6);
        // distancias al frente, en el arranque izquierdo de cada perfil
        const pd = nice(T.anchoKm / 4);
        let yPrev = Infinity;
        for (let km = 0; km <= T.anchoKm + 1e-6; km += pd) {
          const rr = Math.round((km / T.anchoKm) * (P.n - 1)), [lx, ly] = V.linea(rr, 0);
          if (yPrev - ly < 3) continue; yPrev = ly;
          K.add([[lx - 3, ly], [lx - 1, ly]], 1);
          K.escribe(dec(km) + ' KM', lx - 4, ly + 0.8, 1.5, { align: 'right' });
        }
      }
      const lCortes = P.nC ? `MALLA DE ${P.n} × ${P.nC} LÍNEAS · CELDA DE ${fmt(V.espaciado)} × ${fmt(T.anchoKm * 1000 / (P.nC - 1))} M`
        : `PERFILES SUCESIVOS · ${P.n} CORTES CADA ${fmt(V.espaciado)} M`;
      const lVista = `${desde} · EXAGERACIÓN VERTICAL ${exagDe(V)}`;
      if (registro === 'carto') {
        const m = 8, lineas = [lCortes, lVista, lAlt];
        const anchoT = Math.max(anchoTitulo(3.4, 1.4), ...lineas.map((s) => MT.letra.mide(s, 1.8)));
        const bx1 = page.w - m - 6, bx0 = bx1 - anchoT - 8, by1 = page.h - m - 5, by0 = by1 - 35;
        let y = by0 + 11.5;
        titula(K, bx0 + 4, y, 3.4, { track: 1.4 });
        K.add([[bx0 + 4, y + 2.4], [bx1 - 4, y + 2.4]], 1);
        y += 7;
        for (const s of lineas) { K.escribe(s, bx0 + 4, y, 1.8); y += 4.6; }
        K.escribe(`SEMILLA ${seed}`, bx0 + 4, y + 1, 1.5, { slant: SL, track: 0.4 });
        K.marco(bx0, by0, bx1, by1);
        const [fx, fy] = FLECHA_N[P.rot];
        K.flecha(bx0 - 12, (by0 + by1) / 2, fx, fy, 14, 'N');
        K.marco(m, m, page.w - m, page.h - m);
      } else if (registro === 'lamina') {
        const xr = P.L + P.W; let y = P.Y0 + 13;
        titula(K, xr, y, 3, { track: 1.2, align: 'right' }); y += 5.5;
        K.escribe(lCortes, xr, y, 1.7, { align: 'right' }); y += 4;
        K.escribe(lVista, xr, y, 1.7, { align: 'right' }); y += 4;
        K.escribe(`SEMILLA ${seed}`, xr, y + 0.6, 1.4, { slant: SL, track: 0.4, align: 'right' });
      } else {
        K.escribe(`${P.nC ? `MALLA ${P.n} × ${P.nC}` : `${P.n} PERFILES`} · ${exagDe(V)} · S ${seed}`, P.L + P.W, page.h - 12, 1.5, { slant: SL, track: 0.5, align: 'right' });
      }
    } else if (hoja === 'curvas') {
      const S = registro === 'obra' ? 186 : 164;
      const A = plano(registro === 'obra' ? (page.w - S) / 2 : 26, (page.h - S) / 2 - (registro === 'obra' ? 3 : 0), S, registro === 'carto' ? 0 : P.rot);
      const estilo = ['curvas', 'hachuras'].includes(o.planta) ? o.planta : MT.rng(seed + ':hachuras')() < 0.35 ? 'hachuras' : 'curvas';
      estiloPlanta = estilo;
      Cv = dibujaCurvas(K, T, A, curvasCfg({ estilo, ...(estilo === 'hachuras' ? { tanaka: false } : {}) }));
      if (registro === 'obra') {
        K.escribe(estilo === 'hachuras' ? `HACHURAS EN BANDAS DE ${fmt(eq * (eq < 50 ? 2 : 1))} M · S ${seed}` : `CURVAS CADA ${fmt(eq)} M · S ${seed}`, A.x0 + S, A.y0 + S + 6, 1.5, { slant: SL, track: 0.5, align: 'right' });
      } else {
        const x = 204; let y = 32;
        titula(K, x, y, 3.2, { track: 1.2 });
        K.add([[x, y + 2.4], [x + 76, y + 2.4]], 1); y += 9;
        K.escribe(estilo === 'hachuras' ? 'RELIEVE EN HACHURAS' : 'CURVAS DE NIVEL', x, y, 1.9); y += 4.6;
        K.escribe(estilo === 'hachuras' ? `BANDAS DE ${fmt(eq * (eq < 50 ? 2 : 1))} M` : `EQUIDISTANCIA ${fmt(eq)} M`, x, y, 1.7); y += 4.2;
        K.escribe(T.arq === 'canon' ? `DESNIVEL ${fmt(T.relieve)} M` : `ALTITUD ${fmt(T.base)}–${fmt(T.base + T.relieve)} M`, x, y, 1.7); y += 4.2;
        K.escribe(`${dec(T.anchoKm)} KM DE LADO`, x, y, 1.7); y += 10;
        // leyenda: cada signo dice lo que mide
        if (estilo === 'hachuras') {
          for (let k = 0; k <= 10; k++) { const sp = 0.4 + k * 0.09, xx = x + k * k * 0.1; K.add([[xx, y - 2.6], [xx, y - 2.6 + 2.6 * (0.3 + k / 14)]], 0); }
          K.escribe('TRAZO EN LA MÁXIMA PENDIENTE', x + 13, y - 0.6, 1.6); y += 3.8;
          K.escribe('MÁS JUNTO DONDE ES MÁS EMPINADO', x + 13, y - 0.6, 1.4, { slant: SL, track: 0.3 }); y += 5;
        } else {
          K.add([[x, y - 1], [x + 10, y - 1]], 0); K.add([[x + 10, y - 0.8], [x, y - 0.8]], 0);
          K.escribe(`CURVA MAESTRA · CADA ${fmt(eq * cada)} M`, x + 13, y, 1.6); y += 5;
          K.add([[x, y - 1], [x + 10, y - 1]], 0);
          K.escribe(`CURVA ORDINARIA · CADA ${fmt(eq)} M`, x + 13, y, 1.6); y += 5;
        }
        if (T.mar) { K.add([[x, y - 1], [x + 10, y - 1]], 0); K.add([[x + 10, y - 0.8], [x, y - 0.8]], 0); K.escribe('LÍNEA DE COSTA', x + 13, y, 1.6); y += 5; for (const d of [0, 0.7, 1.6]) K.add([[x, y - 2 + d], [x + 10, y - 2 + d]], 1); K.escribe('LÍNEAS DE AGUA', x + 13, y, 1.6); y += 5; }
        if (Cv.luz) {
          for (const [k, d] of [[0, 0], [1, 0.16], [2, 0.32]]) K.add(circulo(x + 5, y - 1.3, 1.9 - d * 0.0), 0);
          const arco = (r0) => Array.from({ length: 9 }, (_, i) => { const a = i / 8 * Math.PI - Math.PI / 4 + 0; return [x + 5 + Math.cos(a) * r0, y - 1.3 + Math.sin(a) * r0]; });
          K.add(arco(2.06), 0); K.add(arco(2.22), 0);
          K.escribe(`CURVAS ILUMINADAS · LUZ DEL ${Cv.luz}`, x + 13, y, 1.6); y += 5;
        }
        if (T.hidro && T.hidro.rios.length) {
          K.add([[x, y - 1.2], [x + 3, y - 1.6], [x + 6, y - 0.9], [x + 10, y - 1.3]], 1); K.add([[x + 10, y - 1.1], [x + 6, y - 0.7], [x + 3, y - 1.4], [x, y - 1]], 1);
          K.escribe('RÍO · MÁS PASADAS AGUAS ABAJO', x + 13, y, 1.6); y += 5;
        }
        if (T.hidro && T.hidro.lagos.length) {
          K.add(circulo(x + 5, y - 1.1, 1.6), 1); K.add(circulo(x + 5, y - 1.1, 0.8), 1);
          K.escribe('LAGO · COTA DE SU SUPERFICIE', x + 13, y, 1.6); y += 5;
        }
        if (Cv.puntos.some((p) => p.c.tipo === 'pico')) { K.add([[x + 4, y - 0.4], [x + 5, y - 2.2], [x + 6, y - 0.4], [x + 4, y - 0.4]], 1); K.escribe('PUNTO ACOTADO', x + 13, y, 1.6); y += 5; }
        if (franjas && franjas.mar) {
          y += 1.5; for (const d of [0, 0.35, 0.7]) K.add([[x, y - 1.6 + d], [x + 10, y - 1.6 + d]], 100);
          K.escribe(T.base < 0 ? `BAJO EL MAR · HASTA ${fmt(T.base)} M` : 'MAR · NIVEL 0 M', x + 13, y, 1.5); y += 5;
        } else if (franjas) { // cada franja dice su rango, de la más alta a la más baja
          y += 1.5; K.escribe(`TINTAS HIPSOMÉTRICAS · ${franjas.nf} FRANJAS`, x, y, 1.6); y += 4.6;
          const lim = [T.base, ...franjas.bordes.map((b) => b - eq / 2), T.base + T.relieve];
          for (let k = franjas.nf - 1; k >= 0; k--) {
            for (const d of [0, 0.35, 0.7]) K.add([[x, y - 1.6 + d], [x + 10, y - 1.6 + d]], 100 + k);
            K.escribe(`${fmt(lim[k])}–${fmt(lim[k + 1])} M`, x + 13, y, 1.5); y += 3.8;
          }
          y += 1;
        }
        y += 8;
        escalaGrafica(K, x, y, S / T.anchoKm, 70, null); y += 13;
        K.escribe('ESCALA ' + escalaNum(T.anchoKm * 1e6 / S), x, y, 1.8); y += 4.2;
        K.escribe('EN HOJA DE 297 × 210 MM', x, y, 1.4, { slant: SL, track: 0.3 });
        const [fx, fy] = FLECHA_N[A.rot];
        K.flecha(x + 8, page.h - 34, fx, fy, 14, 'N');
        K.escribe(`SEMILLA ${seed}`, x, page.h - 14, 1.5, { slant: SL, track: 0.4 });
        if (registro === 'carto') K.marco(8, 8, page.w - 8, page.h - 8);
      }
    } else if (hoja === 'lado') {
      V = MT.vistas.crestas(T, P);
      for (const s of V.strokes) K.add(s, 0);
      rioEnVista(K, T, V);
      rotulados = rotulaCrestas(K, T, V, P, registro, 30);
      const A = plano(170, 30, 104, 0);
      Cv = dibujaCurvas(K, T, A, curvasCfg({ nCotas: Math.round(nCotas * 0.7) }));
      // desde dónde mira la vista B, dibujado sobre la planta A
      const [vx, vy] = AL_OBSERVADOR[P.rot], cx = A.x0 + A.S / 2, cy = A.y0 + A.S / 2, d = A.S / 2 + (registro === 'carto' && (vx < 0 || vy > 0) ? 13 : 8);
      K.flecha(cx + vx * d, cy + vy * d, -vx, -vy, 8, null);
      K.escribe('B', cx + vx * (d + 6), cy + vy * (d + 6) + 1.2, 2.4, { align: 'center' });
      K.flecha(A.x0 + A.S - 4, 184, 0, -1, 12, 'N');
      if (registro === 'obra') {
        K.escribe(`B ${P.n} PERFILES ${exagDe(V)} · A CURVAS CADA ${fmt(eq)} M · S ${seed}`, A.x0 + A.S, page.h - 14, 1.5, { slant: SL, track: 0.5, align: 'right' });
      } else {
        let y = 160;
        K.escribe(`B · ${P.n} PERFILES ${desde}`, P.L, y, 1.8);
        K.escribe(`A · PLANTA · CURVAS CADA ${fmt(eq)} M`, A.x0, y, 1.8); y += 4.4;
        K.escribe(`CORTES CADA ${fmt(V.espaciado)} M · EXAGERACIÓN VERTICAL ${exagDe(V)}`, P.L, y, 1.5, { slant: SL, track: 0.3 });
        K.escribe(`MAESTRAS CADA ${fmt(eq * cada)} M · ESCALA ${escalaNum(T.anchoKm * 1e6 / A.S)}`, A.x0, y, 1.5, { slant: SL, track: 0.3 });
        escalaGrafica(K, A.x0, 176, A.S / T.anchoKm, 70, null);
        titula(K, P.L, 182, 3.2, { track: 1.2 });
        K.escribe(lAlt, P.L, 188.5, 1.7);
        K.escribe(`SEMILLA ${seed}`, P.L, 194, 1.5, { slant: SL, track: 0.4 });
        if (registro === 'carto') K.marco(8, 8, page.w - 8, page.h - 8);
      }
    } else if (hoja === 'bloque' || hoja === 'proyeccion') {
      // C · el terreno recortado como pastel. En 'proyeccion', con su planta en rombo debajo:
      // el rombo se gira θ y el bloque usa ejes U = S(cosθ, −cosθ·tanα), V = S(−senθ, −senθ·tanα),
      // así cada punto cae en la misma vertical en las dos vistas (Fig. 16).
      const rb = MT.rng(seed + ':bloque');
      const alfa = rb.range(22, 32) * Math.PI / 180;
      const theta = (hoja === 'proyeccion' ? rb.range(35, 55) : rb.range(28, 62)) * Math.PI / 180;
      modoBloque = ['secciones', 'curvas', 'malla'].includes(o.modo) ? o.modo : rb() < (hoja === 'proyeccion' ? 0.35 : 0.6) ? 'secciones' : 'curvas';
      if (!o.modo && hoja === 'bloque' && modoBloque === 'secciones' && tiroMalla < 0.4) modoBloque = 'malla';
      let nS = rb.int(...{ carto: [44, 70], lamina: [56, 96], obra: [70, 130] }[registro]);
      if (T.arq === 'dunas' || T.arq === 'poligonos') nS = Math.max(nS, 220);
      const hRel = rb.range(0.16, 0.3), gRel = rb.range(0.035, 0.075);
      const ct = Math.cos(theta), st = Math.sin(theta), ta = Math.tan(alfa);
      const toUV = MT.vistas.aUV[P.rot];
      const niveles = nivelesDe(T, eq, cada);
      const geo = (S, Ox, Oy, Hv) => ({
        O: [Ox, Oy], U: [S * ct, -S * ct * ta], V: [-S * st, -S * st * ta], S, grueso: gRel * S,
        Hv: Math.min(Hv, (T.exagMax || Infinity) * S / (T.anchoKm * 1000) * T.relieve), // exageración con tope
        rot: P.rot, step: 0.3, n: nS, modo: modoBloque, niveles, nC: nCb,
        agua: T.mar ? MT.vistas.lineasAgua(T, S * 0.8, 6) : null,
      });
      const conEstratos = modoBloque === 'curvas' || registro === 'carto';
      const dibujaBloque = (Vb, conRotulos, techo) => {
        for (const c of Vb.caja) K.add(c, 0);
        if (conEstratos) for (const e of Vb.estratos) K.add(e, 0); // dónde corta cada maestra las caras
        K.add(Vb.bordeIzq, 0);
        if (modoBloque !== 'curvas') {
          for (const s of Vb.secc) K.add(s, 0);
          for (const s of Vb.cols) K.add(s, 0);
          for (const f of Vb.fondoDer) K.add(f, 0);
        } else {
          K.add(Vb.bordeDer, 0);
          const cs = [...Vb.curvas].sort((p, q) => (sube ? p.nivel - q.nivel : q.nivel - p.nivel));
          for (const c of cs) { const pl = T.nivelMar ? (c.nivel < 0 ? 100 : 101) : 0; K.add(c.pts, pl); if (c.maestra) K.add(desfasa(c.pts, 0.2).reverse(), pl); }
          for (const c of Vb.cielo) K.add(c, 0);
          for (const w of Vb.agua) K.add(w, 1); // el agua va en la otra tinta
        }
        rioEnVista(K, T, Vb);
        return conRotulos ? rotulaCrestas(K, T, Vb, null, registro, techo, 45) : [];
      };
      const vRumbo = rumbo(P.rot, -st, -ct); desdeBloque = vRumbo;
      const nCb = Math.round(nS * MT.rng(seed + ':malla:b').range(0.6, 1));
      const lModo = modoBloque === 'malla' ? `MALLA DE ${nS} × ${nCb} LÍNEAS`
        : modoBloque === 'secciones' ? `${nS} SECCIONES CADA ${fmt(T.anchoKm * 1000 / (nS - 1))} M`
        : `CURVAS CADA ${fmt(eq)} M · MAESTRAS CADA ${fmt(eq * cada)} M`;

      if (hoja === 'bloque') {
        // el bloque llena la hoja: en obra casi de orilla a orilla, en lámina y mapa deja lugar a la letra
        const area = registro === 'obra' ? { x0: 18, x1: 279, y0: 22, y1: 190 }
          : registro === 'carto' ? { x0: 40, x1: 240, y0: 30, y1: 156 } : { x0: 26, x1: 271, y0: 28, y1: 164 };
        const aw = area.x1 - area.x0, ah = area.y1 - area.y0;
        const altoDe = (S) => {
          const Hv = hRel * S * (ct + st); let m = 0;
          for (let i = 0; i <= 50; i++) for (let j = 0; j <= 50; j++) {
            const a = i / 50, b = j / 50;
            m = Math.min(m, S * (-a * ct * ta - b * st * ta) - T.sample(...toUV(a, b)) * Hv);
          }
          return -m + gRel * S;
        };
        let S = aw / (ct + st);
        if (o.bloqueGeo) S = o.bloqueGeo.S; // en la formación la escala es la de la lámina final
        else if (altoDe(S) > ah) S *= ah / altoDe(S);
        const Hv = o.bloqueGeo ? o.bloqueGeo.Hv : hRel * S * (ct + st);
        const Ox = area.x0 + (aw - S * (ct + st)) / 2 + S * st, Oy = area.y1 - gRel * S;
        V = MT.vistas.bloque(T, geo(S, Ox, Oy, Hv));
        rotulados = dibujaBloque(V, true, vertical ? 30 : 13);
        if (registro !== 'obra') { // altitudes junto a la arista derecha: a la misma altura que los estratos
          const c0 = V.P(1, 0, 0), x = c0[0] + 7, Rl = T.relieve, paso = nice(Rl / 4);
          const yA = (m) => c0[1] - (m - T.base) / Rl * V.hv;
          const mBajo = T.base - gRel * S / V.hv * Rl;
          K.add([[x, c0[1] + gRel * S], [x, yA(T.base + Rl)]], 1);
          for (let m = Math.ceil(Math.max(mBajo, T.mar ? 0 : mBajo) / paso) * paso; m <= T.base + Rl + 1e-6; m += paso) {
            K.add([[x, yA(m)], [x + 1.5, yA(m)]], 1);
            K.escribe(fmt(m), x + 2.5, yA(m) + 0.8, 1.6);
          }
          K.escribe('M', x - 0.7, yA(T.base + Rl) - 2, 1.6);
        }
        const l1 = `BLOQUE DIAGRAMA · ${lModo}`, l2 = `VISTA DESDE EL ${vRumbo} · EXAGERACIÓN VERTICAL ×${dec(V.exag)}`;
        if (registro === 'carto') {
          const m = 8, lineas = [l1, l2, lAlt];
          const anchoT = Math.max(anchoTitulo(3.4, 1.4), ...lineas.map((q) => MT.letra.mide(q, 1.8)));
          const bx1 = page.w - m - 6, bx0 = bx1 - anchoT - 8, by1 = page.h - m - 5, by0 = by1 - 35;
          let y = by0 + 11.5;
          titula(K, bx0 + 4, y, 3.4, { track: 1.4 });
          K.add([[bx0 + 4, y + 2.4], [bx1 - 4, y + 2.4]], 1);
          y += 7;
          for (const q of lineas) { K.escribe(q, bx0 + 4, y, 1.8); y += 4.6; }
          K.escribe(`SEMILLA ${seed}`, bx0 + 4, y + 1, 1.5, { slant: SL, track: 0.4 });
          K.marco(bx0, by0, bx1, by1);
          K.marco(m, m, page.w - m, page.h - m);
        } else if (registro === 'lamina') {
          let y = area.y1 + 14;
          titula(K, area.x1, y, 3, { track: 1.2, align: 'right' }); y += 5.5;
          K.escribe(l1, area.x1, y, 1.7, { align: 'right' }); y += 4;
          K.escribe(l2, area.x1, y, 1.7, { align: 'right' }); y += 4;
          K.escribe(`SEMILLA ${seed}`, area.x1, y + 0.6, 1.4, { slant: SL, track: 0.4, align: 'right' });
        } else {
          K.escribe(`BLOQUE · ${vRumbo} · ×${dec(V.exag)} · S ${seed}`, area.x1, page.h - 18, 1.5, { slant: SL, track: 0.5, align: 'right' });
        }
      } else {
        const Wp = 124, S = Wp / (ct + st), Ox = page.w / 2 - (S * ct - S * st) / 2, yPlano = 258;
        const A = { O: [Ox, yPlano], U: [S * ct, -S * st], V: [-S * st, -S * ct], S, rot: P.rot, x0: Ox - S * st, y0: yPlano - Wp };
        const Oy = A.y0 - 14 - gRel * S;
        let Hv = hRel * S * (ct + st); // lo que pida la semilla, sin salirse por arriba
        for (let i = 0; i <= 50; i++) for (let j = 0; j <= 50; j++) {
          const a = i / 50, b = j / 50, h = T.sample(...toUV(a, b));
          if (h > 0.01) Hv = Math.min(Hv, (Oy + S * (-a * ct * ta - b * st * ta) - 22) / h);
        }
        if (o.bloqueGeo) Hv = o.bloqueGeo.Hv;
        V = MT.vistas.bloque(T, geo(S, Ox, Oy, Hv));
        dibujaBloque(V, false);
        Cv = dibujaCurvas(K, T, A, curvasCfg({ nCotas: Math.round(nCotas * 0.7) }));
        // líneas de proyección: las esquinas laterales y cada punto acotado que el bloque deja ver
        const P2 = (a, b) => [A.O[0] + a * A.U[0] + b * A.V[0], A.O[1] + a * A.U[1] + b * A.V[1]];
        for (const [a, b] of [[0, 1], [1, 0]]) { const p = P2(a, b), q = V.Pb(a, b); K.discontinua([p[0], p[1] - 1], [q[0], q[1] + 1]); }
        for (const p of Cv.puntos) {
          const pr = V.proyecta(p.c.u, p.c.v);
          if (!pr.vis) continue;
          K.discontinua([p.x, p.y - 2.4], [pr.x, pr.y + 1.6]);
          if (p.c.tipo === 'pico') K.add([[pr.x - 0.9, pr.y - 0.3], [pr.x, pr.y - 1.9], [pr.x + 0.9, pr.y - 0.3], [pr.x - 0.9, pr.y - 0.3]], 1);
          else K.add(circulo(pr.x, pr.y, 0.7), 1);
        }
        K.escribe('B', 16, Oy - V.hv * 0.3, 3.4, { align: 'center' });
        K.escribe('A', 16, A.y0 + Wp / 2 + 1.7, 3.4, { align: 'center' });
        const [na, nb] = uvAB[P.rot](0, 1);
        let fx = na * A.U[0] + nb * A.V[0], fy = na * A.U[1] + nb * A.V[1];
        const fl = Math.hypot(fx, fy); fx /= fl; fy /= fl;
        K.flecha(page.w - 20, A.y0 + 16, fx, fy, 12, 'N');
        if (registro === 'obra') {
          K.escribe(`B BLOQUE · A PLANTA · CURVAS CADA ${fmt(eq)} M · S ${seed}`, page.w - 20, page.h - 14, 1.5, { slant: SL, track: 0.5, align: 'right' });
        } else {
          escalaGrafica(K, 20, yPlano + 4, S / T.anchoKm, 50, null);
          let y = 273;
          titula(K, 20, y, 3.2, { track: 1.2 }); y += 5.5;
          K.escribe(`B · BLOQUE VISTO DESDE EL ${vRumbo} · ${lModo} · EXAGERACIÓN ×${dec(V.exag)}`, 20, y, 1.5); y += 4;
          K.escribe(`A · PLANTA PROYECTADA · CURVAS CADA ${fmt(eq)} M · MAESTRAS CADA ${fmt(eq * cada)} M`, 20, y, 1.5); y += 4;
          K.escribe(`${lAlt} · ESCALA ${escalaNum(T.anchoKm * 1e6 / S)}`, 20, y, 1.5); y += 4.2;
          K.escribe(`SEMILLA ${seed}`, 20, y, 1.4, { slant: SL, track: 0.4 });
        }
      }
    } else if (hoja === 'secuencia') {
      // La historia de la montaña en cuatro tiempos, como en los libros de geología: misma
      // escala, misma exageración y mismo punto de vista, para que se pueda comparar de verdad.
      const rb = MT.rng(seed + ':bloque');
      const alfa = rb.range(22, 30) * Math.PI / 180, theta = rb.range(32, 58) * Math.PI / 180;
      modoBloque = ['secciones', 'curvas'].includes(o.modo) ? o.modo : rb() < 0.5 ? 'secciones' : 'curvas';
      const nS = rb.int(...{ carto: [40, 60], lamina: [46, 70], obra: [56, 84] }[registro]);
      const hRel = rb.range(0.2, 0.3), gRel = rb.range(0.04, 0.07);
      const ct = Math.cos(theta), st = Math.sin(theta), ta = Math.tan(alfa);
      const muestreo = (arr) => (u, v) => {
        const N = T.G, x = Math.min(1, Math.max(0, u)) * (N - 1), y = Math.min(1, Math.max(0, v)) * (N - 1);
        const xi = Math.min(N - 2, Math.floor(x)), yi = Math.min(N - 2, Math.floor(y)), fx = x - xi, fy = y - yi, k = yi * N + xi;
        return arr[k] * (1 - fx) * (1 - fy) + arr[k + 1] * fx * (1 - fy) + arr[k + N] * (1 - fx) * fy + arr[k + N + 1] * fx * fy;
      };
      const maxDe = (a) => { let m = -Infinity; for (const v of a) if (v > m) m = v; return m; };
      // las cuatro etapas: [terreno de esa etapa, título, nota]
      let etapas;
      if (T.arq === 'estrato') {
        etapas = [0.06, 0.5, 0.8, 0.95].map((e) => {
          const Te = MT.terreno(seed, { arq: 'estrato', edad: e });
          const esp = Te.rasgos.especiales.find((q) => q.tipo === 'crater' || q.tipo === 'cuello');
          const nota = [esp ? `${esp.term}${esp.dato ? ' ' + esp.dato : ''}` : null, `CIMA ${fmt(Te.alt(maxDe(Te.h)))} M`].filter(Boolean).join(' · ');
          return [Te, Te.nombre.replace('ESTRATOVOLCÁN ', 'CONO '), nota];
        });
      } else {
        const Tx = MT.terreno(seed, { arq: o.arq, edad: o.edad, etapas: true, realismo: o.realismo });
        const E = Object.fromEntries(Tx.etapas.map((e) => [e.clave + (e.k != null ? e.k : ''), e]));
        E.relieve = E.relieve || E.erosion; // sin erosión (dunas) el relieve ya es el final
        const conH = (arr, agua) => ({ ...Tx, h: arr, sample: muestreo(arr), hidro: agua ? Tx.hidro : null });
        const cima = (arr) => `CIMA ${fmt(Tx.alt(maxDe(arr)))} M`;
        if (Tx.arq === 'impactos') {
          const im = Tx.etapas.filter((e) => e.clave === 'impactos');
          const mayor = Tx.rasgos.especiales[0];
          etapas = [
            [conH(im[0].h), 'LLANURA', 'ANTES DEL PRIMER IMPACTO'],
            [conH(im[1].h), 'PRIMEROS IMPACTOS', `${im[1].k} CRÁTERES`],
            [conH(im[2].h), 'MÁS IMPACTOS', `${im[2].k} CRÁTERES · LOS VIEJOS SE ABLANDAN`],
            [conH(Tx.h), 'HOY', `${Tx.nImpactos} CRÁTERES${mayor ? ' · EL MAYOR ' + mayor.dato : ''}`],
          ];
        } else {
          // lo que trajo el agua, sólo lo que vale la pena decir
          const H = Tx.hidro, nl = H ? H.lagos.length : 0, notaAgua = [
            Tx.mar ? 'EL MAR CUBRE LO BAJO' : null,
            nl ? `${nl} ${nl === 1 ? 'LAGO' : 'LAGOS'}` : null,
            H && H.principal && H.principal.largoKm >= 1 ? `RÍO DE ${dec(H.principal.largoKm)} KM` : null,
          ].filter(Boolean).join(' · ') || 'RÍOS SIN LAGO';
          etapas = [
            [conH(E.forma.h), 'LEVANTAMIENTO', 'LA FORMA GRANDE, SIN DETALLE'],
            [conH(E.relieve.h), 'RELIEVE', [cima(E.relieve.h), ...(Tx.eventos || []).filter((e) => !e.joven).map((e) => e.nombre)].join(' · ')],
            [conH(E.erosion.h), (Tx.eventos || []).some((e) => e.joven) ? 'EROSIÓN Y LO NUEVO' : 'EROSIÓN', [`${Tx.pasadas} PASADAS DE CAUCES`, ...(Tx.eventos || []).filter((e) => e.joven).map((e) => e.nombre)].join(' · ')],
            [conH(Tx.h, true), 'EL AGUA', notaAgua],
          ];
        }
      }
      // un mismo bloque para las cuatro: escala en mm por metro común, y que quepa la más alta
      const relMax = Math.max(...etapas.map(([Te]) => Te.relieve));
      const caja0 = { w: 121, h: 62 };
      const altoDe = (S) => {
        let m = 0;
        for (const [Te] of etapas) {
          const Hv = hRel * S * (ct + st) * Te.relieve / relMax, toUV = MT.vistas.aUV[P.rot];
          for (let i = 0; i <= 40; i++) for (let j = 0; j <= 40; j++) {
            const a = i / 40, b = j / 40;
            m = Math.min(m, S * (-a * ct * ta - b * st * ta) - Te.sample(...toUV(a, b)) * Hv);
          }
        }
        return -m + gRel * S;
      };
      let S = caja0.w / (ct + st);
      if (altoDe(S) > caja0.h) S *= caja0.h / altoDe(S);
      const mmPorM = Math.min(hRel * S * (ct + st) / relMax, (T.exagMax || Infinity) * S / (T.anchoKm * 1000));
      const ROM = ['I', 'II', 'III', 'IV'], celdas = [[18, 14], [158, 14], [18, 102], [158, 102]];
      let exag = 0;
      etapas.forEach(([Te, titulo, nota], k) => {
        const [x0, y0] = celdas[k];
        const Ox = x0 + (caja0.w - S * (ct + st)) / 2 + S * st, Oy = y0 + 14 + caja0.h - gRel * S;
        const niveles = nivelesDe(Te, eq, cada);
        const Vk = MT.vistas.bloque(Te, {
          O: [Ox, Oy], U: [S * ct, -S * ct * ta], V: [-S * st, -S * st * ta], S, Hv: mmPorM * Te.relieve,
          grueso: gRel * S, rot: P.rot, step: 0.3, n: nS, modo: modoBloque, niveles,
        });
        exag = Vk.exag;
        for (const c of Vk.caja) K.add(c, 0);
        if (modoBloque === 'curvas') for (const e of Vk.estratos) K.add(e, 0);
        K.add(Vk.bordeIzq, 0);
        if (modoBloque === 'secciones') { for (const s of Vk.secc) K.add(s, 0); for (const f of Vk.fondoDer) K.add(f, 0); }
        else {
          K.add(Vk.bordeDer, 0);
          for (const c of [...Vk.curvas].sort((p, q) => p.nivel - q.nivel)) { K.add(c.pts, 0); if (c.maestra) K.add(desfasa(c.pts, 0.2).reverse(), 0); }
          for (const c of Vk.cielo) K.add(c, 0);
        }
        rioEnVista(K, Te, Vk);
        // número, nombre de la etapa y lo que se midió en ella
        K.escribe(ROM[k], x0, y0 + 5.5, 4, { align: 'left' });
        K.escribe(titulo, x0 + 11, y0 + 3.6, 2.1, { track: 0.8 });
        K.escribe(nota, x0 + 11, y0 + 8, 1.5, { slant: SL, track: 0.3 });
      });
      // flechas de tiempo: I → II y III → IV
      K.flecha(149, 14 + 14 + caja0.h / 2, 1, 0, 7, null);
      K.flecha(149, 102 + 14 + caja0.h / 2, 1, 0, 7, null);
      const lHist = `HISTORIA EN CUATRO TIEMPOS · MISMA ESCALA Y MISMA EXAGERACIÓN VERTICAL ×${dec(exag)} · VISTA DESDE EL ${rumbo(P.rot, -st, -ct)}`;
      desdeBloque = rumbo(P.rot, -st, -ct);
      if (registro === 'obra') {
        K.escribe(`${T.nombre} · I–IV · S ${seed}`, page.w - 18, page.h - 9, 1.5, { slant: SL, track: 0.5, align: 'right' });
      } else {
        K.escribe(T.arq === 'estrato' ? 'VIDA DE UN ESTRATOVOLCÁN' : T.nombre, 18, 194, 3, { track: 1.2 });
        K.escribe(lHist, 18, 199.5, 1.5);
        K.escribe(`${lAlt} · SEMILLA ${seed}`, 18, 203.8, 1.4, { slant: SL, track: 0.3 });
        if (registro === 'carto') K.marco(8, 6, page.w - 8, page.h - 3);
      }
    } else if (hoja === 'corte') {
      // Planta arriba, cruzada por la línea A–A′; abajo, la sección del terreno por esa línea,
      // con la misma escala horizontal: cada punto del perfil cae justo bajo su lugar en la planta.
      const S = 150, x0 = 30, y0 = 20, A = plano(x0, y0, S, P.rot);
      const toUV = MT.vistas.aUV[P.rot], toA = MT.vistas.uvA[P.rot];
      const R = T.rasgos;
      // por dónde se corta: el cráter (o el cuello) si hay, si no la cumbre
      const objetivo = T.arq === 'canon' && R.fondo ? { ...R.fondo, tipo: 'fondo', term: 'FONDO' } // el cañón se corta por su fondo
        : (R.especiales || []).find((e) => ['crater', 'cuello'].includes(e.tipo)) || (R.picos || [])[0];
      let yc, xObj = null;
      if (o.corteGeo) yc = o.corteGeo.yc;
      else {
        const [a, b] = objetivo ? toA(objetivo.u, objetivo.v) : [0.5, 0.5];
        yc = y0 + (1 - Math.min(0.92, Math.max(0.08, b))) * S;
        xObj = x0 + a * S;
      }
      const bc = 1 - (yc - y0) / S;
      Cv = dibujaCurvas(K, T, A, curvasCfg({}));
      // la línea de corte en la planta: raya y punto, con las flechas hacia donde se mira
      for (let x = x0 - 6; x < x0 + S + 6; x += 6) {
        K.add([[x, yc], [Math.min(x0 + S + 6, x + 3.6), yc]], 1);
        if (x + 4.8 < x0 + S + 6) K.add([[x + 4.6, yc], [x + 5, yc]], 1);
      }
      for (const [x, txt] of [[x0 - 6, 'A'], [x0 + S + 6, 'A′']]) {
        K.add([[x, yc], [x, yc - 5]], 1);
        K.add([[x - 1.1, yc - 3.2], [x, yc - 5], [x + 1.1, yc - 3.2]], 1);
        K.escribe(txt, x + (x < x0 ? -1.5 : 1.5), yc + 1.1, 2.6, { align: x < x0 ? 'right' : 'left' });
      }
      // el perfil: muestras a lo largo del corte
      const paso = 0.25, mues = [];
      for (let x = x0; x <= x0 + S + 1e-6; x += paso) {
        const a = (x - x0) / S, [u, v] = toUV(a, bc), hn = T.sample(u, v);
        const N = T.G, k = Math.round(v * (N - 1)) * N + Math.round(u * (N - 1));
        mues.push({ x, alt: T.alt(hn), agua: !!(T.hidro && T.hidro.agua[k]) || (T.mar && hn <= 1e-4) });
      }
      const mmH = S / (T.anchoKm * 1000);
      let geo = o.corteGeo;
      if (!geo) {
        let mn = Infinity, mx = -Infinity;
        for (const m of mues) { if (m.alt < mn) mn = m.alt; if (m.alt > mx) mx = m.alt; }
        const pasoA = nice(Math.max(20, mx - mn) / 4), baseAlt = Math.floor(mn / pasoA) * pasoA - (T.mar ? 0 : pasoA);
        const bruto = 76 / Math.max(1, mx - baseAlt) / mmH; // el perfil puede subir hasta casi tocar la planta
        const EX = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50];
        const exag = EX.filter((e) => e <= bruto).pop() || Math.round(bruto * 10) / 10;
        geo = { yc, baseAlt, pasoA, exag, topAlt: Math.ceil(mx / pasoA) * pasoA };
      }
      corteGeo = geo;
      const yb = 262, mmV = geo.exag * mmH, yAlt = (alt) => yb - (alt - geo.baseAlt) * mmV;
      seccion = { x0, x1: x0 + S, yb, alt: (y) => geo.baseAlt + (yb - y) / mmV }; // para teñirla por franjas
      const prof = mues.map((m) => [m.x, yAlt(m.alt)]);
      // la sección: rayado vertical bajo el perfil (el tono de un corte), luego el perfil con doble pasada
      for (let i = 0, k = 0; i < mues.length; i += 4, k++) {
        const [x, y] = prof[i];
        if (yb - y < 0.6) continue;
        K.add(k % 2 ? [[x, y], [x, yb]] : [[x, yb], [x, y]], 0);
      }
      const linea = MT.simplifica(prof, 0.02);
      K.add([[x0, yb], ...linea, [x0 + S, yb]], 0);
      K.add(desfasa(linea, -0.2).reverse(), 0);
      K.add([[x0, yb], [x0 + S, yb]], 0);
      // agua cortada: la superficie, en la tinta del agua
      let tramo = null;
      for (let i = 0; i <= mues.length; i++) {
        const m = mues[i];
        if (m && m.agua) { if (!tramo) tramo = [i, i]; else tramo[1] = i; continue; }
        if (tramo && tramo[1] - tramo[0] > 2) {
          const ya = yAlt(mues[tramo[0]].alt);
          for (const d of [0, 0.5]) K.add([[mues[tramo[0]].x, ya - d], [mues[tramo[1]].x, ya - d]], 1);
        }
        tramo = null;
      }
      // dónde el corte cruza un río: una marca en el perfil
      if (T.hidro) {
        const cruces = [];
        for (const rv of T.hidro.rios) {
          if (rv.clase < 2) continue;
          const pl = rv.pts.map(([u, v]) => { const [a, b] = toA(u, v); return [x0 + a * S, y0 + (1 - b) * S]; });
          for (let i = 1; i < pl.length; i++) {
            const [ax, ay] = pl[i - 1], [bx, by] = pl[i];
            if ((ay - yc) * (by - yc) <= 0 && ay !== by) {
              const x = ax + (bx - ax) * (yc - ay) / (by - ay);
              if (!cruces.some((c) => Math.abs(c - x) < 3)) cruces.push(x);
            }
          }
        }
        for (const x of cruces) {
          const i = Math.max(0, Math.min(mues.length - 1, Math.round((x - x0) / paso))), y = prof[i][1];
          K.add([[x - 0.9, y - 2.6], [x, y - 0.9], [x + 0.9, y - 2.6]], 1);
        }
      }
      // ejes: altitudes a la izquierda, kilómetros abajo; los extremos se llaman A y A′
      const xa = x0 - 5;
      K.add([[xa, yb], [xa, yAlt(geo.topAlt)]], 1);
      for (let m = geo.baseAlt; m <= geo.topAlt + 1e-6; m += geo.pasoA) {
        K.add([[xa - 1.5, yAlt(m)], [xa, yAlt(m)]], 1);
        K.escribe(fmt(m), xa - 2.5, yAlt(m) + 0.8, 1.6, { align: 'right' });
      }
      K.escribe('M', xa, yAlt(geo.topAlt) - 2.5, 1.6, { align: 'center' });
      const pk = nice(T.anchoKm / 5);
      for (let km = 0; km <= T.anchoKm + 1e-6; km += pk) {
        const x = x0 + km / T.anchoKm * S;
        K.add([[x, yb], [x, yb + 1.5]], 1);
        K.escribe(dec(km), x, yb + 4.5, 1.6, { align: 'center' });
      }
      K.escribe('KM', x0 + S + 3, yb + 4.5, 1.6);
      const yA = (x) => prof[Math.max(0, Math.min(prof.length - 1, Math.round((x - x0) / paso)))][1];
      K.escribe('A', x0 - 1, yA(x0) - 3.5, 2.6, { align: 'right' });
      K.escribe('A′', x0 + S + 1, yA(x0 + S) - 3.5, 2.6);
      // líneas de proyección: de la planta al perfil, en los extremos y en lo que se cortó
      K.discontinua([x0, y0 + S + 1], [x0, yA(x0) - 1]);
      K.discontinua([x0 + S, y0 + S + 1], [x0 + S, yA(x0 + S) - 1]);
      if (xObj != null && objetivo) {
        let ym = Infinity; // el rótulo va sobre lo más alto de los alrededores (en un cañón, sobre el borde)
        for (let x = xObj - 6; x <= xObj + 6; x += paso) ym = Math.min(ym, yA(x));
        K.discontinua([xObj, y0 + S + 1], [xObj, ym - 9]);
        const dato = objetivo.dato || fmt(T.alt(objetivo.h));
        K.escribe(objetivo.term || 'CUMBRE', xObj + 1.5, ym - 6.2, 1.9, { slant: SL, track: 0.5 });
        K.escribe(dato, xObj + 1.5, ym - 2.6, 2.1);
      }
      const [nfx, nfy] = FLECHA_N[A.rot];
      K.flecha(194, y0 + 14, nfx, nfy, 12, 'N');
      const lCorte = `CORTE A–A′ POR ${objetivo && objetivo.term && objetivo.tipo !== 'pico' ? 'EL ' + objetivo.term : 'LA CUMBRE'} · EXAGERACIÓN VERTICAL ×${dec(geo.exag)}`;
      if (registro === 'obra') {
        K.escribe(`A–A′ · ×${dec(geo.exag)} · S ${seed}`, x0 + S, page.h - 12, 1.5, { slant: SL, track: 0.5, align: 'right' });
      } else {
        let y = 276;
        titula(K, x0, y, 3.2, { track: 1.2 }); y += 5.5;
        K.escribe(lCorte, x0, y, 1.6); y += 4;
        K.escribe(`PLANTA · CURVAS CADA ${fmt(eq)} M · MAESTRAS CADA ${fmt(eq * cada)} M · ESCALA ${escalaNum(T.anchoKm * 1e6 / S)}`, x0, y, 1.6); y += 4;
        K.escribe(`${lAlt} · SEMILLA ${seed}`, x0, y, 1.4, { slant: SL, track: 0.3 });
        if (registro === 'carto') K.marco(8, 8, page.w - 8, page.h - 8);
      }
    } else { // torre: bloque arriba, planta abajo, y lo que los une
      P.p = 1; // sin perspectiva: cada punto cae en la misma vertical en las dos vistas
      V = MT.vistas.crestas(T, P);
      for (const s of V.strokes) K.add(s, 0);
      rioEnVista(K, T, V);
      const A = plano(P.L, 118, P.W, P.rot);
      Cv = dibujaCurvas(K, T, A, curvasCfg({ nCotas: Math.round(nCotas * 0.8) }));
      for (const p of Cv.puntos) { // líneas de proyección, como en los libros de topografía
        const pr = V.proyecta(p.c.u, p.c.v);
        if (!pr.vis) continue;
        K.discontinua([p.x, p.y - 2.4], [pr.x, pr.y + 1.6]);
        if (p.c.tipo === 'pico') K.add([[pr.x - 0.9, pr.y - 0.3], [pr.x, pr.y - 1.9], [pr.x + 0.9, pr.y - 0.3], [pr.x - 0.9, pr.y - 0.3]], 1);
        else K.add(circulo(pr.x, pr.y, 0.7), 1);
      }
      K.escribe('B', P.L - 12, P.Y0 - P.D / 2, 3.4, { align: 'center' });
      K.escribe('A', P.L - 12, A.y0 + A.S / 2 + 1.7, 3.4, { align: 'center' });
      const [fx, fy] = FLECHA_N[A.rot];
      K.flecha(A.x0 + A.S + 12, A.y0 + 12, fx, fy, 12, 'N');
      if (registro === 'obra') {
        K.escribe(`B ${P.n} PERFILES · A CURVAS CADA ${fmt(eq)} M · S ${seed}`, A.x0 + A.S, page.h - 14, 1.5, { slant: SL, track: 0.5, align: 'right' });
      } else {
        escalaGrafica(K, A.x0, A.y0 + A.S + 11, A.S / T.anchoKm, 60, null);
        let y = A.y0 + A.S + 26;
        titula(K, P.L, y, 3.2, { track: 1.2 }); y += 5.5;
        K.escribe(`B · BLOQUE ${desde} · ${P.n} PERFILES · EXAGERACIÓN ${exagDe(V)}`, P.L, y, 1.6); y += 4.2;
        K.escribe(`A · PLANTA · CURVAS CADA ${fmt(eq)} M · MAESTRAS CADA ${fmt(eq * cada)} M`, P.L, y, 1.6); y += 4.2;
        K.escribe(`${lAlt} · ESCALA ${escalaNum(T.anchoKm * 1e6 / A.S)}`, P.L, y, 1.6); y += 4.4;
        K.escribe(`SEMILLA ${seed}`, P.L, y, 1.4, { slant: SL, track: 0.4 });
      }
    }

    // la historia de esta montaña, en orden, cuando hay algo que contar
    if (T.historia && registro !== 'obra' && hoja !== 'secuencia') K.escribe('HISTORIA · ' + T.historia.map((h, i) => `${i + 1} ${h}`).join(' · '), 8, 5.4, 1.5, { slant: SL, track: 0.3 });
    // teñir: el relieve que cae en una planta (o en una fila de perfiles) toma la pluma de su franja
    let plumasFin = plumas, trazosFin = K.trazos;
    if (franjas) {
      const nf = franjas.nf, altPlano = (x, y) => {
        for (const pl of planos) {
          const [a, b] = pl.inv(x, y);
          if (a >= -0.002 && a <= 1.002 && b >= -0.002 && b <= 1.002) return T.alt(T.sample(...MT.vistas.aUV[pl.rot](a, b)));
        }
        return null;
      };
      const fila = (x, y) => {
        if (!V || !V.rows || !V.linea) return null;
        const cx = P.L + P.W / 2; let mejor = null, dm = 0.05;
        for (const R of V.rows) {
          const a = (x - cx) / (P.W * R.s) + 0.5; if (a < 0 || a > 1) continue;
          const yp = R.yb - T.sample(...MT.vistas.aUV[P.rot](a, R.t)) * V.hv * R.s;
          if (Math.abs(yp - y) < dm) { dm = Math.abs(yp - y); mejor = R; }
        }
        return mejor;
      };
      trazosFin = [];
      for (const tr of K.trazos) {
        if (tr.pluma >= 100) { trazosFin.push({ pluma: tr.pluma - 100, pts: tr.pts }); continue; }
        if (tr.pluma !== 0) { trazosFin.push({ pluma: nf, pts: tr.pts }); continue; }
        const alturasTrazo = V && V.altitudes && V.altitudes.get(tr.pts);
        const altitudExacta = V && V.altitudEn && V.altitudEn.get(tr.pts);
        const mid = tr.pts[Math.floor(tr.pts.length / 2)];
        const enSeccion = (q) => seccion && q[0] >= seccion.x0 - 0.01 && q[0] <= seccion.x1 + 0.01 && q[1] <= seccion.yb + 0.01 && q[1] > seccion.yb - 120;
        const R = altPlano(...mid) == null && !enSeccion(mid) ? fila(...mid) : null;
        const alt = (q) => { const a = altPlano(...q); return a != null ? a : enSeccion(q) ? seccion.alt(q[1]) : R ? T.alt((R.yb - q[1]) / (V.hv * R.s)) : null; };
        // rectas largas (las rayas del corte) se subdividen: el cambio de pluma cae en su altura
        const pts = [tr.pts[0]], alturas = alturasTrazo ? [alturasTrazo[0]] : null;
        for (let i = 1; i < tr.pts.length; i++) {
          const [ax, ay] = tr.pts[i - 1], [bx, by] = tr.pts[i], n = Math.ceil(Math.hypot(bx - ax, by - ay) / 0.4);
          for (let j = 1; j <= n; j++) {
            pts.push([ax + (bx - ax) * j / n, ay + (by - ay) * j / n]);
            if (alturas) alturas.push(alturasTrazo[i - 1] + (alturasTrazo[i] - alturasTrazo[i - 1]) * j / n);
          }
        }
        let cur = null, k0 = null;
        for (let i = 0; i < pts.length; i++) {
          const q = pts[i], a = altitudExacta ? altitudExacta(q) : alturas ? alturas[i] : alt(q), k = a == null ? (franjas.mar ? franjas.nf - 1 : 0) : franjas.de(a); // sin altura conocida: tierra
          let cruce = null;
          if (k !== k0 && cur) {
            if (altitudExacta && i > 0) {
              const p = pts[i - 1]; let lo = 0, hi = 1;
              for (let j = 0; j < 16; j++) {
                const t = (lo + hi) / 2;
                if (franjas.de(altitudExacta([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t])) === k0) lo = t; else hi = t;
              }
              cruce = [p[0] + (q[0] - p[0]) * hi, p[1] + (q[1] - p[1]) * hi];
            }
            cur.pts.push(cruce || q); trazosFin.push(cur); cur = null;
          }
          if (!cur) { cur = { pluma: k, pts: cruce ? [cruce] : [] }; k0 = k; }
          cur.pts.push(q);
        }
        if (cur && cur.pts.length > 1) trazosFin.push(cur);
      }
      trazosFin = trazosFin.map((t) => (t.pts.length > 3 ? { pluma: t.pluma, pts: MT.simplifica(t.pts, 0.02) } : t));
      trazosFin = trazosFin.map((t, i) => [t, i]).sort((a, b) => a[0].pluma - b[0].pluma || a[1] - b[1]).map((x) => x[0]);
      plumasFin = [...franjas.tintas, franjas.mar ? franjas.tintas[0] : plumas[1]];
    }

    return {
      seed, page, papel, plumas: plumasFin, trazos: trazosFin, registro, hoja,
      opciones: o, // con qué se pidió: la formación debe usar exactamente lo mismo
      meta: {
        etiquetas: K.etiquetas.map(({ topo, caja }) => ({ caja: caja.map((v) => Math.round(v * 10) / 10), nombre: topo.nombre, glosa: topo.glosa || '', clase: topo.clase, lengua: topo.lengua || 'castellano', generico: topo.generico || '', fuente: topo.fuente || '' })),
        arq: T.arq, nombre: T.nombre, toponimo: principal ? principal.nombre : null, glosa: principal ? principal.glosa : null, registro, hoja, rot: P.rot, desde: desdeBloque || DIR[P.rot],
        perfiles: V ? P.n : null, exag: V ? V.exag : null, hv: V ? V.hv : null, bloqueGeo: V && V.S ? { S: V.S, Hv: V.hv } : null, corteGeo, eq: Cv ? eq : null, cotas: Cv ? Cv.cotas : null,
        anchoKm: T.anchoKm, base: T.base, relieve: T.relieve, oscuro, rotulados, modo: modoBloque, planta: estiloPlanta,
        puntos: Cv ? Cv.puntos.map((p) => p.c.term) : null,
        hipso: franjas ? { franjas: franjas.nf, bordes: franjas.bordes } : null,
        iluminadas: !!(Cv && Cv.luz), malla: !!(P.nC || modoBloque === 'malla'),
        eventos: T.eventos && T.eventos.length ? T.eventos : null, historia: T.historia,
      },
    };
  };

  // La formación: la montaña de la llanura a la erosión, en n cuadros, con la escala de la
  // lámina final. Cada cuadro trae sólo el relieve y el nombre de la era.
  MT.ERAS = (arq) => (arq === 'impactos' ? ['I · LLANURA', 'II · IMPACTOS', 'III · MÁS IMPACTOS', 'IV · HOY']
    : arq === 'dunas' ? ['I · ARENA', 'II · VIENTO', 'III · DUNAS', 'IV · HOY']
    : arq === 'pliegues' ? ['I · CAPAS', 'II · PLEGAMIENTO', 'III · EROSIÓN', 'IV · EL AGUA']
    : arq === 'karst' ? ['I · CALIZA', 'II · DISOLUCIÓN', 'III · DOLINAS', 'IV · CENOTES']
    : arq === 'costa' ? ['I · TIERRA', 'II · RELIEVE', 'III · EROSIÓN', 'IV · EL MAR']
    : arq === 'anillos' ? ['I · CAPAS', 'II · DOMO', 'III · EROSIÓN', 'IV · ANILLOS']
    : arq === 'drumlins' ? ['I · LLANURA', 'II · HIELO', 'III · DRUMLINS', 'IV · EL AGUA']
    : arq === 'rift' ? ['I · MESETA', 'II · ESTIRAMIENTO', 'III · HUNDIMIENTO', 'IV · LAGOS']
    : arq === 'poligonos' ? ['I · PERMAFROST', 'II · CONTRACCIÓN', 'III · GRIETAS', 'IV · POLÍGONOS']
    : arq === 'atolon' ? ['I · VOLCÁN', 'II · HUNDIMIENTO', 'III · ARRECIFE', 'IV · HOY']
    : arq === 'meandros' ? ['I · VALLE', 'II · TERRAZAS', 'III · MEANDROS', 'IV · EL AGUA']
    : ['I · LEVANTAMIENTO', 'II · RELIEVE', 'III · EROSIÓN', 'IV · EL AGUA']);
  MT.formaCuadro = function (seed, final, t) {
    MT._lang = (final.opciones && final.opciones.lang) === 'en' ? 'en' : 'es';
    const m = final.meta, eras = MT.ERAS(m.arq);
    // sin rasgos (t < 1): así las curvas no se cortan donde la lámina final pondrá su letra
    const L = MT.lamina(seed, { ...(final.opciones || {}), forma: Math.min(t, 0.999), hvFijo: m.hv, bloqueGeo: m.bloqueGeo, corteGeo: m.corteGeo, hipso: m.hipso ? 1 : 0 });
    const letra = L.plumas.length - 1; // con tintas hipsométricas el relieve usa varias plumas
    const trazos = L.trazos.filter((q) => q.pluma !== letra);
    const era = eras[Math.min(2, Math.floor(t * 3))];
    for (const l of MT.letra.trazos(era, 18, final.page.h - 10, 2.6, { track: 0.8 }).lineas) trazos.push({ pluma: letra, pts: l });
    return { t, trazos };
  };
  MT.formable = (final) => final.hoja !== 'secuencia';
  MT.formacion = function (seed, final, n = 36) {
    if (!MT.formable(final)) return [];
    return Array.from({ length: n }, (_, k) => MT.formaCuadro(seed, final, k / (n - 1)));
  };

  // SVG real en mm, en el orden en que se traza.
  MT.svg = function (Lm) {
    const pl = Lm.trazos.map((t) => `<polyline data-pluma="${t.pluma}" stroke="${Lm.plumas[t.pluma]}" points="${t.pts.map(([x, y]) => x.toFixed(2) + ',' + y.toFixed(2)).join(' ')}"/>`);
    return `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="${Lm.page.w}mm" height="${Lm.page.h}mm" viewBox="0 0 ${Lm.page.w} ${Lm.page.h}">\n<title>Montañas topográficas · semilla ${Lm.seed}</title>\n<rect width="100%" height="100%" fill="${Lm.papel}"/>\n<g fill="none" stroke-width="0.3" stroke-linecap="round" stroke-linejoin="round">\n${pl.join('\n')}\n</g>\n</svg>\n`;
  };
})(typeof globalThis !== 'undefined' ? globalThis : window);
