// atlas.js — el frente de Traspuesta: la edición como atlas que se puede filtrar por rasgos,
// cada miniatura levantada y trazada en vivo (obrero.js), y la deriva fuera de la edición.
(function () {
  const MT = window.MT;
  const q = new URLSearchParams(location.search);
  let lang = q.get('lang') === 'en' ? 'en' : 'es';
  const $ = (s) => document.querySelector(s);

  // ── textos
  const TXT = {
    es: {
      def: 'traspuesta · f. Elevación del terreno que impide ver lo que hay detrás de ella.',
      fuente: 'según el diccionario de María Moliner',
      intro: 'Una edición de {n} láminas topográficas para plotter. Cada semilla levanta un terreno, lo erosiona, le abre ríos y lagos, mide sus cimas y collados para darles nombre, y una pluma lo traza perfil por perfil. Cada perfil esconde el de atrás: eso es una traspuesta.',
      tipo: 'terreno', hoja: 'hoja', papel: 'papel', evento: 'evento', orden: 'orden', buscar: 'buscar un nombre…', todos: 'todos', todas: 'todas',
      ordNum: 'número', ordRara: 'las más raras', ordNombre: 'nombre',
      cuantas: (k, n) => `${k} de ${n} láminas`, lamina: 'lámina', deCada: (k, n) => `la ${k}.ª más rara de ${n}`,
      claro: 'claro', oscuro: 'oscuro', sinEvento: 'sin eventos', mas: 'más láminas',
      deriva: 'Fuera de la edición', derivaTxt: 'La edición son {n} láminas, pero el sistema sigue: cualquier número levanta otro terreno.',
      semilla: 'semilla', abrir: 'abrir', azar: 'una al azar', cosidas: 'este paisaje está cosido con las láminas', portadaOtra: 'otro paisaje',
      repite: (c) => (c > 1 ? `se llama igual que otras ${c - 1}` : 'nombre único en la edición'),
      pie: 'Traspuesta · Canek Zapata · 2026', idioma: 'english',
    },
    en: {
      def: 'traspuesta · n. A rise in the land that hides whatever lies behind it.',
      fuente: 'after María Moliner’s dictionary of Spanish',
      intro: 'An edition of {n} topographic plates for a pen plotter. Each seed raises a terrain, erodes it, opens its rivers and lakes, measures its summits and saddles to give them names, and a pen draws it profile by profile. Each profile hides the one behind it: that is a traspuesta.',
      tipo: 'terrain', hoja: 'sheet', papel: 'paper', evento: 'event', orden: 'order', buscar: 'search a name…', todos: 'all', todas: 'all',
      ordNum: 'number', ordRara: 'rarest first', ordNombre: 'name',
      cuantas: (k, n) => `${k} of ${n} plates`, lamina: 'plate', deCada: (k, n) => `rarest #${k} of ${n}`,
      claro: 'light', oscuro: 'dark', sinEvento: 'no events', mas: 'more plates',
      deriva: 'Beyond the edition', derivaTxt: 'The edition is {n} plates, but the system goes on: any number raises another terrain.',
      semilla: 'seed', abrir: 'open', azar: 'a random one', cosidas: 'this landscape is sewn from the plates', portadaOtra: 'another landscape',
      repite: (c) => (c > 1 ? `shares its name with ${c - 1} other${c > 2 ? 's' : ''}` : 'a name found once in the edition'),
      pie: 'Traspuesta · Canek Zapata · 2026', idioma: 'español',
    },
  };
  const HOJA = {
    es: { crestas: 'perfiles', curvas: 'curvas de nivel', lado: 'díptico', torre: 'lámina con proyecciones', bloque: 'bloque diagrama', proyeccion: 'bloque y planta proyectada', secuencia: 'historia en cuatro tiempos', corte: 'corte A–A′' },
    en: { crestas: 'profiles', curvas: 'contour lines', lado: 'diptych', torre: 'sheet with projections', bloque: 'block diagram', proyeccion: 'block and projected plan', secuencia: 'history in four stages', corte: 'section A–A′' },
  };
  const EV = {
    es: { cruzada: 'cordillera cruzada', volcanes: 'volcanes vecinos', impacto: 'impacto', barranca: 'barranca', falla: 'falla', deslave: 'deslave', lava: 'colada', glaciacion: 'glaciación', abanico: 'abanico aluvial', transformante: 'falla transformante', supercaldera: 'supercaldera', trapps: 'coladas apiladas', toba: 'anillo de toba', morrenas: 'morrenas', sumidero: 'sumidero gigante' },
    en: { cruzada: 'crossing range', volcanes: 'neighbor volcanoes', impacto: 'impact', barranca: 'ravine', falla: 'fault', deslave: 'landslide', lava: 'lava flow', glaciacion: 'glaciation', abanico: 'alluvial fan', transformante: 'transform fault', supercaldera: 'supercaldera', trapps: 'stacked flows', toba: 'tuff ring', morrenas: 'moraines', sumidero: 'giant sinkhole' },
  };
  const t = (k) => TXT[lang][k];
  const tipoEn = (s) => (lang === 'en' && MT.traduce ? MT.traduce(s, 'en') : s).toLowerCase();

  // ── la edición
  let ED = [], N = 0;
  const filtro = { arq: '', hoja: '', papel: '', evento: '', orden: 'num', texto: '' };
  let lista = [], mostradas = 0;
  const LOTE = 36;

  // ── obreros: levantan las láminas fuera del hilo de la página
  const nObreros = Math.max(1, Math.min(4, (navigator.hardwareConcurrency || 2) - 1));
  const obreros = [], cola = [], cache = new Map();
  let idSig = 1;
  for (let i = 0; i < nObreros; i++) {
    const w = new Worker('obrero.js?v=38');
    w.libre = true;
    w.onmessage = (e) => {
      const r = e.data; w.libre = true;
      const pend = w.pend; w.pend = null;
      if (!r.error) { cache.set(pend.k, r); if (cache.size > 240) cache.delete(cache.keys().next().value); }
      if (pend) for (const cb of pend.cbs) cb(r);
      reparte();
    };
    obreros.push(w);
  }
  function pide(s, cb, urgente, tipo) {
    const k = s + '|' + (tipo || lang);
    if (cache.has(k)) return cb(cache.get(k));
    const ya = cola.find((x) => x.k === k) || obreros.map((w) => w.pend).find((p) => p && p.k === k);
    if (ya) { ya.cbs.push(cb); return; }
    const tarea = { k, s, lang, tipo, cbs: [cb], id: idSig++ };
    if (urgente) cola.unshift(tarea); else cola.push(tarea);
    reparte();
  }
  function reparte() {
    for (const w of obreros) {
      if (!w.libre || !cola.length) continue;
      const tarea = cola.shift();
      w.libre = false; w.pend = tarea;
      w.postMessage({ s: tarea.s, lang: tarea.lang, id: tarea.id, tipo: tarea.tipo });
    }
  }
  const olvida = (s) => { const i = cola.findIndex((x) => x.s === s && x.cbs.length === 1); if (i >= 0) cola.splice(i, 1); };

  // ── la pluma: traza la lámina sobre un lienzo, de a poco, como plotter
  function traza(cv, r, segundos) {
    const dpr = Math.min(2, window.devicePixelRatio || 1), W = cv.clientWidth, H = W * r.page.h / r.page.w;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); cv.style.height = H + 'px';
    const c = cv.getContext('2d'), e = (W * dpr) / r.page.w;
    c.fillStyle = r.papel; c.fillRect(0, 0, cv.width, cv.height);
    c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = Math.max(0.5 * dpr, 0.3 * e);
    // los trazos, con su largo, para repartir el tiempo por tinta y no por número de trazos
    const P = r.plano, trazos = [];
    let total = 0;
    for (let k = 0; k < P.length;) {
      const pl = P[k], n = P[k + 1], i0 = k + 2; let L = 0;
      for (let j = 1; j < n; j++) L += Math.hypot(P[i0 + 2 * j] - P[i0 + 2 * j - 2], P[i0 + 2 * j + 1] - P[i0 + 2 * j - 1]);
      trazos.push({ pl, n, i0, L: L + 2 }); total += L + 2; k = i0 + 2 * n;
    }
    let hecho = 0, ti = 0;
    const t0 = performance.now(), dur = segundos * 1000;
    const paso = (ahora) => {
      if (!cv.isConnected) return;
      const meta = segundos <= 0 ? Infinity : total * Math.min(1, (ahora - t0) / dur);
      while (ti < trazos.length && hecho + trazos[ti].L <= meta) {
        const z = trazos[ti];
        c.strokeStyle = r.plumas[z.pl] || r.plumas[0];
        c.beginPath(); c.moveTo(P[z.i0] * e, P[z.i0 + 1] * e);
        for (let j = 1; j < z.n; j++) c.lineTo(P[z.i0 + 2 * j] * e, P[z.i0 + 2 * j + 1] * e);
        c.stroke(); hecho += z.L; ti++;
      }
      if (ti < trazos.length) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  }

  // ── el título, con la misma letra de un trazo que usan las láminas
  function titulo() {
    const cv = $('#titulo'), dpr = Math.min(2, window.devicePixelRatio || 1);
    const W = cv.clientWidth, txt = 'TRASPUESTA';
    const ancho = MT.letra.mide(txt, 10, { track: 4, crudo: true }), e = W / (ancho + 2);
    const H = 14 * e;
    cv.width = W * dpr; cv.height = H * dpr; cv.style.height = H + 'px';
    const c = cv.getContext('2d'), tinta = getComputedStyle(document.documentElement).getPropertyValue('--tinta');
    c.scale(dpr * e, dpr * e); c.translate(1, 12);
    c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = 0.32; c.strokeStyle = tinta;
    const lineas = MT.letra.trazos(txt, 0, 0, 10, { track: 4, crudo: true }).lineas;
    let i = 0;
    const paso = () => {
      for (let k = 0; k < 2 && i < lineas.length; k++, i++) {
        const l = lineas[i]; c.beginPath(); c.moveTo(l[0][0], l[0][1]);
        for (let j = 1; j < l.length; j++) c.lineTo(l[j][0], l[j][1]);
        c.stroke();
      }
      if (i < lineas.length) setTimeout(paso, 45);
    };
    paso();
  }

  // ── color: el de la lámina de portada (cada visita, otra)
  function colorDe(fila) {
    const [papel, tinta] = [fila[13], fila[14]];
    const R = document.documentElement.style;
    R.setProperty('--papel', papel); R.setProperty('--tinta', tinta);
    // la tinta suave: la misma, mezclada con el papel
    R.setProperty('--tenue', `color-mix(in oklch, ${tinta} 55%, ${papel})`);
    R.setProperty('--raya', `color-mix(in oklch, ${tinta} 22%, ${papel})`);
    document.querySelector('meta[name="theme-color"]').setAttribute('content', papel);
  }

  const verURL = (s) => `ver.html?s=${s}${lang === 'en' ? '&lang=en' : ''}`;
  const num = (s) => String(s).padStart(4, '0');

  // ── portada: un paisaje a pantalla completa, cosido con terrenos de la edición
  // (panorama.js). La pluma va del frente hacia atrás, con bruma según la fila; al final,
  // el agua y los nombres de las cimas que quedaron a la vista.
  let portada = null, turnoP = 0;
  function eligeSeis() {
    const vistos = new Set(), out = [];
    for (let k = 0; k < 400 && out.length < MT.panorama.N; k++) {
      const f = ED[Math.floor(Math.random() * ED.length)];
      if ((!vistos.has(f[3]) || k > 200) && !out.includes(f)) { vistos.add(f[3]); out.push(f); }
    }
    return out;
  }
  function ponPortada(filas) {
    portada = filas; const yo = ++turnoP;
    colorDe(filas[0]);
    $('#portada-cosidas').innerHTML = filas.map((f) => `<a href="${verURL(f[0])}">${num(f[0])} ${f[1] || f[4]}</a>`).join(' · ');
    const ter = new Array(filas.length); let faltan = filas.length;
    filas.forEach((f, k) => pide(f[0], (r) => {
      if (r.error || yo !== turnoP) return;
      ter[k] = r.terreno;
      if (--faltan === 0) pinta(ter, filas, yo);
    }, true, 'terreno'));
  }
  function pinta(ter, filas, yo) {
    const cv = $('#panorama-lienzo'), dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = cv.clientWidth, h = cv.clientHeight;
    cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const papel = filas[0][13], tinta = filas[0][14], oscuro = filas[0][7] === 'oscuro';
    const agua = MT.panorama.agua(tinta, oscuro, Math.random());
    const { strokes, rios, letras, n } = MT.panorama(ter, w, h, { lang });
    const linea = (s) => { c.beginPath(); c.moveTo(s[0][0], s[0][1]); for (let j = 1; j < s.length; j++) c.lineTo(s[j][0], s[j][1]); c.stroke(); };
    c.fillStyle = papel; c.fillRect(0, 0, w, h);
    c.lineCap = 'round'; c.lineJoin = 'round';
    const t0 = performance.now(), dur = 7000, total = strokes.length;
    let k = 0;
    const paso = (ahora) => {
      if (yo !== turnoP) return;
      const meta = total * Math.min(1, (ahora - t0) / dur);
      c.strokeStyle = tinta; c.lineWidth = 0.75;
      for (; k < meta && k < total; k++) { c.globalAlpha = 1 - 0.72 * ((strokes[k].fila || 0) / (n - 1)); linea(strokes[k]); }
      if (k < total) { requestAnimationFrame(paso); return; }
      c.strokeStyle = agua; c.lineWidth = 1.1;
      for (const sg of rios) { c.globalAlpha = 1 - 0.6 * (sg.fila / (n - 1)); linea(sg); }
      c.globalAlpha = 1; c.strokeStyle = tinta; c.lineWidth = 0.8;
      for (const l of letras) linea(l);
    };
    requestAnimationFrame(paso);
  }

  // ── filtros
  function opciones(sel, pares, todo) {
    const v = sel.value;
    sel.innerHTML = `<option value="">${todo}</option>` + pares.map(([k, nom, c]) => `<option value="${k}">${nom} · ${c}</option>`).join('');
    sel.value = v;
  }
  function llenaFiltros() {
    const cuenta = (f) => { const m = new Map(); for (const x of ED) for (const k of [].concat(f(x))) m.set(k, (m.get(k) || 0) + 1); return [...m].sort((a, b) => b[1] - a[1]); };
    const tipos = {}; for (const x of ED) tipos[x[3]] = x[4];
    opciones($('#f-arq'), cuenta((x) => x[3]).map(([k, c]) => [k, tipoEn(tipos[k]), c]), t('todos'));
    opciones($('#f-hoja'), cuenta((x) => x[5]).map(([k, c]) => [k, HOJA[lang][k], c]), t('todas'));
    opciones($('#f-papel'), cuenta((x) => x[7]).map(([k, c]) => [k, t(k), c]), t('todos'));
    opciones($('#f-evento'), [['-', t('sinEvento'), ED.filter((x) => !x[9].length).length], ...cuenta((x) => [...new Set(x[9])]).map(([k, c]) => [k, EV[lang][k] || k, c])], t('todos'));
    $('#f-orden').innerHTML = `<option value="num">${t('ordNum')}</option><option value="rara">${t('ordRara')}</option><option value="nombre">${t('ordNombre')}</option>`;
    $('#f-orden').value = filtro.orden;
    $('#f-texto').placeholder = t('buscar');
    for (const [k, id] of [['tipo', 'l-arq'], ['hoja', 'l-hoja'], ['papel', 'l-papel'], ['evento', 'l-evento'], ['orden', 'l-orden']]) $('#' + id).textContent = t(k);
  }
  function aplica() {
    const tx = filtro.texto.trim().toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    lista = ED.filter((x) => (!filtro.arq || x[3] === filtro.arq) && (!filtro.hoja || x[5] === filtro.hoja) && (!filtro.papel || x[7] === filtro.papel)
      && (!filtro.evento || (filtro.evento === '-' ? !x[9].length : x[9].includes(filtro.evento)))
      && (!tx || (x[1] || '').normalize('NFD').replace(/[̀-ͯ]/g, '').includes(tx) || String(x[0]) === tx));
    if (filtro.orden === 'rara') lista.sort((a, b) => a[11] - b[11]);
    else if (filtro.orden === 'nombre') lista.sort((a, b) => (a[1] || '').localeCompare(b[1] || '', 'es'));
    $('#cuenta').textContent = t('cuantas')(lista.length, N);
    for (const c of $('#rejilla').children) olvida(+c.dataset.s);
    $('#rejilla').innerHTML = ''; mostradas = 0;
    mas();
    guardaURL();
  }
  function guardaURL() {
    const p = new URLSearchParams();
    for (const k of ['arq', 'hoja', 'papel', 'evento', 'texto']) if (filtro[k]) p.set(k, filtro[k]);
    if (filtro.orden !== 'num') p.set('orden', filtro.orden);
    if (lang === 'en') p.set('lang', 'en');
    history.replaceState(null, '', p.toString() ? '?' + p : location.pathname);
  }

  // ── la rejilla: tarjetas que se trazan cuando entran a la vista
  const mira = new IntersectionObserver((ents) => {
    for (const en of ents) {
      const card = en.target, s = +card.dataset.s;
      if (en.isIntersecting && !card.dataset.lista) {
        card.dataset.lista = '1';
        pide(s, (r) => { if (!r.error && card.isConnected) traza(card.querySelector('canvas'), r, 1.6); });
      } else if (!en.isIntersecting && card.dataset.lista && !cache.has(s + '|' + lang)) { olvida(s); delete card.dataset.lista; }
    }
  }, { rootMargin: '300px 0px' });
  function tarjeta(x) {
    const [s, nombre, glosa, , tipo, hoja, , , , , pts, lugar, repite] = x;
    const a = document.createElement('a');
    a.className = 'tarjeta'; a.href = verURL(s); a.dataset.s = s;
    const vertical = hoja === 'torre' || hoja === 'proyeccion' || hoja === 'corte';
    a.innerHTML = `<canvas class="${vertical ? 'v' : 'h'}"></canvas>
      <div class="pie"><span class="n">${num(s)}</span> <span class="nom">${nombre || tipo}</span></div>
      <div class="dato">${tipoEn(tipo)} · ${HOJA[lang][hoja]}${lang === 'en' && glosa ? `<br><i>${glosa}</i>` : ''}</div>
      <div class="dato tenue">${t('deCada')(lugar, N)} · ${t('repite')(repite)}</div>`;
    return a;
  }
  function mas() {
    const R = $('#rejilla'), hasta = Math.min(lista.length, mostradas + LOTE);
    for (; mostradas < hasta; mostradas++) { const c = tarjeta(lista[mostradas]); R.appendChild(c); mira.observe(c); }
    $('#mas').hidden = mostradas >= lista.length;
  }
  new IntersectionObserver((e) => { if (e[0].isIntersecting && mostradas < lista.length) mas(); }, { rootMargin: '600px 0px' }).observe($('#mas'));

  // ── textos fijos e idioma
  function textos() {
    document.documentElement.lang = lang === 'en' ? 'en' : 'es-MX';
    $('#def').textContent = t('def'); $('#fuente').textContent = t('fuente');
    $('#intro').textContent = t('intro').replace('{n}', N.toLocaleString(lang === 'en' ? 'en-US' : 'es-MX'));
    $('#deriva-t').textContent = t('deriva'); $('#deriva-txt').textContent = t('derivaTxt').replace('{n}', N.toLocaleString(lang === 'en' ? 'en-US' : 'es-MX'));
    $('#l-semilla').textContent = t('semilla'); $('#abrir').textContent = t('abrir'); $('#azar').textContent = t('azar');
    $('#portada-cosidas-t').textContent = t('cosidas'); $('#portada-otra').textContent = t('portadaOtra');
    $('#mas').textContent = t('mas'); $('#pie').textContent = t('pie'); $('#idioma').textContent = t('idioma');
    $('#a-nomen').textContent = lang === 'en' ? 'gazetteer: every name in the edition, what it means and where it comes from →' : 'nomenclátor: todos los nombres de la edición, qué dicen y de dónde vienen →';
    $('#a-nomen').href = 'nomenclator.html' + (lang === 'en' ? '?lang=en' : '');
  }
  function cambiaIdioma() {
    lang = lang === 'en' ? 'es' : 'en';
    textos(); llenaFiltros(); aplica(); ponPortada(portada);
  }

  // ── arranque
  fetch('edicion/edicion.json?v=38').then((r) => r.json()).then((d) => {
    ED = d.filas; N = d.n;
    for (const k of ['arq', 'hoja', 'papel', 'evento', 'texto', 'orden']) if (q.get(k)) filtro[k] = q.get(k);
    ponPortada(eligeSeis());
    titulo(); textos(); llenaFiltros();
    for (const k of ['arq', 'hoja', 'papel', 'evento', 'orden']) { $('#f-' + k).value = filtro[k]; $('#f-' + k).onchange = (e) => { filtro[k] = e.target.value; aplica(); }; }
    $('#f-texto').value = filtro.texto;
    let tt = null; $('#f-texto').oninput = (e) => { clearTimeout(tt); tt = setTimeout(() => { filtro.texto = e.target.value; aplica(); }, 200); };
    aplica();
  });
  $('#portada-otra').onclick = (e) => { e.preventDefault(); ponPortada(eligeSeis()); };
  $('#idioma').onclick = (e) => { e.preventDefault(); cambiaIdioma(); };
  $('#mas').onclick = mas;
  $('#deriva-f').onsubmit = (e) => { e.preventDefault(); const s = $('#semilla').value.trim(); if (s) location.href = verURL(encodeURIComponent(s)); };
  $('#azar').onclick = () => { location.href = verURL(N + 1 + Math.floor(Math.random() * 999000)); };
  let rt = null; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { titulo(); if (portada) ponPortada(portada); }, 250); });
})();
