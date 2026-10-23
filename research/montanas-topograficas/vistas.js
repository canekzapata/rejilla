// vistas.js — traductores terreno → polilíneas en orden de trazado.
(function (G) {
  const MT = G.MT;
  MT.vistas = MT.vistas || {};

  // rot = desde dónde se mira: 0 sur, 1 este, 2 norte, 3 oeste.
  // (a, b) = (de izquierda a derecha, de adelante hacia atrás) en la hoja; (u, v) = (este, norte) en el terreno.
  const aUV = [(a, b) => [a, b], (a, b) => [1 - b, a], (a, b) => [1 - a, 1 - b], (a, b) => [b, 1 - a]];
  const uvA = [(u, v) => [u, v], (u, v) => [v, 1 - u], (u, v) => [1 - u, 1 - v], (u, v) => [1 - v, u]];
  MT.vistas.aUV = aUV; MT.vistas.uvA = uvA;

  // Distancia euclidiana (en celdas) de cada punto del mar a la tierra más cercana.
  function edt1(f, n, d, v, z) {
    let k = 0; v[0] = 0; z[0] = -Infinity; z[1] = Infinity;
    for (let q = 1; q < n; q++) {
      let s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]);
      while (s <= z[k]) { k--; s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]); }
      k++; v[k] = q; z[k] = s; z[k + 1] = Infinity;
    }
    k = 0;
    for (let q = 0; q < n; q++) { while (z[k + 1] < q) k++; d[q] = (q - v[k]) * (q - v[k]) + f[v[k]]; }
  }
  MT.vistas.campoAgua = function (T) {
    if (T._agua) return T._agua;
    const N = T.G, INF = 1e12, g = new Float64Array(N * N);
    const agua = T.hidro ? T.hidro.agua : null;
    for (let i = 0; i < N * N; i++) g[i] = (agua ? !agua[i] : !T.mar || T.h[i] > T.umbralMar) ? 0 : INF;
    const f = new Float64Array(N), d = new Float64Array(N), v = new Int32Array(N), z = new Float64Array(N + 1);
    for (let x = 0; x < N; x++) { for (let y = 0; y < N; y++) f[y] = g[y * N + x]; edt1(f, N, d, v, z); for (let y = 0; y < N; y++) g[y * N + x] = d[y]; }
    for (let y = 0; y < N; y++) { for (let x = 0; x < N; x++) f[x] = g[y * N + x]; edt1(f, N, d, v, z); for (let x = 0; x < N; x++) g[y * N + x] = d[x]; }
    const h = new Float32Array(N * N); for (let i = 0; i < N * N; i++) h[i] = Math.sqrt(g[i]);
    T._agua = { G: N, h };
    return T._agua;
  };
  // líneas de agua: cada vez más separadas mar adentro (en mm de papel, para un lado de S mm)
  MT.vistas.lineasAgua = function (T, S, k = 8) {
    const C = MT.vistas.campoAgua(T), mmCelda = S / (T.G - 1), out = [];
    for (let j = 1; j <= k; j++) out.push(...MT.vistas.isolineas(C, (0.7 * Math.pow(j, 1.3)) / mmCelda));
    return out;
  };

  // A · Isolíneas por marching squares sobre la rejilla del terreno, ya encadenadas en
  // polilíneas (u, v). `nivel` en altura normalizada.
  MT.vistas.isolineas = function (T, nivel) {
    const N = T.G, h = T.h, M = N - 1;
    const segs = [], porArista = new Map();
    const H = (i, j) => j * N + i, Vt = (i, j) => N * N + j * N + i; // aristas horizontales y verticales
    const pon = (e1, e2) => {
      const k = segs.length; segs.push([e1, e2]);
      for (const e of [e1, e2]) { const l = porArista.get(e); if (l) l.push(k); else porArista.set(e, [k]); }
    };
    for (let j = 0; j < M; j++) {
      for (let i = 0; i < M; i++) {
        const c0 = h[j * N + i], c1 = h[j * N + i + 1], c2 = h[(j + 1) * N + i + 1], c3 = h[(j + 1) * N + i];
        const caso = (c0 >= nivel) | ((c1 >= nivel) << 1) | ((c2 >= nivel) << 2) | ((c3 >= nivel) << 3);
        if (caso === 0 || caso === 15) continue;
        const e0 = H(i, j), e1 = Vt(i + 1, j), e2 = H(i, j + 1), e3 = Vt(i, j);
        const centro = (c0 + c1 + c2 + c3) / 4 >= nivel;
        switch (caso) {
          case 1: case 14: pon(e3, e0); break;
          case 2: case 13: pon(e0, e1); break;
          case 3: case 12: pon(e3, e1); break;
          case 4: case 11: pon(e1, e2); break;
          case 6: case 9: pon(e0, e2); break;
          case 7: case 8: pon(e3, e2); break;
          case 5: if (centro) { pon(e0, e1); pon(e2, e3); } else { pon(e3, e0); pon(e1, e2); } break;
          case 10: if (centro) { pon(e3, e0); pon(e1, e2); } else { pon(e0, e1); pon(e2, e3); } break;
        }
      }
    }
    const punto = (e) => {
      let i, j, a, b, di, dj;
      if (e < N * N) { j = Math.floor(e / N); i = e % N; di = 1; dj = 0; }
      else { e -= N * N; j = Math.floor(e / N); i = e % N; di = 0; dj = 1; }
      a = h[j * N + i]; b = h[(j + dj) * N + i + di];
      const t = b === a ? 0.5 : (nivel - a) / (b - a);
      return [(i + di * t) / M, (j + dj * t) / M];
    };
    // encadenar: primero las que empiezan en la orilla (abiertas), luego los anillos
    const usado = new Uint8Array(segs.length), lineas = [];
    const camina = (k0, desde) => {
      const lin = [desde]; let k = k0, e = desde;
      while (k !== -1 && !usado[k]) {
        usado[k] = 1;
        const otra = segs[k][0] === e ? segs[k][1] : segs[k][0];
        lin.push(otra); e = otra;
        const l = porArista.get(e); k = -1;
        if (l) for (const q of l) if (!usado[q]) { k = q; break; }
      }
      return lin.map(punto);
    };
    for (const [e, l] of porArista) if (l.length === 1 && !usado[l[0]]) lineas.push(camina(l[0], e));
    for (let k = 0; k < segs.length; k++) if (!usado[k]) lineas.push(camina(k, segs[k][0]));
    return lineas.filter((l) => l.length > 2);
  };

  // B · Crestas apiladas. Horizonte flotante: se dibuja de adelante hacia atrás y cada
  // perfil sólo deja tinta donde asoma por encima de todo lo que ya está dibujado.
  MT.vistas.crestas = function (T, P) {
    const { L, W, Y0, D, p, n, step, rot, top } = P;
    const cx = L + W / 2, bins = Math.floor(W / step) + 1;
    const toUV = aUV[rot], toA = uvA[rot];

    // perspectiva suave: atrás los perfiles se angostan y se juntan
    const rows = [], gN = 1 - (1 - p) / 2;
    for (let r = 0; r < n; r++) {
      const t = r / (n - 1), s = 1 - (1 - p) * t;
      rows.push({ t, s, yb: Y0 - D * (t - (1 - p) * t * t / 2) / gN });
    }

    // escala vertical: lo que pida la lámina, sin salirse por arriba
    let hv = P.H;
    if (P.hvFijo) hv = Infinity; // la escala la impone quien llama (p. ej. la formación)
    for (const R of rows) {
      let mx = 0;
      for (let k = 0; k <= 160; k++) { const [u, v] = toUV(k / 160, R.t); mx = Math.max(mx, T.sample(u, v)); }
      if (mx > 0) hv = Math.min(hv, (R.yb - top) / (mx * R.s));
    }
    hv = Math.min(hv, (T.exagMax || Infinity) * W / (T.anchoKm * 1000) * T.relieve); // exageración con tope
    if (P.hvFijo) hv = P.hvFijo;

    const hor = new Float32Array(bins).fill(Infinity), yRow = new Float32Array(bins);
    const snaps = [], strokes = [], altitudes = new WeakMap(), altitudEn = new WeakMap();
    for (let r = 0; r < n; r++) {
      const R = rows[r], old = hor.slice(); snaps.push(old);
      const segs = []; let cur = null, pv = null, px = 0, py = 0, pd = 0;
      for (let i = 0; i < bins; i++) {
        const x = L + i * step, a = (x - cx) / (W * R.s) + 0.5;
        if (a < 0 || a > 1) { yRow[i] = Infinity; if (cur) { segs.push(cur); cur = null; } pv = null; continue; }
        const [u, v] = toUV(a, R.t);
        const y = R.yb - T.sample(u, v) * hv * R.s; yRow[i] = y;
        const d = y - old[i], vis = d < -1e-4;
        if (pv !== null && vis !== pv) { // cruce con el horizonte: cortar en el punto exacto
          const f = (old[i] === Infinity || old[i - 1] === Infinity) ? (vis ? 1 : 0) : pd / (pd - d);
          const q = [px + (x - px) * f, py + (y - py) * f];
          if (pv) { cur.push(q); segs.push(cur); cur = null; } else cur = [q];
        }
        if (vis) { if (!cur) cur = []; cur.push([x, y]); }
        pv = vis; px = x; py = y; pd = d;
      }
      if (cur) segs.push(cur);
      for (let i = 0; i < bins; i++) if (yRow[i] < hor[i]) hor[i] = yRow[i];
      if (r % 2 === 1) { segs.reverse(); segs.forEach((s) => s.reverse()); } // bustrofedón: menos viaje en alto
      for (const s of segs) if (s.length > 1) {
        const pts = MT.simplifica(s, 0.02);
        const altura = ([x]) => {
          const a = (x - cx) / (W * R.s) + 0.5, hn = T.sample(...toUV(a, R.t));
          return T.mar && hn <= T.umbralMar ? 0 : T.alt(hn);
        };
        altitudes.set(pts, pts.map(altura)); altitudEn.set(pts, altura);
        pts.fila = r; strokes.push(pts); // la fila: el panorama del atlas la usa para la bruma
      }
    }

    const linea = (r, a) => {
      const R = rows[r], [u, v] = toUV(a, R.t), h = T.sample(u, v);
      return [cx + (a - 0.5) * W * R.s, R.yb - h * hv * R.s, h];
    };
    // dónde cae un punto del terreno en la hoja, y si se alcanza a ver
    function proyecta(u, v) {
      const [a, b] = toA(u, v), r = Math.round(b * (n - 1));
      const [x, y] = linea(r, a), i = Math.round((x - L) / step), o = snaps[r];
      let vis = i >= 1 && i < bins - 1;
      if (vis) for (let k = i - 1; k <= i + 1; k++) if (!(y < o[k] - 0.4)) vis = false;
      return { x, y, vis, r };
    }
    // lo más alto (en la hoja) del dibujo terminado entre x0 y x1
    function silueta(x0, x1) {
      let m = Infinity;
      const i0 = Math.max(0, Math.floor((x0 - L) / step)), i1 = Math.min(bins - 1, Math.ceil((x1 - L) / step));
      for (let i = i0; i <= i1; i++) if (hor[i] < m) m = hor[i];
      return m;
    }
    const frente = []; for (let k = 0; k <= 400; k++) frente.push(linea(0, k / 400));

    // D · malla: además de los perfiles, líneas de a constante que corren hacia el fondo
    const columnas = [];
    const nH = 300, fino = [];
    const fila = (t) => { const s = 1 - (1 - p) * t; return { s, yb: Y0 - D * (t - (1 - p) * t * t / 2) / gN }; };
    {
      const hf = new Float32Array(bins).fill(Infinity), yR = new Float32Array(bins);
      for (let r = 0; r < nH; r++) {
        const t = r / (nH - 1), F = fila(t); fino.push(hf.slice());
        for (let i = 0; i < bins; i++) {
          const x = L + i * step, a = (x - cx) / (W * F.s) + 0.5;
          if (a < 0 || a > 1) { yR[i] = Infinity; continue; }
          yR[i] = F.yb - T.sample(...toUV(a, t)) * hv * F.s;
        }
        for (let i = 0; i < bins; i++) if (yR[i] < hf[i]) hf[i] = yR[i];
      }
    }
    // un punto del terreno en su lugar exacto (no en la fila más cercana) y si se ve
    const exacto = (a, t) => {
      const F = fila(t), x = cx + (a - 0.5) * W * F.s, y = F.yb - T.sample(...toUV(a, t)) * hv * F.s;
      const i = Math.round((x - L) / step), o = fino[Math.max(0, Math.floor(t * (nH - 1)) - 3)];
      let vis = true;
      for (let q = Math.max(0, i - 1); q <= Math.min(bins - 1, i + 1); q++) if (!(y < o[q] - 0.15)) vis = false;
      return { x, y, vis };
    };
    // cualquier línea del terreno (u, v) tendida sobre los perfiles: tramos visibles
    const drape = (pts) => {
      const out = []; let cur = [];
      for (const [u, v] of pts) {
        const [a, t] = toA(u, v), e = exacto(a, t);
        if (e.vis) cur.push([e.x, e.y]); else { if (cur.length > 1) out.push(cur); cur = []; }
      }
      if (cur.length > 1) out.push(cur);
      return out;
    };
    if (P.nC > 1) {
      const altPunto = new WeakMap();
      for (let c = 0; c < P.nC; c++) {
        const a = c / (P.nC - 1), segs = []; let cur = [];
        for (let k = 0; k <= 500; k++) {
          const t = k / 500, F = fila(t), hn = T.sample(...toUV(a, t)), x = cx + (a - 0.5) * W * F.s, y = F.yb - hn * hv * F.s;
          const i = Math.round((x - L) / step), o = fino[Math.max(0, Math.floor(t * (nH - 1)) - 3)];
          let vis = true;
          for (let q = Math.max(0, i - 1); q <= Math.min(bins - 1, i + 1); q++) if (!(y < o[q] - 0.15)) vis = false;
          if (vis) {
            const pt = [x, y]; altPunto.set(pt, T.mar && hn <= T.umbralMar ? 0 : T.alt(hn)); cur.push(pt);
          } else { if (cur.length > 1) segs.push(cur); cur = []; }
        }
        if (cur.length > 1) segs.push(cur);
        if (c % 2 === 1) { segs.reverse(); segs.forEach((q) => q.reverse()); }
        for (const q of segs) {
          const pts = MT.simplifica(q, 0.02);
          altitudes.set(pts, pts.map((pt) => altPunto.get(pt))); columnas.push(pts);
        }
      }
    }
    return {
      strokes, columnas, altitudes, altitudEn, drape, rows, hv, proyecta, silueta, linea, frente, xmin: L, xmax: L + W,
      exag: (hv / T.relieve) / (W / (T.anchoKm * 1000)),
      espaciado: T.anchoKm * 1000 / (n - 1),
    };
  };

  // Recorre una fila contra el horizonte flotante: devuelve los tramos que asoman,
  // cortados en el cruce exacto. yAt(i) = y en la hoja o null si la fila no pasa por ahí.
  function tramosVisibles(bins, x0, step, old, yAt, yRow) {
    const segs = []; let cur = null, pv = null, px = 0, py = 0, pd = 0;
    for (let i = 0; i < bins; i++) {
      const x = x0 + i * step, y = yAt(i);
      if (y === null) { yRow[i] = Infinity; if (cur) { segs.push(cur); cur = null; } pv = null; continue; }
      yRow[i] = y;
      const d = y - old[i], vis = d < -1e-4;
      if (pv !== null && vis !== pv) {
        const f = (old[i] === Infinity || old[i - 1] === Infinity) ? (vis ? 1 : 0) : pd / (pd - d);
        const q = [px + (x - px) * f, py + (y - py) * f];
        if (pv) { cur.push(q); segs.push(cur); cur = null; } else cur = [q];
      }
      if (vis) { if (!cur) cur = []; cur.push([x, y]); }
      pv = vis; px = x; py = y; pd = d;
    }
    if (cur) segs.push(cur);
    return segs;
  }

  // C · Bloque diagrama. Axonometría: (a, b, h) → O + a·U + b·V − h·Hv. La esquina (0,0)
  // es la más cercana; cada columna de la hoja mira hacia a y b crecientes, así que las
  // secciones de b constante, de adelante hacia atrás, sirven al horizonte flotante.
  // B: {O, U, V, S, Hv, grueso (mm), n, rot, step, modo: 'secciones'|'curvas', niveles: [{hn, maestra}]}
  MT.vistas.bloque = function (T, B) {
    const toUV = aUV[B.rot], toA = uvA[B.rot];
    const hAB = (a, b) => T.sample(...toUV(a, b));
    const P = (a, b, h) => [B.O[0] + a * B.U[0] + b * B.V[0], B.O[1] + a * B.U[1] + b * B.V[1] - h * B.Hv];
    const Pb = (a, b) => { const p = P(a, b, 0); return [p[0], p[1] + B.grueso]; };
    const xmin = B.O[0] + B.V[0], xmax = B.O[0] + B.U[0], step = B.step;
    const bins = Math.floor((xmax - xmin) / step) + 1;
    const filaY = (b) => (i) => {
      const x = xmin + i * step, a = (x - B.O[0] - b * B.V[0]) / B.U[0];
      if (a < -1e-9 || a > 1 + 1e-9) return null;
      return P(a, b, hAB(Math.min(1, Math.max(0, a)), b))[1];
    };

    // horizonte fino (para saber qué se ve) y, si toca, las secciones que se dibujan
    const nH = 260, snaps = [], hor = new Float32Array(bins).fill(Infinity), yRow = new Float32Array(bins);
    const secc = [], nS = B.modo === 'secciones' || B.modo === 'malla' ? B.n : 0, filas = [];
    for (let r = 0; r < nH; r++) filas.push({ b: r / (nH - 1), dibuja: false });
    for (let k = 0; k < nS; k++) filas.push({ b: k / (nS - 1), dibuja: true, k });
    filas.sort((p, q) => p.b - q.b || (p.dibuja ? -1 : 1));
    for (const f of filas) {
      const old = f.dibuja ? hor : hor.slice();
      if (!f.dibuja) snaps.push(old);
      const segs = tramosVisibles(bins, xmin, step, old, filaY(f.b), yRow);
      if (f.dibuja) {
        if (f.k % 2 === 1) { segs.reverse(); segs.forEach((s) => s.reverse()); }
        for (const s of segs) if (s.length > 1) secc.push(MT.simplifica(s, 0.02));
      } else for (let i = 0; i < bins; i++) if (yRow[i] < hor[i]) hor[i] = yRow[i];
    }

    const visible = (a, b, h) => {
      const [x, y] = P(a, b, h), i = Math.round((x - xmin) / step);
      // el horizonte de unas filas antes: la fila vecina queda a décimas de mm y lo taparía todo
      const o = snaps[Math.max(0, Math.min(nH - 1, Math.floor(b * (nH - 1)) - 3))];
      for (let k = Math.max(0, i - 1); k <= Math.min(bins - 1, i + 1); k++) if (!(y < o[k] - 0.15)) return false;
      return true;
    };
    const tramos = (pts3) => { // [a,b,h] → tramos visibles en la hoja
      const out = []; let cur = [];
      for (const [a, b, h] of pts3) {
        if (visible(a, b, h)) cur.push(P(a, b, h)); else { if (cur.length > 1) out.push(cur); cur = []; }
      }
      if (cur.length > 1) out.push(cur);
      return out;
    };
    const borde = (fa, fb, k = 300) => Array.from({ length: k + 1 }, (_, j) => { const t = j / k, a = fa(t), b = fb(t); return [a, b, hAB(a, b)]; });

    // la caja: base, aristas verticales y los dos filos delanteros del terreno (siempre a la vista)
    const caja = [
      [Pb(1, 0), Pb(0, 0), Pb(0, 1)],
      [Pb(0, 1), P(0, 1, hAB(0, 1))],
      [Pb(0, 0), P(0, 0, hAB(0, 0))],
      [Pb(1, 0), P(1, 0, hAB(1, 0))],
    ];
    const bordeIzq = MT.simplifica(borde(() => 0, (t) => 1 - t).map(([a, b, h]) => P(a, b, h)), 0.02);
    const bordeDer = MT.simplifica(borde((t) => t, () => 0).map(([a, b, h]) => P(a, b, h)), 0.02);
    const fondoDer = tramos(borde(() => 1, (t) => t)).map((t) => MT.simplifica(t, 0.02));

    // curvas de nivel sobre la superficie, y su huella en las caras del bloque
    const curvas = [], estratos = [];
    if (B.modo === 'curvas') {
      for (const nv of B.niveles) {
        for (const l of MT.vistas.isolineas(T, nv.hn)) {
          const pts = MT.simplifica(l.map(([u, v]) => toA(u, v)), 0.0012).map(([a, b]) => [a, b, nv.hn]);
          for (const t of tramos(pts)) curvas.push({ maestra: nv.maestra, nivel: nv.m, pts: t });
        }
      }
    }
    for (const nv of B.niveles || []) {
      if (!nv.maestra) continue;
      for (const [fa, fb] of [[(t) => t, () => 0], [() => 0, (t) => t]]) {
        let cur = [];
        for (let j = 0; j <= 300; j++) {
          const t = j / 300, a = fa(t), b = fb(t);
          if (hAB(a, b) >= nv.hn) cur.push(P(a, b, nv.hn)); else { if (cur.length > 1) estratos.push(cur); cur = []; }
        }
        if (cur.length > 1) estratos.push(cur);
      }
    }
    // malla: la otra familia de líneas, de a constante, sólo lo que asoma
    const cols = [];
    if (B.modo === 'malla') {
      for (let c = 0; c < B.nC; c++) {
        const a = c / (B.nC - 1);
        let ts = tramos(borde(() => a, (t) => t, 400)).map((q) => MT.simplifica(q, 0.02));
        if (c % 2 === 1) { ts.reverse(); ts = ts.map((q) => q.reverse()); }
        cols.push(...ts);
      }
    }
    // líneas de agua sobre el mar (sólo en modo curvas: en secciones el mar ya es trama)
    const agua = [];
    if (B.agua && B.modo === 'curvas') {
      for (const l of B.agua) {
        const pts = MT.simplifica(l.map(([u, v]) => toA(u, v)), 0.0012).map(([a, b]) => [a, b, 0]);
        agua.push(...tramos(pts));
      }
    }
    // perfil contra el cielo (en modo curvas no hay secciones que lo dibujen)
    const cielo = [];
    {
      let cur = [];
      for (let i = 0; i < bins; i++) {
        if (hor[i] === Infinity) { if (cur.length > 1) cielo.push(cur); cur = []; continue; }
        cur.push([xmin + i * step, hor[i]]);
      }
      if (cur.length > 1) cielo.push(cur);
    }

    function proyecta(u, v) {
      const [a, b] = toA(u, v), h = hAB(a, b), [x, y] = P(a, b, h);
      return { x, y, vis: visible(a, b, h) };
    }
    function silueta(x0, x1) {
      let m = Infinity;
      const i0 = Math.max(0, Math.floor((x0 - xmin) / step)), i1 = Math.min(bins - 1, Math.ceil((x1 - xmin) / step));
      for (let i = i0; i <= i1; i++) if (hor[i] < m) m = hor[i];
      return m;
    }
    // el filo delantero completo (izquierdo y derecho), para rotular cañones
    const frente = [...borde(() => 0, (t) => 1 - t), ...borde((t) => t, () => 0)].map(([a, b, h]) => [...P(a, b, h), h]);
    return {
      secc, cols, agua, caja, bordeIzq, bordeDer, fondoDer, curvas, estratos, cielo: cielo.map((c) => MT.simplifica(c, 0.02)),
      P, Pb, hAB, proyecta, silueta, frente, xmin, xmax, hv: B.Hv, S: B.S,
      drape: (pts) => tramos(pts.map(([u, v]) => { const [a, b] = toA(u, v); return [a, b, hAB(a, b)]; })),
      exag: (B.Hv / T.relieve) / (B.S / (T.anchoKm * 1000)),
      espaciado: B.n ? T.anchoKm * 1000 / (B.n - 1) : null,
    };
  };
})(typeof globalThis !== 'undefined' ? globalThis : window);
