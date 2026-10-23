// letra.js — letra de un solo trazo, como plantilla Leroy: la pluma la escribe.
// Cada glifo vive en una rejilla de 6 de alto (0 arriba, 6 en la línea base).
(function (G) {
  const MT = G.MT;
  const O = '1.2,0 3,0 4.2,1.2 4.2,4.8 3,6 1.2,6 0,4.8 0,1.2 1.2,0';
  const GL = {
    A: [4, '0,6 2,0 4,6;0.7,4 3.3,4'],
    B: [4, '0,6 0,0 2.9,0 3.8,0.8 3.8,2.2 2.9,3 0,3;2.9,3 4,3.9 4,5.1 3,6 0,6'],
    C: [4, '4,1 3,0 1,0 0,1 0,5 1,6 3,6 4,5'],
    D: [4, '0,0 0,6 2.4,6 4,4.4 4,1.6 2.4,0 0,0'],
    E: [3.6, '3.6,0 0,0 0,6 3.6,6;0,3 2.8,3'],
    F: [3.6, '3.6,0 0,0 0,6;0,3 2.8,3'],
    G: [4, '4,1 3,0 1,0 0,1 0,5 1,6 3,6 4,5 4,3.4 2.4,3.4'],
    H: [4, '0,0 0,6;4,0 4,6;0,3 4,3'],
    I: [0, '0,0 0,6'],
    J: [3.4, '3.4,0 3.4,5 2.4,6 1,6 0,5'],
    K: [4, '0,0 0,6;4,0 0,4;1.3,2.7 4,6'],
    L: [3.4, '0,0 0,6 3.4,6'],
    M: [4.6, '0,6 0,0 2.3,4 4.6,0 4.6,6'],
    N: [4, '0,6 0,0 4,6 4,0'],
    O: [4.2, O],
    P: [4, '0,6 0,0 3,0 4,1 4,2 3,3 0,3'],
    Q: [4.2, O + ';2.6,4.4 4.4,6.4'],
    'Ø': [4.2, O + ';-0.2,6.6 4.4,-0.6'],
    R: [4, '0,6 0,0 3,0 4,1 4,2 3,3 0,3;2.2,3 4,6'],
    S: [4, '4,1 3,0 1,0 0,1 0,2 1,3 3,3 4,4 4,5 3,6 1,6 0,5'],
    T: [4, '0,0 4,0;2,0 2,6'],
    U: [4, '0,0 0,5 1,6 3,6 4,5 4,0'],
    V: [4, '0,0 2,6 4,0'],
    W: [5.2, '0,0 1.3,6 2.6,1.6 3.9,6 5.2,0'],
    X: [4, '0,0 4,6;4,0 0,6'],
    Y: [4, '0,0 2,3 4,0;2,3 2,6'],
    Z: [4, '0,0 4,0 0,6 4,6'],
    0: [3, '0.8,0 2.2,0 3,1 3,5 2.2,6 0.8,6 0,5 0,1 0.8,0'],
    1: [3, '0.4,1.2 1.6,0 1.6,6'],
    2: [3, '0,1 0.8,0 2.2,0 3,1 3,2 0,6 3,6'],
    3: [3, '0,0.8 0.8,0 2.2,0 3,0.8 3,2 2.2,2.8 1.2,2.8;2.2,2.8 3,3.6 3,5.2 2.2,6 0.8,6 0,5.2'],
    4: [3, '2.3,6 2.3,0 0,4.2 3,4.2'],
    5: [3, '2.9,0 0.3,0 0.1,2.8 2.1,2.6 3,3.4 3,5.2 2.2,6 0.8,6 0,5.2'],
    6: [3, '2.8,0.6 2.1,0 0.9,0 0,1 0,5 0.9,6 2.1,6 3,5 3,3.8 2.1,2.9 0.9,2.9 0,3.8'],
    7: [3, '0,0 3,0 1,6'],
    8: [3, '1,2.9 0.2,2.2 0.2,0.8 1,0 2,0 2.8,0.8 2.8,2.2 2,2.9 1,2.9 0,3.8 0,5.2 0.8,6 2.2,6 3,5.2 3,3.8 2,2.9'],
    9: [3, '0.2,5.4 0.9,6 2.1,6 3,5 3,1 2.1,0 0.9,0 0,1 0,2.2 0.9,3.1 2.1,3.1 3,2.2'],
    ' ': [2.2, ''],
    ' ': [0.5, ''],
    '.': [0.4, '0,5.6 0.4,5.6 0.4,6 0,6 0,5.6'],
    ',': [0.6, '0.4,5.4 0.4,6 0,7'],
    '·': [0.4, '0,2.8 0.4,2.8 0.4,3.2 0,3.2 0,2.8'],
    ':': [0.4, '0,1.6 0.4,1.6 0.4,2 0,2 0,1.6;0,5.6 0.4,5.6 0.4,6 0,6 0,5.6'],
    '-': [2.2, '0,3.2 2.2,3.2'],
    '–': [3.4, '0,3.2 3.4,3.2'],
    '×': [2.4, '0,2 2.4,4.4;2.4,2 0,4.4'],
    '/': [2.6, '0,6.4 2.6,-0.4'],
    '(': [1.2, '1.2,-0.4 0,1.6 0,4.4 1.2,6.4'],
    ')': [1.2, '0,-0.4 1.2,1.6 1.2,4.4 0,6.4'],
    '°': [1.6, '0.4,0 1.2,0 1.6,0.5 1.6,1.1 1.2,1.6 0.4,1.6 0,1.1 0,0.5 0.4,0'],
    '+': [3, '0,3 3,3;1.5,1.5 1.5,4.5'],
    "'": [0, '0,0 0,1.6'],
    '′': [0.6, '0.6,-0.2 0,1.6'],
  };
  const ACENTO = { Á: 'A', É: 'E', Í: 'I', Ó: 'O', Ú: 'U' };
  const parse = (s) => s ? s.split(';').map((p) => p.trim().split(/\s+/).map((q) => q.split(',').map(Number))) : [];
  const glifos = {};
  for (const k in GL) glifos[k] = { w: GL[k][0], l: parse(GL[k][1]) };
  for (const k in ACENTO) {
    const b = glifos[ACENTO[k]], c = b.w / 2;
    glifos[k] = { w: b.w, l: [...b.l, [[c - 0.5, -0.8], [c + 0.7, -2]]] };
  }
  // grave (zapoteco: Ru'a Cuàdì) y diéresis (suomi: Mustajärvi, Kivikkö)
  for (const [k, base] of Object.entries({ À: 'A', È: 'E', Ì: 'I', Ò: 'O', Ù: 'U' })) {
    const b = glifos[base], c = b.w / 2;
    glifos[k] = { w: b.w, l: [...b.l, [[c + 0.5, -0.8], [c - 0.7, -2]]] };
  }
  for (const [k, base] of Object.entries({ Ä: 'A', Ë: 'E', Ï: 'I', Ö: 'O', Ü: 'U' })) {
    const b = glifos[base], c = b.w / 2;
    glifos[k] = { w: b.w, l: [...b.l, [[c - 1.1, -1.1], [c - 1.1, -1.7]], [[c + 1.1, -1.1], [c + 1.1, -1.7]]] };
  }
  { const b = glifos.N, c = b.w / 2;
    glifos['Ñ'] = { w: b.w, l: [...b.l, [[c - 1.4, -1.2], [c - 0.6, -1.9], [c + 0.6, -1.2], [c + 1.4, -1.9]]] }; }

  // Ł (diné, polaco): la L con su barra
  glifos['Ł'] = { w: glifos.L.w, l: [...glifos.L.l, [[-0.4, 3.9], [1.8, 2.5]]] };
  // los apóstrofos de otras ortografías (diné ʼ, hawaiano ʻ, tipográfico ’) son el mismo trazo
  for (const k of ['ʼ', 'ʻ', '’', '‘']) glifos[k] = glifos["'"];

  // Diacríticos sueltos: el texto se descompone (NFD) y cada marca se dibuja sobre la letra
  // que la lleva. Así entran Ą́ (diné), Ṯ Ḻ Ṉ Ṟ (pitjantjatjara: línea abajo), Ā (hawaiano,
  // islandés), Ǩ… sin hacer un glifo por combinación.
  const MARCA = {
    '́': (c) => [[[c - 0.5, -0.8], [c + 0.7, -2]]],                                   // aguda
    '̀': (c) => [[[c + 0.5, -0.8], [c - 0.7, -2]]],                                   // grave
    '̈': (c) => [[[c - 1.1, -1.1], [c - 1.1, -1.7]], [[c + 1.1, -1.1], [c + 1.1, -1.7]]], // diéresis
    '̃': (c) => [[[c - 1.4, -1.2], [c - 0.6, -1.9], [c + 0.6, -1.2], [c + 1.4, -1.9]]], // tilde
    '̄': (c) => [[[c - 1.3, -1.4], [c + 1.3, -1.4]]],                                 // macrón
    '̌': (c) => [[[c - 1, -1.9], [c, -1], [c + 1, -1.9]]],                             // caron
    '̨': (c) => [[[c + 0.9, 6], [c + 0.2, 6.8], [c + 0.6, 7.6], [c + 1.3, 7.4]]],      // ogonek
    '̱': (c) => [[[c - 1.4, 7.3], [c + 1.4, 7.3]]],                                   // línea abajo
    '̲': (c) => [[[c - 1.4, 7.3], [c + 1.4, 7.3]]],
    '̣': (c) => [[[c, 7.1], [c, 7.5]]],                                               // punto abajo
    '̇': (c) => [[[c, -1.1], [c, -1.6]]],                                             // punto arriba
  };
  // racimos: [glifo, ancho] por letra visible, con sus marcas ya puestas
  function racimos(s) {
    const out = [];
    for (const ch of s.normalize('NFC')) {
      if (glifos[ch]) { out.push(glifos[ch]); continue; }
      const [base, ...marcas] = ch.normalize('NFD');
      if (marcas.length === 0 && out.length && MARCA[base]) { // marca suelta: va con la letra anterior
        const g = out[out.length - 1];
        out[out.length - 1] = { w: g.w, l: [...g.l, ...MARCA[base](g.w / 2)] }; continue;
      }
      const g = glifos[base];
      if (!g) { out.push({ w: 2.2, l: [] }); continue; }
      out.push({ w: g.w, l: [...g.l, ...marcas.flatMap((m) => (MARCA[m] ? MARCA[m](g.w / 2) : []))] });
    }
    return out;
  }

  const ESP = 1.4;

  // mide(texto, alto de mayúscula en mm, {track}) → ancho en mm
  // el idioma de la lámina (MT._lang) se aplica aquí, al medir y al escribir; o.crudo (los
  // topónimos) no se traduce
  const enIdioma = (str, o) => (o.crudo || !MT.traduce ? String(str) : MT.traduce(String(str).toUpperCase(), MT._lang));
  function mide(str, size, o = {}) {
    const u = size / 6, tr = o.track || 0, s = enIdioma(str, o).toUpperCase();
    let w = 0; for (const g of racimos(s)) w += g.w + ESP + tr;
    return Math.max(0, (w - ESP - tr) * u);
  }

  // trazos(texto, x, y_base, alto, {slant, track, align}) → {lineas, ancho}
  function trazos(str, x, y, size, o = {}) {
    const u = size / 6, sl = o.slant || 0, tr = o.track || 0, s = enIdioma(str, o).toUpperCase();
    const ancho = mide(s, size, { ...o, crudo: true }); // ya está en su idioma
    let x0 = o.align === 'center' ? x - ancho / 2 : o.align === 'right' ? x - ancho : x;
    const lineas = [];
    for (const g of racimos(s)) {
      for (const l of g.l) lineas.push(l.map(([gx, gy]) => [x0 + (gx + (6 - gy) * sl) * u, y - (6 - gy) * u]));
      x0 += (g.w + ESP + tr) * u;
    }
    return { lineas, ancho };
  }

  MT.letra = { mide, trazos };
})(typeof globalThis !== 'undefined' ? globalThis : window);
