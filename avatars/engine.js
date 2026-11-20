// Personajes del leaderboard.
// Cada personaje es una carpeta en avatars/sprites/<id>/ con cuatro imágenes PNG:
//   parado.png · caminando.png · festejo.png · sentado.png
// Este archivo las muestra y les agrega encima lo que pasó en el día (corona, medalla,
// estrella, rayo, lamparita, zzz) y dibuja el podio. Para elegir o cambiar tu personaje
// editá avatars/players.js; este archivo no hace falta tocarlo.
(function (global) {
  "use strict";

  const BASE = "avatars/sprites/";
  const PET_BASE = "avatars/mascotas/";
  // se agrega a cada URL para que el navegador no muestre imágenes viejas guardadas en caché
  const V = () => global.AVATARES_VERSION ? "?v=" + encodeURIComponent(global.AVATARES_VERSION) : "";
  const PET_ALTO = .3;             // alto de la mascota respecto del personaje parado
  const POSES = ["parado", "caminando", "festejo", "sentado"];
  const OUT = "#1a1210";
  const G = "#e8b04a", GL = "#ffe08a", GD = "#a8762a";
  const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];

  // ───────────────────────── color ─────────────────────────
  function mix(a, b, t) {
    const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const A = p(a), B = p(b);
    return "#" + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, "0")).join("");
  }
  const dk = (c, t = .3) => mix(c, "#000000", t);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ───────────────────────── qué personaje usa cada jugador ─────────────────────────
  function hash(s) {
    let h = 2166136261;
    for (const ch of String(s)) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function spriteDe(nombre) {
    const elegido = (global.AVATARES || {})[nombre];
    if (typeof elegido === "string" && /^[a-z0-9_-]+$/i.test(elegido)) return elegido;
    if (elegido !== undefined) console.warn(`[avatares] ${nombre}: "${elegido}" no es un nombre de carpeta válido; se usa uno automático.`);
    const pool = global.SPRITES && global.SPRITES.length ? global.SPRITES : ["rulos"];
    return pool[hash(nombre) % pool.length];
  }

  // ───────────────────────── medidas de cada imagen ─────────────────────────
  // Se leen al cargar: tamaño, dónde empieza la cabeza y su centro, y el tamaño de un "pixel"
  // del dibujo (u) para que los agregados queden en la misma escala que el personaje.
  const META = new Map();          // "id/pose" → { w, h, top, cx, u, ok }

  function medir(img) {
    const w = img.naturalWidth, h = img.naturalHeight;
    const m = { w, h, top: 0, cx: w / 2, u: Math.max(2, Math.round(h / 43)), ok: false };
    try {
      const c = document.createElement("canvas");
      c.width = w; c.height = h;
      const g = c.getContext("2d");
      g.drawImage(img, 0, 0);
      const d = g.getImageData(0, 0, w, h).data;
      // la cabeza empieza en la franja del medio, después del último hueco vacío de arriba:
      // así se saltean las rayitas de festejo (separadas por un hueco) y las manos levantadas
      // (que quedan a los costados, fuera de la franja)
      const a = Math.round(w * .3), b = Math.round(w * .7);
      const filled = y => { let n = 0; for (let x = a; x < b; x++) if (d[(y * w + x) * 4 + 3] > 40) n++; return n; };
      let top = 0;
      while (top < h && !filled(top)) top++;
      for (let y = top; y < h * .35; y++) if (!filled(y)) { let z = y; while (z < h && !filled(z)) z++; top = z; y = z; }
      let sx = 0, n = 0;
      for (let y = top; y < Math.min(h, top + Math.round(h * .1)); y++) for (let x = Math.round(w * .2); x < Math.round(w * .8); x++) if (d[(y * w + x) * 4 + 3] > 40) { sx += x; n++; }
      // talón: el punto más a la izquierda de los pies (el personaje mira a la derecha)
      let talon = w;
      for (let y = Math.round(h * .9); y < h; y++) for (let x = 0; x < w; x++) if (d[(y * w + x) * 4 + 3] > 40) { talon = Math.min(talon, x); break; }
      Object.assign(m, { top: top < h ? top : 0, cx: n ? sx / n : w / 2, talon: talon < w ? talon : 0, ok: true });
    } catch (e) { /* abierto como archivo local: se usan medidas aproximadas */ }
    return m;
  }

  // Mascotas: avatars/mascotas/<id>.png, una imagen chica que acompaña al personaje.
  const PETS = new Map();          // id → { w, h, src }
  function mascotaDe(nombre) {
    const id = (global.MASCOTAS || {})[nombre];
    return typeof id === "string" && /^[a-z0-9_-]+$/i.test(id) && PETS.has(id) ? PETS.get(id) : null;
  }

  function cargar(ids) {
    const jobs = [];
    for (const id of new Set(Object.values(global.MASCOTAS || {}))) {
      if (typeof id !== "string" || PETS.has(id)) continue;
      jobs.push(new Promise(res => {
        const img = new Image();
        img.onload = () => { PETS.set(id, { w: img.naturalWidth, h: img.naturalHeight, src: img.src }); res(); };
        img.onerror = () => { console.warn(`[avatares] falta ${PET_BASE}${id}.png`); res(); };
        img.src = PET_BASE + id + ".png" + V();
      }));
    }
    for (const id of new Set(ids)) for (const pose of POSES) {
      const key = id + "/" + pose;
      if (META.has(key)) continue;
      jobs.push(new Promise(res => {
        const img = new Image();
        img.onload = () => { META.set(key, { ...medir(img), src: img.src }); res(); };
        img.onerror = () => { if (pose === "parado") console.warn(`[avatares] falta ${BASE}${id}/parado.png`); res(); };
        img.src = BASE + id + "/" + pose + ".png" + V();
      }));
    }
    for (const id of new Set(ids)) {
      if (ANIMS.has(id)) continue;
      ANIMS.set(id, null);
      jobs.push(fetch(BASE + id + "/animaciones.json" + V()).then(r => r.ok ? r.json() : null).catch(() => null).then(async man => {
        if (!man || !man.animaciones) return;
        const anims = {};
        for (const [nombre, a] of Object.entries(man.animaciones)) {
          const n = Math.max(1, Math.min(60, a.cuadros | 0));
          const imgs = await Promise.all(Array.from({ length: n }, (_, i) => new Promise(res => {
            const im = new Image();
            im.onload = () => res(im); im.onerror = () => res(null);
            im.src = `${BASE}${id}/${nombre}/${i + 1}.png${V()}`;
          })));
          if (!imgs[0]) { console.warn(`[avatares] falta ${BASE}${id}/${nombre}/1.png`); continue; }
          const m = medir(imgs[0]);
          anims[nombre] = {
            nombre, titulo: a.titulo || nombre, cuadros: n, ms: a.ms || 300, pausa: a.pausa || a.ms || 300,
            alto: a.alto || m.h, mascota: !!a.mascota, w: m.w, h: m.h, talon: m.talon || 0,
            srcs: imgs.map(im => (im || imgs[0]).src), imgs,           // imgs: quedan en memoria para no parpadear
          };
        }
        ANIMS.set(id, { podio: man.podio || {}, anims });
      }));
    }
    return Promise.all(jobs);
  }

  // Animaciones: avatars/sprites/<id>/animaciones.json + una carpeta por animación con 1.png, 2.png…
  const ANIMS = new Map();         // id → { podio: { gana, otro }, anims: { nombre → {...} } }
  function animDe(id, nombre) { const s = ANIMS.get(id); return s && nombre && s.anims[nombre] || null; }
  function animaciones(nombre) { const s = ANIMS.get(spriteDe(nombre)); return s ? Object.values(s.anims).map(a => ({ nombre: a.nombre, titulo: a.titulo })) : []; }

  // Un solo reloj para todas las animaciones de la página: cambia el cuadro de cada
  // elemento con data-frames cuando le toca. En el último cuadro espera "pausa".
  function animar() {
    if (global.__avataresReloj) return;
    if (global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    global.__avataresReloj = setInterval(() => {
      const now = performance.now();
      for (const el of document.querySelectorAll("[data-frames]")) {
        if (now < +(el.dataset.t || 0)) continue;
        const fr = el.dataset.frames.split("|");
        const i = (+(el.dataset.i || 0) + 1) % fr.length;
        el.dataset.i = i;
        el.dataset.t = now + (i === fr.length - 1 ? +el.dataset.pausa : +el.dataset.ms);
        if (el.tagName.toLowerCase() === "image") el.setAttribute("href", fr[i]); else el.src = fr[i];
      }
    }, 40);
  }

  // si falta una pose se usa la de parado; si falta todo, el primer personaje cargado
  function meta(id, pose) {
    return META.get(id + "/" + pose) || META.get(id + "/parado") || META.get([...META.keys()][0]) || null;
  }

  // ───────────────────────── agregados en pixel art ─────────────────────────
  const CROWN = ["a...a...a", "g...g...g", "gg.ggg.gg", "ggggggggg", "gxgxgxgxg", "ddddddddd"];
  const CROWN_PAL = {
    dorada: { a: GL, g: G, d: GD, x: G },
    gemas: { a: GL, g: G, d: GD, x: "#3f86c4" },
    real: { a: "#fff6dc", g: G, d: GD, x: "#c23a7a" },
  };
  const MEDAL = { oro: [G, GL, GD], plata: ["#c8ccd2", "#eef0f3", "#8e939a"], bronce: ["#c07a48", "#e0a070", "#8a5230"] };
  const MEDAL_MAP = ["r.r", ".r.", "mlm", "mmm", "dmd"];
  const STAR = ["..y..", ".yyy.", "yywyy", ".yyy.", ".y.y."];
  const BULB = [".yyy.", "ywyyy", "yyyyy", ".yyy.", "..g..", ".ggg."];
  const BOLT = ["..y", ".y.", "yyy", ".y.", "y.."];
  const ZED = ["####", "..#.", ".#..", "####"];
  const ZED3 = ["###", ".#.", "###"];
  const TROPHY = ["l.ggg.g", "lgggggg", ".ggggg.", "..ggd..", "...g...", "..ddd.."];
  const FLAME = [".....r.....", "....rr.....", "....rro....", "...rroo..r.", "..rrooo.rr.", "..roooorro.", ".rrooyooor.", ".rooyyyoor.", "rrooyyyyoor", "rooyywyyoor", "rooyyyyyoor", ".rooyyyoor.", "..rrooorr..", "...rrrrr..."];
  const FLAME_PAL = [
    null,
    { r: "#d9462a", o: "#f5892e", y: "#ffd24a", w: "#fff1a8" },
    { r: "#c8361f", o: "#f07a26", y: "#ffc93a", w: "#fff1a8" },
    { r: "#2f6fd6", o: "#4f9dff", y: "#9fd0ff", w: "#e6f4ff" },
    { r: "#6a3cc8", o: "#a77bff", y: "#d4bcff", w: "#f6eeff" },
  ];

  // Pasa un dibujo de letras a píxeles, con contorno, en una grilla de lado u.
  function pixelMap(rows, pal, ox, oy, u, cls, outline = true) {
    const m = new Map();
    rows.forEach((r, j) => [...r].forEach((ch, i) => { if (pal[ch]) m.set(i + "," + j, pal[ch]); }));
    if (outline) for (const k of [...m.keys()]) {
      const [x, y] = k.split(",").map(Number);
      for (const [ex, ey] of N4) { const kk = (x + ex) + "," + (y + ey); if (!m.has(kk)) m.set(kk, m.get(kk) || null); }
    }
    let out = "";
    const byRow = new Map();
    for (const [k, c] of m) { const [x, y] = k.split(",").map(Number); if (!byRow.has(y)) byRow.set(y, []); byRow.get(y).push([x, c || OUT]); }
    for (const [y, list] of byRow) {
      list.sort((a, b) => a[0] - b[0]);
      for (let i = 0; i < list.length;) {
        let j = i + 1;
        while (j < list.length && list[j][0] === list[j - 1][0] + 1 && list[j][1] === list[i][1]) j++;
        out += `<rect x="${ox + list[i][0] * u}" y="${oy + y * u}" width="${(list[j - 1][0] - list[i][0] + 1) * u}" height="${u}" fill="${list[i][1]}"/>`;
        i = j;
      }
    }
    return `<g class="${cls}">${out}</g>`;
  }

  // Agregados del día, en coordenadas de la imagen del personaje.
  // estado: { corona: "dorada"|"gemas"|"real", medalla: "oro"|"plata"|"bronce", perfecto, rapido, basico, pendiente }
  function agregados(mt, estado, pose) {
    const { top, cx, u, h } = mt;
    let s = "";
    if (estado.corona) s += pixelMap(CROWN, CROWN_PAL[estado.corona] || CROWN_PAL.dorada, Math.round(cx - 4.5 * u), top - 5 * u, u, "corona");
    if (estado.medalla && pose !== "sentado") {
      const [b, l, d] = MEDAL[estado.medalla] || MEDAL.oro;
      s += pixelMap(MEDAL_MAP, { r: "#8e2f2a", m: b, l, d }, Math.round(cx - 1.5 * u), Math.round(top + (h - top) * .5), u, "medalla");
    }
    if (estado.perfecto) s += pixelMap(STAR, { y: "#f2c94c", w: "#fff1b8" }, Math.round(cx - 11 * u), top - 2 * u, u, "star");
    if (estado.basico) s += pixelMap(BULB, { y: "#ffd75a", w: "#fff6c8", g: "#9a8f80" }, Math.round(cx + 6 * u), top - 3 * u, u, "bulb");
    if (estado.rapido) s += pixelMap(BOLT, { y: "#ffd84d" }, Math.round(cx + 9 * u), top + 4 * u, u, "bolt");
    if (estado.pendiente) {
      s += pixelMap(ZED, { "#": "#cfe3ff" }, Math.round(cx + 6 * u), top - 1 * u, u, "zz1", false);
      s += pixelMap(ZED3, { "#": "#cfe3ff" }, Math.round(cx + 10 * u), top - 5 * u, u, "zz2", false);
    }
    return s;
  }

  // ───────────────────────── personaje en HTML ─────────────────────────
  // opts: { pose, recorte: "cuerpo" | "busto", alto (px), titulo }
  function avatar(nombre, estado = {}, opts = {}) {
    const id = spriteDe(nombre);
    const pose = POSES.includes(opts.pose) ? opts.pose : "parado";
    const mt = meta(id, pose);
    const alto = opts.alto || 48;
    const label = opts.titulo ? ` role="img" aria-label="${esc(opts.titulo)}"` : ' aria-hidden="true"';
    if (!mt) return `<span class="avt avt-${opts.recorte || "cuerpo"}" style="width:${alto}px;height:${alto}px"${label}></span>`;
    const src = esc(mt.src);
    const fx = agregados(mt, estado, pose);
    if (opts.recorte === "busto") {
      // cuadrado alrededor de la cabeza, con lugar arriba para la corona
      const lado = Math.round((meta(id, "parado") || mt).h * .55);
      const k = alto / lado;
      const x0 = mt.cx - lado / 2, y0 = mt.top - 6 * mt.u;
      const pos = `left:${(-x0 * k).toFixed(1)}px;top:${(-y0 * k).toFixed(1)}px;width:${(mt.w * k).toFixed(1)}px;height:${(mt.h * k).toFixed(1)}px`;
      return `<span class="avt avt-busto" style="width:${alto}px;height:${alto}px"${label}><img src="${src}" alt="" style="${pos}"><svg viewBox="0 0 ${mt.w} ${mt.h}" style="${pos}" overflow="visible" shape-rendering="crispEdges">${fx}</svg></span>`;
    }
    // de cuerpo entero, "alto" es la altura del personaje parado: así todas las poses y
    // animaciones de un mismo personaje quedan en la misma escala
    const pet = opts.mascota === false ? null : mascotaDe(nombre);
    const an = animDe(id, opts.anim);
    let k, cw, ch, pj;
    if (an) {
      k = alto / an.alto; cw = an.w * k; ch = an.h * k;
      pj = `<span class="avt-pj" style="width:${cw.toFixed(1)}px;height:${ch.toFixed(1)}px"><img src="${esc(an.srcs[0])}" alt="" data-frames="${esc(an.srcs.join("|"))}" data-ms="${an.ms}" data-pausa="${an.pausa}"></span>`;
    } else {
      k = alto / (meta(id, "parado") || mt).h; cw = mt.w * k; ch = mt.h * k;
      pj = `<span class="avt-pj" style="width:${cw.toFixed(1)}px;height:${ch.toFixed(1)}px"><img src="${src}" alt=""><svg viewBox="0 0 ${mt.w} ${mt.h}" overflow="visible" shape-rendering="crispEdges">${fx}</svg></span>`;
    }
    if (!pet || (an && an.mascota)) return `<span class="avt avt-cuerpo" style="width:${cw.toFixed(1)}px;height:${ch.toFixed(1)}px"${label}>${pj}</span>`;
    // la mascota va a los pies, a la derecha, en la misma escala que el personaje parado
    const ph = Math.round(alto * PET_ALTO), pw = ph * pet.w / pet.h;
    return `<span class="avt avt-cuerpo" style="width:${(cw + pw).toFixed(1)}px;height:${ch.toFixed(1)}px"${label}>${pj}<img class="mascota" src="${esc(pet.src)}" alt="" style="left:${(cw - pw * .15).toFixed(1)}px;top:auto;bottom:0;width:${pw.toFixed(1)}px;height:${ph}px"></span>`;
  }

  // ───────────────────────── insignias sueltas ─────────────────────────
  function nivelRacha(n) { return n >= 10 ? 4 : n >= 5 ? 3 : n >= 3 ? 2 : n >= 2 ? 1 : 0; }
  function rachaSVG(n, alto = 16) {
    const t = nivelRacha(n);
    if (!t) return "";
    return `<span class="racha r${t}" title="${n} victorias seguidas"><svg viewBox="0 0 13 16" width="${Math.round(alto * 13 / 16)}" height="${alto}" shape-rendering="crispEdges" aria-hidden="true">${pixelMap(FLAME, FLAME_PAL[t], 1, 1, 1, "llama")}</svg><b>${n}</b></span>`;
  }
  function iconoSVG(nombre, alto = 14) {
    const maps = { trofeo: [TROPHY, { g: G, l: GL, d: GD }], estrella: [STAR, { y: "#f2c94c", w: "#fff1b8" }], rayo: [BOLT, { y: "#ffd84d" }], lamparita: [BULB, { y: "#ffd75a", w: "#fff6c8", g: "#9a8f80" }] };
    const [rows, pal] = maps[nombre] || maps.estrella;
    const w = rows[0].length + 2, h = rows.length + 2;
    return `<svg class="ico" viewBox="0 0 ${w} ${h}" width="${Math.round(alto * w / h)}" height="${alto}" shape-rendering="crispEdges" aria-hidden="true">${pixelMap(rows, pal, 1, 1, 1, "ico")}</svg>`;
  }

  // ───────────────────────── podio ─────────────────────────
  const DIGITS = {
    1: ["...##...", "..###...", ".####...", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", ".######.", ".######."],
    2: [".#####..", "##...##.", ".....##.", ".....##.", "....##..", "...##...", "..##....", ".##.....", "##......", "#######.", "#######."],
    3: [".#####..", "##...##.", ".....##.", ".....##.", "..####..", ".....##.", ".....##.", ".....##.", "##...##.", ".#####..", "........"],
  };
  const LAUREL = ["...#.", "..##.", ".#.#.", "##.#.", ".#.##", "#..#.", "##.#.", ".###.", "..#.."];
  const BLOCKS = [
    { lugar: 2, x: 6, h: 30, lid: "#9a9aa0", lidL: "#c6c6ca", lidD: "#6c6c72", front: "#38373d", speck: "#42414a", num: "#ebe6dc", laurel: "#8a8a90", frame: "left" },
    { lugar: 3, x: 118, h: 24, lid: "#b0623a", lidL: "#d08a5a", lidD: "#7e4128", front: "#45291f", speck: "#523126", num: "#efdcc4", laurel: "#a85a36" },
    { lugar: 1, x: 62, h: 40, lid: "#e0a93a", lidL: "#f4cb62", lidD: "#a8762a", front: "#3a3024", speck: "#45392a", num: "#f4cb62", laurel: "#d9a23a", frame: "both" },
  ];
  const GROUND = 112, BW = 56, ANCHO = 240, ALTO_PJ = 44;   // alto de un personaje parado, en píxeles del podio
  const CUARTO = { x: 176, w: 60 };                          // 4.º lugar: en el piso, a la derecha del podio

  function rectsDe(map) {
    const byRow = new Map();
    for (const [k, c] of map) { const [x, y] = k.split(",").map(Number); if (!byRow.has(y)) byRow.set(y, []); byRow.get(y).push([x, c]); }
    let out = "";
    for (const [y, list] of byRow) {
      list.sort((a, b) => a[0] - b[0]);
      for (let i = 0; i < list.length;) {
        let j = i + 1;
        while (j < list.length && list[j][0] === list[j - 1][0] + 1 && list[j][1] === list[i][1]) j++;
        out += `<rect x="${list[i][0]}" y="${y}" width="${list[j - 1][0] - list[i][0] + 1}" height="1" fill="${list[i][1]}"/>`;
        i = j;
      }
    }
    return out;
  }

  // top: [{ nombre, estado }, …] en orden 1.º, 2.º, 3.º, 4.º (null = lugar vacío)
  function podioSVG(top3) {
    const m = new Map();
    const set = (x, y, c) => m.set(x + "," + y, c);
    const rect = (x1, y1, x2, y2, c) => { for (let y = y1; y <= y2; y++) for (let x = x1; x <= x2; x++) set(x, y, typeof c === "function" ? c(x, y) : c); };
    const chars = [];
    for (const b of BLOCKS) {
      const p = top3[b.lugar - 1];
      const dim = c => p ? c : mix(c, "#111418", .55);
      const top = GROUND - b.h, x2 = b.x + BW - 1;
      rect(b.x - 1, top + 6, x2 + 1, GROUND, OUT);
      rect(b.x, top + 6, x2, GROUND - 1, (x, y) => dim((x * 7 + y * 13) % 11 === 0 ? b.speck : b.front));
      if (b.frame === "both") { rect(b.x, top + 6, b.x + 1, GROUND - 1, dim(b.lidD)); rect(x2 - 1, top + 6, x2, GROUND - 1, dim(b.lidD)); }
      if (b.frame === "left") rect(b.x, top + 6, b.x, GROUND - 1, dim(b.lidD));
      rect(b.x - 2, top - 1, x2 + 2, top + 6, OUT);
      rect(b.x - 1, top, x2 + 1, top + 5, (x, y) => dim(y === top ? b.lidL : y === top + 4 ? b.lidD : y === top + 5 ? dk(b.lidD, .3) : (x * 5 + y * 3) % 9 === 0 ? b.lidL : b.lid));
      const dig = DIGITS[b.lugar], dx = b.x + (BW - 8) / 2, ddy = top + 6 + Math.floor((b.h - 6 - 11) / 2) + 1;
      const dm = new Set();
      dig.forEach((r, i) => [...r].forEach((ch, j) => { if (ch === "#") dm.add((dx + j) + "," + (ddy + i)); }));
      for (const k of dm) { const [x, y] = k.split(",").map(Number); for (const [ex, ey] of N4) if (!dm.has((x + ex) + "," + (y + ey))) set(x + ex, y + ey, OUT); }
      for (const k of dm) { const [x, y] = k.split(",").map(Number); set(x, y, dim(b.num)); }
      LAUREL.forEach((r, i) => [...r].forEach((ch, j) => { if (ch === "#") { set(dx - 8 + j, ddy + 1 + i, dim(b.laurel)); set(dx + 11 + (4 - j), ddy + 1 + i, dim(b.laurel)); } }));
      if (p) {
        const id = spriteDe(p.nombre), set = ANIMS.get(id);
        // si el personaje tiene animaciones de podio: "gana" para el 1.º, "otro" para 2.º y 3.º
        const an = set ? animDe(id, b.lugar === 1 ? set.podio.gana : set.podio.otro) : null;
        const pose = b.lugar === 1 ? "festejo" : "parado", mt = meta(id, pose), base = meta(id, "parado");
        if (an) {
          const k = ALTO_PJ / an.alto, w = an.w * k, h = an.h * k;
          const x = b.x + BW / 2 - (an.talon + an.alto * .22) * k, y = top - h;
          chars.push(`<image href="${esc(an.srcs[0])}" x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${w.toFixed(2)}" height="${h.toFixed(2)}" data-frames="${esc(an.srcs.join("|"))}" data-ms="${an.ms}" data-pausa="${an.pausa}"/>`);
          const pet = an.mascota ? null : mascotaDe(p.nombre);
          if (pet) {
            // detrás del personaje (mira a la derecha), así no tapa lo que tiene en las manos
            const ph = Math.round(ALTO_PJ * PET_ALTO), pw = ph * pet.w / pet.h;
            const px = Math.max(b.x - 2, x + an.talon * k - pw + 1);
            chars.unshift(`<image class="mascota" href="${esc(pet.src)}" x="${px.toFixed(2)}" y="${top - ph}" width="${pw.toFixed(2)}" height="${ph}" style="image-rendering:pixelated"/>`);
          }
        } else if (mt) {
          const k = ALTO_PJ / (base || mt).h;                 // misma escala para todas las poses del personaje
          const w = mt.w * k, h = mt.h * k, x = b.x + BW / 2 - mt.cx * k, y = top - h;
          chars.push(`<svg x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${w.toFixed(2)}" height="${h.toFixed(2)}" viewBox="0 0 ${mt.w} ${mt.h}" overflow="visible"><image href="${esc(mt.src)}" width="${mt.w}" height="${mt.h}"/><g shape-rendering="crispEdges">${agregados(mt, p.estado || {}, pose)}</g></svg>`);
          const pet = mascotaDe(p.nombre);
          if (pet) {
            const ph = Math.round(ALTO_PJ * PET_ALTO), pw = ph * pet.w / pet.h;
            const px = Math.min(b.x + BW - pw + 2, x + w - 2);
            chars.push(`<image class="mascota" href="${esc(pet.src)}" x="${px.toFixed(2)}" y="${top - ph}" width="${pw.toFixed(2)}" height="${ph}" style="image-rendering:pixelated"/>`);
          }
        }
      }
    }
    // 4.º lugar: sin bloque, tirado en el piso ("podio.ultimo" del personaje); si no tiene esa animación, sentado
    const p4 = top3[3];
    if (p4) {
      const id = spriteDe(p4.nombre), st = ANIMS.get(id);
      const an = st ? animDe(id, st.podio.ultimo) : null;
      const cx = CUARTO.x + CUARTO.w / 2, base = meta(id, "parado");
      if (an) {
        const k = ALTO_PJ / an.alto, w = an.w * k, h = an.h * k;
        chars.push(`<image href="${esc(an.srcs[0])}" x="${(cx - w / 2).toFixed(2)}" y="${(GROUND - h).toFixed(2)}" width="${w.toFixed(2)}" height="${h.toFixed(2)}" data-frames="${esc(an.srcs.join("|"))}" data-ms="${an.ms}" data-pausa="${an.pausa}"/>`);
      } else {
        const mt = meta(id, "sentado");
        if (mt) {
          const k = ALTO_PJ / (base || mt).h, w = mt.w * k, h = mt.h * k, x = cx - mt.cx * k;
          chars.push(`<svg x="${x.toFixed(2)}" y="${(GROUND - h).toFixed(2)}" width="${w.toFixed(2)}" height="${h.toFixed(2)}" viewBox="0 0 ${mt.w} ${mt.h}" overflow="visible"><image href="${esc(mt.src)}" width="${mt.w}" height="${mt.h}"/><g shape-rendering="crispEdges">${agregados(mt, p4.estado || {}, "sentado")}</g></svg>`);
        }
      }
    }
    rect(0, GROUND, ANCHO - 1, GROUND, "#7d9a3e"); rect(0, GROUND + 1, ANCHO - 1, GROUND + 2, "#5d7a2e"); rect(0, GROUND + 3, ANCHO - 1, GROUND + 3, "#3f5222");
    const tuft = (x, h) => { for (let i = 0; i < h; i++) set(x, GROUND - 1 - i, i === h - 1 ? "#9ab84e" : "#6d8a34"); set(x + 2, GROUND - 1, "#6d8a34"); set(x + 2, GROUND - 2, "#9ab84e"); set(x - 1, GROUND - 1, "#6d8a34"); };
    [[2, 3], [12, 2], [36, 3], [58, 4], [70, 2], [96, 3], [114, 4], [124, 2], [150, 3], [168, 3], [176, 2], [228, 3], [236, 2]].forEach(([x, h]) => tuft(x, h));
    const rock = x => { rect(x, GROUND - 2, x + 3, GROUND - 1, "#8a8680"); rect(x + 1, GROUND - 3, x + 2, GROUND - 3, "#a8a49e"); set(x, GROUND - 2, "#6e6a64"); };
    rock(16); rock(160);
    return `<svg class="podio-svg" viewBox="0 20 ${ANCHO} 97" role="img" aria-label="Podio del día"><g shape-rendering="crispEdges">${rectsDe(m)}</g>${chars.join("")}</svg>`;
  }

  animar();
  global.Avatares = { cargar, avatar, spriteDe, mascotaDe, animaciones, podioSVG, rachaSVG, nivelRacha, iconoSVG, POSES };
})(typeof window !== "undefined" ? window : globalThis);
