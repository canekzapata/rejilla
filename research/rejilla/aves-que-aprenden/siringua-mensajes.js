/* Une cada mensaje de la cola con lector de Difonos, agua y respuesta de pájaro. */
(function (root, factory) {
  const api = factory(
    typeof module !== 'undefined' && module.exports ? require('../../../difonos/runtime/lector.js') : root.DifonosLector,
    typeof module !== 'undefined' && module.exports ? require('../objetos/motor/vozagua.js') : root.VozAgua,
    typeof module !== 'undefined' && module.exports ? require('../objetos/motor/pajaro.js') : root.Pajaro,
    typeof module !== 'undefined' && module.exports ? require('./adaptador-siringua.js') : root.SiringuaFonemas
  );
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SiringuaMensajes = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Lector, Agua, Pajaro, Adaptador) {
  'use strict';

  function mapPhones(phones, language) {
    return language === 'en-US' ? Adaptador.adaptar(phones) : phones.slice();
  }

  async function preparar(item, { language, semilla = 181026, lector = Lector.readAsync } = {}) {
    if (language !== 'en-US' && language !== 'es-MX') throw new Error('El mensaje necesita idioma explícito: en-US o es-MX.');
    if (!item || typeof item.text !== 'string') throw new TypeError('El elemento de cola debe contener text.');
    const lectura = await lector(item.text, { language });
    if (!lectura.words.length) throw new Error(`El mensaje ${item.id} no contiene palabras para cantar.`);
    if (lectura.unresolved.length) throw new Error(`El mensaje ${item.id} contiene palabras sin resolver; no se canta incompleto.`);
    const agua = [], ave = [];
    let t = .16;
    lectura.words.forEach((word, i) => {
      const phones = mapPhones(word.phones, language);
      const vowels = phones.filter(p => Agua.FORMANTES[p]).length;
      if (!vowels) throw new Error(`La palabra «${word.text}» no produjo vocales reconocibles por VozAgua.`);
      const consonants = phones.length - vowels;
      const duration = Math.max(.28, vowels * .12 + consonants * .075);
      agua.push({ t, dur:duration, texto:word.text, fonemas:phones,
        nota:55 + [0,2,4,2][i % 4], modo:'canto', voz:1, v:.68 });
      const birdAt = t + duration + .07;
      const base = 65 + [0,2,5,7][(vowels + i) % 4];
      ave.push({ t:birdAt, dur:.19, tipo:'canto',
        notas:[[0,base,.065],[.085,base + [3,5,2,4][i % 4],.07]], voz:1, v:.48 });
      t = birdAt + .25;
    });
    return { id:item.id, source:item.source, messageId:item.messageId, version:item.version,
      language, originalText:item.originalText ?? item.text, text:item.text,
      provider:lectura.provider, words:lectura.words, unresolved:lectura.unresolved,
      seed:semilla, duration:t + .32, waterEvents:agua, birdEvents:ave };
  }

  function mezclar(a, b) {
    const out = new Float32Array(Math.max(a.length,b.length));
    let peak=0;
    for(let i=0;i<out.length;i++){ out[i]=(a[i]||0)*.78+(b[i]||0)*.72; peak=Math.max(peak,Math.abs(out[i])); }
    if(peak>.94) for(let i=0;i<out.length;i++) out[i]*=.94/peak;
    return out;
  }

  function render(canto, sampleRate = 24000) {
    const water=Agua.render({dur:canto.duration,eventos:canto.waterEvents,semilla:canto.seed},sampleRate);
    const bird=Pajaro.render({dur:canto.duration,eventos:canto.birdEvents,semilla:canto.seed+1},sampleRate);
    return { samples:mezclar(water,bird), water, bird, sampleRate, duration:canto.duration };
  }

  return { preparar, render, version:'siringua-message-composer-1' };
});
