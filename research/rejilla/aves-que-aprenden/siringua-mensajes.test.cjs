const test = require('node:test');
const assert = require('node:assert/strict');
const Difonos = require('../../../difonos/runtime/lector.js');
const Siringua = require('./siringua-mensajes.js');

test('convierte texto nuevo inglés de la cola en agua articulada y respuesta de ave', async () => {
  const item = { id:'teia/10/21/v1/1', source:'teia-channel-message', channelId:'10', messageId:'21', version:1,
    text:'The garden remembers every voice.', originalText:'The garden remembers every voice.' };
  const canto = await Siringua.preparar(item, { language:'en-US', semilla:321 });
  assert.equal(canto.provider, 'espeak-ng-wasm-1.53.0');
  assert.equal(canto.words.length, 5);
  assert.equal(canto.waterEvents.length, 5);
  assert.equal(canto.birdEvents.length, 5);
  assert.ok(canto.waterEvents.flatMap(e => e.fonemas).includes('R_EN'));
  const sound = Siringua.render(canto, 16000);
  assert.equal(sound.samples.length, Math.ceil(canto.duration * 16000));
  assert.ok(sound.samples.every(Number.isFinite));
  assert.ok(Math.max(...sound.samples.slice(0, 16000)) <= .941);
});

test('usa explícitamente las reglas españolas y nunca acepta pronunciación incompleta', async () => {
  const item = { id:'test/es', text:'todavía estoy aquí' };
  const canto = await Siringua.preparar(item, { language:'es-MX', lector:(text, options) => Difonos.readAsync(text,{...options,engine:'rules'}) });
  assert.equal(canto.language, 'es-MX');
  assert.ok(canto.waterEvents.every(event => event.fonemas.some(p => /[aeiou]/.test(p))));
  await assert.rejects(() => Siringua.preparar(item,{language:'auto'}), /idioma explícito/);
  await assert.rejects(() => Siringua.preparar({id:'bad',text:'??'},{language:'en-US'}), /no contiene palabras/);
});
