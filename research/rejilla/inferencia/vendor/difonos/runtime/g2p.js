/* g2p.js — texto en español de México → fonemas y difonos. Gemelo de fabrica/g2p.py (mismas reglas, mismos
 * vectores de prueba: pruebas/vectores.json; y una prueba de paridad sobre el corpus).
 * Fonemas de una letra: a e i o u · p b t d k g f s x y C(ch) m n N(ñ) l r R(rr) · # silencio.
 * Navegador: window.DifonosG2P · node: module.exports.
 */
(function (global) {
  'use strict';
  var VOCALES = 'aeiou';
  var X_JOTA = { 'méxico': 1, 'mexico': 1, 'mexicano': 1, 'mexicana': 1, 'mexicanos': 1, 'mexicanas': 1, 'oaxaca': 1, 'texas': 1, 'xavier': 1, 'ximena': 1, 'mexica': 1 };

  function limpiar(t) {
    t = t.toLowerCase().replace(/ñ/g, '\u0001').replace(/ü/g, '\u0002');
    t = t.normalize('NFD').replace(/[̀-ͯ]/g, '');
    return t.replace(/\u0001/g, 'ñ').replace(/\u0002/g, 'ü');
  }

  function palabra(original) {
    var w = limpiar(original).replace(/[^a-zñü]/g, '');
    if (!w) return [];
    if (w === 'y') return ['i'];
    var jota = !!X_JOTA[limpiar(original)], out = [], i = 0, n = w.length;
    while (i < n) {
      var c = w[i], s1 = w[i + 1] || '', s2 = w[i + 2] || '', prev = i ? w[i - 1] : '';
      if (VOCALES.indexOf(c) >= 0) { out.push(c); i++; continue; }
      if (c === 'ü') { out.push('u'); i++; continue; }
      if (c === 'h') { i++; continue; }
      if (c === 'c') {
        if (s1 === 'h') { out.push('C'); i += 2; continue; }
        out.push(s1 === 'e' || s1 === 'i' ? 's' : 'k'); i++; continue;
      }
      if (c === 'q') { out.push('k'); i += s1 === 'u' ? 2 : 1; continue; }
      if (c === 'g') {
        if (s1 === 'u' && (s2 === 'e' || s2 === 'i')) { out.push('g'); i += 2; continue; }
        out.push(s1 === 'e' || s1 === 'i' ? 'x' : 'g'); i++; continue;
      }
      if (c === 'j') { out.push('x'); i++; continue; }
      if (c === 'l' && s1 === 'l') { out.push('y'); i += 2; continue; }
      if (c === 'r') {
        if (s1 === 'r') { out.push('R'); i += 2; continue; }
        out.push(i === 0 || prev === 'n' || prev === 'l' || prev === 's' ? 'R' : 'r'); i++; continue;
      }
      if (c === 'y') { out.push(s1 && (VOCALES.indexOf(s1) >= 0 || s1 === 'ü') ? 'y' : 'i'); i++; continue; }
      if (c === 'z') { out.push('s'); i++; continue; }
      if (c === 'v') { out.push('b'); i++; continue; }
      if (c === 'w') { out.push('u'); i++; continue; }
      if (c === 'ñ') { out.push('N'); i++; continue; }
      if (c === 'x') { if (jota) out.push('x'); else out.push('k', 's'); i++; continue; }
      if ('pbtdkfsmnl'.indexOf(c) >= 0) { out.push(c); i++; continue; }
      i++;
    }
    return out;
  }

  // letra = cualquier letra Unicode o marca combinante (igual que es_letra() en el gemelo Python)
  var CORTE = /([\p{L}\p{M}]+)/u, ES_LETRAS = /^[\p{L}\p{M}]+$/u;

  function frase(texto) {
    var out = ['#'];
    texto.split(CORTE).forEach(function (trozo) {
      if (!trozo) return;
      if (ES_LETRAS.test(trozo)) out.push.apply(out, palabra(trozo));
      else if (/[.,;:!?¿¡—()"«»▓…]/.test(trozo) && out[out.length - 1] !== '#') out.push('#');
    });
    if (out[out.length - 1] !== '#') out.push('#');
    return out;
  }

  function difonos(f) {
    var out = [];
    for (var i = 0; i + 1 < f.length; i++) if (!(f[i] === '#' && f[i + 1] === '#')) out.push(f[i] + f[i + 1]);
    return out;
  }

  var api = { palabra: palabra, frase: frase, difonos: difonos, limpiar: limpiar, FONEMAS: 'aeiou' + 'pbtdkgfsxyCmnNlrR' };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.DifonosG2P = api;
})(typeof window !== 'undefined' ? window : globalThis);
