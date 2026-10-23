// visor.js — la montaña se forma por eras y luego la pluma la pasa en limpio, como plotter.
// Baja la lámina en SVG (para plotear), PNG (A4 a 300 dpi) y GIF (todo el proceso).
(function () {
  const MT = window.MT;
  const lienzo = document.getElementById('papel'), cabeza = document.getElementById('cabeza');
  const ctx = lienzo.getContext('2d'), hctx = cabeza.getContext('2d');
  const info = document.getElementById('info'), estado = info.querySelector('.estado');
  const q = new URLSearchParams(location.search);
  const ARQS = Object.keys(MT.ARQUETIPOS);
  const OPC = ['registro', 'arq', 'rot', 'hoja', 'planta', 'tanaka', 'oscuro', 'hipso', 'realismo', 'lang', 'malla', 'modo'];
  const est = { s: q.get('s') || nuevaSemilla(), eras: q.get('eras') !== '0' };
  for (const k of OPC) est[k] = q.get(k);
  // modo película: sin interfaz, cuadro de tamaño fijo y un reloj que manda el capturador
  // (herramientas/pelicula.js). ?pelicula=1&cuadro=1920x1080&dur=12&foco=cx,cy,ancho&ficha=0
  const PELI = q.get('pelicula') === '1';
  const [CW, CH] = (q.get('cuadro') || '1920x1080').split('x').map(Number);
  const FOCO = q.get('foco') ? q.get('foco').split(',').map(Number) : null; // en fracciones de la hoja
  const FICHA = q.get('ficha');
  const DURACION = PELI && +q.get('dur') > 0 ? +q.get('dur') : 10; // segundos que tarda en trazarse una lámina completa
  const BAJAR = 3;         // mm de tinta que "cuesta" bajar la pluma: cada trazo nuevo tarda algo
  const N_ERAS = 18;       // cuadros de la formación
  const MS_ERA = 110;      // mínimo por cuadro de formación
  const FANTASMA = 0.22;   // cuánto se ve la montaña formada debajo de la pluma

  let Lm = null, esc = 1, ox = 0, oy = 0, base = [1, 0, 0], dpr = 1, turno = 0;
  let cur = null, vel = 1, ultimo = 0, pausa = false;
  let eras = [], fantasma = null; // cuadros de la formación y el relieve que queda de fondo

  function nuevaSemilla() { return String(Math.floor(Math.random() * 1e6)); }
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));

  async function generar() {
    const yo = ++turno;
    estado.textContent = est.lang === 'en' ? 'raising the terrain…' : 'levantando terreno…';
    ayuda();
    cur = null; eras = []; fantasma = null;
    await espera(20);
    Lm = MT.lamina(est.s, Object.fromEntries(OPC.map((k) => [k, est[k]])));
    const p = new URLSearchParams({ s: est.s });
    for (const k of OPC) if (est[k] != null) p.set(k, est[k]);
    if (!est.eras) p.set('eras', '0');
    history.replaceState(null, '', '?' + p);
    document.body.style.background = Lm.papel;
    document.documentElement.style.setProperty('--tinta', Lm.plumas[1]); document.documentElement.style.setProperty('--papel', Lm.papel); if (typeof ficha !== 'undefined' && ficha) ficha.hidden = true;
    let total = 0;
    for (const t of Lm.trazos) for (let i = 1; i < t.pts.length; i++) total += Math.hypot(t.pts[i][0] - t.pts[i - 1][0], t.pts[i][1] - t.pts[i - 1][1]);
    vel = (total + BAJAR * Lm.trazos.length) / DURACION;
    const m = Lm.meta;
    const en = est.lang === 'en', T_ = (x) => MT.traduce(String(x).toUpperCase(), en ? 'en' : 'es').toLowerCase();
    const HOJA_EN = { crestas: 'profiles', curvas: 'contour lines', lado: 'diptych', torre: 'sheet with projections', bloque: 'block diagram', proyeccion: 'block and projected plan', secuencia: 'history in four stages', corte: 'section A–A′' };
    const REG_EN = { carto: 'cartographic', lamina: 'plate', obra: 'artwork' };
    const texto = en
      ? `seed ${Lm.seed} · ${T_(m.nombre)} · ${HOJA_EN[m.hoja]} · ${REG_EN[m.registro]} · view from the ${T_(m.desde)}`
      : `semilla ${Lm.seed} · ${m.nombre.toLowerCase()} · ${MT.NOMBRE_HOJA[m.hoja]} · ${MT.NOMBRE_REGISTRO[m.registro]} · vista desde el ${m.desde.toLowerCase()}`;
    encuadra();
    if (PELI) {
      // la formación se calcula entera antes de que el reloj empiece
      if (est.eras && MT.formable(Lm)) {
        for (let k = 0; k < N_ERAS; k++) { eras.push(MT.formaCuadro(est.s, Lm, k / (N_ERAS - 1))); await espera(0); if (yo !== turno) return; }
        fantasma = eras[eras.length - 1].trazos.filter((t) => t.pluma !== Lm.plumas.length - 1);
      }
      peli.eras = eras.length ? (N_ERAS * MS_ERA + 500) / 1000 : 0;
      peli.total = peli.eras + DURACION + (FICHA != null ? 6 : 0); peli.cam = '';
      peli.hecho = -1; cur = null;
      peli.ir(0); peli.listo = true;
      return;
    }
    // la formación: cada cuadro se calcula y se muestra en cuanto está listo
    if (est.eras && MT.formable(Lm)) {
      for (let k = 0; k < N_ERAS; k++) {
        const t0 = performance.now();
        const c = MT.formaCuadro(est.s, Lm, k / (N_ERAS - 1));
        if (yo !== turno) return;
        eras.push(c);
        estado.textContent = `${texto} · formándose`;
        fondo(); dibuja(ctx, c.trazos, X, Y);
        await espera(Math.max(0, MS_ERA - (performance.now() - t0)));
        if (yo !== turno) return;
      }
      fantasma = eras[eras.length - 1].trazos.filter((t) => t.pluma !== Lm.plumas.length - 1);
      await espera(500);
      if (yo !== turno) return;
    }
    estado.textContent = texto;
    repetir();
  }

  // la ayuda en el idioma del lector
  const AYUDA = {
    es: info.querySelector('.teclas').textContent,
    en: 'Esc atlas · R another · ←→ neighbor seed · A landform · L sheet · M register (map↔artwork) · D viewpoint · P contours or hachures · I illuminated contours · O dark paper · C hypsometric tints · Z no realism · N español · E formation by eras · T draw again · F finish · space pause · download: V SVG (plotter) · B PNG · G GIF · H hide',
  };
  function ayuda() { info.querySelector('.teclas').textContent = AYUDA[est.lang === 'en' ? 'en' : 'es']; document.documentElement.lang = est.lang === 'en' ? 'en' : 'es-MX'; }

  function encuadra() {
    dpr = PELI ? 1 : window.devicePixelRatio || 1;
    const W = PELI ? CW : innerWidth, H = PELI ? CH : innerHeight;
    for (const c of [lienzo, cabeza]) { c.width = W * dpr; c.height = H * dpr; c.style.width = W + 'px'; c.style.height = H + 'px'; }
    if (PELI) { // el escenario mide el cuadro; en una ventana de otro tamaño sólo se escala para verlo
      const f = Math.min(innerWidth / CW, innerHeight / CH);
      Object.assign(document.body.style, { width: CW + 'px', height: CH + 'px', transformOrigin: '0 0', transform: `translate(${(innerWidth - CW * f) / 2}px, ${(innerHeight - CH * f) / 2}px) scale(${f})` });
    }
    if (!Lm) return;
    if (FOCO) { // acercamiento: el centro (cx, cy) y el ancho visible, en fracciones de la hoja
      const [cx, cy, a] = FOCO;
      esc = W / (a * Lm.page.w);
      ox = W / 2 - cx * Lm.page.w * esc; oy = H / 2 - cy * Lm.page.h * esc;
      base = [esc, ox, oy];
      return;
    }
    const m = PELI ? 0.9 : 0.96;
    esc = Math.min((W * m) / Lm.page.w, (H * m) / Lm.page.h);
    ox = (W - Lm.page.w * esc) / 2; oy = (H - Lm.page.h * esc) / 2;
    base = [esc, ox, oy];
  }

  const X = (x) => (ox + x * esc) * dpr, Y = (y) => (oy + y * esc) * dpr;

  function dibuja(c, trazos, fx, fy) {
    for (const t of trazos) {
      c.strokeStyle = Lm.plumas[t.pluma]; c.beginPath();
      c.moveTo(fx(t.pts[0][0]), fy(t.pts[0][1]));
      for (let i = 1; i < t.pts.length; i++) c.lineTo(fx(t.pts[i][0]), fy(t.pts[i][1]));
      c.stroke();
    }
  }

  // papel (y, si la montaña se formó, su fantasma debajo)
  function papel(c, ancho, alto, s, fx, fy) {
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.fillStyle = Lm.papel; c.fillRect(0, 0, ancho, alto);
    c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = s;
    if (fantasma) { c.globalAlpha = FANTASMA; dibuja(c, fantasma, fx, fy); c.globalAlpha = 1; }
  }
  // en película, al acercarse la línea engorda menos que la escala: se sigue leyendo como pluma fina
  const fondo = () => papel(ctx, lienzo.width, lienzo.height, Math.max(0.6, 0.28 * dpr * (PELI ? base[0] * Math.pow(esc / base[0], 0.45) : esc)), X, Y);

  // dibuja desde el cursor hasta consumir `dist` mm de tinta
  function avanza(c, k, dist, fx, fy) {
    while (dist > 0 && k.t < Lm.trazos.length) {
      if (k.espera > 0) { const qq = Math.min(dist, k.espera); k.espera -= qq; dist -= qq; if (k.espera > 0) break; }
      const tr = Lm.trazos[k.t], pts = tr.pts;
      c.strokeStyle = Lm.plumas[tr.pluma];
      c.beginPath();
      let [x, y] = k.p;
      c.moveTo(fx(x), fy(y));
      while (dist > 0 && k.i < pts.length - 1) {
        const [bx, by] = pts[k.i + 1], l = Math.hypot(bx - x, by - y);
        if (l <= dist) { dist -= l; x = bx; y = by; k.i++; }
        else { const f = dist / l; x += (bx - x) * f; y += (by - y) * f; dist = 0; }
        c.lineTo(fx(x), fy(y));
      }
      c.stroke();
      k.p = [x, y];
      if (k.i >= pts.length - 1) { k.t++; k.i = 0; k.espera = BAJAR; if (k.t < Lm.trazos.length) k.p = Lm.trazos[k.t].pts[0]; }
    }
  }
  const cursor = () => ({ t: 0, i: 0, p: Lm.trazos[0].pts[0], espera: 0 });

  function pintaCabeza() {
    hctx.setTransform(1, 0, 0, 1, 0, 0);
    hctx.clearRect(0, 0, cabeza.width, cabeza.height);
    if (!cur || cur.t >= Lm.trazos.length) return;
    hctx.strokeStyle = Lm.plumas[Lm.trazos[cur.t].pluma];
    hctx.lineWidth = 1.2 * dpr;
    hctx.beginPath(); hctx.arc(X(cur.p[0]), Y(cur.p[1]), 3.2 * dpr, 0, Math.PI * 2); hctx.stroke();
  }

  function repetir() { fondo(); cur = cursor(); ultimo = performance.now(); }
  function completo() { if (!Lm) return; fondo(); cur = cursor(); avanza(ctx, cur, Infinity, X, Y); pintaCabeza(); }

  function cuadro(ahora) {
    const dt = Math.min(0.1, (ahora - ultimo) / 1000); ultimo = ahora;
    if (!PELI && Lm && cur && !pausa && cur.t < Lm.trazos.length) { avanza(ctx, cur, vel * dt, X, Y); pintaCabeza(); }
    requestAnimationFrame(cuadro);
  }

  // ── el reloj de la película: peli.ir(t) deja la lámina como va en el segundo t.
  // Hacia adelante sólo agrega tinta; hacia atrás vuelve a trazar desde cero.
  const peli = { listo: false, eras: 0, total: 0, hecho: -1, ir(t) {
    if (!Lm) return;
    peli.t = t;
    if (t < peli.eras) { // formación: un cuadro por era, sin fantasma
      const k = Math.min(eras.length - 1, Math.floor((t * 1000) / MS_ERA)), f = fantasma;
      fantasma = null; fondo(); dibuja(ctx, eras[k].trazos, X, Y); fantasma = f;
      peli.hecho = -1; hctx.clearRect(0, 0, cabeza.width, cabeza.height); ficha.hidden = true;
      return;
    }
    // la cámara: sigue su camino (cam=) mientras la pluma traza; con ficha, al final se acerca
    // al nombre y luego se abre su ficha
    const e = FICHA != null ? fichaPedida() : null;
    const u = e ? suave((t - peli.eras - DURACION - 0.3) / ACERCA_S) : 0;
    let v = camino(Math.max(0, (t - peli.eras) / DURACION)); // u > 1: la pluma ya terminó y la cámara recorre la lámina
    if (u > 0) v = mezclaVista(v, [(e.caja[0] + e.caja[2]) / 2 / Lm.page.w, (e.caja[1] + e.caja[3]) / 2 / Lm.page.h, ACERCA, ...ANCLA], u);
    const cam = aEncuadre(v), clave = cam.join();
    if (clave !== peli.cam) { // la cámara se movió: toda la tinta se vuelve a dibujar con el nuevo encuadre
      peli.cam = clave;
      [esc, ox, oy] = cam;
      peli.hecho = -1;
    }
    const d = vel * Math.min(DURACION, t - peli.eras);
    if (peli.hecho < 0 || d < peli.hecho) { fondo(); cur = cursor(); peli.hecho = 0; }
    avanza(ctx, cur, d - peli.hecho, X, Y); peli.hecho = d;
    pintaCabeza();
    if (e && u >= 1 && t >= peli.eras + DURACION + 0.6 + ACERCA_S) {
      abreFicha(e);
      const [x0, y0, x1, y1] = e.caja, pad = 1.2;
      hctx.strokeStyle = Lm.plumas[Lm.plumas.length - 1]; hctx.lineWidth = 2;
      hctx.strokeRect(X(x0 - pad), Y(y0 - pad), X(x1 + pad) - X(x0 - pad), Y(y1 + pad) - Y(y0 - pad));
    } else ficha.hidden = true;
  } };
  const ANCLA = (q.get('ancla') || '0.3,0.55').split(',').map(Number); // dónde del cuadro queda el nombre al acercarse
  const ACERCA_S = 1.8, ACERCA = +q.get('acerca') || 0.5; // segundos del acercamiento; ancho visible al final, en fracción de la hoja
  const suave = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  // Una vista es [cx, cy, ancho, ax, ay]: el punto (cx, cy) de la hoja (en fracciones) queda en
  // el punto (ax, ay) del cuadro, y se ve `ancho` veces el ancho de la hoja. ancho 0 = la hoja entera.
  // cam=u,cx,cy,ancho;u,cx,cy,ancho… con u la fracción del trazo (0 empieza la pluma, 1 termina;
  // más de 1 es el recorrido después, en duraciones de pluma).
  const CAM = (q.get('cam') || '').split(';').filter(Boolean).map((k) => k.split(',').map(Number)).sort((a, b) => a[0] - b[0]);
  const anchoBase = () => CW / (base[0] * Lm.page.w);
  const vistaBase = () => [(CW / 2 - base[1]) / base[0] / Lm.page.w, (CH / 2 - base[2]) / base[0] / Lm.page.h, anchoBase(), 0.5, 0.5];
  const deClave = ([, cx, cy, w]) => [cx, cy, w > 0 ? w : anchoBase(), 0.5, 0.5];
  function mezclaVista(a, b, u) { // el punto viaja derecho; la escala cambia en proporción constante
    return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] * Math.pow(b[2] / a[2], u), a[3] + (b[3] - a[3]) * u, a[4] + (b[4] - a[4]) * u];
  }
  function camino(u) {
    if (!CAM.length) return vistaBase();
    if (u <= CAM[0][0]) return deClave(CAM[0]);
    for (let i = 1; i < CAM.length; i++) if (u <= CAM[i][0]) return mezclaVista(deClave(CAM[i - 1]), deClave(CAM[i]), suave((u - CAM[i - 1][0]) / (CAM[i][0] - CAM[i - 1][0])));
    return deClave(CAM[CAM.length - 1]);
  }
  function aEncuadre([cx, cy, w, ax, ay]) {
    const s = CW / (w * Lm.page.w);
    return [s, ax * CW - cx * Lm.page.w * s, ay * CH - cy * Lm.page.h * s].map((x) => Math.round(x * 100) / 100);
  }
  // ficha=N es la etiqueta N de la lámina; ficha=texto, la primera cuyo nombre lo contiene
  function fichaPedida() {
    const et = (Lm.meta && Lm.meta.etiquetas) || [];
    return /^\d+$/.test(FICHA) ? et[+FICHA] : et.find((e) => e.nombre.toUpperCase().includes(FICHA.toUpperCase()));
  }
  window.pelicula = peli;

  // ── bajar
  const nombre = (ext) => `montana-s${Lm.seed}-${Lm.meta.arq}-${Lm.registro}.${ext}`;
  function baja(blob, archivo) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = archivo;
    a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }
  function bajaSVG() { baja(new Blob([MT.svg(Lm)], { type: 'image/svg+xml' }), nombre('svg')); }

  // PNG: la lámina terminada, A4 a 300 dpi (3508 px del lado largo), sin fantasma
  function bajaPNG() {
    const s = 3508 / Math.max(Lm.page.w, Lm.page.h), c = document.createElement('canvas');
    c.width = Math.round(Lm.page.w * s); c.height = Math.round(Lm.page.h * s);
    const g = c.getContext('2d');
    g.fillStyle = Lm.papel; g.fillRect(0, 0, c.width, c.height);
    g.lineCap = 'round'; g.lineJoin = 'round'; g.lineWidth = 0.3 * s;
    dibuja(g, Lm.trazos, (x) => x * s, (y) => y * s);
    c.toBlob((b) => baja(b, nombre('png')), 'image/png');
  }

  // GIF: formación → fantasma → la pluma traza. Lado largo de 720 px, ~10 s, en loop.
  async function bajaGIF() {
    const antes = estado.textContent;
    estado.textContent = 'armando el GIF…';
    await espera(30);
    let cuadrosEra = eras;
    if (MT.formable(Lm) && cuadrosEra.length < N_ERAS) {
      cuadrosEra = [];
      for (let k = 0; k < N_ERAS; k++) { cuadrosEra.push(MT.formaCuadro(est.s, Lm, k / (N_ERAS - 1))); estado.textContent = `armando el GIF… era ${k + 1}/${N_ERAS}`; await espera(0); }
    }
    const s = 720 / Math.max(Lm.page.w, Lm.page.h), W = Math.round(Lm.page.w * s), H = Math.round(Lm.page.h * s);
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d', { willReadFrequently: true }), fx = (x) => x * s, fy = (y) => y * s, ancho = Math.max(1, 0.3 * s);
    const paleta = paletaGIF(), indice = indizador(paleta), cuadros = [];
    const toma = (ms) => cuadros.push({ idx: indice(g.getImageData(0, 0, W, H).data), ms });
    const viejo = fantasma;
    fantasma = null;
    for (const e of cuadrosEra) { papel(g, W, H, ancho, fx, fy); dibuja(g, e.trazos, fx, fy); toma(90); }
    if (cuadrosEra.length) {
      cuadros[cuadros.length - 1].ms = 600;
      fantasma = cuadrosEra[cuadrosEra.length - 1].trazos.filter((t) => t.pluma !== Lm.plumas.length - 1);
    }
    papel(g, W, H, ancho, fx, fy); toma(200);
    const k = cursor(), n = 60;
    let total = 0;
    for (const t of Lm.trazos) { total += BAJAR; for (let i = 1; i < t.pts.length; i++) total += Math.hypot(t.pts[i][0] - t.pts[i - 1][0], t.pts[i][1] - t.pts[i - 1][1]); }
    for (let f = 0; f < n; f++) {
      avanza(g, k, total / n, fx, fy); toma(f === n - 1 ? 2000 : 83);
      if (f % 10 === 0) { estado.textContent = `armando el GIF… trazo ${Math.round(100 * f / n)} %`; await espera(0); }
    }
    fantasma = viejo;
    estado.textContent = 'codificando el GIF…'; await espera(0);
    baja(new Blob([codificaGIF(W, H, paleta, cuadros)], { type: 'image/gif' }), `proceso-s${Lm.seed}.gif`);
    estado.textContent = antes;
  }

  // paleta: papel, las dos plumas y sus mezclas con el papel (el antialias y el fantasma)
  function paletaGIF() {
    const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
    const P = rgb(Lm.papel), tintas = Lm.plumas.map(rgb), out = [P];
    const mezcla = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
    const pasos = Math.floor(60 / tintas.length); // con tintas hipsométricas hay más plumas: menos mezclas por pluma
    for (const T of tintas) for (let k = 1; k <= pasos; k++) out.push(mezcla(P, T, k / pasos));
    while (out.length < 64) out.push(P);
    return out;
  }
  function indizador(pal) {
    const cache = new Map();
    return (data) => {
      const idx = new Uint8Array(data.length / 4);
      for (let p = 0, j = 0; p < data.length; p += 4, j++) {
        const key = (data[p] << 16) | (data[p + 1] << 8) | data[p + 2];
        let v = cache.get(key);
        if (v === undefined) {
          let dm = Infinity;
          for (let i = 0; i < pal.length; i++) {
            const dr = data[p] - pal[i][0], dg = data[p + 1] - pal[i][1], db = data[p + 2] - pal[i][2], d = dr * dr + dg * dg + db * db;
            if (d < dm) { dm = d; v = i; }
          }
          cache.set(key, v);
        }
        idx[j] = v;
      }
      return idx;
    };
  }

  // GIF89a con LZW, escrito aquí para no depender de nada.
  function codificaGIF(W, H, pal, cuadros) {
    const bytes = [], b = (x) => bytes.push(x & 255), w16 = (x) => { b(x); b(x >> 8); };
    const nbits = Math.ceil(Math.log2(pal.length)), tam = 1 << nbits;
    for (const ch of 'GIF89a') b(ch.charCodeAt(0));
    w16(W); w16(H); b(0x80 | ((nbits - 1) << 4) | (nbits - 1)); b(0); b(0);
    for (let i = 0; i < tam; i++) { const c = pal[i] || [0, 0, 0]; b(c[0]); b(c[1]); b(c[2]); }
    b(0x21); b(0xff); b(11); for (const ch of 'NETSCAPE2.0') b(ch.charCodeAt(0)); b(3); b(1); w16(0); b(0);
    const min = Math.max(2, nbits);
    for (const cu of cuadros) {
      b(0x21); b(0xf9); b(4); b(0x04); w16(Math.round(cu.ms / 10)); b(0); b(0);
      b(0x2c); w16(0); w16(0); w16(W); w16(H); b(0);
      b(min);
      const datos = lzw(cu.idx, min);
      for (let i = 0; i < datos.length; i += 255) {
        const n = Math.min(255, datos.length - i); b(n);
        for (let j = 0; j < n; j++) bytes.push(datos[i + j]);
      }
      b(0);
    }
    b(0x3b);
    return new Uint8Array(bytes);
  }
  function lzw(idx, min) {
    const out = [], clear = 1 << min, eoi = clear + 1;
    let size = min + 1, next = eoi + 1, acc = 0, nb = 0, tabla = new Map();
    const emite = (code) => { acc |= code << nb; nb += size; while (nb >= 8) { out.push(acc & 255); acc >>>= 8; nb -= 8; } };
    emite(clear);
    let pre = idx[0];
    for (let i = 1; i < idx.length; i++) {
      const k = idx[i], key = (pre << 8) | k, v = tabla.get(key);
      if (v !== undefined) { pre = v; continue; }
      emite(pre);
      if (next === 4096) { emite(clear); tabla = new Map(); size = min + 1; next = eoi + 1; }
      else { if (next >= (1 << size)) size++; tabla.set(key, next++); }
      pre = k;
    }
    emite(pre); emite(eoi);
    if (nb > 0) out.push(acc & 255);
    return out;
  }

  const ciclo = (arr, v) => arr[(arr.indexOf(v) + 1) % arr.length];
  addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k === 'escape' && !ficha.hidden) { ficha.hidden = true; return; }
    if (k === 'escape') { location.href = 'index.html' + (est.lang === 'en' ? '?lang=en' : ''); }
    else if (k === 'r') { est.s = nuevaSemilla(); generar(); }
    else if (k === 'arrowright' || k === 'arrowleft') {
      const n = parseInt(est.s, 10);
      est.s = String(isNaN(n) ? 1 : Math.max(0, n + (k === 'arrowright' ? 1 : -1))); generar();
    }
    else if (k === 'a') { est.arq = ciclo([null, ...ARQS], est.arq); generar(); }
    else if (k === 'm') { est.registro = ciclo([null, ...MT.REGISTROS], est.registro); generar(); }
    else if (k === 'o') { est.oscuro = ciclo([null, '1', '0'], est.oscuro); generar(); }
    else if (k === 'n') { est.lang = est.lang === 'en' ? null : 'en'; generar(); }
    else if (k === 'z') { est.realismo = est.realismo === '0' ? null : '0'; generar(); }
    else if (k === 'c') { est.hipso = ciclo([null, '1', '0'], est.hipso); generar(); }
    else if (k === 'i') { est.tanaka = ciclo([null, '1', '0'], est.tanaka); generar(); }
    else if (k === 'p') { est.planta = ciclo([null, 'curvas', 'hachuras'], est.planta); generar(); }
    else if (k === 'l') { est.hoja = ciclo([null, ...MT.HOJAS], est.hoja); generar(); }
    else if (k === 'd') { est.rot = ciclo([null, '0', '1', '2', '3'], est.rot); generar(); }
    else if (k === 'e') { est.eras = !est.eras; generar(); }
    else if (k === 't') { if (Lm) repetir(); }
    else if (k === 'f') completo();
    else if (k === ' ') { pausa = !pausa; e.preventDefault(); }
    else if (k === 'v') { if (Lm) bajaSVG(); }
    else if (k === 'b') { if (Lm) bajaPNG(); }
    else if (k === 'g') { if (Lm) bajaGIF(); }
    else if (k === 'h') info.classList.toggle('oculto');
  });
  addEventListener('resize', () => { encuadra(); if (PELI) { if (peli.listo) { peli.cam = null; peli.ir(peli.t); } } else if (Lm && cur) completo(); });

  // ── la ficha del nombre: cada nombre propio de la lámina se puede tocar
  const ficha = document.getElementById('ficha');
  const CLASES = {
    es: { cumbre: 'cumbre', paso: 'collado, paso', hondonada: 'hondonada', lago: 'lago', laguna: 'laguna', rio: 'río', mar: 'mar', playa: 'playa', boca: 'boca', especial: 'rasgo del terreno', atolon: 'arrecife', valle: 'valle' },
    en: { cumbre: 'summit', paso: 'pass', hondonada: 'hollow', lago: 'lake', laguna: 'lagoon', rio: 'river', mar: 'sea', playa: 'beach', boca: 'reef pass', especial: 'landform', atolon: 'reef', valle: 'valley' },
  };
  const LENGUA_EN = { castellano: 'Spanish', 'náhuatl': 'Nahuatl', maya: 'Yucatec Maya', quechua: 'Quechua', zapoteco: 'Zapotec', 'rarámuri': 'Rarámuri', 'purépecha': 'Purépecha', 'diné': 'Diné (Navajo)', pitjantjatjara: 'Pitjantjatjara', kalaallisut: 'Kalaallisut', inuttut: 'Inuttut', suomi: 'Finnish', hawaiano: 'Hawaiian', 'islandés': 'Icelandic', mixteco: 'Mixtec', 'tének': 'Tének', dhivehi: 'Dhivehi', 'otomí': 'Otomi (Hñähñu)' };
  const enLamina = (ev) => [(ev.clientX - ox) / esc, (ev.clientY - oy) / esc];
  const etiquetaEn = (ev) => {
    if (!Lm || !Lm.meta || !Lm.meta.etiquetas) return null;
    const [x, y] = enLamina(ev);
    return Lm.meta.etiquetas.find(({ caja: [x0, y0, x1, y1] }) => x >= x0 && x <= x1 && y >= y0 && y <= y1) || null;
  };
  function abreFicha(e) {
    const en = est.lang === 'en';
    // la fuente dice "obra: sentido"; el sentido es lo que el nombre dice
    const i = e.fuente.indexOf(': '), ref = i > 0 ? e.fuente.slice(0, i) : e.fuente, dice = i > 0 ? e.fuente.slice(i + 2) : '';
    ficha.querySelector('.nom').textContent = e.nombre;
    ficha.querySelector('.clase').textContent = `${CLASES[en ? 'en' : 'es'][e.clase] || e.clase} · ${en ? LENGUA_EN[e.lengua] || e.lengua : e.lengua}`;
    ficha.querySelector('.dice').textContent = dice ? (en ? '' : '«' + dice + '»') : '';
    ficha.querySelector('.glosa').textContent = e.glosa ? (en ? '“' + e.glosa + '”' : 'en inglés: ' + e.glosa) : '';
    ficha.querySelector('.fuente').textContent = (en ? 'source: ' : 'fuente: ') + ref;
    ficha.hidden = false;
  }
  addEventListener('mousemove', (ev) => { document.body.style.cursor = etiquetaEn(ev) ? 'pointer' : ''; });
  addEventListener('click', (ev) => {
    if (ficha.contains(ev.target) && !ev.target.classList.contains('cerrar')) return;
    const e = etiquetaEn(ev);
    if (e) abreFicha(e); else ficha.hidden = true;
  });

  // la ayuda se duerme a los pocos segundos para no taparle la cartela a la lámina; el mouse la despierta
  let sueno = null;
  const despierta = () => { info.classList.remove('dormido'); clearTimeout(sueno); sueno = setTimeout(() => info.classList.add('dormido'), 5000); };
  addEventListener('mousemove', despierta); addEventListener('keydown', despierta);

  if (PELI) document.documentElement.classList.add('pelicula');
  encuadra(); generar(); requestAnimationFrame(cuadro); if (!PELI) despierta();
})();
