/*
 * English (US) grapheme-to-phoneme reader for Difonos.
 * This is a transparent letter-rule fallback, not a learned model or a claim
 * of perfect English pronunciation. Ambiguous words are marked for review.
 * Phones use ARPABET-style IDs and keep word identity separate from sound.
 */
(function (root) {
  'use strict';

  var VOWELS = new Set(['AA','AE','AH','AO','AW','AY','EH','ER','EY','IH','IY','OW','OY','UH','UW']);
  var AMBIGUOUS = new Set(['read','lead','wind','tear','bass','record','live','close','use','present','object','content','minute','does','wound']);
  var IRREGULAR = {
    the:['DH','AH'], a:['AH'], an:['AE','N'], i:['AY'], eye:['AY'], aye:['AY'], you:['Y','UW'], your:['Y','AO','R'],
    one:['W','AH','N'], once:['W','AH','N','S'], two:['T','UW'], who:['HH','UW'], what:['W','AH','T'],
    said:['S','EH','D'], says:['S','EH','Z'], were:['W','ER'], are:['AA','R'], was:['W','AH','Z'],
    have:['HH','AE','V'], give:['G','IH','V'], does:['D','AH','Z'], done:['D','AH','N'], come:['K','AH','M'],
    some:['S','AH','M'], love:['L','AH','V'], move:['M','UW','V'], prove:['P','R','UW','V'],
    people:['P','IY','P','AH','L'], water:['W','AO','T','ER'], bird:['B','ER','D'], birds:['B','ER','D','Z'],
    choir:['K','W','AY','R'], read:['R','IY','D'], lead:['L','IY','D'], wind:['W','IH','N','D'], tear:['T','EH','R'],
    bass:['B','AE','S'], record:['R','EH','K','ER','D'], live:['L','IH','V'], close:['K','L','OW','S'],
    present:['P','R','EH','Z','AH','N','T'], object:['AA','B','JH','EH','K','T'], content:['K','AA','N','T','EH','N','T'],
    minute:['M','IH','N','AH','T'], wound:['W','AW','N','D'], colonel:['K','ER','N','AH','L'], one:['W','AH','N'],
    their:['DH','EH','R'], there:['DH','EH','R'], "they're":['DH','EH','R'], our:['AW','ER'], hour:['AW','ER'],
    through:['TH','R','UW'], though:['DH','OW'], thought:['TH','AO','T'], enough:['IH','N','AH','F'], laugh:['L','AE','F'],
    island:['AY','L','AH','N','D'], listen:['L','IH','S','AH','N'], answer:['AE','N','S','ER'], people:['P','IY','P','AH','L'],
    rhythm:['R','IH','DH','AH','M'], beautiful:['B','Y','UW','T','AH','F','AH','L'], queue:['K','Y','UW'],
    "don't":['D','OW','N','T'], "doesn't":['D','AH','Z','AH','N','T'], "can't":['K','AE','N','T'], "won't":['W','OW','N','T'],
    "it's":['IH','T','S'], "i'm":['AY','M'], "i've":['AY','V'], "i'll":['AY','L'], "we're":['W','IH','R'],
    "what's":['W','AH','T','S'], "who's":['HH','UW','Z'], "wasn't":['W','AH','Z','AH','N','T'], "didn't":['D','IH','D','AH','N','T']
  };

  function splitGraphemes(word) {
    var w = word.toLowerCase().replace(/[’]/g, "'");
    var out = [], i = 0;
    // Ordered longest first. These rules cover common spellings; irregular and
    // context-dependent words stay visible in the result's status field.
    var rules = [
      ['tion',['SH','AH','N']], ['sion',['ZH','AH','N']], ['tch',['CH']], ['dge',['JH']], ['igh',['AY']],
      ['ough',['AH','F']], ['eigh',['EY']],
    ['ch',['CH']], ['sh',['SH']], ['th',['TH']], ['ph',['F']], ['ng',['NG']], ['qu',['K','W']],
      ['ck',['K']], ['wh',['W']], ['wr',['R']], ['kn',['N']], ['gn',['N']], ['mb',['M']],
      ['ee',['IY']], ['ea',['IY']], ['oo',['UW']], ['oa',['OW']], ['ow',['OW']], ['ou',['AW']],
      ['oi',['OY']], ['oy',['OY']], ['ai',['EY']], ['ay',['EY']], ['ei',['EY']], ['ey',['EY']],
      ['ar',['AA','R']], ['er',['ER']], ['ir',['ER']], ['ur',['ER']], ['or',['AO','R']],
      ['au',['AO']], ['aw',['AO']], ['ew',['UW']], ['ue',['UW']], ['ie',['IY']],
      ['c',['K']], ['g',['G']], ['x',['K','S']], ['j',['JH']], ['y',['Y']],
      ['a',['AE']], ['e',['EH']], ['i',['IH']], ['o',['AA']], ['u',['AH']],
      ['b',['B']], ['d',['D']], ['f',['F']], ['h',['HH']], ['k',['K']], ['l',['L']], ['m',['M']],
      ['n',['N']], ['p',['P']], ['r',['R']], ['s',['S']], ['t',['T']], ['v',['V']], ['w',['W']], ['z',['Z']],
      ["'",[]], ['-',[' ']]
    ];
    while (i < w.length) {
      var found = false;
      for (var r = 0; r < rules.length; r++) {
        var g = rules[r][0];
        if (w.slice(i, i + g.length) !== g) continue;
        // Silent final e; preserve the long-vowel hint by changing a preceding
        // simple vowel in consonant-vowel-e patterns.
        if (g === 'e' && i === w.length - 1 && i > 1) {
          if (out.length && out[out.length - 1] === 'AE') out[out.length - 1] = 'EY';
          else if (out.length && out[out.length - 1] === 'EH') out[out.length - 1] = 'IY';
          else if (out.length && out[out.length - 1] === 'IH') out[out.length - 1] = 'AY';
          else if (out.length && out[out.length - 1] === 'AA') out[out.length - 1] = 'OW';
          i++; found = true; break;
        }
        var phones = rules[r][1];
        if (g === 'c' && /[eiy]/.test(w[i + 1] || '')) phones = ['S'];
        if (g === 'g' && /[eiy]/.test(w[i + 1] || '')) phones = ['JH'];
        if (g === 'y') phones = i === w.length - 1 ? ['IY'] : (!/[aeiouy]/.test(w[i + 1] || '') && i > 0 ? ['IH'] : ['Y']);
        out.push.apply(out, phones); i += g.length; found = true; break;
      }
      if (!found) { out.push('�'); i++; }
    }
    return out.filter(function (p) { return p !== ' '; });
  }

  function word(text, options) {
    options = options || {};
    var key = String(text).toLowerCase().replace(/[’]/g, "'");
    var correction = options.corrections && options.corrections[key];
    var phones = correction ? (Array.isArray(correction) ? correction.slice() : String(correction).trim().split(/\s+/))
      : (IRREGULAR[key] || splitGraphemes(key));
    var unsupported = phones.filter(function (p) { return p === '�'; });
    return {
      text: String(text), phones: phones,
      inventory: 'arpabet-en-US',
      source: correction ? 'correction' : (IRREGULAR[key] ? 'irregular-rules' : 'grapheme-rules'),
      status: unsupported.length ? 'unresolved' : (AMBIGUOUS.has(key) && !correction ? 'ambiguous-default' : 'read'),
      stress: null, syllables: null,
      note: AMBIGUOUS.has(key) && !correction ? 'Homógrafo: el contexto puede cambiar la pronunciación; aplica corrections si hace falta.' : null
    };
  }

  function isVowel(phone) { return VOWELS.has(phone); }
  var api = { word: word, isVowel: isVowel, VOWELS: Array.from(VOWELS), PROVIDER: 'difonos-en-rules-0.1' };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.DifonosG2PEn = api;
})(typeof window !== 'undefined' ? window : globalThis);
