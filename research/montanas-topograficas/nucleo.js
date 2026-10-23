// nucleo.js — azar sembrado, ruido y color OKLCh. Corre igual en el navegador y en node.
(function (G) {
  const MT = (G.MT = G.MT || {});

  function cyrb128(str) {
    let h1 = 1779033703, h2 = 3144134277, h3 = 1013904242, h4 = 2773480762;
    for (let i = 0, k; i < str.length; i++) {
      k = str.charCodeAt(i);
      h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
      h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
      h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
      h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
    }
    h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067);
    h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233);
    h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213);
    h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);
    h1 ^= h2 ^ h3 ^ h4; h2 ^= h1; h3 ^= h1; h4 ^= h1;
    return [h1 >>> 0, h2 >>> 0, h3 >>> 0, h4 >>> 0];
  }
  function sfc32(a, b, c, d) {
    return function () {
      a |= 0; b |= 0; c |= 0; d |= 0;
      const t = (((a + b) | 0) + d) | 0;
      d = (d + 1) | 0; a = b ^ (b >>> 9); b = (c + (c << 3)) | 0;
      c = (c << 21) | (c >>> 11); c = (c + t) | 0;
      return (t >>> 0) / 4294967296;
    };
  }

  // Cada parte del sistema pide su propio flujo (`semilla:terreno`, `semilla:color`…)
  // para que tocar una no mueva las demás.
  MT.rng = function (seed) {
    const r = sfc32(...cyrb128(String(seed)));
    for (let i = 0; i < 12; i++) r();
    const f = () => r();
    f.range = (a, b) => a + (b - a) * r();
    f.int = (a, b) => Math.floor(a + (b - a + 1) * r());
    f.pick = (arr) => arr[Math.floor(r() * arr.length)];
    return f;
  };

  // Ruido de gradiente 2D con permutación sembrada.
  MT.ruido = function (rng) {
    const P = []; for (let i = 0; i < 256; i++) P[i] = i;
    for (let i = 255; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [P[i], P[j]] = [P[j], P[i]]; }
    const perm = new Uint16Array(512); for (let i = 0; i < 512; i++) perm[i] = P[i & 255];
    const gx = new Float32Array(256), gy = new Float32Array(256);
    for (let i = 0; i < 256; i++) { const a = rng() * Math.PI * 2; gx[i] = Math.cos(a); gy[i] = Math.sin(a); }
    const fade = (t) => t * t * t * (t * (t * 6 - 15) + 10);
    function n2(x, y) {
      const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
      const X = xi & 255, Y = yi & 255, p0 = perm[Y], p1 = perm[Y + 1];
      const u = fade(xf), v = fade(yf);
      let k = perm[X + p0]; const a = gx[k] * xf + gy[k] * yf;
      k = perm[X + 1 + p0]; const b = gx[k] * (xf - 1) + gy[k] * yf;
      k = perm[X + p1]; const c = gx[k] * xf + gy[k] * (yf - 1);
      k = perm[X + 1 + p1]; const d = gx[k] * (xf - 1) + gy[k] * (yf - 1);
      const ab = a + (b - a) * u, cd = c + (d - c) * u;
      return (ab + (cd - ab) * v) * 1.4; // ~[-1, 1]
    }
    n2.fbm = (x, y, oct = 5) => {
      let s = 0, a = 0.5, f = 1, norm = 0;
      for (let o = 0; o < oct; o++) { s += a * n2(x * f + o * 17.3, y * f - o * 9.1); norm += a; a *= 0.5; f *= 2.03; }
      return s / norm;
    };
    // Crestas: 1-|ruido| al cuadrado, cada octava pesada por la anterior (aristas filosas arriba, lomas suaves abajo).
    n2.ridged = (x, y, oct = 5) => {
      let s = 0, a = 0.5, f = 1, w = 1, norm = 0;
      for (let o = 0; o < oct; o++) {
        let r = 1 - Math.abs(n2(x * f + o * 31.7, y * f + o * 12.9));
        r *= r; r *= w; w = Math.min(1, Math.max(0, r * 1.6));
        s += r * a; norm += a; a *= 0.5; f *= 2.1;
      }
      return s / norm;
    };
    return n2;
  };

  // OKLCh → hex sRGB, bajando croma hasta caber en el gamut.
  MT.oklch = function (L, C, h) {
    const hr = (((h % 360) + 360) % 360) * Math.PI / 180;
    for (let k = 0; k < 60; k++) {
      const a = C * Math.cos(hr), b = C * Math.sin(hr);
      const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
      const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
      const s_ = L - 0.0894841775 * a - 1.291485548 * b;
      const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
      const rgb = [
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
      ];
      if (rgb.every((c) => c >= -0.0005 && c <= 1.0005) || C < 0.001) {
        return '#' + rgb.map((c) => {
          c = Math.min(1, Math.max(0, c));
          c = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;
          return Math.round(c * 255).toString(16).padStart(2, '0');
        }).join('');
      }
      C *= 0.93;
    }
  };

  // ¿Cabe (L, C, h) en la pantalla?
  const cabe = (L, C, h) => {
    const hr = h * Math.PI / 180, a = C * Math.cos(hr), b = C * Math.sin(hr);
    const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3, s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s]
      .every((c) => c >= -0.0005 && c <= 1.0005);
  };
  // Neón: para un tono, la luminosidad donde cabe más croma, y ese croma (lo más estridente posible).
  MT.neon = function (h, Lmin = 0.6) {
    h = ((h % 360) + 360) % 360;
    let mejor = [0.8, 0];
    for (let L = Lmin; L <= 0.96; L += 0.01) {
      let lo = 0, hi = 0.4;
      for (let k = 0; k < 18; k++) { const m = (lo + hi) / 2; if (cabe(L, m, h)) lo = m; else hi = m; }
      if (lo > mejor[1]) mejor = [L, lo];
    }
    return MT.oklch(mejor[0], mejor[1] * 0.995, h);
  };

  // Ramer–Douglas–Peucker: menos puntos, misma línea (tolerancia en mm).
  MT.simplifica = function (pts, tol) {
    if (pts.length < 3) return pts;
    const keep = new Uint8Array(pts.length); keep[0] = keep[pts.length - 1] = 1;
    const st = [[0, pts.length - 1]];
    while (st.length) {
      const [a, b] = st.pop();
      const [ax, ay] = pts[a], [bx, by] = pts[b];
      const dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy);
      let md = 0, mi = -1;
      for (let i = a + 1; i < b; i++) {
        // en un anillo cerrado la cuerda mide cero: entonces cuenta la distancia al punto
        const d = L < 1e-9 ? Math.hypot(pts[i][0] - ax, pts[i][1] - ay)
          : Math.abs((pts[i][0] - ax) * dy - (pts[i][1] - ay) * dx) / L;
        if (d > md) { md = d; mi = i; }
      }
      if (md > tol) { keep[mi] = 1; st.push([a, mi], [mi, b]); }
    }
    return pts.filter((_, i) => keep[i]);
  };
})(typeof globalThis !== 'undefined' ? globalThis : window);
