/* Adaptador asíncrono de eSpeak NG WASM al contrato del lector Difonos. */
(function (root) {
  'use strict';

  var IPA_TO_ARPA = {
    'ɑ':'AA', 'æ':'AE', 'ʌ':'AH', 'ə':'AH', 'ɐ':'AH', 'ɔ':'AO', 'aʊ':'AW', 'aɪ':'AY', 'ɛ':'EH',
    'ɜ':'ER', 'ɝ':'ER', 'ɚ':'ER', 'eɪ':'EY', 'ɪ':'IH', 'ᵻ':'IH', 'i':'IY', 'oʊ':'OW', 'ɔɪ':'OY',
    'ʊ':'UH', 'u':'UW', 'b':'B', 'tʃ':'CH', 'd':'D', 'ð':'DH', 'f':'F',
    'ɡ':'G', 'g':'G', 'h':'HH', 'dʒ':'JH', 'k':'K', 'l':'L', 'ɫ':'L', 'm':'M',
    'n':'N', 'ŋ':'NG', 'p':'P', 'ɹ':'R', 'r':'R', 's':'S', 'ʃ':'SH',
    't':'T', 'θ':'TH', 'v':'V', 'w':'W', 'ʍ':'W', 'j':'Y', 'z':'Z', 'ʒ':'ZH', 'ɾ':'D', 'ʔ':'T'
  };
  var VOWELS = new Set(['AA','AE','AH','AO','AW','AY','EH','ER','EY','IH','IY','OW','OY','UH','UW']);
  var CONTEXTUAL = new Set(['read','lead','wind','tear','bass','record','live','close','use','present','object','content','minute','does','wound']);
  var loaderPromise = null;

  function moduleFactory(options) {
    if (options && options.moduleFactory) return options.moduleFactory;
    if (typeof module !== 'undefined' && module.exports) return require('./espeak-wasm/difonos-espeak-en.js');
    if (typeof root.createDifonosEspeak === 'function') return root.createDifonosEspeak;
    throw new Error('Carga runtime/espeak-wasm/difonos-espeak-en.js antes de crear el lector eSpeak.');
  }

  function phonemesOf(ipa) {
    var transcription = String(ipa || ''), symbols = Array.from(transcription.replace(/[\u200c\u200d]/g, ''));
    var phones = [], ipaPhones = [], stressPositions = [], stress = null, i = 0;
    while (i < symbols.length) {
      if (/\s/.test(symbols[i]) || symbols[i] === '|' || /[ːˑ.]/.test(symbols[i])) { i++; continue; }
      if (symbols[i] === 'ˈ' || symbols[i] === 'ˌ') { stress = symbols[i] === 'ˈ' ? 'primary' : 'secondary'; i++; continue; }
      var pair = symbols.slice(i, i + 2).join('');
      if (IPA_TO_ARPA[pair]) {
        phones.push(IPA_TO_ARPA[pair]); ipaPhones.push(pair);
        if (stress) stressPositions.push({index:phones.length - 1,level:stress});
        stress = null; i += 2; continue;
      }
      var one = symbols[i];
      if (IPA_TO_ARPA[one]) {
        phones.push(IPA_TO_ARPA[one]); ipaPhones.push(one);
        if (stress) stressPositions.push({index:phones.length - 1,level:stress});
        stress = null; i++; continue;
      }
      return {phones:phones,ipa:ipaPhones,stress:stressPositions,transcription:transcription,unknown:one};
    }
    return {phones:phones,ipa:ipaPhones,stress:stressPositions,transcription:transcription.replace(/\|/g, ''),unknown:null};
  }

  function create(options) {
    options = options || {};
    if (!loaderPromise) loaderPromise = Promise.resolve().then(function () {
      var factory = moduleFactory(options), moduleOptions = Object.assign({}, options.moduleOptions || {});
      if (!moduleOptions.locateFile && typeof module !== 'undefined' && module.exports) {
        var path = require('path');
        moduleOptions.locateFile = function (file) { return path.join(__dirname, 'espeak-wasm', file); };
      }
      return factory(moduleOptions);
    });
    return loaderPromise.then(function (wasm) {
      function phonemizeWord(word) {
        var ptr = wasm._malloc(wasm.lengthBytesUTF8(word) + 1);
        try {
          wasm.stringToUTF8(word, ptr, wasm.lengthBytesUTF8(word) + 1);
          var result = wasm._difonos_phonemize(ptr);
          return wasm.UTF8ToString(result);
        } finally { wasm._free(ptr); }
      }
      function read(text, readOptions) {
        readOptions = readOptions || {};
        text = String(text);
        var lang = readOptions.language || readOptions.idioma;
        if (lang !== 'en-US') throw new Error('eSpeak WASM cubre en-US; para es-MX usa el lector español.');
        var re = /[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*|\d+|[^\s]/gu, match, words = [], pauses = [], omitted = [];
        while ((match = re.exec(text))) {
          var token = match[0], start = match.index, end = re.lastIndex;
          if (/^[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*$/u.test(token)) {
            var result = phonemesOf(phonemizeWord(token));
            var contextual = CONTEXTUAL.has(token.toLowerCase().replace(/[’]/g, "'"));
            var item = {text:token, start:start, end:end, phones:result.phones, ipa:result.ipa, transcription:result.transcription,
              inventory:'arpabet-en-US', language:lang, source:'espeak-ng-wasm-1.53.0',
              status:result.unknown ? 'partial' : contextual ? 'ambiguous-default' : result.phones.length ? 'read' : 'unresolved',
              stress:result.stress, syllables:null, note:result.unknown ? 'unknown-ipa:' + result.unknown : contextual ? 'Homógrafo: eSpeak da una lectura por defecto; aplica corrections si el contexto pide otra.' : null};
            item.vowels = item.phones.filter(function (phone) { return VOWELS.has(phone); });
            words.push(item);
          } else if (/^\d+$/.test(token)) omitted.push({text:token,start:start,end:end,reason:'number-not-pronounced'});
        }
        var pauseRe = /[,.!?;:…—\n]+/g;
        while ((match = pauseRe.exec(text))) pauses.push({start:match.index,end:pauseRe.lastIndex,text:match[0],kind:/[.!?…]/.test(match[0])?'sentence':'phrase'});
        return {schema:'difonos-reading-1',text:text,language:lang,provider:'espeak-ng-wasm-1.53.0',words:words,
          pauses:pauses,unresolved:words.filter(function (word) { return word.status !== 'read'; }).map(function (word) {
            return {text:word.text,start:word.start,end:word.end,status:word.status,note:word.note};
          }), omitted:omitted, policy:{numbers:'preserved-in-original-not-pronounced',lineBreaks:'sentence-pause',
            punctuation:'preserved-as-pause',stress:'not exposed by current formant adapter'}};
      }
      return {read:read, phonemizeWord:phonemizeWord, version:'espeak-ng-wasm-1.53.0'};
    });
  }

  var api = {create:create, phonemesOf:phonemesOf, version:'espeak-ng-wasm-1.53.0'};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.DifonosEspeakEn = api;
})(typeof window !== 'undefined' ? window : globalThis);
