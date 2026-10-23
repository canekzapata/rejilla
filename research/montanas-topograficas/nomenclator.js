// nomenclator.js — todos los nombres de la edición, como un nomenclátor impreso: ordenados por
// el nombre sin su artículo (PICO DE LA NIEVE, EL), con su clase, lengua, lo que dice, su
// fuente y las láminas donde aparece (subrayadas fuerte: donde es el título).
(function () {
  const q = new URLSearchParams(location.search);
  let lang = q.get('lang') === 'en' ? 'en' : 'es';
  const $ = (s) => document.querySelector(s);
  const TXT = {
    es: {
      t: 'NOMENCLÁTOR', intro: (n, l, s) => `Los ${n} nombres de las ${s} láminas de Traspuesta, en ${l} lenguas. Cada uno sale sólo donde el terreno cumple lo que dice: medido de la forma de la cima, del agua, de la roca, de la altura. Los nombres en lenguas indígenas vienen de diccionarios y vocabularios publicados; nada sagrado.`,
      lengua: 'lengua', clase: 'clase', buscar: 'buscar un nombre o un sentido…', titulos: 'sólo los que titulan una lámina', todas: 'todas', todos: 'todos',
      cuenta: (k, n) => `${k} de ${n} nombres`, mas: 'más nombres', fuente: 'fuente', laminas: 'láminas', volver: '← Traspuesta', idioma: 'english',
      pie: 'Nomenclátor de Traspuesta · Canek Zapata · 2026',
    },
    en: {
      t: 'GAZETTEER', intro: (n, l, s) => `The ${n} names on the ${s} plates of Traspuesta, in ${l} languages. Each one appears only where the land fulfills what it says: measured from the shape of the summit, the water, the rock, the altitude. Names in Indigenous languages come from published dictionaries and vocabularies; nothing sacred.`,
      lengua: 'language', clase: 'class', buscar: 'search a name or a meaning…', titulos: 'only names that title a plate', todas: 'all', todos: 'all',
      cuenta: (k, n) => `${k} of ${n} names`, mas: 'more names', fuente: 'source', laminas: 'plates', volver: '← Traspuesta', idioma: 'español',
      pie: 'Gazetteer of Traspuesta · Canek Zapata · 2026',
    },
  };
  const CLASES = {
    es: { cumbre: 'cumbre', paso: 'paso', hondonada: 'hondonada', lago: 'lago', laguna: 'laguna', rio: 'río', mar: 'mar', playa: 'playa', boca: 'boca', especial: 'rasgo del terreno', atolon: 'arrecife', valle: 'valle' },
    en: { cumbre: 'summit', paso: 'pass', hondonada: 'hollow', lago: 'lake', laguna: 'lagoon', rio: 'river', mar: 'sea', playa: 'beach', boca: 'reef pass', especial: 'landform', atolon: 'reef', valle: 'valley' },
  };
  const LENGUA_EN = { castellano: 'Spanish', 'náhuatl': 'Nahuatl', maya: 'Yucatec Maya', quechua: 'Quechua', zapoteco: 'Zapotec', 'rarámuri': 'Rarámuri', 'purépecha': 'Purépecha', 'diné': 'Diné (Navajo)', pitjantjatjara: 'Pitjantjatjara', kalaallisut: 'Kalaallisut', inuttut: 'Inuttut', suomi: 'Finnish', hawaiano: 'Hawaiian', 'islandés': 'Icelandic', mixteco: 'Mixtec', 'tének': 'Tének', dhivehi: 'Dhivehi', 'otomí': 'Otomi (Hñähñu)' };
  const t = (k) => TXT[lang][k];
  const nomLengua = (l) => (lang === 'en' ? LENGUA_EN[l] || l : l);
  const sinAcento = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '');
  // la forma de nomenclátor: el artículo al final (PICO DE LA NIEVE, EL)
  const ART = /^(EL|LA|LOS|LAS) /;
  const clave = (n) => { const m = n.match(ART); return m ? n.slice(m[0].length) + ', ' + m[1] : n; };
  const num = (s) => String(s).padStart(4, '0');

  let N = [], lista = [], mostrados = 0, laminas = 2000;
  const LOTE = 150, f = { lengua: q.get('lengua') || '', clase: q.get('clase') || '', texto: q.get('q') || '', titulos: q.get('titulos') === '1' };

  function textos() {
    document.documentElement.lang = lang === 'en' ? 'en' : 'es-MX';
    $('#t').textContent = t('t');
    $('#intro').textContent = t('intro')(N.length.toLocaleString(lang === 'en' ? 'en-US' : 'es-MX'), new Set(N.map((x) => x.l)).size, laminas.toLocaleString(lang === 'en' ? 'en-US' : 'es-MX'));
    $('#l-lengua').textContent = t('lengua'); $('#l-clase').textContent = t('clase'); $('#l-titulos').textContent = t('titulos');
    $('#f-texto').placeholder = t('buscar'); $('#mas').textContent = t('mas'); $('#pie').textContent = t('pie');
    $('#volver').textContent = t('volver'); $('#volver').href = 'index.html' + (lang === 'en' ? '?lang=en' : '');
    $('#idioma').textContent = t('idioma');
    const cuenta = (g) => { const m = new Map(); for (const x of N) m.set(g(x), (m.get(g(x)) || 0) + 1); return [...m].sort((a, b) => b[1] - a[1]); };
    $('#f-lengua').innerHTML = `<option value="">${t('todas')}</option>` + cuenta((x) => x.l).map(([k, c]) => `<option value="${k}">${nomLengua(k)} · ${c}</option>`).join('');
    $('#f-clase').innerHTML = `<option value="">${t('todas')}</option>` + cuenta((x) => x.c).map(([k, c]) => `<option value="${k}">${CLASES[lang][k] || k} · ${c}</option>`).join('');
    $('#f-lengua').value = f.lengua; $('#f-clase').value = f.clase; $('#f-texto').value = f.texto; $('#f-titulos').checked = f.titulos;
  }
  const SIN = q.get('sin'); // ?sin=castellano: sólo las otras lenguas (lo usa el video)
  function aplica() {
    const tx = sinAcento(f.texto.trim().toLowerCase());
    lista = N.filter((x) => (!f.lengua || x.l === f.lengua) && x.l !== SIN && (!f.clase || x.c === f.clase) && (!f.titulos || x.t.length)
      && (!tx || sinAcento((x.n + ' ' + x.f + ' ' + x.g).toLowerCase()).includes(tx)));
    $('#cuenta').textContent = t('cuenta')(lista.length.toLocaleString(), N.length.toLocaleString());
    $('#lista').innerHTML = ''; mostrados = 0; ultimaLetra = '';
    mas();
    const p = new URLSearchParams();
    if (f.lengua) p.set('lengua', f.lengua); if (f.clase) p.set('clase', f.clase); if (f.texto) p.set('q', f.texto); if (f.titulos) p.set('titulos', '1'); if (lang === 'en') p.set('lang', 'en');
    history.replaceState(null, '', p.toString() ? '?' + p : location.pathname);
  }
  let ultimaLetra = '';
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  function entrada(x) {
    const i = x.f.indexOf(': '), ref = i > 0 ? x.f.slice(0, i) : x.f, dice = i > 0 ? x.f.slice(i + 2) : '';
    const titulos = new Set(x.t);
    const ls = x.s.slice(0, 40).map((s) => `<a href="ver.html?s=${s}${lang === 'en' ? '&lang=en' : ''}"${titulos.has(s) ? ' class="titulo"' : ''}>${num(s)}</a>`).join('') + (x.s.length > 40 ? ` +${x.s.length - 40}` : '');
    return `<div class="entrada"><div class="nom">${esc(x.k)}</div>
      <div class="meta">${CLASES[lang][x.c] || x.c} · ${esc(nomLengua(x.l))}</div>
      ${dice && lang === 'es' ? `<div class="dice">«${esc(dice)}»</div>` : ''}
      ${x.g ? `<div class="glosa">${lang === 'en' ? '“' + esc(x.g) + '”' : 'en inglés: ' + esc(x.g)}</div>` : ''}
      ${ref ? `<div class="fuente">${t('fuente')}: ${esc(ref)}</div>` : ''}
      <div class="laminas">${t('laminas')}: ${ls}</div></div>`;
  }
  function mas() {
    const L = $('#lista'), hasta = Math.min(lista.length, mostrados + LOTE);
    let html = '';
    for (; mostrados < hasta; mostrados++) {
      const x = lista[mostrados], le = sinAcento(x.k[0] || '');
      if (le !== ultimaLetra) { ultimaLetra = le; html += `<div class="letra">${le}</div>`; }
      html += entrada(x);
    }
    L.insertAdjacentHTML('beforeend', html);
    $('#mas').hidden = mostrados >= lista.length;
  }
  new IntersectionObserver((e) => { if (e[0].isIntersecting && mostrados < lista.length) mas(); }, { rootMargin: '800px 0px' }).observe($('#mas'));

  // el color, de una lámina de la edición al azar (o de la que diga ?color=N)
  function color(ED) {
    const pedida = ED.find((x) => String(x[0]) === q.get('color'));
    const fila = pedida || ED[Math.floor(Math.random() * ED.length)], R = document.documentElement.style;
    R.setProperty('--papel', fila[13]); R.setProperty('--tinta', fila[14]);
    R.setProperty('--tenue', `color-mix(in oklch, ${fila[14]} 60%, ${fila[13]})`);
    R.setProperty('--raya', `color-mix(in oklch, ${fila[14]} 25%, ${fila[13]})`);
    document.querySelector('meta[name="theme-color"]').setAttribute('content', fila[13]);
  }

  Promise.all([fetch('edicion/nomenclator.json?v=38').then((r) => r.json()), fetch('edicion/edicion.json?v=38').then((r) => r.json())]).then(([nom, ed]) => {
    laminas = ed.n; color(ed.filas);
    N = nom.map((x) => ({ ...x, k: clave(x.n) })).sort((a, b) => sinAcento(a.k).localeCompare(sinAcento(b.k), 'es'));
    textos(); aplica();
    for (const k of ['lengua', 'clase']) $('#f-' + k).onchange = (e) => { f[k] = e.target.value; aplica(); };
    $('#f-titulos').onchange = (e) => { f.titulos = e.target.checked; aplica(); };
    let tt = null; $('#f-texto').oninput = (e) => { clearTimeout(tt); tt = setTimeout(() => { f.texto = e.target.value; aplica(); }, 220); };
  });
  $('#idioma').onclick = (e) => { e.preventDefault(); lang = lang === 'en' ? 'es' : 'en'; textos(); aplica(); };
  $('#mas').onclick = mas;
})();
