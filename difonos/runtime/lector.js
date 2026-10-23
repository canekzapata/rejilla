/* Contrato compartido de lectura. Node: require('./lector'); navegador: DifonosLector. */
(function (root) {
  'use strict';
  var EN = typeof module !== 'undefined' && module.exports ? require('./g2p-en.js') : root.DifonosG2PEn;
  var ES = typeof module !== 'undefined' && module.exports ? require('./g2p.js') : root.DifonosG2P;
  var ESPEAK = typeof module !== 'undefined' && module.exports ? require('./espeak-en-wasm.js') : root.DifonosEspeakEn;
  var IPA_EN = {AA:'ɑ',AE:'æ',AH:'ʌ',AO:'ɔ',AW:'aʊ',AY:'aɪ',EH:'ɛ',ER:'ɝ',EY:'eɪ',IH:'ɪ',IY:'i',OW:'oʊ',OY:'ɔɪ',UH:'ʊ',UW:'u',B:'b',CH:'tʃ',D:'d',DH:'ð',F:'f',G:'ɡ',HH:'h',JH:'dʒ',K:'k',L:'l',M:'m',N:'n',NG:'ŋ',P:'p',R:'ɹ',S:'s',SH:'ʃ',T:'t',TH:'θ',V:'v',W:'w',Y:'j',Z:'z',ZH:'ʒ'};
  var IPA_ES = {a:'a',e:'e',i:'i',o:'o',u:'u',p:'p',b:'b',t:'t',d:'d',k:'k',g:'ɡ',f:'f',s:'s',x:'x',y:'ʝ',C:'tʃ',m:'m',n:'n',N:'ɲ',l:'l',r:'ɾ',R:'r'};
  function pauses(text) {
    var out = [], re = /[,.!?;:…—\n]+/g, m;
    while ((m = re.exec(text))) out.push({start:m.index,end:re.lastIndex,text:m[0],kind:/[.!?…]/.test(m[0])?'sentence':'phrase'});
    return out;
  }
  function tokens(text) {
    var re = /[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*|\d+|[^\s]/gu, out = [], m;
    while ((m = re.exec(text))) out.push({text:m[0],start:m.index,end:re.lastIndex});
    return out;
  }
  function read(text, options) {
    options = options || {};
    text = String(text);
    var lang = options.language || options.idioma;
    if (lang !== 'en-US' && lang !== 'es-MX') throw new Error('Indica language: en-US o es-MX.');
    var words = [], unresolved = [], omitted = [], source = lang === 'en-US' ? EN.PROVIDER : 'difonos-es-rules-1';
    tokens(text).forEach(function (tok) {
      if (/^[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*$/u.test(tok.text)) {
        var item;
        if (lang === 'en-US') item = EN.word(tok.text, {corrections:options.corrections});
        else {
          var phones = ES.palabra(tok.text);
          item = {text:tok.text,phones:phones,inventory:'difonos-es-MX',source:'grapheme-rules',status:phones.length?'read':'unresolved',stress:null,syllables:null,note:null};
        }
        item.start = tok.start; item.end = tok.end;
        item.ipa = item.phones.map(function (p) { return (lang === 'en-US' ? IPA_EN[p] : IPA_ES[p]) || null; });
        item.language = lang;
        if (item.status !== 'read') unresolved.push({text:item.text,start:item.start,end:item.end,status:item.status});
        words.push(item);
      } else if (/^\d+$/.test(tok.text)) omitted.push({text:tok.text,start:tok.start,end:tok.end,reason:'number-not-pronounced'});
    });
    return {schema:'difonos-reading-1',text:text,language:lang,provider:source,words:words,pauses:pauses(text),unresolved:unresolved,omitted:omitted,
      policy:{numbers:'preserved-in-original-not-pronounced',lineBreaks:'sentence-pause',punctuation:'preserved-as-pause',stress:'not provided by this rule provider'}};
  }
  function readAsync(text, options) {
    options = options || {};
    var lang = options.language || options.idioma;
    if (lang !== 'en-US' || options.engine === 'rules') return Promise.resolve(read(text, options));
    if (!ESPEAK) return Promise.reject(new Error('Carga runtime/espeak-en-wasm.js para leer inglés con eSpeak NG.'));
    return ESPEAK.create({moduleFactory:options.moduleFactory}).then(function (engine) {
      var result = engine.read(text, options);
      var corrections = options.corrections || {};
      result.words.forEach(function (item) {
        var key = item.text.toLowerCase().replace(/[’]/g, "'");
        if (!Object.prototype.hasOwnProperty.call(corrections, key)) return;
        var phones = Array.isArray(corrections[key]) ? corrections[key].slice() : String(corrections[key]).trim().split(/\s+/);
        item.phones = phones;
        item.ipa = phones.map(function (phone) { return IPA_EN[phone] || null; });
        item.vowels = phones.filter(function (phone) { return EN.isVowel(phone); });
        item.source = 'correction'; item.status = phones.length ? 'read' : 'unresolved'; item.note = null; item.stress = []; item.transcription = null;
      });
      result.unresolved = result.words.filter(function (item) { return item.status !== 'read'; }).map(function (item) {
        return {text:item.text,start:item.start,end:item.end,status:item.status,note:item.note};
      });
      result.policy.stress = 'eSpeak positions are included per word; the current formant instrument does not use them yet';
      return result;
    });
  }
  var api = { read:read, readAsync:readAsync };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.DifonosLector = api;
})(typeof window !== 'undefined' ? window : globalThis);
