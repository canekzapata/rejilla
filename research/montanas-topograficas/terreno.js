// terreno.js — la montaña como dato: un campo de alturas sembrado + sus rasgos leídos.
(function (G) {
  const MT = G.MT;

  const ARQ = {
    monte: 'MONTE AISLADO', dos: 'DOS CUMBRES', cordillera: 'CORDILLERA',
    mesa: 'MESA', archi: 'ARCHIPIÉLAGO', canon: 'CAÑÓN',
    estrato: 'ESTRATOVOLCÁN', escudo: 'VOLCÁN ESCUDO', conos: 'CAMPO DE CONOS', impactos: 'CAMPO DE IMPACTOS',
    pliegues: 'SIERRA PLEGADA', dunas: 'CAMPO DE DUNAS', karst: 'KARST', atolon: 'ATOLÓN', meandros: 'LLANURA DE MEANDROS', costa: 'COSTA', anillos: 'ESTRUCTURA DE ANILLOS', drumlins: 'CAMPO DE DRUMLINS', rift: 'RIFT', tepuyes: 'TEPUYES', testigos: 'CERROS TESTIGO', inselbergs: 'INSELBERGS', poligonos: 'POLÍGONOS DE PERMAFROST', badlands: 'TIERRAS MALAS',
  };
  MT.ARQUETIPOS = ARQ;

  // Escala física por arquetipo: ancho del terreno (km), relieve (m), altitud base (m).
  const FIS = {
    monte: { km: [7, 15], rel: [1400, 4200], base: [300, 2400] },
    dos: { km: [9, 18], rel: [1300, 3600], base: [300, 2200] },
    cordillera: { km: [16, 34], rel: [1600, 4400], base: [400, 2600] },
    mesa: { km: [6, 16], rel: [300, 900], base: [800, 2400] },
    canon: { km: [5, 12], rel: [500, 1500], base: [600, 2000] },
    archi: { km: [10, 24], rel: [500, 2200], base: [0, 0] }, // la base es el mar
    estrato: { km: [8, 18], rel: [1500, 4300], base: [400, 2600] },
    pliegues: { km: [18, 38], rel: [900, 2200], base: [300, 1500] },
    dunas: { km: [2.5, 6], rel: [40, 140], base: [200, 900] },
    karst: { km: [4, 10], rel: [70, 220], base: [10, 400] },
    atolon: { km: [8, 22], rel: [300, 900], base: [0, 0] },
    meandros: { km: [6, 14], rel: [90, 320], base: [20, 1200] },
    costa: { km: [8, 24], rel: [600, 2200], base: [0, 0] },
    anillos: { km: [25, 45], rel: [180, 420], base: [200, 600] },
    drumlins: { km: [5, 12], rel: [30, 80], base: [100, 500] },
    rift: { km: [30, 60], rel: [1500, 3000], base: [400, 1200] },
    tepuyes: { km: [15, 30], rel: [900, 1800], base: [300, 900] },
    testigos: { km: [6, 14], rel: [250, 550], base: [1200, 1800] },
    inselbergs: { km: [10, 22], rel: [200, 420], base: [300, 700] },
    poligonos: { km: [0.6, 1.6], rel: [15, 30], base: [20, 300] },
    badlands: { km: [2.5, 6], rel: [80, 220], base: [600, 1800] },
    escudo: { km: [24, 55], rel: [700, 2000], base: [0, 800] },
    conos: { km: [5, 12], rel: [150, 450], base: [1300, 2400] },
    impactos: { km: [4, 16], rel: [0, 0], base: [200, 1800] }, // el relieve lo dan los cráteres
  };

  const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
  const sst = (a, b, x) => { x = clamp((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x); };

  // Capa 1: la figura. Cada arquetipo devuelve f(u,v) ~[0,1] y cuánto detalle tolera.
  function figura(arq, r, N, edad, seed) {
    switch (arq) {
      case 'estrato': {
        // Estratovolcán con edad E ∈ [0,1]: el cono joven es cóncavo y liso, con cráter nítido;
        // con la edad se agranda el cráter (caldera), se abre una brecha, se apagan las coladas
        // y crece la erosión; al final puede quedar sólo el cuello de lava dura.
        const E = edad, cx = 0.5 + r.range(-0.06, 0.06), cy = 0.5 + r.range(-0.04, 0.08);
        const R = r.range(0.32, 0.46), p = r.range(1.5, 2.3);
        const tiroCuello = r(), tiroBrecha = r(); // siempre se tiran: misma montaña a cualquier edad
        const cuello = E > 0.82 && tiroCuello < 0.65;
        const H = cuello ? 0.32 : 1 - 0.35 * Math.max(0, E - 0.45);
        const rc = r.range(0.022, 0.04) * (1 + 3.2 * Math.max(0, E - 0.45));
        const dc = E < 0.5 ? r.range(0.07, 0.12) : r.range(0.05, 0.09);
        const q = 2 + 6 * Math.max(0, E - 0.4); // fondo cada vez más plano
        const brechaP = { a: r.range(0, 6.283), w: r.range(0.5, 1.1), h: dc * r.range(0.6, 1.2) };
        const brecha = E > 0.35 && tiroBrecha < 0.6 ? brechaP : null;
        const cono = (d) => H * Math.pow(Math.max(0, 1 - d / R), p) + 0.07 * Math.exp(-Math.pow(d / (R * 1.5), 2));
        // barrancas: surcos radiales que serpentean y se ahondan ladera abajo (sin ellos el cono es
        // liso y el agua baja en rayos rectos); los jóvenes ya las tienen, someras
        const nB = r.int(14, 26), hondoB = r.range(0.05, 0.09) * (0.7 + 0.6 * E), torsion = r.range(0.25, 0.6);
        const barranca = (dx, dy, d) => {
          if (d < rc * 1.4 || d > R * 1.05) return 0;
          const t = (d - rc * 1.4) / (R - rc * 1.4);
          const ang = Math.atan2(dy, dx) + torsion * N.fbm(d * 6 + 3, Math.atan2(dy, dx) * 0.8, 3); // el surco se tuerce
          const surco = Math.pow(Math.abs(Math.sin(ang * nB / 2 + 0.6 * N(d * 9, ang * 2))), 0.35); // fondo en V, lomos anchos
          return hondoB * (1 - surco) * Math.sin(Math.PI * Math.min(1, t * 1.15)) * (0.6 + 0.4 * N.fbm(dx * 20, dy * 20, 2));
        };
        const parasitos = [];
        for (let k = r.int(0, 3); k > 0; k--) {
          const a = r.range(0, 6.283), dd = R * r.range(0.3, 0.7);
          parasitos.push({ x: cx + Math.cos(a) * dd, y: cy + Math.sin(a) * dd, rb: R * r.range(0.07, 0.13), hh: r.range(0.05, 0.12) });
        }
        const coladas = [];
        const nfTodas = r.int(1, 4), nf = cuello ? 0 : Math.round(nfTodas * (1 - 0.6 * E));
        // se tiran todas las coladas posibles; la edad sólo decide cuántas siguen a la vista
        for (let k = 0; k < nfTodas; k++) { const c = colada(r, cx, cy, rc * 1.3, R * r.range(0.55, 1.15), r.range(0.014, 0.03), r.range(0.02, 0.045) * (1 - 0.5 * E)); if (k < nf) coladas.push(c); }
        const plugP = { rp: r.range(0.025, 0.04), hp: r.range(0.22, 0.36) }, plug = cuello ? plugP : null;
        const esp = [];
        if (plug) esp.push({ u: cx, v: cy, tipo: 'cuello', term: 'CUELLO', busca: 'max', rad: 0.05 });
        else esp.push({ u: cx, v: cy, tipo: 'crater', term: (rc > 0.06 || (E > 0.6 && rc > 0.045)) ? 'CALDERA' : 'CRÁTER', diam: 2 * rc, busca: 'min', rad: rc * 1.6 });
        if (coladas.length && E < 0.6) { const c0 = coladas[0]; esp.push({ u: c0.medio[0], v: c0.medio[1], tipo: 'colada', term: 'COLADA', largo: c0.largo }); }
        return {
          detA: 0.04 + 0.3 * E, warp: 0.3 + E, esp,
          nombre: cuello ? 'CUELLO VOLCÁNICO' : (rc > 0.06 || (E > 0.6 && rc > 0.045)) ? 'CALDERA' : E < 0.33 ? 'ESTRATOVOLCÁN JOVEN' : 'ESTRATOVOLCÁN DISECTADO',
          terminos: cuello ? { principal: 'CUELLO', otros: 'CIMA' } : null,
          erosion: { fuerza: 0.015 + 0.13 * E, pasadas: 2 + Math.round(4 * E) },
          relieve: cuello ? 0.3 : 1 - 0.35 * Math.max(0, E - 0.45), // lo viejo ya perdió altura
          centro: { cx, cy, R }, cuello,
          f: (u, v) => {
            const dx = u - cx, dy = v - cy, d = Math.hypot(dx, dy);
            let val;
            if (d < rc && !plug) val = cono(rc) - dc * (1 - Math.pow(d / rc, q));
            else val = cono(d) - barranca(dx, dy, d);
            if (!plug) val += dc * 0.18 * Math.exp(-Math.pow((d - rc) / (rc * 0.35), 2)); // labio del cráter
            if (brecha && !plug) {
              let da = Math.abs(Math.atan2(dy, dx) - brecha.a); if (da > Math.PI) da = 2 * Math.PI - da;
              if (da < brecha.w / 2) val -= brecha.h * Math.cos(da / brecha.w * Math.PI) * Math.exp(-Math.pow((d - rc * 1.1) / (R * 0.28), 2));
            }
            for (const c of parasitos) {
              const e = Math.hypot(u - c.x, v - c.y);
              if (e < c.rb) val += c.hh * (e < c.rb * 0.3 ? 0.75 + 0.25 * (e / (c.rb * 0.3)) ** 2 : (1 - e / c.rb) / 0.7);
            }
            for (const c of coladas) val += c.espesor(u, v);
            if (plug) val += plug.hp * Math.exp(-Math.pow(d / plug.rp, 2.5));
            return val;
          },
        };
      }
      case 'escudo': {
        // Volcán escudo: domo tendido, caldera de colapso en la cima, zona de rift y muchas coladas largas.
        const cx = 0.5 + r.range(-0.06, 0.06), cy = 0.5 + r.range(-0.06, 0.06), R = r.range(0.45, 0.62);
        const rc = r.range(0.03, 0.055), dc = r.range(0.05, 0.09), ar = r.range(0, Math.PI);
        const domo = (d) => Math.max(0, 1 - Math.pow(d / R, 1.5)) + 0.08 * Math.exp(-Math.pow(Math.max(0, d - R) / 0.12, 2)); // laderas tendidas, pie suave
        const coladas = [];
        for (let k = r.int(4, 8); k > 0; k--) coladas.push(colada(r, cx, cy, rc * 1.5, R * r.range(0.6, 1.2), r.range(0.024, 0.042), r.range(0.09, 0.14)));
        const c0 = coladas[0];
        return {
          detA: 0.08, warp: 0.6, nombre: 'VOLCÁN ESCUDO', exagMax: 3,
          esp: [{ u: cx, v: cy, tipo: 'crater', term: 'CALDERA', diam: 2 * rc, busca: 'min', rad: rc * 1.6 },
            { u: c0.medio[0], v: c0.medio[1], tipo: 'colada', term: 'COLADA', largo: c0.largo }],
          erosion: { fuerza: 0.03, pasadas: 2 },
          f: (u, v) => {
            const dx = u - cx, dy = v - cy, d = Math.hypot(dx, dy);
            let val = d < rc ? domo(rc) - dc * (1 - Math.pow(d / rc, 8)) : domo(d);
            const q = -dx * Math.sin(ar) + dy * Math.cos(ar);
            val += 0.06 * Math.exp(-((q / 0.03) ** 2)) * domo(d); // rift
            for (const c of coladas) val += c.espesor(u, v);
            return val;
          },
        };
      }
      case 'conos': {
        // Campo volcánico monogenético: conos cineríticos truncados con su cráter (algunos
        // abiertos hacia donde soplaba el viento), maares hundidos y coladas de malpaís.
        const viento = r.range(0, 6.283), conos = [], maares = [];
        for (let k = r.int(7, 22); k > 0; k--) {
          const rb = r.range(0.022, 0.055);
          conos.push({
            x: r.range(0.1, 0.9), y: r.range(0.1, 0.9), rb, ht: rb * r.range(4.5, 7.5),
            rt: rb * r.range(0.3, 0.42), cd: r.range(0.25, 0.5), abierto: r() < 0.35 ? viento + r.range(-0.6, 0.6) : null,
          });
        }
        for (let k = r.int(0, 2); k > 0; k--) maares.push({ x: r.range(0.15, 0.85), y: r.range(0.15, 0.85), rm: r.range(0.03, 0.06), pr: r.range(0.06, 0.12) });
        const coladas = [];
        for (let k = r.int(1, 3); k > 0; k--) {
          const c = conos[k % conos.length];
          coladas.push(colada(r, c.x, c.y, c.rb * 0.6, r.range(0.18, 0.45), r.range(0.02, 0.045), r.range(0.025, 0.05), N));
        }
        const pend = r.range(0, 6.283), pa = r.range(0.04, 0.12);
        const grande = conos.reduce((a, b) => (b.ht > a.ht ? b : a));
        const esp = maares.map((m) => ({ u: m.x, v: m.y, tipo: 'crater', term: 'MAAR', diam: 2 * m.rm, busca: 'min', rad: m.rm }));
        esp.push({ u: grande.x, v: grande.y, tipo: 'crater', term: 'CRÁTER', diam: 2 * grande.rt, busca: 'min', rad: grande.rt * 1.4 });
        { const c0 = coladas[0]; esp.push({ u: c0.medio[0], v: c0.medio[1], tipo: 'colada', term: 'MALPAÍS', largo: c0.largo }); }
        return {
          detA: 0.05, warp: 0.4, nombre: 'CAMPO DE CONOS', esp, exagMax: 2.5,
          terminos: { principal: 'CONO', otros: 'CONO' },
          erosion: { fuerza: 0.012, pasadas: 2 },
          f: (u, v) => {
            let val = 0.12 + pa * ((u - 0.5) * Math.cos(pend) + (v - 0.5) * Math.sin(pend));
            let top = 0;
            for (const c of conos) {
              const dx = u - c.x, dy = v - c.y, d = Math.hypot(dx, dy);
              if (d > c.rb) continue;
              let h = c.ht * sst(0, 1, (c.rb - d) / (c.rb - c.rt));
              if (d < c.rt) h = c.ht * (1 - c.cd * (1 - (d / c.rt) ** 2));
              if (c.abierto != null) {
                let da = Math.abs(Math.atan2(dy, dx) - c.abierto); while (da > Math.PI) da = Math.abs(da - 2 * Math.PI);
                if (da < 0.6) h *= 1 - 0.55 * Math.cos(da / 0.6 * Math.PI / 2) * Math.exp(-Math.pow((d - c.rt) / (c.rb * 0.5), 2));
              }
              top = Math.max(top, h);
            }
            val += top;
            for (const m of maares) {
              const d = Math.hypot(u - m.x, v - m.y);
              if (d < m.rm) val -= m.pr * (1 - (d / m.rm) ** 4);
              val += m.pr * 0.25 * Math.exp(-Math.pow((d - m.rm) / (m.rm * 0.35), 2)); // anillo de toba
            }
            for (const c of coladas) val += c.espesor(u, v);
            return val;
          },
        };
      }
      case 'pliegues': {
        // Sierra plegada: capas duras dobladas en pliegues paralelos; cada pliegue se hunde (nariz)
        // y reaparece, el eje se curva, y la erosión deja las capas duras como crestas afiladas.
        const Nb = MT.ruido(r), th = r.range(0, Math.PI), c = Math.cos(th), s = Math.sin(th), lam = r.range(0.055, 0.1), p = r.range(1.6, 3);
        const curva = r.range(0.02, 0.07), kc = r.range(0.8, 1.8), fase = r.range(0, 6.28);
        return {
          detA: 0.06, warp: 0.5, exagMax: 3, erosion: { fuerza: 0.05, pasadas: 3 },
          terminos: { principal: 'CUMBRE', otros: 'CRESTA' },
          historia: ['SEDIMENTOS EN CAPAS', 'PLEGAMIENTO', 'EROSIÓN DE LAS CAPAS BLANDAS'],
          f: (u, v) => {
            const x = u - 0.5, y = v - 0.5, a = x * c + y * s, q = -x * s + y * c + curva * Math.sin(a * kc * 6.28 + fase) + 0.09 * N.fbm(u * 1.6 + 3, v * 1.6, 4);
            const ph = q / lam + 0.9 * N.fbm(a * 2.5 + 11, q * 0.8, 3);
            const cresta = Math.pow(0.5 + 0.5 * Math.cos(ph * 6.283), p);
            const amp = Math.max(0, 0.2 + 1.1 * (0.5 + 0.5 * Nb.fbm(a * 4, Math.floor(ph) * 0.37, 3)) - 0.3);
            return Math.exp(-Math.pow(q / 0.55, 4)) * (0.15 + amp * cresta) + 0.05 * N.fbm(u * 8, v * 8, 4);
          },
        };
      }
      case 'dunas': {
        // Mar de arena: olas transversales al viento (barlovento suave, cara de avalancha empinada)
        // que se bifurcan; uno de cada cuatro, donde falta arena, barjanes sueltos en media luna.
        const Nb = MT.ruido(r), w = r.range(0, 6.283), c = Math.cos(w), s = Math.sin(w), barjanes = r() < 0.25;
        const fr = (x) => x - Math.floor(x), lam = r.range(0.03, 0.055), sinu = r.range(0.2, 0.6), ks = r.range(3, 7);
        const dunas = [];
        for (let k = r.int(10, 26); k > 0; k--) dunas.push({ x: r.range(0.08, 0.92), y: r.range(0.08, 0.92), S: r.range(0.03, 0.07), H: r.range(0.5, 1) });
        const desde = ['NORTE', 'NORESTE', 'ESTE', 'SURESTE', 'SUR', 'SUROESTE', 'OESTE', 'NOROESTE'][Math.round(((Math.atan2(-c, -s) * 180 / Math.PI + 360) % 360) / 45) % 8];
        return {
          detA: 0.02, warp: 0.3, exagMax: 2.5, erosion: false, nombre: barjanes ? 'BARJANES' : 'CAMPO DE DUNAS',
          terminos: { principal: 'CRESTA', otros: 'CRESTA' },
          historia: [`VIENTO DEL ${desde}`, barjanes ? 'BARJANES' : 'DUNAS TRANSVERSALES', 'ARENA EN MOVIMIENTO'],
          f: (u, v) => {
            if (!barjanes) {
              const a = (u - 0.5) * c + (v - 0.5) * s, q = -(u - 0.5) * s + (v - 0.5) * c;
              const ph = a / lam + sinu * Math.sin(q * ks * 6.28 + N(q * 3, 1) * 3) + 1.4 * N.fbm(q * 4, a * 2, 3);
              const t = fr(ph), perfil = t < 0.78 ? Math.pow(t / 0.78, 1.3) : Math.pow((1 - t) / 0.22, 0.9);
              return (0.55 + 0.45 * Nb.fbm(u * 3, v * 3, 3)) * perfil + 0.15 * Nb.fbm(u * 1.5, v * 1.5, 3);
            }
            let z = 0.06 * Nb.fbm(u * 2, v * 2, 3);
            for (const d of dunas) {
              const al = (u - d.x) * c + (v - d.y) * s, tr = -(u - d.x) * s + (v - d.y) * c;
              if (Math.abs(al) > d.S * 2.2 || Math.abs(tr) > d.S * 1.6) continue;
              const cuerpo = 1 - (al / d.S) ** 2 - (tr / (d.S * 1.15)) ** 2;
              const hueco = 1 - ((al - d.S * 0.75) / (d.S * 0.95)) ** 2 - (tr / (d.S * 0.8)) ** 2;
              const cuerno = Math.exp(-(((Math.abs(tr) - d.S * 0.95) / (d.S * 0.22)) ** 2)) * Math.exp(-(((al - d.S * 0.9) / (d.S * 0.8)) ** 2)) * 0.35;
              z = Math.max(z, d.H * Math.pow(Math.max(Math.max(0, cuerpo) - Math.max(0, hueco) * 1.4, cuerno, 0), 0.7));
            }
            return z;
          },
        };
      }
      case 'karst': {
        // Caliza disuelta: llanura picada de dolinas (muchas chicas, pocas grandes), cenotes de
        // pared vertical que llegan al agua, y poljes: depresiones grandes y alargadas de fondo plano.
        const hoyos = [], poljes = [];
        for (let k = r.int(50, 130); k > 0; k--) {
          const R = Math.min(0.06, 0.008 * Math.pow(1 - r() * 0.95, -0.7));
          hoyos.push({ x: r.range(0.04, 0.96), y: r.range(0.04, 0.96), R, cenote: R < 0.022 && r() < 0.25, d: r.range(0.6, 1.1) });
        }
        for (let k = r.int(0, 2); k > 0; k--) { const a = r.range(0, 3.14); poljes.push({ x: r.range(0.25, 0.75), y: r.range(0.25, 0.75), c: Math.cos(a), s: Math.sin(a), L: r.range(0.12, 0.22), W: r.range(0.05, 0.08) }); }
        const grande = hoyos.reduce((a, b) => (b.R > a.R ? b : a)), cen = hoyos.find((o) => o.cenote);
        const esp = [{ u: grande.x, v: grande.y, tipo: 'crater', term: 'DOLINA', diam: grande.R * 2, busca: 'min', rad: grande.R * 0.5 }];
        if (cen) esp.push({ u: cen.x, v: cen.y, tipo: 'crater', term: 'CENOTE', diam: cen.R * 2, busca: 'min', rad: cen.R * 0.5 });
        for (const p of poljes) esp.push({ u: p.x, v: p.y, tipo: 'colada', term: 'POLJE', largo: p.L * 2 });
        return {
          detA: 0.02, warp: 0.2, exagMax: 3, erosion: { fuerza: 0.012, pasadas: 1 }, esp, lagos: { humedad: r.int(5, 9) },
          terminos: { principal: 'LOMA', otros: 'LOMA' }, historia: ['CALIZA', 'DISOLUCIÓN', 'DOLINAS', 'CENOTES'],
          f: (u, v) => {
            let z = 0.5 + 0.12 * N.fbm(u * 2, v * 2, 4) + 0.03 * N.ridged(u * 6, v * 6, 3);
            for (const p of poljes) { const al = (u - p.x) * p.c + (v - p.y) * p.s, tr = -(u - p.x) * p.s + (v - p.y) * p.c, q = Math.hypot(al / p.L, tr / p.W); if (q < 1) z -= 0.18 * sst(1, 0.75, q); }
            for (const o of hoyos) {
              const dx = u - o.x, dy = v - o.y; if (Math.abs(dx) > o.R || Math.abs(dy) > o.R) continue;
              const q = Math.hypot(dx, dy) / o.R; if (q >= 1) continue;
              z -= o.cenote ? o.R * 9 * o.d * (1 - Math.pow(q, 10)) : o.R * 4 * o.d * (1 - q * q); // el cenote: pared vertical
            }
            return z;
          },
        };
      }
      case 'atolon': {
        // Lo que explicó Darwin: un volcán se hunde y su arrecife sigue creciendo hacia arriba.
        // Atolón: sólo queda el anillo de islotes (motus) y la laguna; barrera: la isla aún asoma.
        const barrera = r() < 0.4, cx = 0.5 + r.range(-0.05, 0.05), cy = 0.5 + r.range(-0.05, 0.05);
        const Ra = r.range(0.28, 0.38), ex = r.range(0.75, 1), w = r.range(0.018, 0.03), pasos = Array.from({ length: r.int(1, 3) }, () => r.range(0, 6.283));
        const pa = pasos[0];
        return {
          detA: 0.02, warp: 0.15, mar: barrera ? 0.02 : 0.15, inclina: barrera ? 1 : 0.15, agua: barrera, // un atolón de 10 m no tiene ríos, y la pendiente regional no debe sacar el fondo de la laguna del agua
          exagMax: barrera ? 3 : 40, relieve: barrera ? 1 : 0.013,
          erosion: barrera ? { fuerza: 0.05, pasadas: 2 } : false, nombre: barrera ? 'ARRECIFE DE BARRERA' : 'ATOLÓN',
          terminos: barrera ? { principal: 'CUMBRE', otros: 'CIMA' } : { principal: 'MOTU', otros: 'MOTU' },
          historia: barrera ? ['VOLCÁN', 'HUNDIMIENTO', 'ARRECIFE DE BARRERA'] : ['VOLCÁN', 'HUNDIMIENTO', 'ARRECIFE', 'ATOLÓN'],
          esp: [{ u: cx, v: cy + Ra * 0.55 * ex, tipo: 'colada', term: 'LAGUNA' }, { u: cx + Math.cos(pa) * Ra, v: cy + Math.sin(pa) * Ra * ex, tipo: 'colada', term: 'PASO' }],
          f: (u, v) => {
            const dx = u - cx, dy = (v - cy) / ex, a = Math.atan2(dy, dx), d = Math.hypot(dx, dy) * (1 + 0.06 * N.fbm(Math.cos(a) * 2, Math.sin(a) * 2, 3));
            const anillo = Math.exp(-(((d - Ra) / w) ** 2)), motu = sst(0.05, 0.3, N.fbm(a * 3 + 7, 1, 4) + 0.15);
            let paso = 1; for (const p of pasos) { let da = Math.abs(a - p); if (da > Math.PI) da = 2 * Math.PI - da; paso *= sst(0.04, 0.12, da); }
            let z = anillo * motu * paso * (barrera ? 0.05 : 0.22);
            if (d < Ra * 0.8) z = Math.max(z, 0.04 * sst(0.55, 0.9, N.fbm(u * 14, v * 14, 3) + 0.3) * (barrera ? 0.25 : 1)); // arrecifes en la laguna
            if (barrera) z = Math.max(z, Math.pow(Math.max(0, 1 - d / (Ra * 0.45)), 1.6) * (0.85 + 0.15 * N.ridged(u * 8, v * 8, 4)));
            return z;
          },
        };
      }
      case 'meandros': {
        // Llanura de inundación: el río serpentea (curva de Kinoshita, la de los geomorfólogos),
        // deja lagos de herradura donde abandonó vueltas, y el valle conserva terrazas en escalón.
        const th = r.range(0, Math.PI), c = Math.cos(th), s = Math.sin(th), W = r.range(0.3, 0.4), nT = r.int(2, 3), off = r.range(-0.08, 0.08);
        const pts = [], A = r.range(1.7, 2.1), lam = r.range(0.22, 0.32), ph = r.range(0, 6.28);
        let x = 0.5 - 0.8 * c - off * s, y = 0.5 - 0.8 * s + off * c, t = 0, entro = false;
        const Nk = (q) => Math.sin(q * 2.3 + ph) * 0.5 + Math.sin(q * 5.1 + ph * 1.7) * 0.3;
        while (t < 2.6) {
          const ks = t / lam * 6.283 + ph + 1.2 * Nk(t * 2), Aa = A * (0.75 + 0.25 * Nk(t * 1.3 + 4));
          const phi = th + Aa * Math.sin(ks) + Aa ** 3 / 32 * (0.4 * Math.sin(3 * ks) - 0.3 * Math.cos(3 * ks));
          pts.push([x, y]); x += Math.cos(phi) * 0.002; y += Math.sin(phi) * 0.002; t += 0.002;
          const fuera = x < -0.05 || y < -0.05 || x > 1.05 || y > 1.05; // nace fuera de la hoja: sólo para cuando ya cruzó
          if (!fuera) entro = true; else if (entro) break;
        }
        const viejos = [];
        for (let m = r.int(2, 4); m > 0; m--) {
          const i0 = Math.floor(r.range(0.15, 0.8) * pts.length), dq = r.range(0.05, 0.1) * (r() < 0.5 ? 1 : -1);
          viejos.push(pts.slice(i0, i0 + Math.floor(pts.length * 0.07)).map(([u, v]) => [u - s * dq, v + c * dq]));
        }
        const v0 = viejos[0][Math.floor(viejos[0].length / 2)];
        return {
          detA: 0.01, warp: 0.12, exagMax: 4, erosion: { fuerza: 0.015, pasadas: 1 }, lagos: { humedad: 6 },
          terminos: { principal: 'LOMA', otros: 'LOMA' }, historia: ['VALLE', 'TERRAZAS', 'MEANDROS', 'LAGOS DE HERRADURA'],
          esp: [{ u: v0[0], v: v0[1], tipo: 'colada', term: 'LAGO DE HERRADURA' }, { u: 0.5 - s * (W * 0.75 + off), v: 0.5 + c * (W * 0.75 + off), tipo: 'colada', term: 'TERRAZA' }],
          f: (u, v) => {
            const a = (u - 0.5) * c + (v - 0.5) * s, q = Math.abs(-(u - 0.5) * s + (v - 0.5) * c - off + 0.03 * N.fbm(a * 3, 2, 3));
            let z = 0.1 - 0.06 * a;
            for (let k = 1; k <= nT; k++) z += 0.035 * sst(W * (0.75 + 0.2 * k) - 0.012, W * (0.75 + 0.2 * k) + 0.012, q); // terrazas: escalones bajos, lejos del cauce
            return z + 0.5 * sst(W * 1.5, W * 2.4, q) * (0.7 + 0.3 * N.fbm(u * 3, v * 3, 4)) + 0.01 * N.fbm(u * 9, v * 9, 3);
          },
          cauce: pts,
          post: (h, GN) => { // el cauce y los meandros abandonados se tallan sobre la rejilla
            aLinea(h, GN, pts, 0.018, (z, d) => z - 0.06 * Math.sqrt(1 - d / 0.018)); // el cauce, ancho y hondo: por ahí corre el agua
            for (const vj of viejos) aLinea(h, GN, vj, 0.014, (z, d, tt) => z - 0.05 * (1 - d / 0.014) * sst(0, 0.15, tt) * sst(1, 0.85, tt));
          },
        };
      }
      case 'costa': {
        // Donde la tierra se acaba. Tres costas: acantilados con islotes que el mar dejó sueltos;
        // fiordos, valles glaciares que el mar inundó; y el delta, donde el río se abre en brazos.
        const t = r(); let modo = t < 0.4 ? 'acantilado' : t < 0.7 ? 'fiordo' : 'delta';
        if (modo === 'acantilado' && MT.rng(seed + ':flecha')() < 0.5) modo = 'flecha'; // tirada aparte: no mueve a las demás costas
        const th = r.range(0, 6.283), c = Math.cos(th), s = Math.sin(th), off = r.range(-0.18, -0.02);
        const costa = (a) => off + 0.08 * N.fbm(a * 2.5 + 5, 1, 4) + 0.025 * N.fbm(a * 9, 3, 3);
        const loc = (u, v) => { const x = u - 0.5, y = v - 0.5, a = x * c + y * s; return [a, -x * s + y * c - costa(a)]; }; // d > 0: tierra
        const aUV2 = (a, q) => [0.5 + a * c - q * s, 0.5 + a * s + q * c];
        const esp = [], extra = {};
        if (modo === 'acantilado') {
          const islotes = Array.from({ length: r.int(4, 10) }, () => { const a = r.range(-0.4, 0.4); return { a, d: r.range(-0.05, -0.012), R: r.range(0.006, 0.016), H: r.range(0.5, 1) }; });
          extra.f = (u, v) => {
            const [a, d] = loc(u, v), N2 = 0.5 + 0.5 * N.fbm(u * 3, v * 3, 4);
            let z = d < 0 ? 0.02 + 0.03 * sst(-0.06, 0, d) : 0.16 + 0.25 * sst(0, 0.012, d) + 0.6 * sst(0.01, 0.6, d) * N2 * (0.7 + 0.3 * N.ridged(u * 6, v * 6, 4));
            for (const o of islotes) { const [ix, iy] = aUV2(o.a, costa(o.a) + o.d), q = Math.hypot(u - ix, v - iy) / o.R; if (q < 1) z = Math.max(z, 0.16 + 0.25 * o.H * sst(1, 0.6, q)); }
            return z;
          };
          const a0 = r.range(-0.2, 0.2), [ex, ey] = aUV2(a0, costa(a0) + 0.006);
          esp.push({ u: ex, v: ey, tipo: 'colada', term: 'ACANTILADO' });
          const o = islotes[0], [ox, oy] = aUV2(o.a, costa(o.a) + o.d); esp.push({ u: ox, v: oy, tipo: 'cuello', term: 'ISLOTE', busca: 'max', rad: 0.01 });
        } else if (modo === 'flecha') {
          // la corriente estira arena desde la costa: en gancho (flecha) o hasta una isla (tómbolo)
          const tomb = MT.rng(seed + ':tombolo')() < 0.5, isla = { a: r.range(-0.1, 0.15), d: -r.range(0.12, 0.2), R: r.range(0.05, 0.09) };
          const qi = costa(isla.a) + isla.d, [ix, iy] = aUV2(isla.a, qi), flecha = [];
          { let a = r.range(-0.3, -0.15), q = costa(a) - 0.004, dir = -0.3;
            for (let k = 0; k < 120; k++) { flecha.push(aUV2(a, q)); a += Math.cos(dir) * 0.004; q += Math.sin(dir) * 0.004; dir += tomb ? 0 : 0.012;
              if (tomb) { dir = Math.atan2(qi - q, isla.a - a); if (Math.hypot(isla.a - a, qi - q) < isla.R * 0.8) break; } } }
          const dSeg = (u, v) => { let dm = 9; for (let k = 1; k < flecha.length; k++) { const [ax, ay] = flecha[k - 1], [bx, by] = flecha[k], dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy || 1e-12, tt = Math.max(0, Math.min(1, ((u - ax) * dx + (v - ay) * dy) / l2)); dm = Math.min(dm, Math.hypot(u - ax - dx * tt, v - ay - dy * tt)); } return dm; };
          extra.f = (u, v) => {
            const [, d] = loc(u, v);
            let z = d < 0 ? 0.0 : 0.16 + 0.6 * sst(0, 0.5, d) * (0.6 + 0.4 * N.fbm(u * 3, v * 3, 4));
            const di = Math.hypot(u - ix, v - iy) / isla.R; if (di < 1) z = Math.max(z, 0.16 + 0.6 * Math.pow(1 - di, 1.3)); // la isla
            const df = dSeg(u, v); if (df < 0.012) z = Math.max(z, 0.13 + 0.03 * (1 - df / 0.012)); // la lengua de arena, apenas sobre el agua
            return z;
          };
          const m = flecha[Math.floor(flecha.length * 0.6)];
          esp.push({ u: m[0], v: m[1], tipo: 'colada', term: tomb ? 'TÓMBOLO' : 'FLECHA', largo: flecha.length * 0.004 });
          extra.tomb = tomb;
        } else if (modo === 'fiordo') {
          extra.f = (u, v) => { const [, d] = loc(u, v); return d < 0 ? 0.0 : 0.16 + 0.84 * sst(0, 0.35, d) * (0.45 + 0.55 * N.ridged(u * 4, v * 4, 5)); };
          // los fiordos: valles que entran desde la costa, se ramifican y se hunden bajo el mar
          const brazos = [];
          for (let k = r.int(2, 4); k > 0; k--) {
            let a = r.range(-0.35, 0.35), q = costa(a) - 0.04, dir = Math.PI / 2 + r.range(-0.4, 0.4); const pts = [];
            const L = r.range(0.3, 0.6);
            for (let st = 0; st < L / 0.006; st++) { const [x, y] = aUV2(a, q); pts.push([x, y]); dir += r.range(-0.18, 0.18); a += Math.cos(dir) * 0.006; q += Math.sin(dir) * 0.006; }
            brazos.push({ pts, w: r.range(0.014, 0.026) });
            if (r() < 0.6) { const i0 = Math.floor(pts.length * r.range(0.3, 0.6)), [bx, by] = pts[i0], rama = [[bx, by]]; let d2 = r.range(0.6, 1.2) * (r() < 0.5 ? 1 : -1), x = bx, y = by, h0 = Math.atan2(pts[i0 + 1][1] - by, pts[i0 + 1][0] - bx) + d2;
              for (let st = 0; st < r.range(25, 45); st++) { h0 += r.range(-0.2, 0.2); x += Math.cos(h0) * 0.006; y += Math.sin(h0) * 0.006; rama.push([x, y]); }
              brazos.push({ pts: rama, w: r.range(0.01, 0.018) }); }
          }
          extra.post = (h, GN) => { for (const b of brazos) aLinea(h, GN, b.pts, b.w * 1.5, (z, d) => { const q = d / b.w; return q < 1 ? Math.min(z, z * Math.pow(q, 3)) : z; }); };
          const b0 = brazos[0], m = b0.pts[Math.floor(b0.pts.length * 0.6)];
          let L0 = 0; for (let k = 1; k < b0.pts.length; k++) L0 += Math.hypot(b0.pts[k][0] - b0.pts[k - 1][0], b0.pts[k][1] - b0.pts[k - 1][1]);
          esp.push({ u: m[0], v: m[1], tipo: 'colada', term: 'FIORDO', largo: L0 });
        } else {
          // delta: el río llega a una llanura baja y se abre en brazos que avanzan sobre el mar
          const a0 = r.range(-0.15, 0.15), q0 = costa(a0), brazos = [];
          for (let k = r.int(3, 6); k > 0; k--) {
            const ang = -Math.PI / 2 + r.range(-0.9, 0.9), L = r.range(0.07, 0.17), pts = [];
            let a = a0, q = q0 + 0.02, dir = ang; for (let st = 0; st < L / 0.004; st++) { pts.push(aUV2(a, q)); dir += r.range(-0.1, 0.1); a += Math.cos(dir) * 0.004; q += Math.sin(dir) * 0.004; }
            brazos.push({ pts, w: r.range(0.018, 0.032) });
          }
          const rio = []; { let a = a0, q = q0 + 0.02, dir = Math.PI / 2; for (let st = 0; st < 180; st++) { rio.push(aUV2(a, q)); dir += r.range(-0.15, 0.15) + (Math.PI / 2 - dir) * 0.05; a += Math.cos(dir) * 0.004; q += Math.sin(dir) * 0.004; } }
          const dSeg = (u, v, pts) => { let dm = Infinity; for (let k = 1; k < pts.length; k += 2) { const [ax, ay] = pts[k - 1], [bx, by] = pts[k], dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy || 1e-12, tt = Math.max(0, Math.min(1, ((u - ax) * dx + (v - ay) * dy) / l2)); dm = Math.min(dm, Math.hypot(u - ax - dx * tt, v - ay - dy * tt)); } return dm; };
          extra.f = (u, v) => {
            const [, d] = loc(u, v);
            let z = d < 0 ? 0.0 : 0.16 + 0.45 * sst(0.05, 0.8, d) * (0.6 + 0.4 * N.fbm(u * 3, v * 3, 4));
            for (const b of brazos) { const dd = dSeg(u, v, b.pts); if (dd < b.w) z = Math.max(z, 0.14 + 0.02 * (1 - dd / b.w)); } // lóbulos de lodo apenas sobre el agua
            return z;
          };
          extra.post = (h, GN) => { aLinea(h, GN, rio, 0.006, (z, d) => Math.max(0, z - 0.02 * (1 - d / 0.006))); for (const b of brazos) aLinea(h, GN, b.pts, 0.004, (z, d) => Math.max(0, z - 0.02 * (1 - d / 0.004))); };
          const [dx0, dy0] = aUV2(a0, q0 - 0.05); esp.push({ u: dx0, v: dy0, tipo: 'colada', term: 'DELTA' });
          extra.canal = { rio, brazos: brazos.map((b) => b.pts) }; // sólo para nombrarlos: el agua dibujada no cambia
        }
        return {
          detA: 0.03, warp: 0.2, mar: 0.1, exagMax: modo === 'fiordo' ? 2.5 : 3.5,
          relieve: modo === 'fiordo' ? 1.2 : modo === 'delta' ? 0.15 : 0.6, erosion: { fuerza: modo === 'delta' ? 0.015 : 0.05, pasadas: modo === 'delta' ? 1 : 3 },
          nombre: modo === 'acantilado' ? 'COSTA DE ACANTILADOS' : modo === 'fiordo' ? 'FIORDOS' : modo === 'flecha' ? (extra.tomb ? 'TÓMBOLO' : 'COSTA CON FLECHA') : 'DELTA', esp,
          terminos: modo === 'fiordo' ? { principal: 'CUMBRE', otros: 'CIMA' } : { principal: 'LOMA', otros: 'LOMA' },
          historia: modo === 'flecha' ? (extra.tomb ? ['COSTA E ISLA', 'CORRIENTE', 'LA ARENA UNE LA ISLA'] : ['COSTA', 'CORRIENTE', 'FLECHA DE ARENA']) : modo === 'acantilado' ? ['LEVANTAMIENTO', 'EROSIÓN', 'EL MAR MUERDE LA COSTA'] : modo === 'fiordo' ? ['LEVANTAMIENTO', 'GLACIACIÓN', 'DESHIELO', 'EL MAR INUNDA LOS VALLES'] : ['VALLE', 'EL RÍO LLEGA AL MAR', 'DELTA'],
          lagos: modo === 'delta' ? { humedad: 4 } : undefined,
          ...extra,
        };
      }
      case 'anillos': {
        // Ojo del Sahara: capas duras y blandas en un domo; la erosión las deja en anillos
        const Nb = MT.ruido(r), cx = 0.5 + r.range(-0.06, 0.06), cy = 0.5 + r.range(-0.06, 0.06), R = r.range(0.32, 0.45), lam = r.range(0.035, 0.06), ex = r.range(0.8, 1);
        const fr = (x) => x - Math.floor(x);
        return {
          detA: 0.02, warp: 0.15, exagMax: 3, erosion: { fuerza: 0.02, pasadas: 1 },
          historia: ['CAPAS', 'DOMO', 'EROSIÓN DE LAS CAPAS BLANDAS', 'ANILLOS'],
          esp: [{ u: cx + R * 0.95, v: cy, tipo: 'crater', term: 'ANILLOS', diam: 2 * R }],
          f: (u, v) => {
            const dx = u - cx, dy = (v - cy) / ex, d = Math.hypot(dx, dy), a = Math.atan2(dy, dx);
            const t = fr(d / lam + 0.6 * N.fbm(Math.cos(a) * 1.5 + 3, Math.sin(a) * 1.5, 3) + 0.4 * N.fbm(u * 4, v * 4, 3));
            const cuesta = t < 0.75 ? t / 0.75 : (1 - t) / 0.25, dentro = sst(R * 1.1, R * 0.8, d);
            return 0.2 + 0.1 * Nb.fbm(u * 2, v * 2, 3) + dentro * (0.22 * Math.pow(cuesta, 1.4) + 0.12 * (1 - d / R)) - 0.08 * Math.exp(-((d / (R * 0.12)) ** 2));
          },
        };
      }
      case 'drumlins': {
        // el hielo moldeó cientos de colinas ovaladas, alineadas, romas contra el hielo
        const th = r.range(0, 6.283), c = Math.cos(th), s = Math.sin(th), ds = [];
        for (let k = r.int(90, 200); k > 0; k--) ds.push({ x: r.range(0.03, 0.97), y: r.range(0.03, 0.97), L: r.range(0.025, 0.055), W: r.range(0.01, 0.02), H: r.range(0.5, 1) });
        const desde = ['NORTE', 'NORESTE', 'ESTE', 'SURESTE', 'SUR', 'SUROESTE', 'OESTE', 'NOROESTE'][Math.round(((Math.atan2(-c, -s) * 180 / Math.PI + 360) % 360) / 45) % 8];
        return {
          detA: 0.02, warp: 0.1, exagMax: 3, erosion: { fuerza: 0.01, pasadas: 1 }, lagos: { humedad: 6 },
          terminos: { principal: 'DRUMLIN', otros: 'DRUMLIN' }, historia: [`HIELO DEL ${desde}`, 'EL HIELO MODELA', 'DRUMLINS'],
          esp: [{ u: ds[0].x, v: ds[0].y, tipo: 'cuello', term: 'DRUMLIN', busca: 'max', rad: 0.02 }],
          f: (u, v) => {
            const b = 0.15 + 0.12 * N.fbm(u * 2.5, v * 2.5, 3); let z = b;
            for (const d of ds) {
              const dx = u - d.x, dy = v - d.y; if (Math.abs(dx) > d.L * 1.3 || Math.abs(dy) > d.L * 1.3) continue;
              const al = dx * c + dy * s, tr = -dx * s + dy * c, q = (al / (al < 0 ? d.L * 0.65 : d.L * 1.1)) ** 2 + (tr / d.W) ** 2;
              if (q < 1) z = Math.max(z, b + d.H * 0.6 * Math.pow(1 - q, 0.6));
            }
            return z;
          },
        };
      }
      case 'rift': {
        // la corteza se estira: un bloque se hunde entre dos fallas; en el fondo, lagos y volcanes
        const Nb = MT.ruido(r), th = r.range(0, Math.PI), c = Math.cos(th), s = Math.sin(th), W = r.range(0.12, 0.2), off = r.range(-0.08, 0.08), vol = [];
        for (let k = r.int(1, 3); k > 0; k--) vol.push({ a: r.range(-0.4, 0.4), q: r.range(-W * 0.6, W * 0.6), R: r.range(0.04, 0.08), H: r.range(0.25, 0.5) });
        return {
          detA: 0.05, warp: 0.2, exagMax: 2.5, erosion: { fuerza: 0.05, pasadas: 3 }, lagos: { humedad: 4, maxLago: 0.05 },
          historia: ['MESETA', 'ESTIRAMIENTO', 'HUNDIMIENTO', 'LAGOS Y VOLCANES'],
          esp: [{ u: 0.5 - s * off, v: 0.5 + c * off, tipo: 'colada', term: 'RIFT', largo: W * 2 }],
          f: (u, v) => {
            const a = (u - 0.5) * c + (v - 0.5) * s, q = (u - 0.5) * -s + (v - 0.5) * c - off - 0.03 * N.fbm(a * 3, 1, 3), aq = Math.abs(q);
            let z = 0.62 + 0.15 * N.fbm(u * 2, v * 2, 4) + 0.12 * sst(W * 2.5, W, aq) * sst(W * 0.9, W * 1.3, aq);
            const esc = sst(W * 1.02, W * 0.96, aq) + 0.5 * sst(W * 0.8, W * 0.74, aq);
            z -= 0.45 * Math.min(1, esc) + 0.06 * sst(W * 0.6, 0, aq) * (0.5 + 0.5 * Nb.fbm(a * 6, 2, 3));
            for (const o of vol) { const vx = 0.5 + o.a * c - (o.q + off) * s, vy = 0.5 + o.a * s + (o.q + off) * c, d = Math.hypot(u - vx, v - vy) / o.R; if (d < 1) z = Math.max(z, 0.17 + o.H * Math.pow(1 - d, 1.6)); }
            return z;
          },
        };
      }
      case 'tepuyes':
      case 'testigos': {
        // mesas de paredes verticales: tepuyes (pocos, enormes) o cerros testigo (muchos, con agujas)
        const Nb = MT.ruido(r), tep = arq === 'tepuyes';
        // las mesas se siembran por la hoja: pocas y enormes (tepuyes) o muchas, chicas y agujas (testigos)
        const escT = r.range(4, 7), umbralT = r.range(0.25, 0.4);
        const mesas = Array.from({ length: tep ? r.int(2, 4) : r.int(9, 18) }, (_, k) => ({ x: r.range(0.18, 0.82), y: r.range(0.18, 0.82), R: tep ? r.range(0.12, 0.22) : (k % 3 === 2 ? r.range(0.01, 0.02) : r.range(0.025, 0.07)) }));
        return {
          detA: 0.01, warp: 0.1, exagMax: 3, erosion: { fuerza: 0.02, pasadas: 1 },
          terminos: tep ? { principal: 'TEPUY', otros: 'CIMA' } : { principal: 'MESA', otros: 'AGUJA' },
          historia: tep ? ['ARENISCA', 'LEVANTAMIENTO', 'EROSIÓN', 'TEPUYES'] : ['MESETA', 'EROSIÓN', 'MESAS, CERROS Y AGUJAS'],
          f: (u, v) => {
            let m;
            if (tep) { m = -1; for (const o of mesas) m = Math.max(m, 1 - Math.hypot(u - o.x, v - o.y) / o.R); m += 0.35 * N.fbm(u * 5 + 3, v * 5, 4); } // tepuyes: sembrados, bordes recortados
            else m = N.fbm(u * escT + 3, v * escT, 4) - umbralT; // testigos: lo que la erosión no se llevó, donde caiga
            const pared = sst(-0.02, tep ? 0.01 : 0.015, m), talud = 0.12 * sst(-0.12, 0, m);
            const cima = tep ? 0.03 * Nb.ridged(u * 20, v * 20, 3) : 0.02 * Nb.fbm(u * 10, v * 10, 3);
            return 0.08 + 0.05 * Nb.fbm(u * 3, v * 3, 3) + talud + pared * (0.7 + cima);
          },
        };
      }
      case 'inselbergs': {
        // domos de granito que salen de una llanura casi perfecta
        const Nb = MT.ruido(r), ds = Array.from({ length: r.int(2, 5) }, () => ({ x: r.range(0.15, 0.85), y: r.range(0.15, 0.85), R: r.range(0.05, 0.12), e: r.range(0.5, 1), a: r.range(0, 3.14), H: r.range(0.5, 1) }));
        return {
          detA: 0.01, warp: 0.05, exagMax: 3, erosion: { fuerza: 0.01, pasadas: 1 },
          terminos: { principal: 'DOMO', otros: 'DOMO' }, historia: ['GRANITO BAJO TIERRA', 'EROSIÓN DE LO BLANDO', 'INSELBERGS'],
          f: (u, v) => {
            let z = 0.04 * N.fbm(u * 2, v * 2, 3);
            for (const d of ds) { const c = Math.cos(d.a), s = Math.sin(d.a), al = (u - d.x) * c + (v - d.y) * s, tr = -(u - d.x) * s + (v - d.y) * c, q = Math.hypot(al / d.R, tr / (d.R * d.e));
              if (q < 1) z = Math.max(z, d.H * Math.pow(1 - q * q, 0.35) * (0.95 + 0.05 * Nb(u * 40, v * 40))); }
            return z;
          },
        };
      }
      case 'poligonos': {
        // permafrost: el suelo helado se contrae y se agrieta en polígonos (relieve estilizado:
        // el real es de medio metro y no cabría ni una curva)
        const M = r.int(14, 26), pts = [];
        for (let j = 0; j <= M; j++) for (let i = 0; i <= M; i++) pts.push([(i + r.range(0.1, 0.9)) / M, (j + r.range(0.1, 0.9)) / M]);
        return {
          detA: 0.0, warp: 0.03, exagMax: 12, erosion: false, lagos: { humedad: 9 },
          terminos: { principal: 'BORDO', otros: 'BORDO' }, historia: ['PERMAFROST', 'EL SUELO SE CONTRAE', 'GRIETAS DE HIELO', 'POLÍGONOS'],
          f: (u, v) => {
            const ci = Math.floor(u * M), cj = Math.floor(v * M); let f1 = 9, f2 = 9;
            for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) { const i = ci + di, j = cj + dj; if (i < 0 || j < 0 || i > M || j > M) continue; const [px, py] = pts[j * (M + 1) + i], d = Math.hypot(u - px, v - py); if (d < f1) { f2 = f1; f1 = d; } else if (d < f2) f2 = d; }
            const borde = (f2 - f1) * M;
            return 0.3 + 0.08 * N.fbm(u * 2, v * 2, 3) - 0.07 * sst(0.12, 0, borde) + 0.06 * sst(0.05, 0.25, borde) * sst(0.6, 0.3, borde) - 0.04 * sst(0.4, 0.9, borde);
          },
        };
      }
      case 'badlands': {
        // Tierras malas: en vez de erosionar ruido, se hace crecer la red de cárcavas (un árbol
        // que invade la rejilla desde las salidas del agua, siempre por lo "más blando") y la
        // altura sale de la red: más alto lejos de la salida, más hondo donde llega más agua.
        const M = 130, salidas = r.int(3, 7), hondo = r.range(0.06, 0.09), azar = Array.from({ length: M * M }, () => r());
        const sal = Array.from({ length: salidas }, () => Math.floor(r.range(0.05, 0.95) * M));
        return {
          detA: 0, warp: 0, exagMax: 2.5, erosion: false, lagos: { humedad: 1 },
          terminos: { principal: 'LOMA', otros: 'LOMA' }, historia: ['ARCILLAS', 'LLUVIAS RARAS Y VIOLENTAS', 'CÁRCAVAS', 'TIERRAS MALAS'],
          f: () => 0.5,
          post: (h, GN) => {
            const n = M * M, padre = new Int32Array(n).fill(-1), en = new Uint8Array(n), key = new Float32Array(n);
            for (let i = 0; i < n; i++) { const x = (i % M) / M, y = Math.floor(i / M) / M; key[i] = azar[i] * 0.45 + 2.2 * y + 0.35 * N.fbm(x * 2.5, y * 2.5, 3); }
            const hk = [], hi = [], hp = [];
            const sw = (a, b) => { [hk[a], hk[b]] = [hk[b], hk[a]]; [hi[a], hi[b]] = [hi[b], hi[a]]; [hp[a], hp[b]] = [hp[b], hp[a]]; };
            const push = (k, i, p) => { let c = hk.length; hk.push(k); hi.push(i); hp.push(p); while (c > 0) { const q = (c - 1) >> 1; if (hk[q] <= hk[c]) break; sw(q, c); c = q; } };
            const pop = () => { const top = [hi[0], hp[0]], lk = hk.pop(), li = hi.pop(), lp = hp.pop(); if (hk.length) { hk[0] = lk; hi[0] = li; hp[0] = lp; let c = 0; for (;;) { let m = c * 2 + 1; if (m >= hk.length) break; if (m + 1 < hk.length && hk[m + 1] < hk[m]) m++; if (hk[c] <= hk[m]) break; sw(m, c); c = m; } } return top; };
            for (const x of sal) push(-1, x, -2);
            const orden = [];
            while (hk.length) {
              const [i, p] = pop(); if (en[i]) continue; en[i] = 1; padre[i] = p; orden.push(i);
              const x = i % M, y = Math.floor(i / M);
              for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= M || ny >= M) continue; const j = ny * M + nx; if (!en[j]) push(key[j], j, i); }
            }
            const D = new Float32Array(n), A = new Float32Array(n).fill(1);
            for (const i of orden) D[i] = padre[i] >= 0 ? D[padre[i]] + 1 : 0;
            for (let k = orden.length - 1; k >= 0; k--) { const i = orden[k]; if (padre[i] >= 0) A[padre[i]] += A[i]; }
            let dMax = 0; for (const v of D) dMax = Math.max(dMax, v);
            const g = new Float32Array(n); for (let i = 0; i < n; i++) g[i] = Math.pow(D[i] / dMax, 0.7) - hondo * Math.log(A[i]) / Math.log(n) * 4;
            for (let j = 0; j < GN; j++) for (let i = 0; i < GN; i++) {
              const x = i / (GN - 1) * (M - 1), y = (1 - j / (GN - 1)) * (M - 1), xi = Math.min(M - 2, Math.floor(x)), yi = Math.min(M - 2, Math.floor(y)), fx = x - xi, fy = y - yi, k = yi * M + xi;
              h[j * GN + i] = g[k] * (1 - fx) * (1 - fy) + g[k + 1] * fx * (1 - fy) + g[k + M] * (1 - fx) * fy + g[k + M + 1] * fx * fy;
            }
            const sv = suaviza(h, GN, 1); for (let p = 0; p < 2; p++) h.set(suaviza(h, GN, 1)); void sv;
          },
        };
      }
      case 'impactos': {
        // Llanura apenas ondulada: los cráteres se estampan después, en metros, del más viejo al más joven.
        return { detA: 0.03, warp: 0.5, nombre: 'CAMPO DE IMPACTOS', impactos: true, erosion: false, exagMax: 9, f: () => 0.3 };
      }

      case 'monte': {
        const cx = 0.5 + r.range(-0.08, 0.08), cy = 0.5 + r.range(-0.04, 0.1);
        const s = r.range(0.18, 0.28), e = r.range(1.1, 1.8), crater = r() < 0.3;
        const ang = r.range(0, 6.283), sd = r.range(0.12, 0.22);
        const hx = cx + Math.cos(ang) * sd, hy = cy + Math.sin(ang) * sd;
        const hs = s * r.range(0.4, 0.7), hh = r.range(0.15, 0.35);
        return {
          detA: r.range(0.25, 0.45),
          f: (u, v) => {
            const d = Math.hypot(u - cx, v - cy);
            let b = Math.exp(-Math.pow(d / s, e));
            b += hh * Math.exp(-Math.pow(Math.hypot(u - hx, v - hy) / hs, 2)); // hombro
            if (crater) b -= 0.1 * Math.exp(-Math.pow(d / (s * 0.13), 2));
            return b;
          },
        };
      }
      case 'dos': {
        const a = r.range(0, Math.PI), d = r.range(0.26, 0.4);
        const cx = 0.5 + r.range(-0.05, 0.05), cy = 0.5 + r.range(-0.03, 0.07);
        const x1 = cx + Math.cos(a) * d / 2, y1 = cy + Math.sin(a) * d / 2;
        const x2 = cx - Math.cos(a) * d / 2, y2 = cy - Math.sin(a) * d / 2;
        const s1 = r.range(0.13, 0.19), s2 = r.range(0.11, 0.17), h2 = r.range(0.6, 0.9), e = r.range(1.2, 1.7);
        return {
          detA: r.range(0.25, 0.42),
          f: (u, v) => Math.exp(-Math.pow(Math.hypot(u - x1, v - y1) / s1, e)) +
            h2 * Math.exp(-Math.pow(Math.hypot(u - x2, v - y2) / s2, e)),
        };
      }
      case 'cordillera': {
        const th = r.range(0, Math.PI), w = r.range(0.07, 0.13), k = r.range(4, 9);
        const ph = r.range(0, 6.28), am = r.range(0.03, 0.1), off = r.range(0, 50);
        const c = Math.cos(th), s = Math.sin(th);
        return {
          detA: r.range(0.3, 0.5),
          f: (u, v) => {
            const x = u - 0.5, y = v - 0.5, a = x * c + y * s;
            const q = -x * s + y * c + am * Math.sin(a * k + ph);
            const env = Math.exp(-Math.pow(a / 0.4, 2));
            const along = clamp(0.6 + 0.4 * (N.fbm(a * 4 + off, off, 3) * 1.2 + 0.5), 0.2, 1.2);
            return env * (Math.exp(-((q / w) ** 2)) * along + 0.15 * Math.exp(-((q / (w * 3.2)) ** 2)));
          },
        };
      }
      case 'mesa': {
        const cx = 0.5 + r.range(-0.05, 0.05), cy = 0.5 + r.range(-0.03, 0.08), R = r.range(0.2, 0.3);
        const tx = r.range(-0.12, 0.12), ty = r.range(-0.12, 0.12), off = r.range(0, 50);
        return {
          detA: r.range(0.06, 0.12),
          f: (u, v) => {
            const d = Math.hypot(u - cx, v - cy) + 0.09 * N.fbm(u * 3 + off, v * 3 + off, 4) +
              0.035 * N.ridged(u * 10 + off, v * 10, 4);
            const cantil = 1 / (1 + Math.exp((d - R) / 0.016));
            const talud = 0.22 * Math.exp(-Math.pow(Math.max(0, d - R) / 0.07, 2));
            return 0.1 * Math.exp(-d * d / 0.35) + talud + cantil * (0.66 + tx * (u - 0.5) + ty * (v - 0.5));
          },
        };
      }
      case 'canon': {
        const th = r.range(-0.6, 0.6) + (r() < 0.5 ? 0 : Math.PI / 2);
        const w = r.range(0.06, 0.11), k = r.range(5, 10), ph = r.range(0, 6.28), am = r.range(0.04, 0.1);
        const S = r.int(3, 6), off = r.range(0, 50), tx = r.range(-0.12, 0.12);
        const c = Math.cos(th), s = Math.sin(th);
        return {
          detA: r.range(0.08, 0.14),
          f: (u, v) => {
            const x = u - 0.5, y = v - 0.5, a = x * c + y * s;
            let q = -x * s + y * c - am * Math.sin(a * k + ph) - am * 0.4 * Math.sin(a * k * 2.3 + ph * 1.7);
            q += 0.02 * N.fbm(u * 8 + off, v * 8, 3);
            const z = clamp(Math.abs(q) / w, 0, 1) * S, fl = Math.floor(z);
            const terr = Math.min(1, (fl + sst(0.6, 1, z - fl)) / S); // escalones: estratos
            return 0.12 + 0.72 * terr + tx * a + 0.06 * N.fbm(u * 2 + off, v * 2 + off, 3);
          },
        };
      }
      case 'archi': {
        const k = r.int(4, 7), bl = [];
        for (let i = 0; i < k; i++) bl.push({ x: r.range(0.15, 0.85), y: r.range(0.15, 0.85), s: r.range(0.06, 0.15), h: i === 0 ? 1 : r.range(0.35, 0.85) });
        return {
          detA: r.range(0.3, 0.5), mar: r.range(0.12, 0.2),
          f: (u, v) => {
            let b = 0;
            for (const o of bl) b = Math.max(b, o.h * Math.exp(-Math.pow(Math.hypot(u - o.x, v - o.y) / o.s, 1.6)));
            return b;
          },
        };
      }
    }
  }

  // Una colada de lava: lengua que baja desde la boca, se ensancha y termina en frente lobulado.
  function colada(r, cx, cy, r0, L, w, t, N) {
    const a0 = r.range(0, 6.283), amp = r.range(0.15, 0.5), fr = r.range(2, 5), ph = r.range(0, 6.28);
    const pts = [];
    for (let k = 0; k <= 30; k++) {
      const q = k / 30, a = a0 + amp * Math.sin(q * fr + ph) * q, d = r0 + q * L;
      pts.push([cx + Math.cos(a) * d, cy + Math.sin(a) * d]);
    }
    let largo = 0, x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (let k = 0; k < pts.length; k++) {
      if (k) largo += Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]);
      x0 = Math.min(x0, pts[k][0]); x1 = Math.max(x1, pts[k][0]); y0 = Math.min(y0, pts[k][1]); y1 = Math.max(y1, pts[k][1]);
    }
    const m = w * 1.6;
    return {
      medio: pts[17], largo,
      espesor(u, v) {
        if (u < x0 - m || u > x1 + m || v < y0 - m || v > y1 + m) return 0;
        let dm = Infinity, sm = 0;
        for (let k = 1; k < pts.length; k++) {
          const [ax, ay] = pts[k - 1], [bx, by] = pts[k], dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy;
          const f = Math.max(0, Math.min(1, ((u - ax) * dx + (v - ay) * dy) / L2));
          const d = Math.hypot(u - ax - dx * f, v - ay - dy * f);
          if (d < dm) { dm = d; sm = (k - 1 + f) / 30; }
        }
        const ancho = w * (0.6 + 0.5 * sm) * (1 + 0.25 * Math.sin(sm * 17 + ph));
        if (dm > ancho) return 0;
        let e = t * Math.sqrt(1 - (dm / ancho) ** 2) * Math.min(1, sm / 0.06);
        if (N) e *= 1 + 0.4 * N(u * 70, v * 70); // malpaís: la superficie de la lava es áspera
        return e;
      },
    };
  }

  // Cráteres de impacto estampados en metros, del más viejo al más joven: el joven borra lo
  // que cae dentro de su tazón, y entre impacto e impacto el terreno se suaviza un poco,
  // así los viejos quedan romos y los jóvenes filosos.
  function estampaImpactos(h, N, r, kmLado, fotos) {
    const mCelda = kmLado * 1000 / (N - 1), R0 = r.range(40, 140);
    const hm = new Float32Array(h.length);
    for (let i = 0; i < h.length; i++) hm[i] = h[i] * R0;
    const n = r.int(14, 45), Dmin = kmLado * 1000 * 0.025, Dmax = kmLado * 1000 * r.range(0.16, 0.32), al = 1.8;
    const lista = [];
    for (let k = 0; k < n; k++) {
      const D = Dmin * Math.pow(1 - r() * (1 - Math.pow(Dmin / Dmax, al)), -1 / al);
      lista.push({ x: r.range(0.05, 0.95), y: r.range(0.05, 0.95), D, k });
    }
    const Dc = kmLado * 1000 * 0.12, tmp = new Float32Array(hm.length);
    const en = (x, y) => hm[Math.max(0, Math.min(N - 1, Math.round(y))) * N + Math.max(0, Math.min(N - 1, Math.round(x)))];
    const tomas = [];
    for (const c of lista) {
      if (fotos && (c.k === 0 || c.k === Math.floor(n / 3) || c.k === Math.floor(2 * n / 3))) tomas.push({ k: c.k, hm: hm.slice() });
      const Rc = c.D / 2 / mCelda, cx = c.x * (N - 1), cy = c.y * (N - 1), complejo = c.D > Dc;
      let ref = 0;
      for (let a = 0; a < 12; a++) ref += en(cx + Math.cos(a / 12 * 6.283) * Rc * 1.3, cy + Math.sin(a / 12 * 6.283) * Rc * 1.3);
      ref /= 12;
      const prof = (complejo ? 0.1 : 0.2) * c.D, borde = 0.04 * c.D;
      const i0 = Math.max(0, Math.floor(cx - 3 * Rc)), i1 = Math.min(N - 1, Math.ceil(cx + 3 * Rc));
      const j0 = Math.max(0, Math.floor(cy - 3 * Rc)), j1 = Math.min(N - 1, Math.ceil(cy + 3 * Rc));
      for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
        const rr = Math.hypot(i - cx, j - cy) / Rc, k = j * N + i;
        const labio = borde * Math.exp(-(((rr - 1) / 0.18) ** 2));
        if (rr < 1) {
          let taza;
          if (!complejo) taza = -prof * (1 - rr * rr);
          else { // fondo plano, paredes en terrazas, pico central
            const z = sst(0.5, 1, rr) * 3, fl = Math.floor(z), tt = Math.min(1, (fl + sst(0.55, 1, z - fl)) / 3);
            taza = -prof * (1 - tt) + 0.6 * prof * Math.exp(-((rr / 0.13) ** 2));
          }
          const w = sst(1, 0.85, rr);
          hm[k] = (hm[k] + labio) * (1 - w) + (ref + taza + labio) * w;
        } else hm[k] += labio + borde * 0.5 * Math.pow(1 / rr, 3) * sst(1, 1.15, rr) * (rr < 3 ? 1 : 0);
      }
      tmp.set(hm);
      for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) {
        const k = y * N + x;
        hm[k] = 0.6 * tmp[k] + 0.1 * (tmp[k - 1] + tmp[k + 1] + tmp[k - N] + tmp[k + N]);
      }
      c.complejo = complejo;
    }
    let mn = Infinity, mx = -Infinity;
    for (const v of hm) { if (v < mn) mn = v; if (v > mx) mx = v; }
    for (let i = 0; i < h.length; i++) h[i] = (hm[i] - mn) / (mx - mn);
    const esp = [...lista].sort((a, b) => b.D - a.D).slice(0, 3).map((c) => ({
      u: c.x, v: c.y, tipo: 'crater', term: c.complejo ? 'CRÁTER COMPLEJO' : 'CRÁTER',
      diam: c.D / (kmLado * 1000), busca: 'min', rad: c.D / kmLado / 1000 * 0.35,
    }));
    const norm = (a) => { const o = new Float32Array(a.length); for (let i = 0; i < a.length; i++) o[i] = (a[i] - mn) / (mx - mn); return o; };
    return { relieve: Math.round((mx - mn) / 10) * 10, esp, n, tomas: tomas.map((t) => ({ k: t.k, h: norm(t.hm) })) };
  }

  // ── Hidrología: dónde se junta el agua y por dónde corre.
  // 1) Relleno por prioridad (Barnes): el agua sube en cada hondonada hasta su nivel de
  //    derrame; lo que queda bajo ese nivel es lago. 2) Cada celda escurre a su vecina más
  //    baja de esa superficie y acumula el área que le llega. 3) Donde el área pasa un umbral
  //    nace un río; se sigue aguas abajo hasta el borde, el mar, un lago o otro río.
  function hidrologia(T, r, o = {}) { // o: {humedad, maxLago} sólo para experimentos
    const N = T.G, n = N * N, h = T.h;
    const W = new Float32Array(n), cerrado = new Uint8Array(n), mar = new Uint8Array(n);
    // para enrutar, el terreno lleva un temblor mínimo: en lo plano la rejilla trazaría ríos rectos
    const Nr = MT.ruido(r), z = new Float32Array(n);
    for (let i = 0; i < n; i++) z[i] = h[i] + 0.014 * Nr.fbm((i % N) / N * 7, ((i / N) | 0) / N * 7, 5);
    const hk = new Float64Array(n + 1), hi = new Int32Array(n + 1); let hn = 0; // montículo binario
    const push = (k, i) => { let c = ++hn; while (c > 1 && hk[c >> 1] > k) { hk[c] = hk[c >> 1]; hi[c] = hi[c >> 1]; c >>= 1; } hk[c] = k; hi[c] = i; };
    const pop = () => {
      const i = hi[1], k = hk[hn], j0 = hi[hn--]; let c = 1;
      while (true) { let m = c * 2; if (m > hn) break; if (m + 1 <= hn && hk[m + 1] < hk[m]) m++; if (hk[m] >= k) break; hk[c] = hk[m]; hi[c] = hi[m]; c = m; }
      hk[c] = k; hi[c] = j0; return i;
    };
    for (let i = 0; i < n; i++) {
      const x = i % N, y = (i / N) | 0;
      if (T.mar && h[i] <= T.umbralMar) mar[i] = 1;
      if (x === 0 || y === 0 || x === N - 1 || y === N - 1 || mar[i]) { W[i] = z[i]; cerrado[i] = 1; push(z[i], i); }
    }
    const EPS = 1e-6;
    while (hn > 0) {
      const c = pop(), x = c % N, y = (c / N) | 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        if (!dx && !dy) continue;
        const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= N || ny >= N) continue;
        const j = ny * N + nx; if (cerrado[j]) continue;
        cerrado[j] = 1; W[j] = Math.max(z[j], W[c] + EPS); push(W[j], j);
      }
    }
    // lagos: hondonadas de al menos unos metros de hondo y un área que se vea
    const lago = new Int32Array(n).fill(-1), cand = [], minHondo = 8 / Math.max(1, T.relieve), minArea = Math.round(n * r.range(0.0012, 0.003));
    const tiroH = r.int(1, 4), humedad = o.humedad || tiroH, maxArea = n * (o.maxLago || 0.02);
    for (let i = 0; i < n; i++) {
      if (lago[i] !== -1 || mar[i] || W[i] - z[i] <= minHondo * 0.25) continue;
      const cola = [i], celdas = []; lago[i] = -2; let maxD = 0, iD = i;
      while (cola.length) {
        const c = cola.pop(); celdas.push(c);
        const d = W[c] - z[c]; if (d > maxD) { maxD = d; iD = c; }
        const x = c % N, y = (c / N) | 0;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= N || ny >= N) continue;
          const j = ny * N + nx;
          if (lago[j] === -1 && !mar[j] && W[j] - z[j] > minHondo * 0.25) { lago[j] = -2; cola.push(j); }
        }
      }
      for (const c of celdas) lago[c] = -3;
      if (celdas.length >= minArea && celdas.length <= maxArea && maxD > minHondo) cand.push({ i: iD, area: celdas.length, nivel: W[iD], hondo: maxD, celdas });
    }
    // sólo se llenan las más hondas (los cráteres ganan solos); el resto son cuencas secas
    const lagos = cand.sort((a, b) => b.hondo - a.hondo).slice(0, humedad);
    lagos.forEach((l, k) => { for (const c of l.celdas) lago[c] = k; delete l.celdas; });
    // la superficie del lago es plana: el terreno visible pasa a ser el agua
    const agua = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      if (lago[i] >= 0) { h[i] = W[i]; agua[i] = 1; } else if (mar[i]) agua[i] = 1;
    }
    // direcciones y área drenada sobre la superficie rellena
    const SH = 2 ** 18, keys = new Float64Array(n), rec = new Int32Array(n).fill(-1), A = new Float32Array(n).fill(1);
    for (let i = 0; i < n; i++) keys[i] = Math.floor((1 - Math.min(1, Math.max(0, W[i]))) * 16777215) * SH + i;
    keys.sort();
    // cada celda escoge entre sus vecinas más bajas, con probabilidad según la pendiente:
    // con la vecina más baja siempre, en lo parejo saldrían rectas de regla
    const cj = new Int32Array(8), cw = new Float32Array(8);
    for (let i = 0; i < n; i++) {
      if (mar[i]) continue;
      const x = i % N, y = (i / N) | 0; let k = 0, tot = 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        if (!dx && !dy) continue;
        const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= N || ny >= N) continue;
        const j = ny * N + nx, d = (W[i] - W[j]) / (dx && dy ? 1.414 : 1);
        if (d > 0) { cj[k] = j; cw[k] = Math.pow(d, 1.3); tot += cw[k]; k++; }
      }
      if (!k) continue;
      let t = r() * tot, q = 0;
      while (q < k - 1 && t > cw[q]) { t -= cw[q]; q++; }
      rec[i] = cj[q];
    }
    for (let q = 0; q < n; q++) { const i = keys[q] % SH; if (rec[i] >= 0) A[rec[i]] += A[i]; }

    // ríos: celdas con área mayor al umbral, fuera de lagos y mar
    // en una cuenca seca (rellena pero sin lago) el río se pierde: ahí la rejilla trazaría rectas
    const umbral = n * r.range(0.0035, 0.008), esRio = (i) => A[i] >= umbral && !agua[i] && W[i] - z[i] < 2e-5;
    const llega = new Uint8Array(n);
    for (let i = 0; i < n; i++) if (esRio(i) && rec[i] >= 0 && esRio(rec[i])) llega[rec[i]] = 1;
    const visto = new Uint8Array(n), rios = [];
    const uv = (i) => [(i % N) / (N - 1), ((i / N) | 0) / (N - 1)];
    const clase = (a) => (a > umbral * 10 ? 3 : a > umbral * 3 ? 2 : 1);
    for (let s = 0; s < n; s++) {
      if (!esRio(s) || llega[s]) continue; // nacimiento: nadie le llega
      let c = s, tramo = [uv(c)], cl = clase(A[c]);
      while (true) {
        visto[c] = 1;
        const d = rec[c];
        if (d < 0) break;
        tramo.push(uv(d));
        const cd = clase(A[d]);
        if (agua[d] || visto[d]) break; // desemboca en lago/mar o en otro río
        if (cd !== cl) { rios.push({ clase: cl, pts: tramo }); tramo = [uv(d)]; cl = cd; }
        c = d;
      }
      if (tramo.length > 1) rios.push({ clase: cl, pts: tramo });
    }
    // suavizado (Chaikin): el escalón de la rejilla no es un río
    for (const rv of rios) {
      let p = rv.pts;
      for (let k = 0; k < 3 && p.length > 2; k++) {
        const q = [p[0]];
        for (let i = 0; i < p.length - 1; i++) {
          const [ax, ay] = p[i], [bx, by] = p[i + 1];
          q.push([ax * 0.75 + bx * 0.25, ay * 0.75 + by * 0.25], [ax * 0.25 + bx * 0.75, ay * 0.25 + by * 0.75]);
        }
        q.push(p[p.length - 1]); p = q;
      }
      rv.pts = p;
    }
    // el cauce principal: desde la salida con más área, aguas arriba por el afluente mayor
    let sal = -1;
    for (let i = 0; i < n; i++) if (!agua[i] && (rec[i] < 0 || agua[rec[i]]) && (sal < 0 || A[i] > A[sal])) sal = i;
    const sube = new Map();
    for (let i = 0; i < n; i++) if (rec[i] >= 0 && esRio(i)) { const l = sube.get(rec[i]); if (l) l.push(i); else sube.set(rec[i], [i]); }
    const tallo = [];
    for (let c = sal; c >= 0 && esRio(c);) {
      tallo.push(uv(c));
      const l = sube.get(c); if (!l) break;
      c = l.reduce((a, b) => (A[b] > A[a] ? b : a));
    }
    let largo = 0;
    for (let k = 1; k < tallo.length; k++) largo += Math.hypot(tallo[k][0] - tallo[k - 1][0], tallo[k][1] - tallo[k - 1][1]);
    return {
      rios, agua, lagos: lagos.map((l) => ({ u: uv(l.i)[0], v: uv(l.i)[1], nivel: l.nivel, area: l.area, hondo: l.hondo })),
      principal: tallo.length > 8 ? { pts: tallo.reverse(), largoKm: largo * T.anchoKm } : null,
    };
  }

  // ── Eventos geológicos: lo que le pasó a la montaña después de levantarse.
  // 40 % de las semillas tiene al menos uno, 10 % dos, 2 % tres. Los viejos pasan antes de la
  // erosión (quedan suavizados); los jóvenes después (quedan filosos). Un evento que no se
  // alcanzaría a leer en el papel (menos de 5 mm en una planta de 150 mm) no pasó.
  const TIPOS_EVENTO = {
    // otra cadena que atraviesa la hoja en otro ángulo; su eje puede quedar fuera del mapa
    cruzada(r, km) {
      const th = r.range(0, Math.PI), off = r.range(-0.35, 0.35), w = r.range(0.06, 0.11), amp = r.range(0.55, 0.95);
      const N = MT.ruido(r), c = Math.cos(th), s = Math.sin(th), ph = r.range(0, 50);
      return {
        nombre: 'CORDILLERA CRUZADA', km, siempreViejo: true,
        f: (u, v, h) => {
          const x = u - 0.5, y = v - 0.5, a = x * c + y * s, q = -x * s + y * c - off + 0.05 * N.fbm(a * 3 + ph, ph, 3);
          const largo = 0.65 + 0.35 * N.fbm(a * 4 + ph, 9, 3), cresta = 1 - 0.5 * Math.abs(N.ridged(u * 9 + ph, v * 9, 4) - 0.5);
          return h + amp * largo * cresta * Math.exp(-((q / w) ** 2));
        },
      };
    },
    // volcanes grandes, vecinos y distintos (como el Popo y el Izta): conos con su cráter
    volcanes(r, km) {
      const n = r.int(1, 3), conos = [], Nv = MT.ruido(r);
      for (let k = 0; k < n; k++) {
        const kmc = r.range(3, 7.5), R = kmc / km / 2;
        conos.push({ x: r.range(0.18, 0.82), y: r.range(0.18, 0.82), R, H: r.range(0.55, 1.1), p: r.range(1.4, 2.2), rc: R * r.range(0.07, 0.13), dc: r.range(0.05, 0.1), km: kmc });
      }
      return {
        nombre: n === 1 ? 'VOLCÁN' : `${n} VOLCANES`, km: Math.min(...conos.map((c) => c.km)),
        f: (u, v, h) => {
          let top = 0;
          for (const c of conos) {
            const d = Math.hypot(u - c.x, v - c.y);
            if (d > c.R) continue;
            // cárcavas radiales: el cono no es de compás
            const ang = Math.atan2(v - c.y, u - c.x), surco = 1 - 0.12 * Math.abs(Nv(ang * 4 + c.x * 50, d / c.R * 3));
            let z = c.H * Math.pow(1 - d / c.R, c.p) * surco;
            if (d < c.rc) z = c.H * Math.pow(1 - c.rc / c.R, c.p) - c.dc * (1 - (d / c.rc) ** 2);
            top = Math.max(top, z);
          }
          return h + top * 0.85; // el cono se suma a lo que había: sin bordes de compás
        },
        esp: conos.map((c) => ({ u: c.x, v: c.y, tipo: 'crater', term: 'CRÁTER', diam: 2 * c.rc, busca: 'min', rad: c.rc * 1.5 })),
      };
    },
    // cráter de impacto: borra lo que cae en su tazón y levanta un borde
    impacto(r, km) {
      const kmc = r.range(0.8, Math.min(4, km * 0.3)), R = kmc / km / 2, x = r.range(0.2, 0.8), y = r.range(0.2, 0.8);
      const prof = r.range(0.12, 0.25), complejo = kmc > 2.2;
      return {
        nombre: complejo ? 'IMPACTO GRANDE' : 'IMPACTO', km: kmc, ref: 0,
        prepara(G) { let s = 0; for (let a = 0; a < 16; a++) s += G(x + Math.cos(a / 16 * 6.283) * R * 1.3, y + Math.sin(a / 16 * 6.283) * R * 1.3); this.ref = s / 16; },
        f(u, v, h) {
          const rr = Math.hypot(u - x, v - y) / R, borde = 0.05 * Math.exp(-(((rr - 1) / 0.18) ** 2));
          if (rr >= 1) return h + (rr < 2.5 ? borde : 0);
          let taza = -prof * (1 - rr * rr);
          if (complejo) taza = -prof * 0.6 * (1 - sst(0.5, 1, rr)) + 0.25 * prof * Math.exp(-((rr / 0.15) ** 2));
          const w = sst(1, 0.8, rr);
          return h * (1 - w) + (this.ref + taza + borde) * w;
        },
        esp: [{ u: x, v: y, tipo: 'crater', term: complejo ? 'CRÁTER DE IMPACTO' : 'IMPACTO', diam: 2 * R, busca: 'min', rad: R * 0.6 }],
      };
    },
    // barranca: un tajo en V que serpentea de borde a borde
    barranca(r, km) {
      const th = r.range(0, Math.PI), c = Math.cos(th), s = Math.sin(th), off = r.range(-0.25, 0.25), Nb = MT.ruido(r);
      const am = r.range(0.04, 0.09), k = r.range(6, 12), ph = r.range(0, 6.28), w = r.range(0.018, 0.035), prof = r.range(0.15, 0.3);
      return {
        nombre: 'BARRANCA', km: w * 2 * km, siempreViejo: true,
        f: (u, v, h) => {
          const x = u - 0.5, y = v - 0.5, a = x * c + y * s, q = -x * s + y * c - off - am * Math.sin(a * k + ph) - 0.03 * Nb.fbm(a * 14 + ph, 3, 4);
          const d = Math.abs(q) / w;
          return d < 1 ? h - prof * (1 - d) * Math.min(1, h * 2 + 0.3) : h;
        },
      };
    },
    // falla: un escalón que parte el terreno en dos alturas; el salto crece y se apaga a lo largo
    falla(r, km) {
      const th = r.range(0, Math.PI), c = Math.cos(th), s = Math.sin(th), off = r.range(-0.25, 0.25), salto = r.range(0.08, 0.18), w = r.range(0.006, 0.014), Nf = MT.ruido(r);
      return {
        nombre: 'FALLA', km, falla: { x: 0.5 - s * off, y: 0.5 + c * off, nx: -s, ny: c, w },
        f: (u, v, h) => {
          const a = (u - 0.5) * c + (v - 0.5) * s, q = (u - 0.5) * -s + (v - 0.5) * c - off - 0.008 * Nf.fbm(a * 12, 1, 3);
          return h + salto * (0.55 + 0.45 * Nf.fbm(a * 3 + 7, 5, 3)) * (sst(-w, w, q) - 0.5);
        },
      };
    },
    // glaciación: el hielo cava circos con su lago al pie de las cumbres, valles en U con
    // escalones de roca (detrás de cada uno, una cubeta que será lago) y deja su morrena al final
    glaciacion(r, km) {
      return {
        nombre: 'GLACIACIÓN', km: km * 0.2, siempreJoven: true, esp: [],
        grid(h, N) {
          const G = muestreo(h, N), hb = suaviza(h, N, 4), nieve = r.range(0.42, 0.55), circos = [];
          for (let k = 0, n = r.int(4, 7); k < 4000 && circos.length < n; k++) {
            const u = r.range(0.08, 0.92), v = r.range(0.08, 0.92), z = G(u, v);
            if (z > nieve && z < 0.92 && circos.every((c) => Math.hypot(c[0] - u, c[1] - v) > 0.13)) circos.push([u, v]);
          }
          let largo = 0, medio = null, fin = null;
          for (const [u0, v0] of circos) {
            let i = Math.round(u0 * (N - 1)), j = Math.round(v0 * (N - 1)), pi = 0, pj = 0; const pts = [[u0, v0]];
            for (let st = 0; st < 220; st++) {
              let best = hb[j * N + i], bi = 0, bj = 0;
              for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
                if (!di && !dj) continue; const x = i + di, y = j + dj; if (x < 1 || y < 1 || x >= N - 1 || y >= N - 1) continue;
                const z = hb[y * N + x] - (di === pi && dj === pj ? 0.0004 : 0); if (z < best) { best = z; bi = di; bj = dj; }
              }
              if (!bi && !bj) break; i += bi; j += bj; pi = bi; pj = bj;
              if (st % 3 === 0) pts.push([i / (N - 1), j / (N - 1)]);
              if (hb[j * N + i] < nieve * 0.3) break;
            }
            if (pts.length < 6) continue;
            const w = r.range(0.045, 0.07), D = r.range(0.14, 0.22), paso = r.range(0.18, 0.3), z0 = G(u0, v0);
            const fondo = (s) => { const k = Math.min(pts.length - 1, Math.round(s * (pts.length - 1))); return hb[Math.round(pts[k][1] * (N - 1)) * N + Math.round(pts[k][0] * (N - 1))] - D * (0.55 + 0.6 * (s / paso - Math.floor(s / paso))); };
            const L = aLinea(h, N, pts, w * 1.4, (z, d, s) => { const f = fondo(s), q = d / w; return q < 1 ? Math.min(z, f + (z - f) * Math.pow(q, 3)) : Math.min(z, z - (1.4 - q) / 0.4 * 0.004); });
            const rc = w * 1.7, [ue, ve] = pts[pts.length - 1], [up, vp] = pts[pts.length - 4], dx = ue - up, dy = ve - vp, dl = Math.hypot(dx, dy) || 1;
            for (let k = 0; k < h.length; k++) {
              const u = (k % N) / (N - 1), v = Math.floor(k / N) / (N - 1), d = Math.hypot(u - u0, v - v0) / rc;
              if (d < 1) h[k] = Math.min(h[k], z0 - D * 1.3 + (h[k] - z0 + D * 1.3) * Math.pow(d, 2.5)); // circo
              const de = Math.hypot(u - ue, v - ve);
              if (((u - ue) * dx + (v - ve) * dy) / dl > -w * 0.4 && de < w * 2.2) h[k] += 0.018 * Math.exp(-(((de - w * 1.1) / (w * 0.3)) ** 2)); // morrena
            }
            this.esp.push({ u: u0, v: v0, tipo: 'crater', term: 'CIRCO', busca: 'min', rad: rc * 0.5 });
            if (L > largo) { largo = L; medio = pts[Math.floor(pts.length / 2)]; fin = [ue, ve]; }
          }
          if (medio) this.esp.push({ u: medio[0], v: medio[1], tipo: 'colada', term: 'VALLE GLACIAR', largo }, { u: fin[0], v: fin[1], tipo: 'colada', term: 'MORRENA' });
        },
      };
    },
    // abanico aluvial: donde un torrente sale de la montaña a la llanura, suelta su escombro en
    // un cono de pendiente suave, surcado por cauces que se abren en abanico
    abanico(r, km) {
      const a = r.range(0, 6.283), fL = r.range(0.6, 0.95), mitad = r.range(0.55, 0.95), nC = r.int(5, 9), grosor = r.range(0.11, 0.16);
      return {
        nombre: 'ABANICO ALUVIAL', km: km * 0.2, siempreJoven: true, esp: [],
        grid(h, N) {
          const { cx, cy, R, top } = conoDe(h, N), G = muestreo(h, N), c = Math.cos(a), s = Math.sin(a);
          let d0 = 0.05; while (d0 < 0.6 && G(cx + c * d0, cy + s * d0) > top * 0.22) d0 += 0.005; // el pie del monte, donde empieza lo plano
          const ax = cx + c * d0, ay = cy + s * d0, L = R * fL;
          for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
            const u = i / (N - 1), v = j / (N - 1), dx = u - ax, dy = v - ay, d = Math.hypot(dx, dy); if (d > L || d < 1e-4) continue;
            let da = Math.abs(Math.atan2(dy, dx) - a); if (da > Math.PI) da = 2 * Math.PI - da; if (da > mitad) continue;
            const borde = sst(mitad, mitad * 0.7, da) * sst(L, L * 0.8, d);
            const cuerpo = grosor * Math.pow(1 - d / L, 1.2) * (1 - 0.15 * Math.abs(Math.sin(da / mitad * nC * Math.PI))); // los cauces que se abren
            const kk = j * N + i; h[kk] += cuerpo * borde;
          }
          this.esp = [{ u: ax + c * L * 0.5, v: ay + s * L * 0.5, tipo: 'colada', term: 'ABANICO', largo: L }];
        },
      };
    },
    // falla transformante: desliza de lado; todo lo que la cruza (valles, crestas, ríos) queda desplazado
    transformante(r, km) {
      const th = r.range(0, Math.PI), c = Math.cos(th), s = Math.sin(th), off = r.range(-0.15, 0.15), D = r.range(0.06, 0.1), w = 0.006, Nz = MT.ruido(r);
      return {
        nombre: 'FALLA TRANSFORMANTE', km: km * 0.2, siempreJoven: true, esp: [],
        grid(h, N) {
          const orig = h.slice(), G = muestreo(orig, N);
          for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
            const u = i / (N - 1), v = j / (N - 1), q = (u - 0.5) * -s + (v - 0.5) * c - off, sh = D / 2 * Math.tanh(q / w);
            h[j * N + i] = G(u - c * sh, v - s * sh) - 0.03 * Math.exp(-((q / 0.008) ** 2)) * (0.6 + 0.4 * Nz(u * 20, v * 20)); // charcos sobre la falla
          }
          this.esp = [{ u: 0.5 - s * off, v: 0.5 + c * off, tipo: 'falla', term: 'FALLA', dato: `DESPLAZAMIENTO ${Math.round(D * km * 100) * 10} M` }];
        },
      };
    },
    // ── Rarezas (cada una con su sorteo, ~2 %): lo excéntrico de la serie.
    // supercaldera: un hundimiento mayor que la hoja; sólo se ve un borde curvo que la cruza
    supercaldera(r, km) {
      const a = r.range(0, 6.283), Rk = r.range(1.4, 2.6), d = Rk * r.range(0.75, 1.05), salto = r.range(0.22, 0.35), w = r.range(0.01, 0.02);
      const cx = 0.5 + Math.cos(a) * d, cy = 0.5 + Math.sin(a) * d;
      return {
        nombre: 'SUPERCALDERA', km, siempreViejo: true,
        f: (u, v, h) => { const q = Math.hypot(u - cx, v - cy) - Rk; return h - salto * sst(w, -w, q) + 0.04 * Math.exp(-(((q - w * 3) / (w * 3)) ** 2)); },
        esp: [{ u: 0.5 + Math.cos(a) * (d - Rk) * 0.98, v: 0.5 + Math.sin(a) * (d - Rk) * 0.98, tipo: 'falla', term: 'SUPERCALDERA', dato: `Ø ${Math.round(Rk * 2 * km)} KM` }],
      };
    },
    // meseta de lava (trapps): coladas apiladas, el relieve en escalones
    trapps(r, km) {
      const k = r.int(5, 9), filo = r.range(0.55, 0.8);
      return {
        nombre: 'COLADAS APILADAS', km, siempreViejo: true,
        f: (u, v, h) => { const z = h * k, f = Math.floor(z), t = z - f; return (f + sst(filo, 1, t)) / k * 0.85 + h * 0.15; },
      };
    },
    // anillo de toba: cráter ancho y bajo, con su anillo de ceniza
    toba(r, km) {
      const n = r.int(1, 2), an = Array.from({ length: n }, () => ({ x: r.range(0.2, 0.8), y: r.range(0.2, 0.8), R: r.range(0.08, 0.14), H: r.range(0.08, 0.14) }));
      return {
        nombre: n === 1 ? 'ANILLO DE TOBA' : '2 ANILLOS DE TOBA', km: km * 0.25,
        f: (u, v, h) => { for (const o of an) { const q = Math.hypot(u - o.x, v - o.y) / o.R; if (q < 1) h = Math.min(h, h * 0.3 + 0.02); h += o.H * Math.exp(-(((q - 1) / 0.22) ** 2)); } return h; },
        esp: an.map((o) => ({ u: o.x, v: o.y, tipo: 'crater', term: 'ANILLO DE TOBA', diam: o.R * 2, busca: 'min', rad: o.R * 0.5 })),
      };
    },
    // morrenas en escalera: arcos anidados que el hielo dejó al ir retrocediendo
    morrenas(r, km) {
      const a = r.range(0, 6.283), c = Math.cos(a), s = Math.sin(a), n = r.int(3, 6), R0 = r.range(0.15, 0.25), paso = r.range(0.045, 0.07), abre = r.range(0.9, 1.4);
      const cx = 0.5 - c * r.range(0.25, 0.4), cy = 0.5 - s * r.range(0.25, 0.4), Nm = MT.ruido(r);
      return {
        nombre: 'MORRENAS', km: km * 0.25,
        f: (u, v, h) => {
          const dx = u - cx, dy = v - cy, d = Math.hypot(dx, dy); let da = Math.abs(Math.atan2(dy, dx) - a); if (da > Math.PI) da = 2 * Math.PI - da;
          if (da > abre) return h;
          let z = 0; for (let k = 0; k < n; k++) z = Math.max(z, (1 - k / n * 0.5) * Math.exp(-(((d - R0 - k * paso) / 0.013) ** 2)));
          return h + 0.16 * z * sst(abre, abre * 0.7, da) * (0.8 + 0.2 * Nm(u * 30, v * 30));
        },
        esp: [{ u: cx + c * R0, v: cy + s * R0, tipo: 'colada', term: `${n} MORRENAS` }],
      };
    },
    // sumidero gigante: un pozo de paredes verticales que se tragó el terreno
    sumidero(r, km) {
      const x = r.range(0.3, 0.7), y = r.range(0.3, 0.7), R = r.range(0.07, 0.11), hondo = r.range(0.45, 0.6);
      return {
        nombre: 'SUMIDERO GIGANTE', km: R * 2 * km,
        f: (u, v, h) => { const q = Math.hypot(u - x, v - y) / R; return q < 1 ? h - hondo * (1 - Math.pow(q, 14)) : h; },
        esp: [{ u: x, v: y, tipo: 'crater', term: 'SUMIDERO', diam: R * 2, busca: 'min', rad: R * 0.5 }],
      };
    },
    // deslave: una ladera empinada se viene abajo; arriba el anfiteatro, abajo el lóbulo de escombro
    deslave(r, km) {
      const Nz = MT.ruido(r), a = r.range(0, 6.283), f0 = r.range(0.4, 0.6), fS = r.range(0.16, 0.26);
      return {
        nombre: 'DESLAVE', km: km * 0.2, esp: [],
        grid(h, N) {
          const { cx, cy, R } = conoDe(h, N), c = Math.cos(a), s = Math.sin(a), S = R * fS;
          const px = cx + c * R * f0, py = cy + s * R * f0, lx = px + c * S * 2.6, ly = py + s * S * 2.6, prof = 0.12;
          for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
            const u = i / (N - 1), v = j / (N - 1), k = j * N + i;
            const al = (u - px) * c + (v - py) * s, tr = -(u - px) * s + (v - py) * c, q = Math.hypot(al / S, tr / (S * 0.8));
            if (q < 1 && al < S * 0.5) h[k] -= prof * (1 - q * q) * sst(S * 0.5, 0, al);
            const al2 = (u - lx) * c + (v - ly) * s, tr2 = -(u - lx) * s + (v - ly) * c, q2 = Math.hypot(al2 / (S * 1.3), tr2 / (S * 1.5));
            if (q2 < 1) h[k] += prof * 0.55 * Math.sqrt(1 - q2 * q2) * (0.6 + 0.8 * Math.abs(Nz(u * 70, v * 70)));
          }
          this.esp = [{ u: lx, v: ly, tipo: 'colada', term: 'DESLAVE', largo: Math.hypot(lx - px, ly - py) + S * 2.3 }];
        },
      };
    },
    // colada: lava que sigue el terreno desde la cima o un flanco
    lava(r, km) {
      const Nz = MT.ruido(r), vol = r.range(75, 120), a = r.range(0, 6.283), flanco = r() < 0.5;
      return {
        nombre: 'COLADA', km: km * 0.2, esp: [],
        grid(h, N) {
          const { cx, cy, R } = conoDe(h, N);
          const c = lavaGrid(h, N, flanco ? cx + Math.cos(a) * R * 0.3 : cx, flanco ? cy + Math.sin(a) * R * 0.3 : cy, vol, r, Nz);
          this.esp = [{ u: c.medio[0], v: c.medio[1], tipo: 'colada', term: 'COLADA', largo: c.largo }];
        },
      };
    },
  };
  // ── Volcán que colapsa y renace, deslaves y lava (loop 14).
  const muestreo = (h, N) => (u, v) => {
    const x = clamp(u, 0, 1) * (N - 1), y = clamp(v, 0, 1) * (N - 1), xi = Math.min(N - 2, Math.floor(x)), yi = Math.min(N - 2, Math.floor(y)), fx = x - xi, fy = y - yi, k = yi * N + xi;
    return h[k] * (1 - fx) * (1 - fy) + h[k + 1] * fx * (1 - fy) + h[k + N] * (1 - fx) * fy + h[k + N + 1] * fx * fy;
  };
  const normaliza = (h) => { let a = Infinity, z = -Infinity; for (const v of h) { if (v < a) a = v; if (v > z) z = v; } for (let k = 0; k < h.length; k++) h[k] = (h[k] - a) / (z - a); };
  // dónde está el monte principal: lo más alto (suavizado) y su radio, medido por rayos
  function conoDe(h, N) {
    let best = -1, cx = 0.5, cy = 0.5;
    for (let j = 6; j < N - 6; j += 2) for (let i = 6; i < N - 6; i += 2) {
      let s = 0; for (let b = -4; b <= 4; b += 2) for (let a = -4; a <= 4; a += 2) s += h[(j + b) * N + i + a];
      if (s > best) { best = s; cx = i / (N - 1); cy = j / (N - 1); }
    }
    const G = muestreo(h, N), top = G(cx, cy); let R = 0;
    for (let a = 0; a < 16; a++) for (let d = 0.01; d < 0.6; d += 0.005) {
      if (G(cx + Math.cos(a / 16 * 6.283) * d, cy + Math.sin(a / 16 * 6.283) * d) < top * 0.3) { R += d; break; }
    }
    return { cx, cy, R: Math.max(0.12, R / 16), top };
  }
  // Lava como fluido espeso: cientos de porciones bajan desde la boca con inercia y algo de azar,
  // soltando roca; lo que sueltan sube el terreno y desvía a las siguientes: la colada se ensancha
  // en lo plano, se represa y termina en frentes lobulados. Devuelve su largo y su punto medio.
  function lavaGrid(h, N, u0, v0, vol, r, Nz) {
    const lay = new Float32Array(N * N), P = 360, K = 2, per = vol / P, cj = new Int32Array(8), cw = new Float32Array(8), dirs = [];
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (dx || dy) dirs.push([dx, dy]);
    const deposita = (x, y, q) => {
      const a = q / ((2 * K + 1) ** 2);
      for (let dy = -K; dy <= K; dy++) for (let dx = -K; dx <= K; dx++) { const i = x + dx, j = y + dy; if (i >= 0 && j >= 0 && i < N && j < N) lay[j * N + i] += a; }
    };
    for (let p = 0; p < P; p++) {
      let x = Math.round(u0 * (N - 1) + r.range(-2, 2)), y = Math.round(v0 * (N - 1) + r.range(-2, 2)), q = per, pdx = 0, pdy = 0;
      for (let st = 0; st < 360 && q > per * 0.02; st++) {
        const z = h[y * N + x] + lay[y * N + x]; let k = 0, tot = 0;
        for (let d = 0; d < 8; d++) {
          const [dx, dy] = dirs[d], i = x + dx, j = y + dy;
          if (i < 1 || j < 1 || i >= N - 1 || j >= N - 1) continue;
          const caida = (z - h[j * N + i] - lay[j * N + i]) / (dx && dy ? 1.414 : 1);
          if (caida <= 0) continue;
          cj[k] = d; cw[k] = Math.pow(caida, 1.2) * (dx === pdx && dy === pdy ? 2.5 : 1); tot += cw[k]; k++;
        }
        if (!k) { deposita(x, y, q); q = 0; break; }
        let t = r() * tot, c = 0; while (c < k - 1 && t > cw[c]) { t -= cw[c]; c++; }
        [pdx, pdy] = dirs[cj[c]]; x += pdx; y += pdy;
        const dq = q * 0.028; deposita(x, y, dq); q -= dq;
      }
      if (q > 0) deposita(x, y, q);
    }
    let lejos = 0, li = 0, lj = 0;
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      const k = j * N + i; if (lay[k] < 0.004) continue;
      h[k] += lay[k] * (0.85 + 0.3 * Math.abs(Nz(i * 0.35, j * 0.35))); // malpaís: superficie áspera
      const d = Math.hypot(i / (N - 1) - u0, j / (N - 1) - v0); if (d > lejos) { lejos = d; li = i; lj = j; }
    }
    return { largo: lejos, medio: [(u0 + li / (N - 1)) / 2, (v0 + lj / (N - 1)) / 2] };
  }
  // El estratovolcán viejo puede colapsar y renacer: caldera cerrada con lago e isla (Crater
  // Lake), abierta en herradura con avalancha y cono interior (Colima, el Teide), o con un
  // domo y lagos de cráter a sus lados (el Nevado de Toluca).
  function colapsa(h, N, r, centro) {
    const Nz = MT.ruido(r), G = muestreo(h, N), { cx, cy, R } = centro;
    const cada = (f) => { for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const k = j * N + i; h[k] = f(i / (N - 1), j / (N - 1), h[k]); } };
    const t = r(), modo = t < 0.3 ? 'lago' : t < 0.65 ? 'herradura' : 'domo';
    const rcal = Math.min(0.2, R * r.range(0.4, 0.58));
    let rim = 0; for (let a = 0; a < 24; a++) rim += G(cx + Math.cos(a / 24 * 6.283) * rcal, cy + Math.sin(a / 24 * 6.283) * rcal); rim /= 24;
    const floor = rim * r.range(0.62, 0.78), aB = r.range(0, 6.283), cB = Math.cos(aB), sB = Math.sin(aB);
    const abierta = modo !== 'lago', ancho = modo === 'herradura' ? r.range(1.2, 1.8) : r.range(0.3, 0.45);
    const fl = (u, v) => floor - (abierta ? 0.035 * ((u - cx) * cB + (v - cy) * sB) / rcal : 0); // el piso escurre hacia la salida
    cada((u, v, z) => {
      const dx = u - cx, dy = v - cy, d = Math.hypot(dx, dy);
      let da = Math.abs(Math.atan2(dy, dx) - aB); if (da > Math.PI) da = 2 * Math.PI - da;
      let out = z;
      if (d < rcal) { // pared escalonada
        const q = sst(0.78, 1, d / rcal) * 3, f = Math.floor(q), terr = Math.min(1, (f + sst(0.55, 1, q - f)) / 3);
        out = Math.min(z, fl(u, v) + (z - fl(u, v)) * terr);
      }
      if (abierta && da < ancho / 2 + 0.15 && d > rcal * 0.7) {
        const w = sst(ancho / 2 + 0.15, ancho / 2 - 0.05, da);
        out = Math.min(out, out * (1 - w) + (fl(u, v) - 0.015 - (d - rcal * 0.7) * 0.5) * w);
      }
      return out;
    });
    const aR = aB + Math.PI + r.range(-0.8, 0.8); // la caldera se rotula en su borde, no en el fondo
    const esp = [{ u: cx + Math.cos(aR) * rcal, v: cy + Math.sin(aR) * rcal, tipo: 'crater', term: 'CALDERA', diam: 2 * rcal }];
    const hist = [modo === 'herradura' ? 'COLAPSO DE FLANCO' : 'COLAPSO'];
    if (modo === 'herradura') {
      const lx = cx + cB * rcal * 2.6, ly = cy + sB * rcal * 2.6;
      cada((u, v, z) => { const q = Math.hypot(u - lx, v - ly) / (rcal * 1.5); return q < 1 ? z + 0.05 * (1 - q * q) * (0.4 + Math.abs(Nz(u * 60, v * 60))) : z; });
      esp.push({ u: lx, v: ly, tipo: 'colada', term: 'AVALANCHA', largo: rcal * 2.6 });
    }
    const ao = r.range(0, 6.283), off = r.range(0.05, 0.3) * rcal, ix = cx + Math.cos(ao) * off, iy = cy + Math.sin(ao) * off;
    let vent = [ix, iy];
    if (modo === 'domo') {
      const Ri = rcal * r.range(0.22, 0.32), Hd = (rim - floor) * r.range(0.45, 0.75);
      cada((u, v, z) => { const d = Math.hypot(u - ix, v - iy) / Ri; return d < 1 ? Math.max(z, fl(u, v) + Hd * Math.sqrt(1 - d * d) * (0.9 + 0.1 * Nz(u * 80, v * 80))) : z; });
      esp.push({ u: ix, v: iy, tipo: 'cuello', term: 'DOMO', busca: 'max', rad: Ri * 0.5 });
      for (const lado of [1, -1]) { // cráteres en el piso, a los lados del domo: ahí se junta el agua
        const a = ao + Math.PI / 2 * lado + r.range(-0.4, 0.4), dd = rcal * r.range(0.5, 0.68), mx = ix + Math.cos(a) * dd, my = iy + Math.sin(a) * dd, rm = rcal * r.range(0.24, 0.32);
        cada((u, v, z) => { const d = Math.hypot(u - mx, v - my) / rm; return d < 1 ? Math.min(z, fl(u, v) - 0.07 * (1 - d * d)) : z; });
      }
      hist.push('DOMO', 'CRÁTERES');
    } else {
      const Ri = rcal * r.range(0.55, 0.75), Hc = (rim - floor) * r.range(0.7, 1.15), rci = Ri * 0.14;
      cada((u, v, z) => {
        const d = Math.hypot(u - ix, v - iy); if (d > Ri) return z;
        let c = fl(u, v) + Hc * Math.pow(1 - d / Ri, 1.5);
        if (d < rci) c = fl(u, v) + Hc * Math.pow(1 - rci / Ri, 1.5) - 0.02 * (1 - (d / rci) ** 2);
        return Math.max(z, c);
      });
      esp.push({ u: ix, v: iy, tipo: 'cuello', term: modo === 'lago' ? 'ISLA' : 'CONO INTERIOR', busca: 'max', rad: Ri * 0.4 });
      hist.push('CONO INTERIOR');
      if (modo === 'herradura') {
        const a = ao + Math.PI + r.range(-0.6, 0.6), mx = cx + Math.cos(a) * rcal * 0.62, my = cy + Math.sin(a) * rcal * 0.62, rm = rcal * r.range(0.16, 0.22);
        cada((u, v, z) => { const d = Math.hypot(u - mx, v - my) / rm; return d < 1 ? Math.min(z, fl(u, v) - 0.07 * (1 - d * d)) : z; });
        hist.push('CRÁTER ANIDADO');
      }
    }
    normaliza(h);
    return { esp, hist, vent, lagoCal: modo === 'lago', nombre: modo === 'lago' ? 'CALDERA CON LAGO' : modo === 'herradura' ? 'CALDERA ABIERTA' : 'CALDERA CON DOMO' };
  }

  const RAROS = {
    supercaldera: [0.0, 0.05, ['cordillera', 'monte', 'dos', 'mesa', 'pliegues', 'escudo', 'estrato', 'rift', 'tepuyes', 'canon']],
    trapps: [0.013, 0.05, ['mesa', 'canon', 'monte', 'cordillera', 'dos', 'testigos', 'escudo', 'estrato']],
    toba: [0.0, 0.05, ['conos', 'escudo', 'karst', 'meandros', 'drumlins', 'impactos', 'mesa', 'archi', 'monte', 'dos', 'cordillera', 'estrato']],
    morrenas: [0.0, 0.05, ['monte', 'dos', 'drumlins', 'meandros', 'mesa']], // en lo bajo: en una sierra alta no se leen
    sumidero: [0.013, 0.045, ['karst', 'mesa', 'meandros', 'dunas', 'tepuyes', 'testigos', 'drumlins', 'monte', 'cordillera', 'canon']],
  };
  function eventosDe(seed, arq, km) {
    const r = MT.rng(seed + ':eventos'), t = r();
    const n = t < 0.02 ? 3 : t < 0.1 ? 2 : t < 0.4 ? 1 : 0;
    let tipos = ['poligonos', 'drumlins', 'badlands'].includes(arq) ? [] : ['anillos', 'rift', 'tepuyes', 'testigos', 'inselbergs'].includes(arq) ? ['impacto', 'falla', 'deslave'] : arq === 'atolon' ? [] : arq === 'costa' ? ['impacto', 'falla', 'deslave'] : arq === 'karst' || arq === 'meandros' ? ['impacto', 'falla']
      : arq === 'dunas' ? ['impacto'] : arq === 'archi' || arq === 'impactos' ? ['impacto', 'volcanes']
      : arq === 'conos' ? ['impacto', 'falla', 'barranca', 'deslave', 'lava']
      : Object.keys(TIPOS_EVENTO).filter((q) => !['glaciacion', 'abanico', 'transformante', 'supercaldera', 'trapps', 'toba', 'morrenas', 'sumidero'].includes(q) && (q !== 'lava' || arq === 'estrato' || arq === 'escudo'));
    tipos = tipos.map((q) => [q, r()]).sort((a, b) => a[1] - b[1]).map((q) => q[0]).slice(0, n);
    return tipos.map((tipo) => {
      const joven = r() < 0.5, e = TIPOS_EVENTO[tipo](r, km);
      return { tipo, ...e, joven: e.siempreViejo ? false : joven };
    }).filter((e) => (e.km / km) * 150 >= 5)
      // la glaciación va en su propia tirada: así no mueve los eventos que ya existían
      .concat(['cordillera', 'monte', 'dos'].includes(arq) && (() => { const g = MT.rng(seed + ':glaciar')(); return g >= 0.33 && g < 0.61; })() // rango que no toca semillas ya publicadas
        ? [{ tipo: 'glaciacion', ...TIPOS_EVENTO.glaciacion(MT.rng(seed + ':glaciar:forma'), km), joven: true }] : [])
      // abanico aluvial: también tirada propia, en un rango que no toca semillas publicadas
      .concat(['cordillera', 'monte', 'dos', 'pliegues', 'mesa', 'canon'].includes(arq) && (() => { const g = MT.rng(seed + ':abanico')(); return g >= 0.2 && g < 0.43; })()
        ? [{ tipo: 'abanico', ...TIPOS_EVENTO.abanico(MT.rng(seed + ':abanico:forma'), km), joven: true }] : [])
      .concat(['cordillera', 'monte', 'dos', 'pliegues', 'mesa'].includes(arq) && (() => { const g = MT.rng(seed + ':transformante')(); return g >= 0.7 && g < 0.85; })()
        ? [{ tipo: 'transformante', ...TIPOS_EVENTO.transformante(MT.rng(seed + ':transformante:forma'), km), joven: true }] : [])
      // rarezas: ~2 % cada una, en ventanas de sorteo que no tocan semillas publicadas
      .concat(Object.entries(RAROS).filter(([q, [a, b, arqs]]) => arqs.includes(arq) && (() => { const g = MT.rng(seed + ':raro:' + q)(); return g >= a && g < b; })())
        .map(([q]) => { const e = TIPOS_EVENTO[q](MT.rng(seed + ':raro:' + q + ':forma'), km); return { tipo: q, ...e, joven: !e.siempreViejo }; }));
  }
  function aplicaEventos(h, N, lista, conservaMar = false) {
    const G = (u, v) => {
      const x = clamp(u, 0, 1) * (N - 1), y = clamp(v, 0, 1) * (N - 1), xi = Math.min(N - 2, Math.floor(x)), yi = Math.min(N - 2, Math.floor(y)), fx = x - xi, fy = y - yi, k = yi * N + xi;
      return h[k] * (1 - fx) * (1 - fy) + h[k + 1] * fx * (1 - fy) + h[k + N] * (1 - fx) * fy + h[k + N + 1] * fx * fy;
    };
    for (const e of lista) {
      if (e.grid) { e.grid(h, N); continue; } // eventos que se simulan sobre la rejilla (lava, deslave)
      if (e.prepara) e.prepara(G);
      const out = new Float32Array(h.length);
      for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const k = j * N + i; out[k] = e.f(i / (N - 1), j / (N - 1), h[k]); }
      h.set(out);
    }
    if (conservaMar) return; // los eventos cambian la costa, no el datum del océano
    let a = Infinity, z = -Infinity;
    for (const v of h) { if (v < a) a = v; if (v > z) z = v; }
    for (let k = 0; k < h.length; k++) h[k] = (h[k] - a) / (z - a);
  }

  // distancia de cada celda a una polilínea (u,v) y su posición a lo largo (0..1), dentro de un margen
  function aLinea(h, N, pts, margen, f) {
    let x0 = 1, y0 = 1, x1 = 0, y1 = 0; for (const [u, v] of pts) { x0 = Math.min(x0, u); y0 = Math.min(y0, v); x1 = Math.max(x1, u); y1 = Math.max(y1, v); }
    const cum = [0]; for (let k = 1; k < pts.length; k++) cum.push(cum[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]));
    const L = cum[cum.length - 1] || 1;
    const i0 = Math.max(0, Math.floor((x0 - margen) * (N - 1))), i1 = Math.min(N - 1, Math.ceil((x1 + margen) * (N - 1)));
    const j0 = Math.max(0, Math.floor((y0 - margen) * (N - 1))), j1 = Math.min(N - 1, Math.ceil((y1 + margen) * (N - 1)));
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
      const u = i / (N - 1), v = j / (N - 1); let dm = Infinity, sm = 0;
      for (let k = 1; k < pts.length; k++) {
        const [ax, ay] = pts[k - 1], [bx, by] = pts[k], dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy || 1e-12;
        const t = Math.max(0, Math.min(1, ((u - ax) * dx + (v - ay) * dy) / l2)), d = Math.hypot(u - ax - dx * t, v - ay - dy * t);
        if (d < dm) { dm = d; sm = (cum[k - 1] + t * Math.sqrt(l2)) / L; }
      }
      if (dm < margen) { const k = j * N + i; h[k] = f(h[k], dm, sm); }
    }
    return L;
  }
  function suaviza(src, N, R) {
    const a = new Float32Array(src.length), b = new Float32Array(src.length);
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { let s = 0, c = 0; for (let d = -R; d <= R; d++) { const x = i + d; if (x >= 0 && x < N) { s += src[j * N + x]; c++; } } a[j * N + i] = s / c; }
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { let s = 0, c = 0; for (let d = -R; d <= R; d++) { const y = j + d; if (y >= 0 && y < N) { s += a[y * N + i]; c++; } } b[j * N + i] = s / c; }
    return b;
  }

  MT.terreno = function (seed, opts = {}) {
    const r = MT.rng(seed + ':terreno');
    // la tirada se hace siempre, aunque se fuerce el arquetipo: así no se corren las que siguen
    const sorteado = r.pick(['monte', 'monte', 'dos', 'cordillera', 'cordillera', 'mesa', 'archi', 'canon']);
    // Reparto de tipos (rebalanceado en el loop 24: las montañas son lo común, los paisajes
    // exóticos lo raro). Lo que no cae en ninguna franja es un clásico (monte, cordillera, dos
    // cumbres, mesa, cañón, archipiélago: ~47 %). Las franjas conservan el tipo de las favoritas.
    const rv = MT.rng(seed + ':arq2')();
    const FRANJAS = [
      [0, 0.10, 'estrato'], [0.10, 0.14, 'escudo'], [0.14, 0.18, 'conos'], [0.18, 0.22, 'impactos'],
      [0.22, 0.27, 'pliegues'], [0.27, 0.30, 'dunas'], [0.30, 0.33, 'karst'], [0.33, 0.36, 'meandros'],
      [0.69, 0.73, 'costa'], [0.85, 0.865, 'atolon'], [0.865, 0.88, 'anillos'], [0.88, 0.895, 'drumlins'],
      [0.895, 0.915, 'rift'], [0.915, 0.93, 'tepuyes'], [0.95, 0.965, 'testigos'], [0.965, 0.98, 'inselbergs'],
      [0.98, 0.99, 'poligonos'], [0.99, 1.01, 'badlands'],
    ];
    const franja = FRANJAS.find(([a, b]) => rv >= a && rv < b);
    const nuevo = franja ? franja[2] : null;
    const arq = ARQ[opts.arq] ? opts.arq : nuevo || sorteado;
    const fis = FIS[arq]; // (mismo orden de tiradas que antes: arquetipo, km, relieve, base)
    const anchoKm = Math.round(r.range(...fis.km) * 2) / 2, relieve = Math.round(r.range(...fis.rel) / 10) * 10, base = Math.round(r.range(...fis.base) / 10) * 10;
    const edad = opts.edad != null ? +opts.edad : MT.rng(seed + ':edad')();
    const rf = MT.rng(seed + ':terreno:' + arq); // la figura no depende de si el arquetipo se forzó
    const N1 = MT.ruido(rf), N2 = MT.ruido(rf), N3 = MT.ruido(rf);
    const F = figura(arq, rf, N3, edad, seed);
    const warpA = rf.range(0.03, 0.08) * (F.warp != null ? F.warp : 1), warpF = rf.range(1.5, 3);
    // realismo (opcional, su propio sorteo): la hoja como ventana sobre un territorio que sigue
    // más allá del borde, un grano geológico (el relieve fino se alarga en un rumbo), más
    // deformación de las formas redondas, y una pendiente regional
    const RZ = opts.realismo !== false && opts.realismo !== '0' && opts.realismo !== 0 ? (() => { // desde el loop 22, encendido por defecto
      const q = MT.rng(seed + ':realismo'), a = q.range(0, Math.PI), ventana = !F.post && !F.mar && !F.impactos;
      return { k: ventana ? q.range(0.62, 0.85) : 1, ox: ventana ? q.range(-0.17, 0.17) : 0, oy: ventana ? q.range(-0.17, 0.17) : 0,
        c: Math.cos(a), s: Math.sin(a), e: q.range(1.8, 2.8), warp: q.range(1.8, 2.6), tilt: q.range(0.03, 0.08), tb: q.range(0, 6.283) };
    })() : null;
    const aFig = (u, v) => (RZ ? [0.5 + (u - 0.5) * RZ.k + RZ.ox, 0.5 + (v - 0.5) * RZ.k + RZ.oy] : [u, v]); // de la hoja a la figura
    const aHoja = (u, v) => (RZ ? [0.5 + (u - 0.5 - RZ.ox) / RZ.k, 0.5 + (v - 0.5 - RZ.oy) / RZ.k] : [u, v]);
    const grano = (u, v) => { if (!RZ) return [u, v]; const x = u - 0.5, y = v - 0.5; return [0.5 + (x * RZ.c + y * RZ.s) / RZ.e, 0.5 - x * RZ.s + y * RZ.c]; };
    const detF = rf.range(3, 6.5), ox = rf.range(0, 100), oy = rf.range(0, 100);
    // relieve regional: lomas bajas en todo el terreno, para que la llanura no quede de vidrio
    const regA = rf.range(0.015, arq === 'mesa' || arq === 'canon' ? 0.05 : 0.11), regF = rf.range(1.2, 2.6);

    const GN = 360;
    // el terreno completo (con sus etapas, si se piden); la formación lo pide muchas veces,
    // así que se guarda por semilla y cada cuadro sólo mezcla etapas
    const eventos = opts.eventos === false ? [] : eventosDe(seed, arq, anchoKm);
    const genera = (conEtapas) => {
      const h = new Float32Array(GN * GN), fig = conEtapas && !F.impactos ? new Float32Array(GN * GN) : null;
      let mn = Infinity, mx = -Infinity;
      for (let j = 0; j < GN; j++) {
        for (let i = 0; i < GN; i++) {
          const [u, v] = aFig(i / (GN - 1), j / (GN - 1)), [gu, gv] = grano(u, v), wA = warpA * (RZ ? RZ.warp : 1);
          const du = wA * N2.fbm(gu * warpF + ox, gv * warpF + oy, 4), dv = wA * N2.fbm(gu * warpF + oy + 31, gv * warpF + ox + 17, 4);
          const wu = u + du, wv = v + dv, nu = gu + du, nv = gv + dv;
          const b = F.f(wu, wv);
          if (fig) fig[j * GN + i] = b;
          const rd = N1.ridged(nu * detF + ox, nv * detF + oy, 6);
          // En el mar, el detalle y la pendiente disminuyen hacia la costa: no levantan
          // una llanura submarina ni hunden una flecha de arena. La deformación horizontal sigue.
          const margenMar = F.mar ? sst(0, 0.12, Math.abs(b - F.mar)) : 1;
          let val = b * (1 - F.detA + F.detA * rd) + 0.03 * N1.fbm(nu * detF * 0.5 + 7, nv * detF * 0.5 + 3, 3)
            + regA * N2.ridged(nu * regF + 53, nv * regF + 11, 3);
          if (F.mar) val = b + margenMar * (val - b);
          // pendiente regional que ondula (un plano perfecto haría ríos de regla, paralelos)
          if (RZ) val += margenMar * RZ.tilt * (F.inclina ?? 1) * ((i / (GN - 1) - 0.5) * Math.cos(RZ.tb) + (j / (GN - 1) - 0.5) * Math.sin(RZ.tb) + 0.6 * N3.fbm(gu * 1.8 + 9, gv * 1.8 + 4, 3));
          // El ruido genérico no cruza el datum; erosión y eventos sí pueden cambiar la costa.
          if (F.mar) val = b <= F.mar ? Math.min(F.mar - 1e-4, val) : Math.max(F.mar + 1e-4, val);
          h[j * GN + i] = val;
          if (val < mn) mn = val; if (val > mx) mx = val;
        }
      }
      if (!F.mar) for (let k = 0; k < h.length; k++) h[k] = (h[k] - mn) / (mx - mn);
      if (F.post) { F.post(h, GN); if (!F.mar) normaliza(h); } // conservar el datum al tallar un cauce costero
      const viejos = eventos.filter((e) => !e.joven), jovenes = eventos.filter((e) => e.joven);
      if (viejos.length) aplicaEventos(h, GN, viejos, !!F.mar); // antes de la erosión: quedarán suavizados
      let imp = null, pasadas = 0;
      const etapas = conEtapas ? [] : null;
      if (fig) { // la forma grande, sin detalle, en la misma escala que el relieve
        let a = Infinity, z = -Infinity;
        for (const v of fig) { if (v < a) a = v; if (v > z) z = v; }
        // una figura plana (tierras malas: la altura sale de la red, no de la figura) queda plana, no NaN
        if (!F.mar) for (let k = 0; k < fig.length; k++) fig[k] = z - a > 1e-9 ? (fig[k] - a) / (z - a) : 0;
        etapas.push({ clave: 'forma', h: fig });
      }
      if (F.impactos) imp = estampaImpactos(h, GN, MT.rng(seed + ':impactos'), anchoKm, !!etapas);
      if (opts.erosion !== false && F.erosion !== false) {
        const ef = MT.rng(seed + ':erosion').range(0.6, 1.4);
        const fz = F.erosion ? F.erosion.fuerza * ef : { monte: 0.075, dos: 0.075, cordillera: 0.08, archi: 0.06, mesa: 0.04, canon: 0.04 }[arq] * ef;
        pasadas = F.erosion ? F.erosion.pasadas : 3;
        if (etapas) { // la erosión en dos tiempos da lo mismo que de un jalón, y deja ver el intermedio
          etapas.push({ clave: 'relieve', h: h.slice() });
          erosiona(h, GN, fz, 1); etapas.push({ clave: 'erosion1', h: h.slice() });
          erosiona(h, GN, fz, pasadas - 1);
        } else erosiona(h, GN, fz, pasadas);
        let a = Infinity, z = -Infinity;
        for (let k = 0; k < h.length; k++) { if (h[k] < a) a = h[k]; if (h[k] > z) z = h[k]; }
        if (!F.mar) {
          for (let k = 0; k < h.length; k++) h[k] = (h[k] - a) / (z - a);
          if (etapas) for (const e of etapas) if (e.clave !== 'forma') for (let k = 0; k < e.h.length; k++) e.h[k] = (e.h[k] - a) / (z - a);
        }
      }
      if (jovenes.length) { // después de la erosión: filosos, apenas con su poquito de agua
        aplicaEventos(h, GN, jovenes, !!F.mar);
        if (arq !== 'impactos') { erosiona(h, GN, 0.025, 1); aplicaEventos(h, GN, [], !!F.mar); }
      }
      // el estratovolcán viejo puede colapsar y renacer (la mitad de las veces)
      let col = null;
      if (F.centro && !F.cuello && edad > 0.6 && MT.rng(seed + ':colapso')() < 0.5) {
        const c = conoDe(h, GN);
        col = colapsa(h, GN, MT.rng(seed + ':colapso:forma'), { cx: c.cx, cy: c.cy, R: F.centro.R });
        erosiona(h, GN, 0.02, 1); normaliza(h);
      }
      if (F.mar) {
        // Se resta el mismo nivel después de todos los procesos; sólo cambia la escala
        // vertical, nunca el origen. Fondo y superficie comparten exactamente la costa.
        let cima = F.mar;
        for (const v of h) cima = Math.max(cima, v);
        const escala = Math.max(1e-6, cima - F.mar);
        const inunda = (v) => (v - F.mar) / escala;
        for (let k = 0; k < h.length; k++) h[k] = inunda(h[k]);
        if (etapas) for (const e of etapas) for (let k = 0; k < e.h.length; k++) e.h[k] = Math.max(0, inunda(e.h[k]));
      }
      const hPre = F.mar && opts.fondo ? h.slice() : null;
      if (F.mar) for (let k = 0; k < h.length; k++) h[k] = Math.max(0, h[k]);
      if (etapas && !imp) etapas.push({ clave: 'erosion', h: h.slice() }); // ya erosionado, antes del agua
      // el fondo del mar: lo que se inundó conserva su relieve y sigue bajando (×3), y el nivel
      // del mar queda como un número (nivelMar) en vez de ser el piso de la rejilla
      let fondoMin = 0;
      if (hPre) {
        for (let k = 0; k < h.length; k++) if (h[k] <= 1e-4) h[k] = Math.min(-1e-4, 3 * hPre[k]);
        for (const v of h) if (v < fondoMin) fondoMin = v;
        for (let k = 0; k < h.length; k++) h[k] = (h[k] - fondoMin) / (1 - fondoMin);
        if (etapas) for (const e of etapas) for (let k = 0; k < e.h.length; k++) e.h[k] = (e.h[k] - fondoMin) / (1 - fondoMin);
        if (etapas) { const ultima = etapas.find((e) => e.clave === 'erosion'); if (ultima) ultima.h = h.slice(); }
      }
      return { h, etapas, imp, pasadas, col, fondoMin };
    };
    const clave = [seed, arq, edad, opts.erosion, String(opts.realismo), !!opts.fondo, opts.eventos].join('|');
    let gen;
    if (opts.forma != null) {
      MT._cacheFormacion = MT._cacheFormacion || new Map();
      gen = MT._cacheFormacion.get(clave);
      if (!gen) { gen = genera(true); MT._cacheFormacion.clear(); MT._cacheFormacion.set(clave, gen); }
    } else gen = genera(!!opts.etapas);
    const { imp, pasadas, col, fondoMin } = gen, etapas = gen.etapas;
    let h = gen.h;
    // forma = t ∈ [0,1]: la montaña a medio hacer, de la llanura a la erosión completa
    // (en la llanura de impactos: de antes del primer cráter a hoy)
    if (opts.forma != null) {
      const plano = new Float32Array(gen.h.length).fill(fondoMin < 0 ? -fondoMin / (1 - fondoMin) : 0);
      const st = imp ? [...imp.tomas.map((q) => q.h), gen.h]
        : [plano, ...['forma', 'relieve', 'erosion1', 'erosion'].map((c) => etapas.find((e) => e.clave === c)).filter(Boolean).map((e) => e.h)];
      const x = Math.min(1, Math.max(0, +opts.forma)) * (st.length - 1), i = Math.min(st.length - 2, Math.floor(x)), f = x - i;
      const sm = f * f * (3 - 2 * f), A = st[i], B = st[i + 1];
      h = new Float32Array(gen.h.length);
      for (let k = 0; k < h.length; k++) h[k] = A[k] + (B[k] - A[k]) * sm;
    }

    const sample = (u, v) => {
      const x = clamp(u, 0, 1) * (GN - 1), y = clamp(v, 0, 1) * (GN - 1);
      const xi = Math.min(GN - 2, Math.floor(x)), yi = Math.min(GN - 2, Math.floor(y));
      const fx = x - xi, fy = y - yi, k = yi * GN + xi;
      return h[k] * (1 - fx) * (1 - fy) + h[k + 1] * fx * (1 - fy) + h[k + GN] * (1 - fx) * fy + h[k + GN + 1] * fx * fy;
    };

    const T = { seed, arq, nombre: col ? col.nombre : F.nombre || ARQ[arq], G: GN, h, sample, edad, terminos: F.terminos || null, exagMax: F.exagMax || Infinity, mar: !!F.mar };
    T.anchoKm = anchoKm;
    T.relieve = imp ? imp.relieve : Math.max(F.mar ? 10 : 0, Math.round(relieve * (F.relieve || 1) / 10) * 10);
    T.base = base;
    if (fondoMin < 0) { // la escala va del fondo del mar a la cumbre; el 0 es el nivel del mar
      T.base = T.relieve * fondoMin; T.relieve = T.relieve - T.base; T.nivelMar = -fondoMin / (1 - fondoMin);
    }
    T.alt = (hn) => T.base + hn * T.relieve;
    T.umbralMar = (T.nivelMar || 0) + 1e-4 / (1 - fondoMin);
    T.esMar = (u, v) => T.mar && sample(u, v) <= T.umbralMar;
    T.rasgos = opts.forma != null && +opts.forma < 1 ? { picos: [], fondo: null } : rasgos(T);
    // en la llanura de impactos no hay agua que corra
    if (arq !== 'impactos' && arq !== 'dunas' && F.agua !== false && opts.agua !== false && (opts.forma == null || +opts.forma >= 1)) T.hidro = hidrologia(T, MT.rng(seed + ':agua'), col ? { maxLago: col.lagoCal ? 0.15 : 0.02, humedad: 3 } : F.lagos || {});
    if (T.mar && T.hidro) {
      // Chaikin puede meter la desembocadura en el mar o cortar una bahía.
      // Terminar en el primer cruce, medido sobre el mismo terreno que se dibuja.
      const hastaCosta = (pts) => {
        const out = [];
        for (const p of pts) {
          if (!out.length) { if (T.esMar(...p)) break; out.push(p); continue; }
          const a = out[out.length - 1], n = Math.max(1, Math.ceil(Math.hypot(p[0] - a[0], p[1] - a[1]) * GN * 2));
          for (let j = 1; j <= n; j++) {
            const t = j / n, q = [a[0] + (p[0] - a[0]) * t, a[1] + (p[1] - a[1]) * t];
            if (!T.esMar(...q)) continue;
            let lo = (j - 1) / n, hi = t;
            for (let k = 0; k < 20; k++) {
              const m = (lo + hi) / 2;
              if (T.esMar(a[0] + (p[0] - a[0]) * m, a[1] + (p[1] - a[1]) * m)) hi = m; else lo = m;
            }
            out.push([a[0] + (p[0] - a[0]) * lo, a[1] + (p[1] - a[1]) * lo]);
            return out;
          }
          out.push(p);
        }
        return out;
      };
      T.hidro.rios = T.hidro.rios.map((rv) => ({ ...rv, pts: hastaCosta(rv.pts) })).filter((rv) => rv.pts.length > 1);
      if (T.hidro.principal) {
        const pts = hastaCosta(T.hidro.principal.pts);
        let largoKm = 0;
        for (let k = 1; k < pts.length; k++) largoKm += Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]) * anchoKm;
        T.hidro.principal = pts.length > 1 ? { pts, largoKm } : null;
      }
    }
    const espEventos = eventos.flatMap((e) => e.esp || []);
    for (const e of eventos) if (e.falla) { // la falla dice cuánto se movió: el salto medido a los lados
      const { x, y, nx, ny, w } = e.falla, d = w * 5;
      espEventos.push({ u: x, v: y, tipo: 'falla', term: 'FALLA', dato: `SALTO ${Math.round(Math.abs(sample(x + nx * d, y + ny * d) - sample(x - nx * d, y - ny * d)) * T.relieve / 10) * 10} M` });
    }
    if (F.cauce && T.hidro) { // el cauce tallado es el río: se dibuja él, no lo que el agua adivine en lo plano
      const enHoja = F.cauce.filter(([u, v]) => u >= 0 && v >= 0 && u <= 1 && v <= 1);
      T.hidro.rios = T.hidro.rios.filter((rv) => rv.clase < 3);
      T.hidro.rios.push({ clase: 3, pts: enHoja });
      let L = 0; for (let k = 1; k < enHoja.length; k++) L += Math.hypot(enHoja[k][0] - enHoja[k - 1][0], enHoja[k][1] - enHoja[k - 1][1]);
      T.hidro.principal = { pts: enHoja, largoKm: L * T.anchoKm };
    }
    if (F.canal) T.canal = { rio: F.canal.rio.map(([u, v]) => aHoja(u, v)), brazos: F.canal.brazos.map((pts) => pts.map(([u, v]) => aHoja(u, v))) };
    T.rasgos.especiales = opts.forma != null && +opts.forma < 1 ? [] : especiales(T, [...(imp ? imp.esp : (col ? (F.esp || []).filter((e) => e.tipo !== 'crater') : F.esp || []).map((e) => { const [u, v] = aHoja(e.u, e.v); return { ...e, u, v, rad: e.rad && e.rad / (RZ ? RZ.k : 1) }; })), ...espEventos, ...(col ? col.esp : [])]);
    // las rarezas se rotulan primero: la lámina dice qué la hace rara
    const RARO = /SUPERCALDERA|SUMIDERO|ANILLO DE TOBA|MORRENAS/;
    T.rasgos.especiales.sort((p, q) => (RARO.test(q.term) ? 1 : 0) - (RARO.test(p.term) ? 1 : 0));
    T.eventos = eventos.map((e) => ({ tipo: e.tipo, nombre: e.nombre, joven: e.joven }));
    T.historia = F.historia && !col ? [...F.historia, ...eventos.map((e) => e.nombre)] : eventos.length || col ? [arq === 'impactos' ? 'IMPACTOS' : 'LEVANTAMIENTO', ...(col ? ['CONO'] : []), ...eventos.filter((e) => !e.joven).map((e) => e.nombre),
      ...(arq === 'impactos' ? [] : ['EROSIÓN']), ...eventos.filter((e) => e.joven).map((e) => e.nombre), ...(col ? col.hist : [])] : null;
    if (T.hidro) for (const l of [...T.hidro.lagos].sort((a, b) => b.area - a.area).slice(0, 3))
      T.rasgos.especiales.push({ u: l.u, v: l.v, h: l.nivel, tipo: 'lago', term: 'LAGO', dato: null });
    if (imp) T.nImpactos = imp.n;
    if (etapas && opts.forma == null) {
      if (imp) for (const t of imp.tomas) etapas.push({ clave: 'impactos', k: t.k, h: t.h });
      etapas.push({ clave: 'final', h: T.h });
      T.etapas = etapas; T.pasadas = pasadas;
    }
    return T;
  };

  // Erosión por cauces: se calcula por dónde escurre el agua (cada celda drena a su vecina
  // más baja y acumula el área que le llega) y se excava cada cauce en proporción a su
  // caudal y a su pendiente. Unas pocas pasadas bastan para que aparezcan valles ramificados.
  function erosiona(h, N, fuerza, pasadas = 3) {
    const n = N * N, SH = 2 ** 18, keys = new Float64Array(n), ord = new Uint32Array(n);
    const rec = new Int32Array(n), A = new Float32Array(n), corte = new Float32Array(n), tmp = new Float32Array(n);
    const LN = Math.log(1 + n);
    for (let it = 0; it < pasadas; it++) {
      for (let i = 0; i < n; i++) keys[i] = Math.floor((1 - Math.min(1, Math.max(0, h[i]))) * 16777215) * SH + i;
      keys.sort();
      for (let q = 0; q < n; q++) ord[q] = keys[q] % SH;
      for (let i = 0; i < n; i++) {
        const x = i % N, y = (i / N) | 0; let mj = -1, md = 0;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          if (!dx && !dy) continue;
          const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= N || ny >= N) continue;
          const j = ny * N + nx, d = (h[i] - h[j]) / (dx && dy ? 1.414 : 1);
          if (d > md) { md = d; mj = j; }
        }
        rec[i] = mj; A[i] = 1; corte[i] = md; // de momento, la pendiente
      }
      for (let q = 0; q < n; q++) { const i = ord[q]; if (rec[i] >= 0) A[rec[i]] += A[i]; }
      for (let i = 0; i < n; i++) {
        const qn = Math.log(1 + A[i]) / LN; // caudal en escala logarítmica: también cuentan los afluentes
        corte[i] = fuerza * Math.pow(qn, 2.6) * Math.min(1, corte[i] * N / 2);
      }
      for (let b = 0; b < 3; b++) { // el cauce tiene ancho: se reparte el corte a los lados
        tmp.set(corte);
        for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) {
          const k = y * N + x;
          corte[k] = (4 * tmp[k] + 2 * (tmp[k - 1] + tmp[k + 1] + tmp[k - N] + tmp[k + N]) + tmp[k - N - 1] + tmp[k - N + 1] + tmp[k + N - 1] + tmp[k + N + 1]) / 16;
        }
      }
      for (let i = 0; i < n; i++) h[i] -= corte[i];
    }
  }

  // Rasgos propios de cada figura (cráteres, coladas, cuellos): se ajustan sobre la rejilla
  // final, porque la deformación y la erosión los movieron, y llevan su medida.
  function especiales(T, lista) {
    const N = T.G, h = T.h, km = (f) => { const v = Math.round(f * T.anchoKm * 10) / 10; return v.toFixed(Number.isInteger(v) ? 0 : 1); };
    return lista.map((e) => {
      let u = e.u, v = e.v;
      if (e.busca) {
        const ci = Math.round(u * (N - 1)), cj = Math.round(v * (N - 1)), rr = Math.max(2, Math.round(e.rad * (N - 1)));
        let best = null;
        for (let j = Math.max(0, cj - rr); j <= Math.min(N - 1, cj + rr); j++) for (let i = Math.max(0, ci - rr); i <= Math.min(N - 1, ci + rr); i++) {
          const z = h[j * N + i];
          if (best === null || (e.busca === 'min' ? z < best : z > best)) { best = z; u = i / (N - 1); v = j / (N - 1); }
        }
      }
      const dato = e.dato || (e.diam != null ? `Ø ${km(e.diam)} KM` : e.largo != null ? `${km(e.largo)} KM` : null);
      return { u, v, h: T.sample(u, v), tipo: e.tipo, term: e.term, dato };
    });
  }

  // Rasgos con sentido: cumbres por prominencia y su collado clave, por unión de cuencas
  // (se recorre el terreno de arriba abajo; cuando dos islas se tocan, la de pico más bajo
  // termina ahí: esa celda es su collado y la diferencia es su prominencia).
  function rasgos(T) {
    const N = T.G, h = T.h, n = N * N;
    // orden descendente sin comparador: altura cuantizada y el índice empacados en un float64
    const SH = 2 ** 18, keys = new Float64Array(n);
    for (let i = 0; i < n; i++) keys[i] = Math.floor((1 - h[i]) * 16777215) * SH + i;
    keys.sort();
    const ord = new Uint32Array(n); for (let q = 0; q < n; q++) ord[q] = keys[q] % SH;
    const par = new Int32Array(n).fill(-1), pk = new Int32Array(n);
    const find = (i) => { while (par[i] !== i) { par[i] = par[par[i]]; i = par[i]; } return i; };
    const crudos = [], roots = [];
    for (let q = 0; q < n; q++) {
      const i = ord[q], x = i % N, y = (i / N) | 0; roots.length = 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        if (!dx && !dy) continue;
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= N || ny >= N) continue;
        const j = ny * N + nx;
        if (par[j] !== -1) { const rt = find(j); if (!roots.includes(rt)) roots.push(rt); }
      }
      if (!roots.length) { par[i] = i; pk[i] = i; continue; }
      roots.sort((a, b) => h[pk[b]] - h[pk[a]]);
      const m = roots[0]; par[i] = m;
      for (let k = 1; k < roots.length; k++) {
        crudos.push({ i: pk[roots[k]], prom: h[pk[roots[k]]] - h[i], col: i });
        par[roots[k]] = m;
      }
    }
    crudos.push({ i: ord[0], prom: h[ord[0]] - h[ord[n - 1]], col: -1 });
    const uv = (i) => ({ u: (i % N) / (N - 1), v: ((i / N) | 0) / (N - 1), h: h[i] });
    const picos = crudos.filter((c) => c.prom > 0.02).sort((a, b) => b.prom - a.prom)
      .map((c) => ({ ...uv(c.i), prom: c.prom, col: c.col >= 0 ? uv(c.col) : null }));
    // el punto más hondo lejos de la orilla (el fondo del cañón)
    let fondo = null;
    const m0 = Math.floor(N * 0.12), m1 = N - m0;
    for (let y = m0; y < m1; y++) for (let x = m0; x < m1; x++) {
      const i = y * N + x; if (!fondo || h[i] < fondo.h) fondo = uv(i);
    }
    return { picos, fondo };
  }

  // para experimentos (experimentos/*.js): las piezas del motor, sin cambiar lo que hace
  MT._internos = { erosiona, hidrologia, rasgos, especiales };
})(typeof globalThis !== 'undefined' ? globalThis : window);
