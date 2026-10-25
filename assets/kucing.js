// Pompom (kucing gembul): sprite dari ilustrasi karakter + gerak 3D semu (perspektif, putar, miring, squash & stretch) 60 fps.
// Dijalankan di jendela induk. P = window, CFG = pengaturan dari server ({sapa, nama, kabar, css, spr}).
var D = P.document;
if (P.__ujKucing) {
  var K0 = P.__ujKucing; K0.show();
  if (CFG.sapa) K0.sambut(CFG);
  else if (CFG.kabar) K0.kabarBaru(CFG.kabar);
  return;
}
var W = 96, H = 104;
var st = D.createElement('style'); st.id = 'uj-kucing-css'; st.textContent = CFG.css; D.head.appendChild(st);
var root = D.createElement('div'); root.id = 'uj-kucing'; root.setAttribute('data-c', 'k|chat'); root.setAttribute('role', 'button');
root.setAttribute('aria-label', 'Tanya Pompom');
root.innerHTML = '<div class="bayang"></div><div class="tilt"></div>';
D.body.appendChild(root);
var tilt = root.querySelector('.tilt'), bayang = root.querySelector('.bayang');
var gl = D.createElement('div'); gl.id = 'uj-gelembung'; D.body.appendChild(gl);

// ------------------------------------------------------------------ sprite (satu <img> per pose, ditumpuk)
var FK = { walk: .95, jump: .95, sit: 1, lick: .95, wave: .72, laugh: .72 };
var IM = {};
Object.keys(CFG.spr).forEach(function (n) {
  var d = CFG.spr[n], f = FK[n.replace(/\d+$/, '')] || 1, im = D.createElement('img');
  im.src = d[0]; im.alt = ''; im.draggable = false; im.style.width = (d[1] * f).toFixed(1) + 'px'; im.style.height = (d[2] * f).toFixed(1) + 'px';
  im.style.opacity = 0; tilt.appendChild(im); IM[n] = im;
});
var cur = '', prev = '', fd = 1, zc = 1;
function pose(n, cepat) {
  if (!IM[n] || n === cur) return;
  if (prev && IM[prev]) IM[prev].style.opacity = 0;
  prev = cur; cur = n; zc++; IM[n].style.zIndex = zc;
  if (cepat || !prev) { fd = 1; IM[n].style.opacity = 1; if (prev && IM[prev]) IM[prev].style.opacity = 0; prev = ''; }
  else { fd = 0; IM[n].style.opacity = 0; }
}

// ------------------------------------------------------------------ keadaan & tween
var S = { x: 0, y: 0, jy: 0, dx: -1, yw: 0, pt: 0, ro: 0, ln: 0, sc: 1, sq: 0, st: 0, tx: 0, sp: 0, op: 1 };
var T = [], tok = 0, ph = 0, vx = 0, vy = 0, lastX = 0, lastY = 0, lastT = 0, nowS = 0;
var E = {
  io: function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; },
  out: function (t) { return 1 - Math.pow(1 - t, 3); },
  inn: function (t) { return t * t * t; },
  lin: function (t) { return t; },
  sine: function (t) { return -(Math.cos(Math.PI * t) - 1) / 2; },
  back: function (t) { var c = 1.7; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); }
};
function tw(to, dur, ease) {
  return new Promise(function (res) {
    for (var i = 0; i < T.length; i++) for (var k in to) delete T[i].to[k];
    var tk = { from: {}, to: to, t0: P.performance.now(), dur: Math.max(1, dur), ease: ease || E.io, res: res };
    for (var k2 in to) tk.from[k2] = S[k2];
    T.push(tk);
  });
}
function stopAll() { tok++; var t = T; T = []; t.forEach(function (x) { x.res(); }); clearTimeout(K.timer); clearTimeout(K.wt); }
function chk(my) { if (my !== tok) throw 'batal'; }

var K = { el: root, gl: gl, sembunyi: false, kenyang: 0, kenyangT: 0, fedLast: 0, lastAct: '', timer: 0, wt: 0, wk: false, cy: null };
function maxX() { return Math.max(0, (P.innerWidth || 360) - W - 24); }
function home() { return { x: maxX(), y: 10 }; }
function maxY() { return Math.max(60, (P.innerHeight || 640) - H - 6); }
function rnd(a, b) { return a + Math.random() * (b - a); }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

// ------------------------------------------------------------------ gambar tiap frame
var WALK = ['walk0', 'walk1', 'walk2', 'walk3'];
function apply(dt) {
  var t = nowS, spd = Math.sqrt(vx * vx + vy * vy), sp = Math.min(1, spd / 90);
  var bergerak = K.wk && sp > .04;
  if (K.wk) ph += dt * (3 + sp * 9);
  if (K.cy) { var i = Math.floor((P.performance.now() - K.cy.t0) / 1000 * K.cy.fps) % K.cy.l.length; pose(K.cy.l[i], true); }
  else if (K.wk) { pose(bergerak ? WALK[Math.floor(ph / (Math.PI / 2)) % 4] : 'sit0', true); }
  if (fd < 1) { fd = Math.min(1, fd + dt / .1); if (cur && IM[cur]) IM[cur].style.opacity = fd; if (fd >= 1 && prev && IM[prev]) { IM[prev].style.opacity = 0; prev = ''; } }
  var bob = bergerak ? Math.abs(Math.sin(ph * 2)) * 3.4 * sp : 0;
  var ds = (.9 + clamp(S.y / maxY(), 0, 1) * .14) * S.sc;            // makin ke bawah makin besar (kesan kedalaman)
  root.style.opacity = S.op;
  root.style.transform = 'translate3d(' + S.x.toFixed(2) + 'px,' + Math.max(2, S.y + S.jy - bob).toFixed(2) + 'px,0)';
  var breathe = Math.sin(t * 2.3) * .014, idle = (!K.wk && !K.cy) ? 1 : .4;
  var yaw = (1 - S.dx) * 90 + S.yw + S.sp + Math.sin(t * .8) * 5 * idle;
  var lean = (K.wk || Math.abs(S.jy) > 2) ? clamp(vx / 90, -1, 1) * 6 : 0;
  var sx = (1 + S.tx) * (1 + S.sq * .5) * (1 - breathe * .5) * ds, sy = (1 - S.sq * .9 + breathe) * (1 + S.st) * ds;
  tilt.style.transform = 'rotateX(' + (S.pt + Math.sin(t * 1.3) * 1.2 * idle).toFixed(2) + 'deg) rotateZ(' + (S.ro + S.ln + lean).toFixed(2) + 'deg) rotateY(' +
    yaw.toFixed(2) + 'deg) scale(' + sx.toFixed(3) + ',' + sy.toFixed(3) + ')';
  var hh = Math.min(1, Math.abs(S.jy) / 90);
  bayang.style.transform = 'translateX(-50%) scale(' + ((1 - hh * .45) * (1 + S.tx * .8) * ds).toFixed(3) + ',' + (1 - hh * .4).toFixed(3) + ')';
  bayang.style.opacity = (.85 - hh * .5).toFixed(3);
  if (gl.classList.contains('tampil')) posGl();
}
function frame(now) {
  var dt = Math.min(.05, (now - (lastT || now)) / 1000); lastT = now; nowS = now / 1000;
  for (var i = T.length - 1; i >= 0; i--) {
    var tk = T[i], p = Math.min(1, (now - tk.t0) / tk.dur), e = tk.ease(p);
    for (var k in tk.to) S[k] = tk.from[k] + (tk.to[k] - tk.from[k]) * e;
    if (p >= 1) { T.splice(i, 1); tk.res(); }
  }
  if (dt > 0) { vx = vx * .7 + ((S.x - lastX) / dt) * .3; vy = vy * .7 + ((S.y - lastY) / dt) * .3; }
  lastX = S.x; lastY = S.y;
  if (!K.sembunyi && !D.hidden) apply(dt);
  P.requestAnimationFrame(frame);
}
function posGl() {
  var gw = gl.offsetWidth, gh = gl.offsetHeight, vw = P.innerWidth || 360;
  var cx = S.x + W / 2, below = S.y + S.jy < 120;
  var gx = Math.min(Math.max(6, cx - gw / 2), vw - gw - 6);
  var gy = below ? S.y + S.jy + H + 6 : S.y + S.jy - gh - 8;
  gl.style.transform = 'translate3d(' + gx.toFixed(1) + 'px,' + Math.max(4, gy).toFixed(1) + 'px,0)';
  gl.classList.toggle('atas', !below);
  gl.style.setProperty('--ekor', Math.min(gw - 22, Math.max(10, cx - gx - 6)) + 'px');
}

// ------------------------------------------------------------------ bantuan gerak
function w(ms, my) { return new Promise(function (res) { K.wt = setTimeout(res, ms); }).then(function () { chk(my); }); }
function pz(o, ms, e, my) { return tw(o, ms, e).then(function () { chk(my); }); }
function par(list, my) { return Promise.all(list).then(function () { chk(my); }); }
var bt = 0;
function say(t, ms, menu) {
  gl.innerHTML = ''; var sp = D.createElement('span'); sp.textContent = t; gl.appendChild(sp);
  gl.classList.toggle('menu', !!menu);
  if (menu) {
    var box = D.createElement('div'); box.className = 'mkn';
    [['🍗', 'ayam goreng'], ['🍤', 'udang'], ['🐟', 'ikan'], ['🥩', 'daging'], ['🥛', 'susu'], ['🍚', 'nasi']].forEach(function (f) {
      var b = D.createElement('button'); b.type = 'button'; b.textContent = f[0]; b.title = f[1]; b.setAttribute('aria-label', f[1]);
      b.addEventListener('click', function (ev) { ev.stopPropagation(); K.beriMakan(f[0], b); }); box.appendChild(b);
    });
    gl.appendChild(box);
  }
  gl.classList.add('tampil'); posGl(); clearTimeout(bt);
  if (ms) bt = setTimeout(function () { gl.classList.remove('tampil'); gl.classList.remove('menu'); }, ms);
}
function diam() { gl.classList.remove('tampil'); gl.classList.remove('menu'); clearTimeout(bt); }
function fx(emoji, x, y, dx, dy, ms, size) {
  var n = D.createElement('div'); n.className = 'uj-fx'; n.textContent = emoji; n.style.fontSize = (size || 18) + 'px'; D.body.appendChild(n);
  var t0 = P.performance.now();
  (function f(now) { var p = Math.min(1, (now - t0) / ms);
    n.style.transform = 'translate3d(' + (x + dx * p) + 'px,' + (y + dy * p - Math.sin(p * Math.PI) * 14) + 'px,0) scale(' + (.6 + Math.sin(p * Math.PI) * .7) + ')';
    n.style.opacity = p < .7 ? 1 : (1 - p) / .3;
    if (p < 1) P.requestAnimationFrame(f); else n.remove(); })(t0);
}
function hati(n) { for (var i = 0; i < (n || 3); i++) (function (i) { setTimeout(function () { fx('❤️', S.x + 26 + rnd(0, 40), S.y + S.jy, rnd(-14, 14), -rnd(36, 60), 1200, 16 + rnd(0, 6)); }, i * 180); })(i); }
function cyc(list, fps) { K.cy = list ? { l: list, fps: fps || 4, t0: P.performance.now() } : null; }
function duduk(n) { K.wk = false; K.cy = null; pose(n || 'sit0'); }
function menghadap(d, ms, my) { return pz({ dx: d }, ms || 320, E.io, my); }
function ke(x, y, ms, my, e) { return pz({ x: clamp(x, 0, maxX()), y: clamp(y, 0, maxY()) }, ms, e || E.sine, my); }
async function jalanKe(x, y, ms, my) {
  await menghadap(x < S.x ? -1 : 1, 280, my);
  K.cy = null; K.wk = true; pose('walk0', true);
  await ke(x, y, ms, my); K.wk = false; duduk('sit0');
}
async function lompatKe(x, y, ms, tinggi, my) {
  // merunduk → melesat (badan miring ke depan lalu menukik) → mendarat memantul; semua dengan pose gambar karakter
  var d = x > S.x ? 1 : -1; tinggi = tinggi || 46; ms = ms || 640; K.wk = false; K.cy = null;
  await par([tw({ dx: d }, 220)], my);
  pose('jump5'); await par([tw({ sq: .2, tx: .06 }, 150, E.out)], my);
  pose('jump0');
  var a = tw({ x: clamp(x, 0, maxX()), y: clamp(y, 0, maxY()) }, ms, E.sine);
  var b = tw({ sq: -.06, tx: -.02, pt: -8 }, ms * .3, E.out).then(function () { return tw({ pt: 10 }, ms * .6, E.io); });
  var up = tw({ jy: -tinggi }, ms * .5, E.out).then(function () { return tw({ jy: 0 }, ms * .5, E.inn); });
  var seq = (async function () {
    await w2(ms * .12); pose('jump1', true); await w2(ms * .2); pose('jump2', true); await w2(ms * .22); pose('jump3', true); await w2(ms * .2); pose('jump4', true);
  })();
  await par([a, b, up, seq], my);
  pose('jump5', true); await par([tw({ sq: .22, tx: .08, pt: 0 }, 110, E.out)], my);
  await par([tw({ sq: 0, tx: 0 }, 300, E.back)], my); duduk('sit0');
}
function w2(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
async function netral(ms, my) { await pz({ yw: 0, pt: 0, ro: 0, ln: 0, sq: 0, st: 0, tx: 0, jy: 0, sc: 1, sp: 0 }, ms || 380, E.io, my); }
async function pulang(my) {
  var h = home(); K.cy = null;
  if (Math.abs(S.x - h.x) > 3 || Math.abs(S.y - h.y) > 3) {
    if (S.y > h.y + 120 || Math.abs(S.x - h.x) > 160) { await lompatKe(h.x, h.y, 800, 70, my); } else { await jalanKe(h.x, h.y, 800, my); }
  }
  duduk('sit0'); await par([tw({ dx: -1 }, 420), netral(420, my)], my);
}

// ------------------------------------------------------------------ 25+ aktivitas
var AK = {};
AK.duduk_santai = async function (my) { duduk('sit0'); await pz({ yw: 16 }, 1000, E.io, my); await w(1200, my); pose('sit5'); await pz({ yw: -14, ln: -2 }, 1100, E.io, my); await w(1400, my); pose('sit0'); };
AK.menguap = async function (my) { duduk('sit0'); await par([tw({ pt: -6, st: .05 }, 500, E.io)], my); pose('laugh2'); await par([tw({ st: .12, sq: -.02 }, 900, E.io)], my); await w(1400, my);
  await par([tw({ st: 0, pt: 0, sq: 0 }, 700, E.io)], my); pose('laugh4'); await w(900, my); };
AK.jilat_kaki = async function (my) { cyc(['lick0', 'lick1'], 2.4); await par([tw({ ln: -2, yw: 10 }, 900, E.sine)], my); await w(2600, my); await par([tw({ ln: 0, yw: 0 }, 600, E.io)], my); };
AK.cuci_muka = async function (my) { cyc(['lick1', 'lick0'], 5); for (var i = 0; i < 4; i++) { await pz({ yw: 12, ro: 2 }, 420, E.sine, my); await pz({ yw: -12, ro: -2 }, 420, E.sine, my); } await par([tw({ yw: 0, ro: 0 }, 400, E.io)], my); duduk('sit0'); pose('laugh4'); await w(700, my); };
AK.garuk_telinga = async function (my) { duduk('sit1'); await par([tw({ ro: -6, yw: 12 }, 500, E.io)], my);
  for (var i = 0; i < 8; i++) await pz({ ro: -6 + (i % 2 ? 3 : -3), ln: i % 2 ? 2 : -2 }, 110, E.sine, my);
  await par([tw({ ro: 0, ln: 0, yw: 0 }, 600, E.io)], my); };
AK.melambai = async function (my) { say('Hai hai! 👋', 3400); cyc(['wave0', 'wave1'], 3.2); await par([tw({ yw: 14, ro: 2 }, 600, E.io)], my);
  for (var i = 0; i < 4; i++) { await pz({ jy: -7 }, 260, E.out, my); await pz({ jy: 0 }, 260, E.inn, my); } await par([tw({ yw: 0, ro: 0 }, 500, E.io)], my); };
AK.mengeong = async function (my) { duduk('wave0');
  for (var i = 0; i < 2; i++) { say(i ? 'Meooong~' : 'Meong!', 1500); await par([tw({ st: .08, pt: -6, sc: 1.04 }, 220, E.out)], my); await w(520, my); await par([tw({ st: 0, pt: 0, sc: 1 }, 320, E.io)], my); await w(380, my); } };
AK.minta_makan = async function (my) {
  if (K.kenyang >= 4 && Date.now() - K.kenyangT < 120000) { say('Aku kenyang banget… 🥱', 3000); duduk('sit2'); await par([tw({ sq: .06 }, 800, E.io)], my); await w(2400, my); await netral(500, my); return; }
  duduk('sit5'); await par([tw({ ln: -3, yw: 8 }, 500, E.io)], my);
  say('Aku lapar 🍗 kasih makan dong…', 12000, true);
  for (var i = 0; i < 6; i++) { await par([tw({ st: .08, pt: -8, ro: -3 }, 300, E.out)], my); if (i % 2) { pose('wave1'); } else { pose('sit5'); } await pz({ st: 0, pt: 0, ro: 3 }, 460, E.io, my); await w(900, my); }
  diam(); await netral(500, my); say('Hmm… ya sudah 🙁', 2600); duduk('sit2'); await w(1800, my); };
AK.tidur = async function (my) { duduk('sit2'); await par([tw({ sq: .08, ln: 5, pt: 6 }, 1500, E.io)], my);
  var i = 0; while (i < 3) { say(['Zzz…', 'Zzz… zzz…', 'Zzzz~'][i], 2400); await pz({ sq: .11 }, 1300, E.sine, my); await pz({ sq: .07 }, 1300, E.sine, my); i++; }
  diam(); pose('laugh2'); await par([tw({ sq: 0, ln: 0, pt: -5, st: .1 }, 800, E.io)], my); await w(800, my); await netral(600, my); };
AK.peregangan = async function (my) { duduk('jump5'); await par([tw({ tx: .2, sq: .12, pt: 8, yw: 10 }, 1100, E.io)], my); await w(1500, my);
  await par([tw({ tx: 0, sq: 0, pt: 0, yw: 0, st: .08 }, 900, E.io)], my); pose('laugh2'); await w(500, my); await netral(500, my); };
AK.jalan_santai = async function (my) { var h = home(), tx = Math.max(10, h.x - rnd(140, 260)); await jalanKe(tx, h.y, 2800, my);
  pose('sit1'); await par([tw({ yw: -20 }, 500)], my); await w(700, my); pose('sit5'); await par([tw({ yw: 20 }, 600)], my); await w(800, my); };
AK.lari_keliling = async function (my) { say('Wuuush! 💨', 1800); await menghadap(-1, 200, my); K.wk = false; cyc(['jump1', 'jump2', 'jump3', 'jump2'], 9);
  await par([tw({ x: 6, y: home().y + 12, pt: 4 }, 1150, E.sine)], my); await par([tw({ sq: .1 }, 120)], my); await w(200, my);
  await menghadap(1, 260, my); await par([tw({ x: home().x, y: home().y, sq: 0 }, 1150, E.sine)], my); cyc(null); duduk('sit0'); await par([tw({ pt: 0 }, 300)], my); };
AK.lompat_ditempat = async function (my) { var x0 = S.x, y0 = S.y; for (var i = 0; i < 3; i++) { await lompatKe(x0, y0, 560, 38 + i * 8, my); await w(120, my); } pose('wave1'); await par([tw({ jy: -6 }, 200, E.out)], my); await pz({ jy: 0 }, 200, E.inn, my); await w(500, my); };
AK.lompat_jauh = async function (my) { var h = home(); await lompatKe(Math.max(8, h.x - rnd(120, 230)), h.y + rnd(80, 190), 900, 88, my);
  pose('wave1'); await w(900, my); await lompatKe(h.x, h.y, 950, 96, my); };
AK.kejar_ekor = async function (my) { duduk('sit3'); await par([tw({ sq: .08 }, 250)], my);
  for (var i = 0; i < 5; i++) { var d = i % 2 ? 1 : -1; await par([tw({ yw: 58 * d, ln: 5 * d, jy: -6 }, 330, E.sine)], my); await par([tw({ yw: -58 * d, ln: -5 * d, jy: 0 }, 330, E.sine)], my); }
  await par([tw({ yw: 0, jy: 0, ln: 0, sq: 0 }, 300)], my);
  pose('sit0'); for (var j = 0; j < 3; j++) { await pz({ ro: j % 2 ? 5 : -5 }, 280, E.sine, my); } await par([tw({ ro: 0 }, 300)], my); pose('laugh2'); await w(700, my); };
AK.berguling = async function (my) { duduk('sit0'); await par([tw({ sq: .1 }, 200)], my); pose('laugh3');
  await par([tw({ ro: 360, jy: -8, sq: 0 }, 1300, E.io), tw({ pt: 14 }, 650, E.sine)], my); S.ro = 0; await par([tw({ jy: 0, pt: 0 }, 250)], my);
  await w(700, my); await par([tw({ ro: 0 }, 10)], my); pose('laugh4'); await w(600, my); await netral(300, my); };
AK.menoleh = async function (my) { say('Ada apa ya? 👀', 2800); duduk('sit0'); await par([tw({ yw: -34 }, 700, E.io)], my); await w(500, my); pose('sit1');
  await par([tw({ yw: 34 }, 900, E.io)], my); await w(500, my); pose('sit5'); await par([tw({ yw: 0 }, 650, E.io)], my); await w(600, my); };
AK.mengintip = async function (my) { var vw = P.innerWidth || 360; await menghadap(-1, 250, my); duduk('sit1');
  await pz({ x: vw - W * .45 }, 1000, E.io, my); await par([tw({ yw: -26, ro: -4 }, 450)], my); await w(1700, my);
  pose('laugh4'); await w(600, my); await pz({ x: home().x, yw: 0, ro: 0 }, 1000, E.io, my); };
AK.menari = async function (my) { say('♪ ♫', 4800); var ps = ['laugh1', 'laugh4', 'wave1', 'laugh0', 'laugh4'];
  for (var i = 0; i < 6; i++) { var s = i % 2 ? 1 : -1; pose(ps[i % ps.length]);
    await par([tw({ ro: 7 * s, yw: 18 * s, jy: -9 }, 260, E.out)], my); await par([tw({ jy: 0 }, 200, E.inn)], my); await par([tw({ sq: .08 }, 80)], my); await par([tw({ sq: 0 }, 140)], my); }
  await netral(500, my); };
AK.kupu_kupu = async function (my) {
  var h = home(); duduk('sit5');
  var kp = D.createElement('div'); kp.className = 'uj-fx'; kp.textContent = '🦋'; kp.style.fontSize = '22px'; D.body.appendChild(kp);
  var t0 = P.performance.now(), dur = 3800, sx = h.x - 190, sy = h.y + 150;
  var kx = function (p) { return sx + (S.x - sx + 14) * p + Math.sin(p * 9) * 26; }, ky = function (p) { return sy + (S.y - sy + 10) * p + Math.cos(p * 7) * 20; };
  var run = true; (function f(now) { var p = Math.min(1, (now - t0) / dur); kp.style.transform = 'translate3d(' + kx(p) + 'px,' + ky(p) + 'px,0) rotate(' + Math.sin(p * 30) * 14 + 'deg)'; if (run && p < 1) P.requestAnimationFrame(f); else kp.remove(); })(t0);
  try {
    for (var i = 0; i < 6; i++) { var p2 = Math.min(1, (i + 1) / 7); var dxk = kx(p2) - S.x - 40; await par([tw({ yw: clamp(dxk * .35, -34, 34), pt: -clamp((ky(p2) - S.y) * .02, -6, 6) }, 540, E.sine)], my); }
    say('Tangkap! 🦋', 1800); await lompatKe(S.x - 10, S.y + 6, 440, 54, my); run = false; kp.remove(); pose('laugh4'); await w(700, my);
  } finally { run = false; kp.remove(); }
  await netral(500, my); };
AK.mengendus = async function (my) { await menghadap(-1, 300, my); K.cy = null; K.wk = false; pose('walk3'); await par([tw({ pt: 10, sq: .04 }, 400)], my);
  for (var i = 0; i < 3; i++) { await par([tw({ x: S.x - 22 }, 650, E.sine)], my); pose(i % 2 ? 'walk2' : 'walk3'); await par([tw({ pt: 14 }, 220, E.sine)], my); await par([tw({ pt: 8 }, 220, E.sine)], my); }
  await par([tw({ pt: 0, sq: 0 }, 400)], my); duduk('sit0'); say('Wangi ayam goreng! 🍗', 2600); await w(1200, my); };
AK.kaget = async function (my) { say('!?', 1800); duduk('sit0'); await par([tw({ st: .14, sq: -.05, pt: -6 }, 120, E.out)], my); pose('jump3');
  await par([tw({ jy: -54, pt: -10 }, 260, E.out), tw({ x: Math.min(maxX(), S.x + 24) }, 520, E.sine)], my); await par([tw({ jy: 0, st: 0, pt: 6 }, 260, E.inn)], my);
  pose('jump5'); await par([tw({ sq: .2, tx: .06 }, 90)], my); await w(600, my); duduk('sit0'); await netral(600, my); say('Ternyata cuma angin 😅', 2600); await w(1500, my); };
AK.senyum_ceria = async function (my) { pose('laugh4'); await par([tw({ ro: 5, sc: 1.05 }, 450, E.back)], my); hati(5); await w(800, my);
  pose('laugh2'); await par([tw({ ro: -5 }, 500, E.sine)], my); await w(900, my); await netral(500, my); };
AK.mengantuk = async function (my) { say('Hoaaam… 🥱', 2500); duduk('sit0');
  for (var i = 0; i < 3; i++) { await par([tw({ ln: 9, pt: 8, sq: .06 }, 1100, E.io)], my); await par([tw({ ln: 0, pt: 0, sq: 0 }, 260, E.out)], my); await w(160, my); }
  pose('laugh2'); await par([tw({ st: .1, pt: -5 }, 600)], my); await w(900, my); await netral(500, my); };
AK.berdiri = async function (my) { pose('wave0'); await par([tw({ st: .05 }, 500, E.back)], my); say('Ta-daaa! ✨', 2800);
  var ps = ['wave1', 'laugh0', 'wave0']; for (var i = 0; i < 3; i++) { pose(ps[i]); await par([tw({ ro: 4, yw: 12 }, 380, E.sine)], my); await par([tw({ ro: -4, yw: -12 }, 380, E.sine)], my); }
  await netral(700, my); };
AK.turun_naik = async function (my) { var h = home(), by = maxY(); say('Jalan-jalan dulu ya~', 2500);
  await lompatKe(Math.max(8, h.x - 70), h.y + 150, 800, 70, my); await lompatKe(Math.max(8, h.x - 150), by - 60, 900, 70, my);
  await jalanKe(Math.max(8, h.x - 280), by, 2200, my); await w(600, my); await jalanKe(Math.max(8, h.x - 120), by, 1800, my); await lompatKe(h.x, h.y, 1100, 110, my); };

var DAFTAR = Object.keys(AK);
function pilihAk() {
  var c = DAFTAR.filter(function (n) { return n !== K.lastAct; });
  var n = c[Math.floor(Math.random() * c.length)];
  if (n === 'minta_makan' && Date.now() - K.fedLast < 60000) n = 'senyum_ceria';
  return n;
}

// ------------------------------------------------------------------ pengatur giliran (tiap ±5 detik)
function mulaiGiliran(delay) {
  clearTimeout(K.timer);
  K.timer = setTimeout(function () { jalankan(pilihAk()); }, delay == null ? 5000 : delay);
}
function jalankan(nama, fn) {
  if (K.sembunyi) { mulaiGiliran(3000); return; }
  stopAll(); var my = tok; diam(); K.lastAct = nama || K.lastAct; K.sibuk = nama || 'x'; K.cy = null; K.wk = false;
  (async function () { try { await (fn ? fn(my) : AK[nama](my)); chk(my); await pulang(my); } catch (e) { if (e !== 'batal') console.warn(e); } })()
    .then(function () { if (my === tok) { K.sibuk = ''; mulaiGiliran(5000); } });
}
K.hide = function () { K.sembunyi = true; root.classList.add('sembunyi'); diam(); };
K.show = function () { K.sembunyi = false; root.classList.remove('sembunyi'); };
K.kabarBaru = function (t) { say(t, 6000); hati(2); };

// ------------------------------------------------------------------ sambutan: tersenyum, melompat dari kiri ke kanan, lalu melambai
K.sambut = function (c) {
  K.show();
  jalankan('sambut', async function (my) {
    var h = home(); S.x = -W; S.y = h.y + 62; S.op = 0; S.dx = 1; S.sc = 1; S.jy = 0; pose('wave1', true);
    await par([tw({ op: 1, x: 4 }, 450, E.out), tw({ ro: 3 }, 300, E.sine)], my);
    say(c.sapa, 5200); hati(3); await w(900, my);
    var goal = h.x, n = Math.max(3, Math.round((goal - S.x) / 78));
    for (var i = 1; i <= n; i++) {
      var tx = S.x + (goal - S.x) / (n - i + 1);
      await lompatKe(tx, i === n ? h.y : h.y + 62 + (i % 2 ? 8 : -2), 640, 34 + (i % 3) * 10, my);
      pose('wave1'); await par([tw({ jy: -4, ro: 4 }, 100, E.out)], my); await par([tw({ jy: 0, ro: 0 }, 120, E.inn)], my);
    }
    await par([tw({ dx: -1, ro: 0 }, 450, E.io)], my);
    say('Halo ' + (c.nama || '') + '! Mau pesan apa hari ini? 🍛', 5600);
    cyc(['wave0', 'wave1'], 3.6); await par([tw({ yw: 14 }, 400, E.io)], my); await w(2600, my); cyc(null); duduk('wave1');
    await par([tw({ yw: 0 }, 400, E.io)], my);
    if (c.kabar) { say(c.kabar, 6000); await w(2500, my); }
    await w(900, my); duduk('sit0'); await netral(500, my);
  });
};

// ------------------------------------------------------------------ memberi makan
var FOOD = { '🍗': ['Nyam nyam! Ayam goreng kriuk 😻', 'ayam'], '🍤': ['Udang goreng! Gurih banget~ 😋', 'udang'], '🐟': ['Ikan! Favoritkuuu 🐟💕', 'ikan'],
  '🥩': ['Dagingnya empuk! 😍', 'daging'], '🥛': ['Slurp… susunya enak~ 🥛', 'susu'], '🍚': ['Nasi hangat… ngenyangin 🍚', 'nasi'] };
K.beriMakan = function (e, btn) {
  var r = btn ? btn.getBoundingClientRect() : { left: S.x, top: S.y + H + 20 };
  var mx = S.x + W / 2 - 8, my2 = S.y + S.jy + H * .4;
  var sx = r.left, sy = r.top; fx(e, sx, sy, mx - sx, my2 - sy, 700, 24);
  K.kenyang = (Date.now() - K.kenyangT > 120000) ? 1 : K.kenyang + 1; K.kenyangT = Date.now(); K.fedLast = Date.now();
  var info = FOOD[e] || ['Enak!', 'makanan'], penuh = K.kenyang >= 4;
  jalankan('makan', async function (my) {
    duduk('sit5'); await par([tw({ yw: 0, pt: -8, st: .06 }, 300)], my); await w(520, my);
    pose('laugh1'); await par([tw({ sc: 1.06 }, 160, E.out)], my);                  // hap! membuka mulut
    cyc(['lick0', 'lick1'], 5); await par([tw({ sc: 1, pt: 4, ln: 3 }, 200)], my);   // mengunyah
    for (var i = 0; i < 4; i++) { await pz({ ln: -3, yw: 6 }, 260, E.sine, my); await pz({ ln: 3, yw: -6 }, 260, E.sine, my); }
    cyc(null); pose('laugh4'); await par([tw({ pt: 0, ln: 0, yw: 0, st: 0 }, 400, E.io)], my);
    say(penuh ? 'Huaah… kenyang! Makasih ya 🥰' : info[0], 3400); hati(4);
    await par([tw({ jy: -8 }, 220, E.out)], my); await par([tw({ jy: 0 }, 220, E.inn)], my); await w(1800, my); await netral(500, my); });
};

// ------------------------------------------------------------------ interaksi
root.addEventListener('click', function () {
  jalankan('sentuh', async function (my) {
    say('Meong! Mau tanya apa? 🐾', 2800); hati(3); pose('laugh4');
    await par([tw({ sq: .16 }, 120, E.out)], my);
    await par([tw({ jy: -26, sq: -.06 }, 260, E.out)], my); await par([tw({ jy: 0 }, 260, E.inn)], my);
    await par([tw({ sq: .12 }, 80)], my); await par([tw({ sq: 0 }, 260, E.back)], my);
    await w(1200, my); });
}, true);
D.addEventListener('pointerdown', function (e) {
  if (K.sembunyi || K.sibuk === 'sambut') return;
  var t = e.target; if (!t || !t.closest) return;
  if (t.closest('#uj-kucing,#uj-gelembung,button,a,input,select,textarea,label,table,[data-c],[role=dialog],[data-testid=stDialog],[data-baseweb],[data-testid=stExpander],iframe,svg')) return;
  var tx = e.clientX - W / 2, ty = e.clientY - H * .7;
  jalankan('panggil', async function (my) {
    say('Datang~ 🐾', 1600); var far = Math.hypot(tx - S.x, ty - S.y);
    if (far > 140) await lompatKe(tx, ty, Math.min(1100, 520 + far), 70, my); else await jalanKe(tx, ty, 900, my);
    pose('wave1'); hati(2); await w(2400, my); });
}, true);
P.addEventListener('resize', function () { if (!K.sibuk) { var h = home(); S.x = h.x; } });
D.addEventListener('visibilitychange', function () { lastT = 0; });

// ------------------------------------------------------------------ mulai
K.jalankan = jalankan; K.AK = AK;
P.__ujKucing = K;
var h0 = home(); S.x = h0.x; S.y = h0.y; lastX = S.x; lastY = S.y; pose('sit0', true);
P.requestAnimationFrame(frame);
if (CFG.sapa) K.sambut(CFG); else { mulaiGiliran(2500); if (CFG.kabar) setTimeout(function () { K.kabarBaru(CFG.kabar); }, 1500); }
