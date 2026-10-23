/* objeto.js — un instrumento físico que cambia de naturaleza (loop 10 de la rejilla, «objetos que cantan»).
 *
 * Un solo lazo de guía de onda (un tubo), muestra por muestra, con tres maneras de excitarlo que se mezclan:
 *   caña   (saxofón): tubo cónico (dos retardos, posición de la boquilla) + tabla de caña no lineal (STK Saxofony)
 *   chorro (flauta):  tubo cilíndrico + retardo del chorro + no linealidad cúbica, con soplo ruidoso (STK Flute)
 *   golpe  (percusión): el mismo tubo sin soplo, golpeado, con dispersión (alpasos en el lazo) que vuelve los
 *          armónicos inarmónicos, como una barra o un tubo de metal
 * Los pesos de las tres y los parámetros del tubo (conicidad, pérdida, brillo, dispersión) cambian con el tiempo:
 * la transformación es física (el mismo lazo cambia de excitación y de material), no un fundido de dos grabaciones.
 *
 *   Objeto.render(control, sr) → Float32Array      control: {dur, f(t), w(t) → [caña, chorro, golpe], soplo(t),
 *                                                      ruido(t), pos(t), perdida(t), brillo(t), disp(t), golpes:[[t, v]], vibrato}
 * Sin dependencias: corre en node (renders) y en el navegador.
 */
(function (global) {
  'use strict';
  function Retardo(max) { this.b = new Float64Array(max); this.i = 0; this.d = 1; }
  Retardo.prototype.lee = function () {                 // lectura fraccionaria (interpolación lineal)
    var n = this.b.length, r = this.i - this.d; while (r < 0) r += n;
    var i0 = Math.floor(r), f = r - i0; return this.b[i0 % n] * (1 - f) + this.b[(i0 + 1) % n] * f;
  };
  Retardo.prototype.escribe = function (x) { this.b[this.i] = x; this.i = (this.i + 1) % this.b.length; };

  // STK Saxofony: offset .7, pendiente +0.3 (con −0.3, la del clarinete, el saxofón no oscilaba: medido); oscila con soplo ≥ 0.8
  var tablaCana = function (x) { var y = .7 + .3 * x; return y > 1 ? 1 : y < -1 ? -1 : y; };
  var tablaChorro = function (x) { var y = x * (x * x - 1); return y > 1 ? 1 : y < -1 ? -1 : y; };    // STK JetTable

  // ruido sembrado (xorshift): el mismo control da siempre el mismo sonido
  function rngDe(semilla) { var h = semilla >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }

  /* tres lazos completos en paralelo, afinados a la misma nota y acoplados (κ): cada uno oscila por su cuenta.
   * Mezclar las tres excitaciones en UN lazo dejaba la mitad del impulso a cada una y a medio camino ninguna oscilaba
   * (medido: sax → flauta sin altura en el tercio medio). Aquí la transformación mueve el AIRE de un lazo a otro: el
   * soplo de cada viento es nominal × (0.6 + 0.4 w), así que al bajar su peso cruza su umbral y deja de oscilar
   * (se vuelve aire) y el otro la alcanza; el acoplamiento hace que cada lazo resuene con los otros (simpatía). */
  function Lazo(maxD) { this.A = new Retardo(maxD); this.B = new Retardo(maxD); this.J = new Retardo(maxD); this.lp = 0; this.dcx = 0; this.dcy = 0;
                        this.ap = [0, 0, 0, 0, 0, 0]; this.apX = [0, 0, 0, 0, 0, 0]; this.sal = 0; }
  Lazo.prototype.disp = function (x, a) {
    if (a === 0) return x;
    for (var k = 0; k < 6; k++) { var yk = a * x + this.apX[k] - a * this.ap[k]; this.apX[k] = x; this.ap[k] = yk; x = yk; }
    return x;
  };
  /* la barra: síntesis modal. Seis modos (resonadores de dos polos) cuyas razones se deslizan de los armónicos de un
   * tubo (k·f) a los modos de una barra libre (1 : 2.756 : 5.404 : 8.933 : 13.345 : 18.638) según u: la geometría
   * cambia. (Con una cadena de alpasos en el lazo los parciales sólo se estiraban como una cuerda rígida: 1 : 1.98 :
   * 3.0 : 4.07, medido.) Los modos altos se apagan antes, como en un objeto real. */
  var BARRA = [1, 2.756, 5.404, 8.933, 13.345, 18.638];
  function Modal(sr) { this.sr = sr; this.y1 = new Float64Array(6); this.y2 = new Float64Array(6); this.c1 = new Float64Array(6); this.c2 = new Float64Array(6); this.g = new Float64Array(6); }
  Modal.prototype.afina = function (f, u, t60) {
    for (var k = 0; k < 6; k++) {
      var fk = f * ((k + 1) + (BARRA[k] - (k + 1)) * u); if (fk > this.sr * .45) { this.g[k] = 0; continue; }
      var R = Math.pow(10, -3 / (t60 / (1 + k * .7) * this.sr)), w = 2 * Math.PI * fk / this.sr;
      this.c1[k] = 2 * R * Math.cos(w); this.c2[k] = -R * R; this.g[k] = (1 - R) * [1, .7, .5, .35, .25, .18][k] * 24;   // ×24: con ×6 la barra sonaba 10 veces más baja que el saxofón (medido)
    }
  };
  Modal.prototype.tick = function (x) {
    var s = 0;
    for (var k = 0; k < 6; k++) { var y = this.c1[k] * this.y1[k] + this.c2[k] * this.y2[k] + this.g[k] * x; this.y2[k] = this.y1[k]; this.y1[k] = y; s += y; }
    return s;
  };

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), r = rngDe(c.semilla || 7), maxD = Math.ceil(sr / 20) + 8;
    var Lc = new Lazo(maxD), Lj = new Lazo(maxD), Lg = { sal: 0 }, M = new Modal(sr), KAPPA = c.acople == null ? .06 : c.acople;
    var golpes = (c.golpes || []).map(function (g) { return [Math.round(g[0] * sr), g[1]]; }), gi = 0, chispa = 0;
    var BLOQUE = 32, P = {}, S = PURO.saxofon, F = PURO.flauta, G = PURO.golpe;
    for (var i = 0; i < n; i++) {
      if (i % BLOQUE === 0) {                                   // controles por bloque (cada 0.7 ms)
        var t = i / sr, w = c.w(t), sw = w[0] + w[1] + w[2] || 1;
        P.wc = w[0] / sw; P.wj = w[1] / sw; P.wg = w[2] / sw;
        // el vibrato es de AIRE (presión), como en un viento real: modular el largo del tubo lo hacía saltar de registro
        var f = c.f(t), vib = c.vibrato ? c.vibrato[1] * Math.sin(2 * Math.PI * c.vibrato[0] * t) * Math.min(1, t / .6) : 0;
        var env = c.soplo(t) * (1 + vib);                       // la respiración (0-1)
        P.bc = P.wc > 0 ? S.soplo * env * (.6 + .4 * P.wc) : 0; P.bj = P.wj > 0 ? F.soplo * env * (.6 + .4 * P.wj) : 0;
        P.pos = c.pos(t); P.disp = c.disp(t); P.a = -.25 * P.disp;   // en los vientos, la dispersión es suave (rigidez)
        // largos: caña L − .5, chorro L − 2, barra L − 1, menos el retardo de los alpasos ((1 − a)/(1 + a) por etapa)
        var dd = P.a !== 0 ? 6 * (1 - P.a) / (1 + P.a) : 0, L = sr / f;
        var lc = Math.max(2, L - .5 - dd), lj = Math.max(2, L - 2 - dd);
        M.afina(f, Math.min(1, P.disp / G.disp), c.t60 ? c.t60(t) : 1.6);   // disp: de tubo (0) a barra (G.disp)
        Lc.A.d = Math.max(1, (1 - P.pos) * lc); Lc.B.d = Math.max(1, P.pos * lc);
        Lj.A.d = lj; Lj.J.d = Math.max(1, .32 * lj);
        P.gc = Math.sqrt(P.wc); P.gj = Math.sqrt(P.wj); P.gg = Math.sqrt(P.wg);
      }
      while (gi < golpes.length && golpes[gi][0] <= i) { chispa = Math.round(.002 * sr); P.vg = golpes[gi][1] * Math.sqrt(P.wg); gi++; }
      var exc = 0; if (chispa > 0) { exc = r() * P.vg * (chispa / (.002 * sr)); chispa--; }
      var simp = KAPPA * (Lc.sal + Lj.sal + Lg.sal);            // lo que los tres lazos dejan sonar en el aire

      // caña (STK Saxofony): tubo cónico (dos retardos; pos → 0 lo vuelve cilíndrico, como un clarinete)
      var yA = Lc.A.lee(), yB = Lc.B.lee(); Lc.lp = (1 - S.brillo) * yA + S.brillo * Lc.lp;
      var x = Lc.disp(Lc.lp, P.a), sop = P.bc * (1 + S.ruido * r());
      var temp = -S.perdida * x, sal = temp - yB, pd = sop - sal, ent = sop - pd * tablaCana(pd) - temp + simp - KAPPA * Lc.sal;
      Lc.A.escribe(ent > 3 ? 3 : ent < -3 ? -3 : ent); Lc.B.escribe(temp); Lc.sal = sal;
      // chorro (STK Flute)
      var yJ = Lj.A.lee(); Lj.lp = (1 - F.brillo) * yJ + F.brillo * Lj.lp;
      var xj = Lj.disp(Lj.lp, P.a); Lj.dcy = xj - Lj.dcx + .995 * Lj.dcy; Lj.dcx = xj; var tf = Lj.dcy, sopj = P.bj * (1 + F.ruido * r());
      Lj.J.escribe(sopj - .5 * tf); var entj = tablaChorro(Lj.J.lee()) + .5 * tf + simp - KAPPA * Lj.sal;
      Lj.A.escribe(entj > 3 ? 3 : entj < -3 ? -3 : entj); Lj.sal = yJ;
      // barra (modal): la chispa del golpe y lo que los vientos dejan sonar (simpatía)
      var yG = M.tick(exc + (simp - KAPPA * Lg.sal) * .5); Lg.sal = yG;

      y[i] = .3 * (P.gc * sal + P.gj * yJ + P.gg * yG);
    }
    return y;
  }

  // atajos para curvas: constante, o puntos [[t, v]…] interpolados
  function curva(v) {
    if (typeof v === 'function') return v;
    if (!Array.isArray(v) || !Array.isArray(v[0])) return function () { return v; };   // número o vector constante
    return function (t) {
      if (t <= v[0][0]) return v[0][1];
      for (var i = 1; i < v.length; i++) if (t <= v[i][0]) { var u = (t - v[i - 1][0]) / (v[i][0] - v[i - 1][0]); return Array.isArray(v[i][1]) ? v[i][1].map(function (q, k) { return v[i - 1][1][k] + (q - v[i - 1][1][k]) * u; }) : v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u; }
      return v[v.length - 1][1];
    };
  }
  // los tres objetos puros (puntos de partida para las transformaciones)
  var PURO = {
    saxofon: { w: [1, 0, 0], pos: .3, perdida: .95, brillo: .5, disp: 0, soplo: .74, ruido: .08 },   // soplo .74: afinado La2-Mi5; >= .85 sobresopla a la octava
    flauta:  { w: [0, 1, 0], pos: .3, perdida: .95, brillo: .8, disp: 0, soplo: .85, ruido: .18 },   // brillo .8 + soplo .85: 22/23 notas afinadas (La2-Sol4)
    golpe:   { w: [0, 0, 1], pos: .3, perdida: .985, brillo: .35, disp: .8, soplo: 0, ruido: 0 }
  };
  // el soplo con que cada objeto toca su nota (barrido medido: herramientas/barrido.js)
  var soploDe = function (obj) { return PURO[obj].soplo; };
  var api = { render: render, curva: curva, PURO: PURO, soploDe: soploDe };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Objeto = api;
})(typeof window !== 'undefined' ? window : globalThis);
