// Traduce el inventario inglés del lector a los controles actuales de VozAgua.
// Los diptongos se vuelven transiciones de dos vocales. R_EN evita confundirse
// con R, que en el inventario español de Difonos significa rr.
(function (root) {
  'use strict';
  var DIPTONGOS = {AW:['AA','UH'],AY:['AA','IH'],EY:['EH','IY'],OW:['AO','UW'],OY:['AO','IH']};
  function adaptar(fonemas) {
    return fonemas.reduce(function (out, f) {
      if (DIPTONGOS[f]) out.push.apply(out, DIPTONGOS[f]);
      else out.push(f === 'R' ? 'R_EN' : f);
      return out;
    }, []);
  }
  var api = { adaptar:adaptar, DIPTONGOS:DIPTONGOS, version:'siringua-arpabet-adapter-1' };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SiringuaFonemas = api;
})(typeof window !== 'undefined' ? window : globalThis);
