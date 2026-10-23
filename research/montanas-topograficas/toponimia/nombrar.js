// toponimia/nombrar.js — mide cada rasgo del terreno y le da un nombre que es cierto.
// MT.nombra(T, seed) → [{ u, v, h, clase, nombre, glosa }]; el primero es el de la lámina.
(function (G) {
  const MT = G.MT;
  const R8 = ['norte', 'noreste', 'oriente', 'sureste', 'sur', 'suroeste', 'poniente', 'noroeste'];
  const R8en = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'];

  function medidas(T) {
    const S = (u, v) => T.sample(Math.min(1, Math.max(0, u)), Math.min(1, Math.max(0, v)));
    const anillo = (u, v, r, k = 16) => { const z = []; for (let i = 0; i < k; i++) { const a = i / k * 6.283; z.push(S(u + Math.cos(a) * r, v + Math.sin(a) * r)); } return z; };
    const prom = (a) => a.reduce((x, y) => x + y, 0) / a.length;
    const desv = (a) => { const m = prom(a); return Math.sqrt(prom(a.map((x) => (x - m) ** 2))); };
    const mPorU = T.anchoKm * 1000, mPorH = T.relieve;
    const pendiente = (u, v, r) => (S(u, v) - prom(anillo(u, v, r))) * mPorH / (r * mPorU); // m/m
    return { S, anillo, prom, desv, pendiente, mPorU, mPorH };
  }

  // lo que se puede decir de una cima
  function deCima(T, M, q, todas, i) {
    const { anillo, prom, desv, pendiente, S } = M;
    const h = q.h, d1 = h - prom(anillo(q.u, q.v, 0.012)), d2 = h - prom(anillo(q.u, q.v, 0.045));
    const a5 = anillo(q.u, q.v, 0.05, 24);
    // elongación: cuánto más alto está el anillo en una dirección que en la perpendicular
    let ej = 0; for (let k = 0; k < 12; k++) ej = Math.max(ej, Math.abs((a5[k] + a5[k + 12]) - (a5[(k + 6) % 24] + a5[(k + 18) % 24])));
    const p = Math.max(pendiente(q.u, q.v, 0.03), 0);
    const lejos = prom(anillo(q.u, q.v, 0.25, 24));
    const rasgos = (T.rasgos.especiales || []);
    const cerca = (tipo, rmax) => rasgos.some((e) => e.tipo === tipo && (tipo !== 'colada' || /^(COLADA|MALPA)/.test(e.term || '')) && Math.hypot(e.u - q.u, e.v - q.v) < rmax); // 'colada' también guarda fiordos y deltas: sólo la lava cuenta
    const rios = (T.hidro && T.hidro.rios) || [];
    const dRio = rios.filter((r) => r.clase >= 2).reduce((mn, r) => Math.min(mn, ...r.pts.filter((_, k) => k % 3 === 0).map(([u, v]) => Math.hypot(u - q.u, v - q.v))), 9);
    const lagos = (T.hidro && T.hidro.lagos) || [];
    const ang = Math.atan2(q.u - 0.5, -(q.v - 0.5)); // norte = v bajo
    const dc = Math.hypot(q.u - 0.5, q.v - 0.5), ir = Math.round(((ang * 180 / Math.PI + 360) % 360) / 45) % 8;
    const gemela = todas.find((o, k) => k !== i && Math.hypot(o.u - q.u, o.v - q.v) < 0.08 && Math.abs(o.h - q.h) < 0.12 * q.h);
    return {
      _crudo: { elong: ej / Math.max(1e-3, h - prom(a5)), pend: p, aisl: lejos / Math.max(1e-3, h), forma: d2 > 0 ? d1 / d2 : 0, cono: desv(a5) / Math.max(1e-3, h - prom(a5)), prom: q.prom },
      // umbrales calibrados en percentiles sobre 479 cimas (toponimia/medir.js): cada rasgo
      // describe más o menos a la cuarta parte de las cimas, la que de verdad lo es
      principal: i === 0, altoRel: h, chico: q.prom < 0.14, altM: T.alt(h),
      arq: T.arq, enIsla: !!T.nivelMar || T.arq === 'archi' || T.arq === 'atolon',
      roca: ['estrato', 'escudo', 'conos', 'archi', 'atolon'].includes(T.arq) ? 'volcanica' : ['badlands', 'tepuyes', 'testigos', 'canon', 'pliegues'].includes(T.arq) ? 'arenisca' : ['karst', 'mesa'].includes(T.arq) ? 'caliza' : null,
      nLagos: lagos.filter((l) => Math.hypot(l.u - q.u, l.v - q.v) < 0.3).length,
      nCimas: todas.filter((o) => Math.hypot(o.u - q.u, o.v - q.v) < 0.18).length,
      agudo: d2 > 0 && d1 / d2 > 0.42, romo: d2 > 0 && d1 / d2 < 0.2, plano: d1 * M.mPorH < 6,
      escarpado: p > 0.63, conico: desv(a5) / Math.max(1e-3, h - prom(a5)) < 0.27, alargado: ej / Math.max(1e-3, h - prom(a5)) > 1.85,
      ancho: d2 * M.mPorH < 120 && !(d1 / d2 > 0.42),
      aislado: lejos < 0.27 * h, llanoAlrededor: lejos < 0.15 * h, solitario: todas.length === 1,
      partido: !!gemela, cercaLago: lagos.some((l) => Math.hypot(l.u - q.u, l.v - q.v) < 0.12),
      cercaHoya: cerca('crater', 0.14) || cerca('fondo', 0.14), cercaColada: cerca('colada', 0.15), cercaRio: dRio < 0.03,
      seco: dRio > 0.2 && !lagos.length, nRios: 0,
      rumbo: dc > 0.3 ? R8[ir] : null, rumboEn: dc > 0.3 ? 'of the ' + R8en[ir] : null,
      mayor: i === 0 && todas.filter((o) => o.prom >= 0.15).length >= 3 && q.prom > 0.3, menor: i > 0 && q.prom < 0.14,
      enmedio: i > 0 && todas.length >= 3 && dc < 0.2, costa: !!T.nivelMar || T.mar,
      polar: ['drumlins', 'poligonos'].includes(T.arq) || T.nombre === 'FIORDOS' || (T.eventos || []).some((e) => ['glaciacion', 'morrenas'].includes(e.tipo)),
      // la ladera: hacia dónde cae más la cima (norte = v bajo; el sol del mediodía viene del sur)
      solana: (h - S(q.u, q.v + 0.04)) > 1.6 * Math.max(1e-4, h - S(q.u, q.v - 0.04)), umbria: (h - S(q.u, q.v - 0.04)) > 1.6 * Math.max(1e-4, h - S(q.u, q.v + 0.04)),
    };
  }

  const tit = (s) => s.toUpperCase();
  const rocaDe = (arq) => (['estrato', 'escudo', 'conos', 'archi', 'atolon'].includes(arq) ? 'volcanica' : ['badlands', 'tepuyes', 'testigos', 'canon', 'pliegues'].includes(arq) ? 'arenisca' : ['karst', 'mesa'].includes(arq) ? 'caliza' : null);
  const CAJON = new Set(['cerro', 'pico', 'monte', 'hoyada', 'collado', 'laguna', 'vaguada', 'llano']);
  const SOSO = new Set(['pico', 'monte']); // ciertos para casi toda cima principal: valen poco
  // complementos que contradicen a su genérico
  const CHOCA = { 'laguna seca': ['seco', 'del agua', 'del río'], isla: ['solo'], loma: ['redondo', 'gordo'], cuchilla: ['redondo', 'gordo', 'chato'], mesa: ['agudo', 'redondo'], teso: ['agudo'], picacho: ['chato', 'gordo', 'pelón', 'agudo'], aguja: ['agudo', 'redondo', 'gordo', 'chato', 'pelón'], mamelón: ['agudo'], mogote: ['agudo', 'largo'], cueto: ['largo', 'chato'] };
  // si hay un nombre náhuatl que el rasgo de verdad se gana, a veces es ése (y uno por lámina cada uno)
  // Una sola lengua además del castellano por lámina, como en la geografía real, y escogida
  // por la región que el terreno sugiere: lo glaciar (fiordos, drumlins, polígonos, morrenas)
  // en kalaallisut, inuttut o suomi; la caliza en maya, como en Yucatán; la alta montaña en
  // quechua o náhuatl; la sierra en zapoteco o náhuatl; lo demás en náhuatl.
  const LENGUAS = {
    'náhuatl': { lista: () => MT.NAHUATL, ref: 'Macazaga, Diccionario de geografía náhuatl', p: 0.45 },
    maya: { lista: () => MT.MAYA, ref: 'Diccionario Maya Cordemex', p: 0.45 },
    quechua: { lista: () => MT.QUECHUA, ref: 'Simi Taqe, Academia Mayor de la Lengua Quechua', p: 0.5 },
    zapoteco: { lista: () => MT.ZAPOTECO, ref: 'Nellis y Goodner, Diccionario zapoteco de Juárez', p: 0.5 },
    kalaallisut: { lista: () => MT.KALAALLISUT, ref: 'toponimia de Groenlandia', p: 0.75 },
    inuttut: { lista: () => MT.INUTTUT, ref: 'English-Inuttut Dictionary, Labrador Virtual Museum', p: 0.75 },
    suomi: { lista: () => MT.SUOMI, ref: 'toponimia finlandesa (Maanmittauslaitos)', p: 0.75 },
    'diné': { lista: () => MT.DINE, ref: 'Young y Morgan, The Navajo Language (vía Wiktionary)', p: 0.6 },
    pitjantjatjara: { lista: () => MT.PITJANTJATJARA, ref: 'Kungka Kunpu, AGSA; Goddard', p: 0.65 },
    'rarámuri': { lista: () => MT.RARAMURI, ref: 'Diccionario Ralámuli de Norogachi', p: 0.8 },
    hawaiano: { lista: () => MT.HAWAIANO, ref: 'Wiktionary (hawaiano)', p: 0.65 },
    'islandés': { lista: () => MT.ISLANDES, ref: 'Wiktionary (islandés)', p: 0.65 },
    'purépecha': { lista: () => MT.PUREPECHA, ref: 'lista Swadesh purépecha (Wiktionary)', p: 0.6 },
    mixteco: { lista: () => MT.MIXTECO, ref: 'Diccionario básico del mixteco de Yosondúa (ILV, 2012)', p: 0.6 },
    'otomí': { lista: () => MT.OTOMI, ref: 'Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', p: 0.6 },
    'tének': { lista: () => MT.TENEK, ref: 'Tsakam lejkix káw Tének (Webonary)', p: 0.6 },
  };
  let LENGUA = 'náhuatl', COMPS_USADOS = new Set(), VARIANTE = 0;
  const MEXICANOS = new Set(['del encinal', 'de los ocotes', 'de los oyameles', 'del pinar', 'del zacatal', 'de los mezquites', 'de los órganos', 'del maguey', 'del palo blanco', 'de los sabinos', 'del coyote', 'del oso', 'de los zopilotes']);
  function lenguaDe(T, seed) {
    const r = MT.rng(seed + ':lengua'), x = r();
    const ev = new Set((T.eventos || []).map((e) => e.tipo)), a = T.arq, fiordo = T.nombre === 'FIORDOS';
    const elige = (pares) => { let t = x * pares.reduce((s, p) => s + p[1], 0); for (const [l, w] of pares) { if ((t -= w) < 0) return l; } return pares[0][0]; };
    const altMax = T.alt(Math.max(...(T.rasgos.picos || [{ h: 0 }]).map((q) => q.h)));
    if (fiordo) return elige([['kalaallisut', 0.65], ['inuttut', 0.35]]);
    if (a === 'poligonos') return elige([['inuttut', 0.6], ['kalaallisut', 0.4]]);
    if (a === 'drumlins' || ev.has('morrenas')) return elige([['suomi', 0.7], ['inuttut', 0.15], ['kalaallisut', 0.15]]);
    if (ev.has('glaciacion')) return elige([['suomi', 0.34], ['inuttut', 0.33], ['kalaallisut', 0.33]]);
    if (ev.has('trapps')) return 'islandés'; // las coladas apiladas: el basalto de Islandia
    if (a === 'karst') return elige([['maya', 0.6], ['tének', 0.4]]); // Yucatán; la Huasteca potosina
    if (a === 'mesa') return 'maya';
    if (a === 'escudo') return elige([['hawaiano', 0.5], ['islandés', 0.5]]);
    if (a === 'conos') return elige([['purépecha', 0.7], ['hawaiano', 0.3]]); // el campo Michoacán–Guanajuato
    if (a === 'estrato' && altMax < 3900) return elige([['purépecha', 0.35], ['náhuatl', 0.65]]);
    if (a === 'meandros') return elige([['tének', 0.5], ['náhuatl', 0.5]]);
    // el desierto: cañones, cerros testigo, cuellos y tierras malas en diné o rarámuri;
    // inselbergs y dunas en pitjantjatjara
    if (a === 'canon') return elige([['rarámuri', 0.45], ['diné', 0.3], ['otomí', 0.25]]); // la Tarahumara; la barranca de Metztitlán
    if (a === 'badlands') return elige([['mixteco', 0.45], ['otomí', 0.25], ['diné', 0.3]]); // la Mixteca Alta, deslavada; el Mezquital
    if (a === 'tepuyes') return 'castellano'; // la Gran Sabana: en castellano (Canek); el pemón no, por respeto a lo sagrado
    if (a === 'testigos') return elige([['diné', 0.55], ['otomí', 0.45]]);
    if (T.nombre === 'CUELLO VOLCÁNICO') return 'diné';
    if (a === 'inselbergs') return 'pitjantjatjara';
    if (a === 'dunas') return elige([['pitjantjatjara', 0.5], ['náhuatl', 0.5]]);
    if (altMax > 4000 && ['cordillera', 'estrato', 'dos', 'monte', 'pliegues', 'rift'].includes(a)) return elige([['quechua', 0.55], ['náhuatl', 0.45]]);
    // la sierra andina media también es quechua (los Andes no son sólo nieve)
    if (altMax > 3200 && ['cordillera', 'dos', 'monte', 'pliegues', 'rift'].includes(a)) return elige([['quechua', 0.4], ['zapoteco', 0.2], ['náhuatl', 0.4]]);
    if (['pliegues', 'cordillera', 'monte', 'dos', 'rift'].includes(a)) return altMax < 3200 ? elige([['zapoteco', 0.25], ['mixteco', 0.25], ['rarámuri', 0.15], ['otomí', 0.1], ['náhuatl', 0.25]]) : elige([['zapoteco', 0.45], ['náhuatl', 0.55]]);
    return 'náhuatl';
  }
  function enNahuatl(clase, med, r, usados) {
    const L = LENGUAS[LENGUA]; if (!L) return null; // en castellano
    const c = ((L.lista() || {})[clase] || []).map((x) => ({ ...x, lengua: LENGUA, ref: x.ref || L.ref })).filter((x) => x.r(med) && !usados.has(x.w)); // cada nombre puede traer su propia fuente
    if (!c.length || r() > L.p) return null;
    const x = c[Math.floor(r() * c.length)];
    usados.add(x.w);
    return { nombre: tit(x.solo ? x.w : x.pre + ' ' + x.w), glosa: x.en, generico: x.w, fuente: x.ref + ': ' + x.es, lengua: x.lengua, nahuatl: x.lengua === 'náhuatl' };
  }
  function arma(clase, med, r, usados, gensUsados, vecino) {
    // la lengua indígena nombra los rasgos de la lámina; el título, sólo una de cada tres veces
    const nah = med.principal && r() > 0.35 ? null : enNahuatl(clase, med, r, usados);
    if (nah) return nah;
    const cands = MT.GLOSARIO[clase].filter((x) => x.r(med));
    let lista = cands.length ? cands : MT.GLOSARIO[clase].slice(0, 1);
    const frescos = lista.filter((x) => !gensUsados.has(x.w)); // no repetir genérico en la misma lámina si hay otro
    if (frescos.length) lista = frescos;
    // los genéricos específicos (los que exigen algo) pesan el triple que los de cajón
    const pesos = lista.map((x) => (SOSO.has(x.w) ? 0.4 : CAJON.has(x.w) ? 1 : 3)), tot = pesos.reduce((a, b) => a + b, 0);
    let t = r() * tot, gi = 0; while (gi < lista.length - 1 && t > pesos[gi]) { t -= pesos[gi]; gi++; }
    const gen = lista[gi];
    gensUsados.add(gen.w);
    let comps = MT.COMPLEMENTOS.filter((c) => c.c(med) && !(CHOCA[gen.w] || []).includes(c.m) && (c.p == null || r() < c.p));
    // lo que el genérico ya dice (la loma ya es larga) casi nunca se repite como complemento
    if (gen.w === 'loma' && r() > 0.25) comps = comps.filter((c) => c.m !== 'largo');
    if (med.arq === 'tepuyes') comps = comps.filter((c) => !MEXICANOS.has(c.m)); // en la Gran Sabana no hay encinos ni coyotes
    if (gen.w === 'teso' && r() > 0.25) comps = comps.filter((c) => c.m !== 'chato'); // el teso ya es chato
    if (comps.some((c) => !COMPS_USADOS.has(c.m))) comps = comps.filter((c) => !COMPS_USADOS.has(c.m)); // dos rasgos de la misma lámina no repiten complemento
    // lo que está junto a una cima con nombre lleva su nombre: LA LAGUNA DEL CERRAJÓN
    if (vecino) comps = [{ m: 'de' + (vecino.g === 'm' ? 'l ' : ' la ') + vecino.w, f: 'de' + (vecino.g === 'm' ? 'l ' : ' la ') + vecino.w, en: 'of the ' + vecino.en }, ...comps];
    const yaUsado = usados.has(tit([gen.g === 'f' ? 'la' : 'el', gen.w].join(' ')));
    const sinComp = !comps.length || (!yaUsado && !vecino && !med.principal && r() < 0.3); // el nombre de la lámina siempre lleva complemento
    const comp = sinComp ? null : vecino ? comps[0] : comps[Math.floor(r() * comps.length)];
    if (comp) COMPS_USADOS.add(comp.m);
    const art = gen.g === 'f' ? 'la' : 'el';
    const val = (x) => (typeof x === 'function' ? x(med) : x);
    const txt = [art, gen.w, comp ? val(comp[gen.g]) : ''].filter(Boolean).join(' ');
    const en = [gen.en, comp ? val(comp.en) : ''].filter(Boolean).join(', ');
    let nombre = tit(txt);
    if (usados.has(nombre)) nombre += usados.has(nombre + ' II') ? ' III' : ' II';
    usados.add(nombre);
    return { nombre, glosa: en, generico: gen.w, fuente: gen.src, gen };
  }

  // El atolón no tiene cerros: tiene cayos (INEGI: isla pequeña, rasa y arenosa, de arrecife),
  // una laguna y bocas. Así se nombran los de Alacranes y Chinchorro: por su rumbo (Cayo Norte,
  // Cayo Centro) o por lo que vive en ellos (Isla Pájaros, Cayo Lobos).
  const ARRECIFE = [['de los pájaros', 'of the birds'], ['de las tortugas', 'of the turtles'], ['de los lobos', 'of the sea lions'],
    ['de la arena', 'of the sand'], ['de las fragatas', 'of the frigatebirds'], ['de los bobos', 'of the boobies'], ['del naufragio', 'of the wreck'], ['de los cocos', 'of the coconuts']];
  const RUMBO = [['norte', 'north'], ['oriente', 'east'], ['sur', 'south'], ['poniente', 'west']];
  function nombraAtolon(T, r) {
    const out = [], usados = new Set();
    const cx = T.rasgos.picos.length ? T.rasgos.picos.reduce((a, q) => a + q.u, 0) / T.rasgos.picos.length : 0.5;
    const cy = T.rasgos.picos.length ? T.rasgos.picos.reduce((a, q) => a + q.v, 0) / T.rasgos.picos.length : 0.5;
    // la mitad de los atolones se nombran en dhivehi, la lengua de las Maldivas que le dio su
    // palabra al atolón (atholhu): faru arrecife, fushi isla, kandu canal, bodu grande, kuda chico
    if (MT.rng(T.seed + ':lengua' + (VARIANTE ? ':v' + VARIANTE : ''))() < 0.5) return nombraDhivehi(T);
    const ar = ARRECIFE[Math.floor(r() * ARRECIFE.length)], banco = r() < 0.3;
    out.push({ u: cx, v: cy, h: 0, clase: 'atolon', nombre: tit((banco ? 'el banco ' : 'el arrecife ') + ar[0]), glosa: (banco ? 'reef bank, ' : 'reef, ') + ar[1], generico: banco ? 'banco' : 'arrecife', fuente: 'INEGI: arrecife, banco' });
    const islas = (T.rasgos.picos || []).filter((q) => q.u > 0.04 && q.u < 0.96 && q.v > 0.04 && q.v < 0.96).slice(0, 5);
    islas.forEach((q, i) => {
      const a = Math.atan2(cy - q.v, q.u - cx), k = ((Math.round(a / (Math.PI / 2)) % 4) + 4) % 4, rb = RUMBO[[1, 0, 3, 2][k]]; // v crece hacia el sur
      const cerca = Math.hypot(q.u - cx, q.v - cy) < 0.08;
      let [m, en] = i > 0 && r() < 0.35 ? ARRECIFE[Math.floor(r() * ARRECIFE.length)] : cerca ? ['centro', 'center'] : rb;
      const gen = q.prom < 0.3 && r() < 0.4 ? ['el islote', 'islet'] : ['el cayo', 'cay'];
      let nombre = tit(gen[0] + ' ' + m);
      if (usados.has(nombre)) { nombre += ' chico'.toUpperCase(); en += ', small'; }
      usados.add(nombre);
      out.push({ u: q.u, v: q.v, h: q.h, clase: 'cumbre', nombre, glosa: gen[1] + ', ' + en, generico: gen[0].split(' ')[1], fuente: 'INEGI: cayo, isla pequeña de arrecife' });
    });
    for (const e of T.rasgos.especiales || []) {
      if (e.term === 'LAGUNA') out.push({ u: e.u, v: e.v, h: 0, clase: 'laguna', nombre: 'LA LAGUNA ARRECIFAL', glosa: 'reef lagoon', generico: 'laguna', fuente: 'INEGI: laguna arrecifal' });
      if (e.term === 'PASO') out.push({ u: e.u, v: e.v, h: 0, clase: 'boca', nombre: tit('la boca ' + (r() < 0.5 ? 'grande' : 'del canal')), glosa: 'reef pass', generico: 'boca', fuente: 'INEGI: boca, entrada de mar entre arrecifes' });
    }
    return out;
  }

  function nombraDhivehi(T) {
    const out = [], P = (T.rasgos.picos || []).filter((q) => q.u > 0.04 && q.u < 0.96 && q.v > 0.04 && q.v < 0.96).slice(0, 5);
    const cx = P.length ? P.reduce((a, q) => a + q.u, 0) / P.length : 0.5, cy = P.length ? P.reduce((a, q) => a + q.v, 0) / P.length : 0.5;
    const ref = 'términos de atolón de las Maldivas (Maldives Complete)';
    const grande = P.length >= 5; // muchas islas: el arrecife grande
    out.push({ u: cx, v: cy, h: 0, clase: 'atolon', nombre: grande ? 'BODU FARU' : 'KUDA FARU', glosa: grande ? 'great reef' : 'little reef', generico: 'faru', fuente: ref + ': faru, el arrecife que encierra la laguna; bodu grande, kuda chico', lengua: 'dhivehi' });
    P.forEach((q, i) => {
      const [nombre, glosa] = i === 0 ? ['BODUFUSHI', 'big island'] : q.prom < 0.3 ? ['KUDAFUSHI', 'little island'] : ['FUSHI', 'island'];
      const ya = out.filter((o) => o.nombre.startsWith(nombre)).length;
      out.push({ u: q.u, v: q.v, h: q.h, clase: 'cumbre', nombre: ya ? nombre + ' ' + ['', 'II', 'III', 'IV', 'V'][ya] : nombre, glosa, generico: 'fushi', fuente: ref, lengua: 'dhivehi' });
    });
    for (const e of T.rasgos.especiales || []) {
      if (e.term === 'LAGUNA') out.push({ u: e.u, v: e.v, h: 0, clase: 'laguna', nombre: 'LA LAGUNA ARRECIFAL', glosa: 'reef lagoon', generico: 'laguna', fuente: 'INEGI: laguna arrecifal' });
      if (e.term === 'PASO') out.push({ u: e.u, v: e.v, h: 0, clase: 'boca', nombre: 'BODU KANDU', glosa: 'great channel', generico: 'kandu', fuente: ref + ': kandu, canal', lengua: 'dhivehi' });
    }
    return out;
  }

  // Dos cimas gemelas: la toponimia mexicana las nombra en pareja, y según cómo son. Sólo
  // cuando de verdad lo son: casi de la misma altura, juntas y las dos con presencia.
  const PAREJAS = [
    { n: 'las tetillas', en: 'the teats (twin hills)', c: (o) => o.romas },
    { n: 'los cuates', en: 'the twins', c: (o) => o.dh < 0.025 },
    { n: 'los gemelos', en: 'the twins', c: (o) => o.dh < 0.025 },
    { n: 'los amantes', en: 'the lovers', c: (o) => o.d < 0.045 },
    { n: 'los novios', en: 'the sweethearts', c: (o) => o.d < 0.045 },
    { n: 'el compadre y la comadre', en: 'the godparents', c: (o) => o.dh >= 0.025 },
    { n: 'las dos hermanas', en: 'the two sisters', c: (o) => o.dh >= 0.025 },
    { n: 'los compadres', en: 'the compadres', c: (o) => o.d >= 0.045 },
    { n: 'los cuernos', en: 'the horns', c: (o) => o.agudas },
    { n: 'las orejas', en: 'the ears', c: (o) => o.agudas && o.d < 0.05 },
  ];
  function gemelas(q, q2, med, r) {
    if (!q2 || !med.partido || q2.prom < 0.1) return null;
    const dh = Math.abs(q2.h - q.h) / q.h, d = Math.hypot(q2.u - q.u, q2.v - q.v);
    if (dh > 0.05 || d > 0.07) return null;
    const o = { dh, d, romas: med.romo || (med.conico && !med.agudo), agudas: med.agudo };
    const c = PAREJAS.filter((p) => p.c(o));
    if (!c.length) return null;
    const p = c[Math.floor(r() * c.length)];
    const conRumbo = med.rumbo && r() < 0.4;
    return { nombre: tit(p.n + (conRumbo ? ' del ' + med.rumbo : '')), glosa: p.en + (conRumbo ? ', ' + med.rumboEn : ''), generico: p.n, fuente: 'toponimia mexicana: dos cimas gemelas' };
  }

  // ── los rasgos especiales ───────────────────────────────────────────────────
  // Lo que la lámina rotulaba con su término técnico (COLADA, RIFT, FIORDO…) recibe un nombre
  // propio: un genérico de la toponimia en castellano y la cima vecina o el rumbo. Su medida
  // (el diámetro, el largo, el salto) se queda en el renglón de abajo.
  const ESPECIAL = {
    COLADA: [['el malpaís', 'lava field'], ['el pedregal', 'lava field']],
    'MALPAÍS': [['el malpaís', 'lava field'], ['el pedregal', 'lava field']],
    CUELLO: [['el peñón', 'volcanic plug']],
    DOMO: [['el peñón', 'lava dome'], ['la cúpula', 'dome']],
    ISLOTE: [['el islote', 'islet'], ['el farallón', 'sea stack']],
    DRUMLIN: [['el lomo', 'drumlin']],
    FIORDO: [['el fiordo', 'fjord']],
    TERRAZA: [['la terraza', 'terrace'], ['el rellano', 'terrace']],
    ACANTILADO: [['el cantil', 'sea cliff'], ['los cantiles', 'sea cliffs']],
    POLJE: [['la nava', 'karst plain'], ['el polje', 'polje']],
    ANILLOS: [['los anillos', 'rings']],
    RIFT: [['la fosa', 'rift valley']],
    FALLA: [['la falla', 'fault']],
    DESLAVE: [['el deslave', 'landslide'], ['el derrumbe', 'landslide']],
    AVALANCHA: [['el derrumbadero', 'debris avalanche'], ['el deslave', 'debris avalanche']],
    SUPERCALDERA: [['la gran caldera', 'great caldera']],
    MORRENA: [['la morrena', 'moraine']],
    MORRENAS: [['las morrenas', 'moraines']],
    SUMIDERO: [['el sumidero', 'sinkhole']],
    'ANILLO DE TOBA': [['el anillo de toba', 'tuff ring']],
    CIRCO: [['el circo', 'cirque'], ['la hoya', 'cirque']],
    'VALLE GLACIAR': [['el valle glaciar', 'glacial valley'], ['la artesa', 'U-shaped valley']],
    ABANICO: [['el abanico', 'alluvial fan'], ['el cono de deyección', 'alluvial fan']],
  };
  const R8E = ['norte', 'noreste', 'oriente', 'sureste', 'sur', 'suroeste', 'poniente', 'noroeste'], R8Een = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'];
  function nombraEspeciales(T, r, usados, out, vecinoDe) {
    const rioPrin = out.find((n) => n.clase === 'rio' && /^EL RÍO /.test(n.nombre));
    for (const e of T.rasgos.especiales || []) {
      const term = String(e.term || '').toUpperCase();
      let nombre = null, glosa = '';
      if (term === 'DELTA') { // el delta se llama como su río
        nombre = rioPrin ? 'EL DELTA DEL ' + rioPrin.nombre.replace(/^EL /, '') : 'EL DELTA'; glosa = 'delta' + (rioPrin ? ' of the ' + rioPrin.glosa : '');
      } else if (ESPECIAL[term]) {
        const ops = ESPECIAL[term], [gen, en] = ops[Math.floor(r() * ops.length)];
        const vec = vecinoDe(e.u, e.v, 0.3);
        const ang = Math.atan2(e.u - 0.5, -(e.v - 0.5)), ir = Math.round(((ang * 180 / Math.PI + 360) % 360) / 45) % 8, lejos = Math.hypot(e.u - 0.5, e.v - 0.5) > 0.25;
        let comp = null;
        if (vec && r() < 0.7) comp = ['de' + (vec.g === 'm' ? 'l ' : ' la ') + vec.w, 'of the ' + vec.en];
        else if (lejos) comp = ['del ' + R8E[ir], 'of the ' + R8Een[ir]];
        nombre = tit(gen + (comp ? ' ' + comp[0] : '')); glosa = en + (comp ? ', ' + comp[1] : '');
      }
      if (!nombre || usados.has(nombre)) continue;
      usados.add(nombre);
      out.push({ u: e.u, v: e.v, h: e.h || 0, clase: 'especial', term, nombre, glosa, generico: term.toLowerCase(), fuente: 'genérico de la toponimia en castellano' });
    }
  }

  // ── el agua ─────────────────────────────────────────────────────────────────
  // Los tramos de río (hidrologia) se cosen en cursos: de cada nacimiento, aguas abajo, tramo
  // tras tramo. Un curso se nombra sólo si es largo (X: un cuarto del ancho de la hoja) y
  // caudaloso (Y: llega a clase 2 o más). Dos a lo más.
  const RIO_X = 0.25, RIO_Y = 2;
  function cursos(T) {
    const R = ((T.hidro && T.hidro.rios) || []).filter((x) => x.clase >= 1 && x.pts.length > 1);
    const k = (p) => Math.round(p[0] * 300) + ',' + Math.round(p[1] * 300);
    const desde = new Map(), llegan = new Set();
    for (const x of R) { const a = k(x.pts[0]); if (!desde.has(a)) desde.set(a, []); desde.get(a).push(x); llegan.add(k(x.pts[x.pts.length - 1])); }
    const largo = (p) => { let L = 0; for (let i = 1; i < p.length; i++) L += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); return L; };
    const out = [];
    for (const x of R) {
      if (llegan.has(k(x.pts[0]))) continue; // no es nacimiento
      let pts = [...x.pts], cl = x.clase, c = x, n = 0;
      while (n++ < 400) {
        const sig = (desde.get(k(c.pts[c.pts.length - 1])) || []).find((y) => y !== c);
        if (!sig) break;
        pts = pts.concat(sig.pts.slice(1)); cl = Math.max(cl, sig.clase); c = sig;
      }
      out.push({ pts, clase: cl, largo: largo(pts) });
    }
    return out.sort((a, b) => b.largo * b.clase - a.largo * a.clase);
  }
  const RIO_COMP = [
    { c: (m) => m.principal && m.largo > 0.6, w: 'grande', en: 'great' },
    { c: (m) => m.encajado, w: 'hondo', en: 'deep' },
    { c: (m) => m.empinado, w: 'bravo', en: 'wild' },
    { c: (m) => m.glaciar || m.altM > 3000, w: 'frío', en: 'cold' },
    { c: (m) => m.roca === 'caliza', w: 'blanco', en: 'white' },
    { c: (m) => m.roca === 'arenisca', w: 'colorado', en: 'red' },
    { c: (m) => m.roca === 'volcanica', w: 'prieto', en: 'dark' },
    { c: (m) => ['dunas', 'badlands', 'testigos', 'inselbergs'].includes(m.arq), w: 'seco', en: 'dry' },
    { c: (m) => ['dunas', 'badlands'].includes(m.arq), w: 'salado', en: 'salty' },
    { c: (m) => ['meandros', 'costa'].includes(m.arq) && !m.encajado, w: 'verde', en: 'green' },
    { c: (m) => !m.encajado && !m.empinado && m.roca !== 'arenisca', w: 'claro', en: 'clear' },
    { c: (m) => !m.principal, w: 'chico', en: 'little' },
  ];
  function nombraAgua(T, M, r, usados, gensUsados, out, vecinoDe) {
    const glaciar = (T.eventos || []).some((e) => ['glaciacion', 'morrenas', 'abanico'].includes(e.tipo));
    const delta = T.nombre === 'DELTA';
    // ríos
    let C = cursos(T).filter((x) => x.largo >= RIO_X && x.clase >= RIO_Y);
    if (T.canal) { // el delta: su río es el canal tallado, y su brazo más largo
      const largo = (p) => { let L = 0; for (let i = 1; i < p.length; i++) L += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); return L; };
      const enHoja = (p) => p.filter(([u, v]) => u >= 0 && v >= 0 && u <= 1 && v <= 1);
      const rio = enHoja(T.canal.rio), br = T.canal.brazos.map(enHoja).filter((p) => p.length > 4).sort((a, b) => largo(b) - largo(a));
      C = [{ pts: rio, clase: 3, largo: largo(rio) }, ...(br[0] && largo(br[0]) > 0.08 ? [{ pts: br[0], clase: 2, largo: largo(br[0]) }] : [])];
    }
    const elegidos = [];
    for (const x of C) {
      const m = x.pts[Math.floor(x.pts.length * 0.45)];
      if (!T.canal && elegidos.some((e) => Math.hypot(e.m[0] - m[0], e.m[1] - m[1]) < 0.2)) continue;
      elegidos.push({ ...x, m });
      if (elegidos.length === 2) break;
    }
    elegidos.forEach((x, i) => {
      // el rótulo, a medio curso y lejos de la orilla de la hoja
      let m = x.m;
      for (const f of [0.45, 0.55, 0.35, 0.65, 0.25]) { const p = x.pts[Math.floor(x.pts.length * f)]; if (p[0] > 0.1 && p[0] < 0.9 && p[1] > 0.1 && p[1] < 0.9) { m = p; break; } }
      const lados = M.anillo(m[0], m[1], 0.05), hondura = (M.prom(lados) - M.S(m[0], m[1])) * M.mPorH;
      const med = { principal: i === 0, largo: x.largo, encajado: hondura > 60, empinado: hondura > 200, entreMontes: Math.min(...lados) > M.S(m[0], m[1]) + 0.05,
        roca: rocaDe(T.arq), arq: T.arq, glaciar, nace: false, altM: T.alt(M.S(m[0], m[1])) };
      const base = { u: m[0], v: m[1], h: M.S(m[0], m[1]), clase: 'rio', pts: x.pts };
      // una barranca muy honda se nombra como barranca; si no, por su río
      const nah = enNahuatl('valle', med, r, usados);
      if (nah) { out.push({ ...base, ...nah }); return; }
      if (med.encajado && med.empinado && r() < 0.4) { out.push({ ...base, ...arma('valle', med, r, usados, gensUsados, vecinoDe(m[0], m[1], 0.3)) }); return; }
      const gen = delta && i > 0 ? ['el brazo', 'branch'] : x.clase >= 3 || i === 0 ? ['el río', 'river'] : ['el arroyo', 'creek'];
      const vec = vecinoDe(m[0], m[1], 0.25);
      let comps = RIO_COMP.filter((c) => c.c(med)).map((c) => [c.w, c.en]);
      if (vec && r() < 0.35) comps = [['de' + (vec.g === 'm' ? 'l ' : ' la ') + vec.w, 'of the ' + vec.en]];
      let [cw, cen] = comps.length ? comps[Math.floor(r() * comps.length)] : ['', ''];
      let nombre = tit((gen[0] + ' ' + cw).trim());
      if (usados.has(nombre)) nombre = tit(gen[0] + ' ' + (i === 0 ? 'grande' : 'chico'));
      usados.add(nombre);
      out.push({ ...base, nombre, glosa: gen[1] + (cen ? ', ' + cen : ''), generico: gen[0].split(' ')[1], fuente: 'INEGI: río, arroyo; complemento medido' });
    });
    // el mar: bahía, ensenada, golfo o la mar, según cuánto ocupa y cuántas orillas de la hoja toca
    if (T.mar || T.nivelMar) {
      const G = T.G, h = T.h, nivel = (T.nivelMar || 0) + 1e-4;
      let n = 0, su = 0, sv = 0; const borde = [0, 0, 0, 0];
      for (let j = 0; j < G; j++) for (let i2 = 0; i2 < G; i2++) {
        if (h[j * G + i2] > nivel) continue;
        n++; su += i2; sv += j;
        if (j === 0) borde[0]++; if (j === G - 1) borde[2]++; if (i2 === 0) borde[3]++; if (i2 === G - 1) borde[1]++;
      }
      const f = n / (G * G), orillas = borde.filter((b) => b > G * 0.2).length;
      if (f > 0.06) {
        // el punto de mar más cercano al centro de masa
        let cu = su / n / (G - 1), cv = sv / n / (G - 1), best = null, dm = 9;
        for (let j = 0; j < G; j += 3) for (let i2 = 0; i2 < G; i2 += 3) { if (h[j * G + i2] > nivel) continue; const u = i2 / (G - 1), v = j / (G - 1); const d = Math.hypot(u - cu, v - cv) + (u < 0.08 || u > 0.92 || v < 0.08 || v > 0.92 ? 1 : 0); if (d < dm) { dm = d; best = [u, v]; } }
        const [gen, gen_en] = f < 0.15 ? ['la ensenada', 'cove'] : f >= 0.45 && orillas <= 2 ? ['el golfo', 'gulf'] : orillas <= 1 ? ['la bahía', 'bay'] : ['la mar', 'the sea'];
        const ang = Math.atan2(cu - 0.5, -(cv - 0.5)), R8 = ['norte', 'noreste', 'oriente', 'sureste', 'sur', 'suroeste', 'poniente', 'noroeste'], R8en = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'];
        const ir = Math.round(((ang * 180 / Math.PI + 360) % 360) / 45) % 8, lejos = Math.hypot(cu - 0.5, cv - 0.5) > 0.2;
        const op = [];
        if (T.arq === 'archi') op.push(['de las islas', 'of the islands']);
        if (delta) op.push(['de la barra', 'of the sandbar']);
        if (lejos && gen !== 'la mar') op.push(['del ' + R8[ir], 'of the ' + R8en[ir]]);
        if (gen === 'la mar') op.push(['', '']);
        const [cw, cen] = op.length ? op[Math.floor(r() * op.length)] : ['', ''];
        const nombre = tit((gen + ' ' + cw).trim());
        if (best && !usados.has(nombre)) { usados.add(nombre); out.push({ u: best[0], v: best[1], h: 0, clase: 'mar', nombre, glosa: gen_en + (cen ? ', ' + cen : ''), generico: gen.split(' ')[1], fuente: 'INEGI: bahía, ensenada, golfo' }); }
        // la playa: el tramo de costa más tendido
        if (['costa', 'archi', 'atolon'].includes(T.arq) || delta) {
          let pb = null, pm = 9;
          for (let j = 4; j < G - 4; j += 2) for (let i2 = 4; i2 < G - 4; i2 += 2) {
            const k2 = j * G + i2; if (h[k2] <= nivel || h[k2] > nivel + 0.03) continue;
            if (!(h[k2 - 2] <= nivel || h[k2 + 2] <= nivel || h[k2 - 2 * G] <= nivel || h[k2 + 2 * G] <= nivel)) continue;
            const p = Math.abs(h[k2 + 2] - h[k2 - 2]) + Math.abs(h[k2 + 2 * G] - h[k2 - 2 * G]), u = i2 / (G - 1), v = j / (G - 1);
            if (u < 0.1 || u > 0.9 || v < 0.1 || v > 0.9) continue;
            if (p < pm) { pm = p; pb = [u, v]; }
          }
          if (pb) {
            const roca = rocaDe(T.arq), op2 = [['playa larga', 'long beach']];
            if (roca === 'volcanica') op2.push(['playa prieta', 'dark beach']); else op2.push(['playa blanca', 'white beach']);
            if (delta) op2.push(['la barra', 'the sandbar']);
            const [pn, pen] = op2[Math.floor(r() * op2.length)];
            const nombre2 = tit(pn);
            if (!usados.has(nombre2)) { usados.add(nombre2); out.push({ u: pb[0], v: pb[1], h: M.S(pb[0], pb[1]), clase: 'playa', nombre: nombre2, glosa: pen, generico: 'playa', fuente: 'uso mexicano: Playa Blanca, Playa Larga, la barra' }); }
          }
        }
      }
    }
  }

  // variante: otra tirada de nombres sobre el mismo terreno medido (la lengua no cambia). Con
  // ella se reparten los títulos de la edición para que ninguno se repita de más
  // (herramientas/repartir.js → edicion/variantes.js).
  MT.nombra = function (T, seed, variante = 0) {
    LENGUA = lenguaDe(T, seed); COMPS_USADOS = new Set(); VARIANTE = variante;
    const r = MT.rng(seed + ':toponimia' + (variante ? ':v' + variante : '')), M = medidas(T), usados = new Set(), gensUsados = new Set(), out = [];
    // la cima con nombre más cercana a un punto (para LA LAGUNA DEL CERRAJÓN)
    const vecinoDe = (u, v, rmax) => { let b = null, dm = rmax; for (const n of out) if (n.clase === 'cumbre' && n.gen && Math.hypot(n.u - u, n.v - v) < dm) { dm = Math.hypot(n.u - u, n.v - v); b = n.gen; } return b; };
    const sobreAgua = (q) => !T.nivelMar || q.h > T.nivelMar + 0.005;
    if (T.arq === 'atolon' && T.base + T.relieve < 50) return nombraAtolon(T, r);
    const cimas = (T.rasgos.picos || []).filter((q) => q.prom >= 0.06 && sobreAgua(q) && q.u > 0.04 && q.u < 0.96 && q.v > 0.04 && q.v < 0.96).slice(0, 5);
    cimas.forEach((q, i) => {
      const med = deCima(T, M, q, cimas, i);
      if (MT._registroMed) MT._registroMed.push(med);
      const g = i === 0 && gemelas(q, cimas[1], med, r);
      if (g) { out.push({ u: q.u, v: q.v, h: q.h, clase: 'cumbre', ...g }); usados.add(g.nombre); return; }
      // EL DESIERTO DE LOS LEONES: contradictorio pero cierto. "Desierto" es lugar solitario y
      // retirado (los desiertos carmelitas), y al puma en México le decían león: un bosque alto
      // de oyamel, lejos de todo, en la sierra. Raro.
      if (i === 0 && !med.polar && !med.seco && med.altM > 2700 && med.altM < 3700 && med.aislado && r() < 0.12) {
        out.push({ u: q.u, v: q.v, h: q.h, clase: 'cumbre', nombre: 'EL DESIERTO DE LOS LEONES', glosa: 'the desert of the lions: a secluded fir forest where pumas roam', generico: 'desierto', fuente: 'paradójico pero cierto: desierto = lugar solitario y retirado (Moliner); león = puma en el habla de México' });
        usados.add('EL DESIERTO DE LOS LEONES'); return;
      }
      out.push({ u: q.u, v: q.v, h: q.h, clase: 'cumbre', ...arma('cumbre', med, r, usados, gensUsados) });
    });
    // el paso entre la segunda cima y la primera
    // los collados de la segunda y la tercera cima (la lámina rotula el de su segunda cima visible)
    const cols = [cimas[1], cimas[2]].filter((q) => q && q.col && sobreAgua(q.col)).map((q) => q.col).filter((c, i, a) => a.findIndex((o) => Math.hypot(o.u - c.u, o.v - c.v) < 0.02) === i);
    for (const col of cols) {
      const p = M.pendiente(col.u, col.v, 0.02);
      const med = { bajo: col.h < 0.4, estrecho: Math.abs(p) > 0.25, ancho: Math.abs(p) <= 0.12, enCadena: ['cordillera', 'pliegues', 'rift'].includes(T.arq), rumbo: null };
      out.push({ u: col.u, v: col.v, h: col.h, clase: 'paso', ...arma('paso', med, r, usados, gensUsados) });
    }
    // hondonadas: cráteres, dolinas, sumideros, el fondo del cañón
    for (const e of (T.rasgos.especiales || []).filter((e) => ['crater', 'fondo'].includes(e.tipo)).slice(0, 2)) {
      const a = M.anillo(e.u, e.v, 0.02), b = M.anillo(e.u, e.v, 0.05);
      const med = { chico: (e.dato || '').match(/Ø 0\.[0-4]/) != null, arq: T.arq, roca: rocaDe(T.arq), poniente: e.u < 0.33, circular: M.desv(b) < 0.06, escarpado: (M.prom(a) - e.h) * M.mPorH / (0.02 * M.mPorU) > 0.3, hondo: (M.prom(b) - e.h) * M.mPorH > 80, rumbo: null };
      out.push({ u: e.u, v: e.v, h: e.h, clase: 'hondonada', ...arma('hondonada', med, r, usados, gensUsados, vecinoDe(e.u, e.v, 0.2)) });
    }
    // lagos
    for (const l of ((T.hidro && T.hidro.lagos) || []).slice(0, 3)) out.push({ u: l.u, v: l.v, h: l.nivel, clase: 'lago', ...arma('lago', { chico: l.area < 400, nacimiento: false, arq: T.arq, roca: rocaDe(T.arq), juntoCumbre: !!vecinoDe(l.u, l.v, 0.12) }, r, usados, gensUsados, vecinoDe(l.u, l.v, 0.25)) });
    // el agua: ríos largos y caudalosos, el mar, la playa, la boca del delta (loop 35)
    nombraAgua(T, M, r, usados, gensUsados, out, vecinoDe);
    nombraEspeciales(T, r, usados, out, vecinoDe);
    // dos rasgos con el mismo nombre: el de más arriba y el de más abajo (como LA LAGUNA DE ARRIBA)
    const porNombre = {};
    for (const n of out) { const base = n.nombre.replace(/ (II|III)$/, ''); (porNombre[base] = porNombre[base] || []).push(n); }
    for (const [base, ns] of Object.entries(porNombre)) {
      if (ns.length < 2) continue;
      ns.sort((a, b) => b.h - a.h);
      ns.forEach((n, k) => { n.nombre = base + (k === 0 ? ' DE ARRIBA' : k === ns.length - 1 ? ' DE ABAJO' : ' DE EN MEDIO'); n.glosa += k === 0 ? ', upper' : k === ns.length - 1 ? ', lower' : ', middle'; });
    }
    // desde la sexta variante, la lámina puede llamarse como su segunda cima (al repartir)
    if (variante >= 6 && out[1] && out[1].clase === 'cumbre' && out[0].clase === 'cumbre') { const t = out[0]; out[0] = out[1]; out[1] = t; }
    return out;
  };
})(typeof globalThis !== 'undefined' ? globalThis : window);
