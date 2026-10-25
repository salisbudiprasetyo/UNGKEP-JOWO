// Meong: kerangka animasi halus (60 fps). Dijalankan di dalam fungsi (P = window.parent, CFG = pengaturan dari server).
var D = P.document;
if (P.__ujKucing) {
  var K0 = P.__ujKucing; K0.show();
  if (CFG.sapa) K0.sambut(CFG);
  else if (CFG.kabar) K0.kabarBaru(CFG.kabar);
  return;
}
var W = 84, H = 98;
var st = D.createElement('style'); st.id = 'uj-kucing-css'; st.textContent = CFG.css; D.head.appendChild(st);
var root = D.createElement('div'); root.id = 'uj-kucing'; root.setAttribute('data-c', 'k|chat'); root.setAttribute('role', 'button');
root.setAttribute('aria-label', 'Tanya Meong'); root.innerHTML = '<div class="dalam">' + CFG.svg + '</div>'; D.body.appendChild(root);
var dalam = root.firstChild;
var gl = D.createElement('div'); gl.id = 'uj-gelembung'; D.body.appendChild(gl);
var q = function (c) { return root.querySelector('.' + c); };
var el = { body: q('k-body'), head: q('k-head'), tail: q('k-tail'), tail2: q('k-tail2'), pl: q('k-pl'), pr: q('k-pr'), fl: q('k-fl'), fr: q('k-fr'),
  face: q('k-face'), eyes: q('k-eyes'), eyesH: q('k-eyes-h'), mt: q('k-mt'), mo: q('k-mo'), smile: q('k-smile'), shadow: q('k-shadow'),
  ears: q('k-ears'), bl: q('k-bl'), br: q('k-br'), collar: q('k-collar'), bell: q('k-bell'), eye: root.querySelectorAll('.k-eye'), pup: root.querySelectorAll('.k-pup') };

// ------------------------------------------------------------------ keadaan & tween
var S = { x: 0, y: 0, jy: 0, dx: -0.4, sp: 0, ro: 0, sc: 1, by: 0, br: 0, sq: 0, st: 0, hx: 0, hy: 0, hr: 0, tr: 0, tr2: 0,
  pl: 0, pr: 0, mo: 0, ey: 0, hp: 0, sm: 0, bl: 0.25, op: 1, lx: 0, ly: 0 };
var T = [], tok = 0, ph = 0, blink = 0, nextBlink = 2500, vx = 0, vy = 0, lastX = 0, lastY = 0, lastT = 0, nowS = 0;
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

var K = { el: root, gl: gl, sembunyi: false, kenyang: 0, kenyangT: 0, fedLast: 0, lastAct: '', timer: 0, wt: 0 };
function home() { return { x: Math.max(0, (P.innerWidth || 360) - W - 6), y: 8 }; }
function maxY() { return Math.max(60, (P.innerHeight || 640) - H - 6); }
function rnd(a, b) { return a + Math.random() * (b - a); }

// ------------------------------------------------------------------ gambar tiap frame
function apply(dt) {
  var s = S, t = nowS;
  // kecepatan → langkah kaki
  var sp = Math.min(1, Math.sqrt(vx * vx + vy * vy) / 70);
  ph += dt * (5 + sp * 9);
  var step = Math.sin(ph), lift = Math.max(0, Math.cos(ph));
  var bob = Math.abs(Math.sin(ph)) * 2.6 * sp;
  var breathe = Math.sin(t * 1.9) * 0.012 + 0.0;
  root.style.opacity = s.op;
  root.style.transform = 'translate3d(' + s.x.toFixed(2) + 'px,' + (s.y + s.jy).toFixed(2) + 'px,0)';
  dalam.style.transform = 'rotateY(' + (s.dx * 24 + s.sp).toFixed(2) + 'deg) rotateZ(' + s.ro.toFixed(2) + 'deg) scale(' + s.sc + ')';
  // bayangan mengecil saat melompat
  var hh = Math.min(1, Math.abs(s.jy) / 90);
  el.shadow.style.transform = 'scale(' + (1 - hh * .5).toFixed(3) + ',' + (1 - hh * .4).toFixed(3) + ')';
  el.shadow.style.opacity = (1 - hh * .55).toFixed(3);
  var sqx = 1 + s.sq * .55, sqy = 1 - s.sq + breathe + s.st * .12;
  el.body.style.transform = 'translate(0px,' + (s.by - bob).toFixed(2) + 'px) rotate(' + (s.br + sp * s.dx * 3).toFixed(2) + 'deg) scale(' + sqx.toFixed(3) + ',' + sqy.toFixed(3) + ')';
  el.head.style.transform = 'translate(' + (s.hx + s.dx * 3).toFixed(2) + 'px,' + (s.hy - bob * .6 - s.st * 6).toFixed(2) + 'px) rotate(' + (s.hr - sp * s.dx * 2).toFixed(2) + 'deg) scale(' + (1 + s.sq * .15).toFixed(3) + ')';
  el.face.style.transform = 'translate(' + (s.dx * 7 + s.lx).toFixed(2) + 'px,' + (s.ly).toFixed(2) + 'px)';
  el.ears.style.transform = 'translate(' + (s.dx * 2).toFixed(2) + 'px,' + (Math.sin(t * .9) > .985 ? -1 : 0) + 'px)';
  var sway = Math.sin(t * 2.1) * (6 + sp * 10), sway2 = Math.sin(t * 2.1 - 1.1) * (10 + sp * 12);
  el.tail.style.transform = 'rotate(' + (s.tr + sway - sp * s.dx * 10).toFixed(2) + 'deg)';
  el.tail2.style.transform = 'rotate(' + (s.tr2 + sway2).toFixed(2) + 'deg)';
  el.pl.style.transform = 'translate(0px,' + (-lift * 3 * sp).toFixed(2) + 'px) rotate(' + (s.pl + step * 16 * sp).toFixed(2) + 'deg)';
  el.pr.style.transform = 'translate(0px,' + (-Math.max(0, -Math.cos(ph)) * 3 * sp).toFixed(2) + 'px) rotate(' + (s.pr - step * 16 * sp).toFixed(2) + 'deg)';
  el.fl.style.transform = 'translate(' + (step * 6 * sp).toFixed(2) + 'px,' + (-lift * 4 * sp).toFixed(2) + 'px)';
  el.fr.style.transform = 'translate(' + (-step * 6 * sp).toFixed(2) + 'px,' + (-Math.max(0, -Math.cos(ph)) * 4 * sp).toFixed(2) + 'px)';
  // mata & mulut
  var cl = Math.max(s.ey, blink);
  var open = 1 - cl, happy = s.hp;
  for (var i = 0; i < el.eye.length; i++) el.eye[i].style.transform = 'scaleY(' + (Math.max(.05, open) * (1 - happy)).toFixed(3) + ')';
  el.eyes.style.opacity = (1 - happy).toFixed(3);
  el.eyesH.style.opacity = happy.toFixed(3);
  var m = Math.min(1, s.mo);
  el.mo.style.opacity = (m > .03 ? 1 : 0); el.mo.style.transform = 'scaleY(' + Math.max(.12, m).toFixed(3) + ')';
  el.mt.style.opacity = (m > .03 || s.sm > .5) ? 0 : 1;
  el.smile.style.opacity = (m > .03 ? 0 : Math.min(1, s.sm)).toFixed(3);
  el.bl.style.opacity = el.br.style.opacity = Math.min(.9, s.bl).toFixed(3);
  el.bell.style.transform = 'rotate(' + (Math.sin(t * 6) * (sp * 8 + Math.abs(vy) * .02)).toFixed(2) + 'deg)';
  el.bell.style.transformOrigin = '60px 92px';
  // gelembung mengikuti kucing
  if (gl.classList.contains('tampil')) posGl();
}
function posGl() {
  var gw = gl.offsetWidth, gh = gl.offsetHeight, vw = P.innerWidth || 360;
  var cx = S.x + W / 2, below = S.y + S.jy < 110;
  var gx = Math.min(Math.max(6, cx - gw / 2), vw - gw - 6);
  var gy = below ? S.y + S.jy + H + 8 : S.y + S.jy - gh - 10;
  gl.style.transform = 'translate3d(' + gx.toFixed(1) + 'px,' + Math.max(4, gy).toFixed(1) + 'px,0)';
  gl.classList.toggle('atas', !below);
  gl.style.setProperty('--ekor', Math.min(gw - 22, Math.max(10, cx - gx - 6)) + 'px');
}
function frame(now) {
  var dt = Math.min(.05, (now - (lastT || now)) / 1000); lastT = now; nowS = now / 1000;
  // tween
  for (var i = T.length - 1; i >= 0; i--) {
    var tk = T[i], p = Math.min(1, (now - tk.t0) / tk.dur), e = tk.ease(p);
    for (var k in tk.to) S[k] = tk.from[k] + (tk.to[k] - tk.from[k]) * e;
    if (p >= 1) { T.splice(i, 1); tk.res(); }
  }
  if (dt > 0) { vx = vx * .7 + ((S.x - lastX) / dt) * .3; vy = vy * .7 + ((S.y - lastY) / dt) * .3; }
  lastX = S.x; lastY = S.y;
  // kedip acak
  if (now > nextBlink) { blink = 1; nextBlink = now + rnd(2800, 5500); setTimeout(function () { blink = 0; }, 130); }
  if (!K.sembunyi && !D.hidden) apply(dt);
  P.requestAnimationFrame(frame);
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
function hati(n) { for (var i = 0; i < (n || 3); i++) (function (i) { setTimeout(function () { fx('❤️', S.x + 20 + rnd(0, 40), S.y + S.jy, rnd(-14, 14), -rnd(36, 60), 1200, 16 + rnd(0, 6)); }, i * 180); })(i); }
function menghadap(d, ms, my) { return pz({ dx: d }, ms || 320, E.io, my); }
function ke(x, y, ms, my, e) { return pz({ x: Math.max(0, Math.min((P.innerWidth || 360) - W, x)), y: Math.max(0, Math.min(maxY(), y)) }, ms, e || E.sine, my); }
async function jalanKe(x, y, ms, my) { await menghadap(x < S.x ? -1 : 1, 260, my); await ke(x, y, ms, my); }
async function lompatKe(x, y, ms, tinggi, my) {
  // merunduk → melesat → mendarat memantul (semua mulus, tidak patah-patah)
  var d = x > S.x ? 1 : -1; tinggi = tinggi || 46; ms = ms || 640;
  await par([tw({ dx: d }, 200), tw({ sq: .2, by: 5, hy: 3, tr: -10, pl: 18, pr: -18 }, 150, E.out)], my);
  var ty = Math.max(0, Math.min(maxY(), y));
  var a = tw({ x: Math.max(0, Math.min((P.innerWidth || 360) - W, x)), y: ty }, ms, E.sine);
  var b = tw({ sq: -.1, by: -2, pl: 55, pr: -55, tr: 20, hy: -2 }, ms * .35, E.out);
  var up = tw({ jy: -tinggi }, ms * .5, E.out).then(function () { return tw({ jy: 0 }, ms * .5, E.inn); });
  await par([a, b, up], my);
  await par([tw({ sq: .22, by: 5, pl: 10, pr: -10, tr: 0 }, 110, E.out)], my);
  await par([tw({ sq: 0, by: 0, hy: 0, pl: 0, pr: 0, tr: 0 }, 260, E.back)], my);
}
async function netral(ms, my) { await pz({ by: 0, br: 0, sq: 0, st: 0, hx: 0, hy: 0, hr: 0, tr: 0, tr2: 0, pl: 0, pr: 0, mo: 0, ey: 0, hp: 0, sm: 0, ro: 0, lx: 0, ly: 0, sc: 1, jy: 0, sp: 0 }, ms || 380, E.io, my); }
async function pulang(my) { var h = home(); if (Math.abs(S.x - h.x) > 3 || Math.abs(S.y - h.y) > 3) {
  if (S.y > h.y + 120 || Math.abs(S.x - h.x) > 160) { await lompatKe(h.x, h.y, 800, 70, my); } else { await jalanKe(h.x, h.y, 800, my); } }
  await par([tw({ dx: -.45 }, 420), netral(420, my)], my); }

// ------------------------------------------------------------------ 25 aktivitas
var AK = {};
AK.duduk_santai = async function (my) { await pz({ hr: 4, tr: 8 }, 900, E.io, my); await w(2200, my); await pz({ hr: -4 }, 900, E.io, my); await w(1200, my); };
AK.menguap = async function (my) { await par([tw({ hy: -3, hr: -7, mo: 1, ey: 1, st: .2 }, 900, E.io)], my); await w(1400, my); await par([tw({ mo: 0, ey: 0, hy: 0, hr: 0, st: 0 }, 700, E.io)], my); await pz({ sm: 1, bl: .7 }, 300, E.io, my); await w(600, my); };
AK.jilat_kaki = async function (my) {
  await par([tw({ pr: -128, hr: 12, hy: 5, ey: .5 }, 700, E.io)], my);
  for (var i = 0; i < 4; i++) { await pz({ mo: .45, pr: -134 }, 260, E.sine, my); await pz({ mo: .05, pr: -122 }, 260, E.sine, my); }
  await par([tw({ pr: 0, hr: 0, hy: 0, ey: 0, mo: 0 }, 650, E.io)], my); };
AK.cuci_muka = async function (my) {
  await par([tw({ pl: 150, pr: -150, hy: 4, ey: .6 }, 700, E.io)], my);
  for (var i = 0; i < 5; i++) { await par([tw({ pl: 158, pr: -142, hr: 5 }, 300, E.sine)], my); await par([tw({ pl: 142, pr: -158, hr: -5 }, 300, E.sine)], my); }
  await par([tw({ pl: 0, pr: 0, hy: 0, hr: 0, ey: 0 }, 700, E.io)], my); await pz({ sm: 1 }, 300, E.io, my); await w(500, my); };
AK.garuk_telinga = async function (my) {
  await par([tw({ hr: -14, pr: -168, ey: .5, mo: .1 }, 650, E.io)], my);
  for (var i = 0; i < 7; i++) await pz({ pr: -160 - (i % 2) * 14 }, 110, E.sine, my);
  await par([tw({ hr: 0, pr: 0, ey: 0, mo: 0 }, 600, E.io)], my); };
AK.melambai = async function (my) {
  say('Hai hai! 👋', 3200); await par([tw({ sm: 1, hp: 1, bl: .6, pr: -150, hr: 6, dx: -.2 }, 520, E.back)], my);
  for (var i = 0; i < 5; i++) { await pz({ pr: -128 }, 230, E.sine, my); await pz({ pr: -158 }, 230, E.sine, my); }
  await par([tw({ pr: 0, hr: 0, hp: 0, sm: 0 }, 520, E.io)], my); };
AK.mengeong = async function (my) {
  for (var i = 0; i < 2; i++) { say(i ? 'Meooong~' : 'Meong!', 1500); await par([tw({ mo: 1, hy: -3, st: .1, hr: -4 }, 220, E.out)], my); await w(520, my); await par([tw({ mo: 0, hy: 0, st: 0, hr: 0 }, 320, E.io)], my); await w(380, my); }
};
AK.minta_makan = async function (my) {
  if (K.kenyang >= 4 && Date.now() - K.kenyangT < 120000) { say('Aku kenyang banget… 🥱', 3000); await par([tw({ ey: .7, sq: .06, hr: 6 }, 800, E.io)], my); await w(2400, my); await netral(500, my); return; }
  await par([tw({ pl: 22, pr: -22, hy: -2, hr: -5, bl: .6 }, 500, E.io)], my);
  say('Aku lapar 🍗 kasih makan dong…', 12000, true);
  for (var i = 0; i < 7; i++) { await par([tw({ mo: .8, hr: -7, hy: -3 }, 260, E.out)], my); await pz({ mo: 0, hr: 5, hy: 0 }, 420, E.io, my); await w(900, my); }
  diam(); await netral(500, my); say('Hmm… ya sudah 🙁', 2600); await w(1800, my); };
AK.tidur = async function (my) {
  await par([tw({ sq: .1, by: 7, hy: 9, hr: 14, ey: 1, tr: 40, tr2: 30, pl: 6, pr: -6, sc: .98 }, 1500, E.io)], my);
  var i = 0; while (i < 3) { say(['Zzz…', 'Zzz… zzz…', 'Zzzz~'][i], 2400); await w(2600, my); i++; }
  diam(); await par([tw({ ey: 0 }, 500, E.io)], my); await pz({ st: .25, mo: .5, hr: -8, hy: -2 }, 800, E.io, my); await pz({ mo: 0 }, 400, E.io, my); await netral(600, my); };
AK.peregangan = async function (my) {
  await par([tw({ br: 15, hy: 12, hr: -8, tr: -34, tr2: -22, ey: .8, mo: .3, pl: -20, pr: 20, sq: -.04 }, 1100, E.io)], my);
  await w(1600, my); await par([tw({ br: 0, hy: 0, hr: 0, tr: 0, tr2: 0, ey: 0, mo: 0, pl: 0, pr: 0, sq: 0, st: .35 }, 900, E.io)], my);
  await w(400, my); await netral(500, my); };
AK.jalan_santai = async function (my) {
  var h = home(), tx = Math.max(10, h.x - rnd(140, 260)); await jalanKe(tx, h.y, 2600, my);
  await par([tw({ dx: .6, hr: 5 }, 400)], my); await w(700, my); await par([tw({ dx: -.6, hr: -5 }, 500)], my); await w(700, my); };
AK.lari_keliling = async function (my) {
  say('Wuuush! 💨', 1800); await jalanKe(6, home().y + 10, 1250, my); await par([tw({ sq: .12 }, 140)], my); await w(250, my);
  await par([tw({ dx: 1, sq: 0 }, 180)], my); await ke(home().x, home().y, 1250, my); };
AK.lompat_ditempat = async function (my) { var x0 = S.x, y0 = S.y; for (var i = 0; i < 3; i++) { await lompatKe(x0, y0, 560, 36 + i * 8, my); await w(120, my); } await pz({ sm: 1, hp: 1 }, 250, E.io, my); await w(500, my); };
AK.lompat_jauh = async function (my) {
  var h = home(); await lompatKe(Math.max(8, h.x - rnd(120, 230)), h.y + rnd(80, 190), 900, 88, my);
  await par([tw({ dx: 1, sm: 1, hp: .7 }, 300)], my); await w(900, my); await par([tw({ hp: 0 }, 250)], my); await lompatKe(h.x, h.y, 950, 96, my); };
AK.kejar_ekor = async function (my) {
  await par([tw({ hy: 5, ey: 0 }, 300)], my);
  await par([tw({ sp: 720, tr: 20, br: 4 }, 2100, E.io), tw({ hr: 10 }, 400)], my); S.sp = 0; await netral(500, my); await pz({ ey: .5, hr: 8 }, 300, E.io, my); await w(500, my); await netral(500, my); };
AK.berguling = async function (my) {
  await par([tw({ sq: .12, hy: 4 }, 200)], my); await par([tw({ ro: 360, jy: -6, sq: .1, pl: 40, pr: -40, hp: 1 }, 1250, E.io)], my);
  S.ro = 0; await netral(450, my); await pz({ sm: 1, hp: 1, bl: .7 }, 250, E.io, my); await w(500, my); };
AK.menoleh = async function (my) {
  say('Ada apa ya? 👀', 2800); await par([tw({ dx: -1, hr: -6, hx: -2 }, 600)], my); await w(500, my);
  await par([tw({ dx: 1, hr: 7, hx: 2 }, 800)], my); await w(500, my); await par([tw({ dx: 0, hr: 0, hx: 0, ly: -2 }, 600)], my); await w(500, my); };
AK.mengintip = async function (my) {
  var vw = P.innerWidth || 360; await par([tw({ dx: -1 }, 250)], my);
  await pz({ x: vw - W * .32 }, 900, E.io, my); await par([tw({ dx: -1, hr: -10, hy: 2, bl: .6 }, 400)], my); await w(1700, my);
  await par([tw({ ey: .8, sm: 1 }, 250)], my); await w(500, my); await pz({ x: home().x }, 900, E.io, my); await netral(450, my); };
AK.menari = async function (my) {
  say('♪ ♫', 4600); await par([tw({ sm: 1, hp: 1, bl: .7 }, 300)], my);
  for (var i = 0; i < 5; i++) { var s = i % 2 ? 1 : -1;
    await par([tw({ br: 7 * s, hr: -6 * s, by: -3, pl: s > 0 ? 70 : 8, pr: s > 0 ? -8 : -70, tr: 20 * s, tr2: 24 * s }, 430, E.sine)], my);
    await par([tw({ by: 0 }, 140, E.io)], my); }
  await netral(600, my); };
AK.kupu_kupu = async function (my) {
  var vw = P.innerWidth || 360, h = home();
  var kp = D.createElement('div'); kp.className = 'uj-fx'; kp.textContent = '🦋'; kp.style.fontSize = '22px'; D.body.appendChild(kp);
  var t0 = P.performance.now(), dur = 3600, sx = h.x - 190, sy = h.y + 150;
  var kx = function (p) { return sx + (S.x - sx + 10) * p + Math.sin(p * 9) * 26; }, ky = function (p) { return sy + (S.y - sy + 8) * p + Math.cos(p * 7) * 20; };
  var run = true; (function f(now) { var p = Math.min(1, (now - t0) / dur); kp.style.transform = 'translate3d(' + kx(p) + 'px,' + ky(p) + 'px,0) rotate(' + Math.sin(p * 30) * 14 + 'deg)'; if (run && p < 1) P.requestAnimationFrame(f); else kp.remove(); })(t0);
  try {
    await par([tw({ dx: -.8, hy: 2, ey: 0, tr: 12 }, 400)], my);
    for (var i = 0; i < 6; i++) { var p2 = Math.min(1, (i + 1) / 7); await par([tw({ lx: (kx(p2) - S.x - 40) * .05, ly: (ky(p2) - S.y - 40) * .06, hr: (kx(p2) - S.x - 40) * .04 }, 520, E.sine)], my); }
    await par([tw({ sq: .18, by: 4, tr: -10 }, 220)], my); say('Tangkap! 🦋', 1800);
    await lompatKe(S.x - 10, S.y + 6, 420, 54, my); run = false; kp.remove(); await w(600, my);
  } finally { run = false; kp.remove(); }
  await netral(500, my); };
AK.mengendus = async function (my) {
  var h = home(); await par([tw({ dx: -1, hy: 10, hr: -8, sq: .04 }, 500)], my);
  for (var i = 0; i < 3; i++) { await par([tw({ x: S.x - 22, lx: -3 }, 600, E.sine), tw({ hy: 12 }, 300, E.sine)], my); await par([tw({ hy: 7 }, 300, E.sine)], my); }
  await par([tw({ hy: 0, hr: 0, sq: 0, lx: 0 }, 500)], my); say('Wangi ayam goreng! 🍗', 2600); await w(1200, my); };
AK.kaget = async function (my) {
  say('!?', 1800); await par([tw({ sq: -.14, st: .3, ey: 0, tr: 30, tr2: 20, pl: 50, pr: -50, mo: .5, hy: -4 }, 120, E.out)], my);
  await par([tw({ jy: -50 }, 260, E.out), tw({ x: Math.min((P.innerWidth || 360) - W, S.x + 24) }, 520, E.sine)], my); await par([tw({ jy: 0 }, 260, E.inn)], my);
  await par([tw({ sq: .2 }, 90)], my); await w(700, my); await netral(700, my); say('Ternyata cuma angin 😅', 2600); await w(1500, my); };
AK.senyum_ceria = async function (my) {
  await par([tw({ sm: 1, hp: 1, bl: .85, hr: 7, by: -2 }, 500, E.back)], my); hati(5); await w(900, my);
  await par([tw({ hr: -7, tr: 22 }, 500, E.sine)], my); await w(900, my); await netral(600, my); };
AK.mengantuk = async function (my) {
  say('Hoaaam… 🥱', 2500);
  for (var i = 0; i < 3; i++) { await par([tw({ hy: 9, hr: 10, ey: .9 }, 1100, E.io)], my); await par([tw({ hy: 0, hr: 0, ey: 0 }, 260, E.out)], my); await w(160, my); }
  await par([tw({ mo: .9, ey: 1, hy: -3 }, 600)], my); await w(900, my); await netral(500, my); };
AK.berdiri = async function (my) {
  await par([tw({ st: 1, hy: -4, pl: 38, pr: -38, tr: -14, bl: .5 }, 800, E.back)], my); say('Ta-daaa! ✨', 2600);
  for (var i = 0; i < 3; i++) { await par([tw({ br: 4, pl: 60, pr: -20 }, 380, E.sine)], my); await par([tw({ br: -4, pl: 20, pr: -60 }, 380, E.sine)], my); }
  await netral(700, my); };
AK.turun_naik = async function (my) {
  var h = home(), by = maxY(); say('Jalan-jalan dulu ya~', 2500);
  await lompatKe(Math.max(8, h.x - 70), h.y + 150, 800, 70, my); await lompatKe(Math.max(8, h.x - 150), by - 60, 900, 70, my);
  await jalanKe(Math.max(8, h.x - 280), by, 2000, my); await par([tw({ dx: 1, hr: 5 }, 400)], my); await w(600, my);
  await jalanKe(Math.max(8, h.x - 120), by, 1700, my); await lompatKe(h.x, h.y, 1100, 110, my); };

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
  stopAll(); var my = tok; diam(); K.lastAct = nama || K.lastAct; K.sibuk = nama || 'x';
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
    var h = home(); S.x = -W; S.y = h.y + 62; S.op = 0; S.dx = 1; S.sc = 1;
    await par([tw({ op: 1, sm: 1, hp: 1, bl: .85 }, 400, E.out), tw({ x: 4 }, 500, E.out)], my);
    say(c.sapa, 5200); hati(3); await w(800, my);
    var vw = P.innerWidth || 360, goal = h.x, n = Math.max(3, Math.round((goal - S.x) / 78));
    for (var i = 1; i <= n; i++) {
      var tx = S.x + (goal - S.x) / (n - i + 1);
      await lompatKe(tx, i === n ? h.y : h.y + 62 + (i % 2 ? 8 : -2), 640, 34 + (i % 3) * 10, my);
      S.hp = 1; S.sm = 1; await par([tw({ hp: 1, sm: 1, bl: .85 }, 120)], my);
    }
    await par([tw({ dx: -.3, sm: 1, hp: 1 }, 400)], my);
    say('Halo ' + (c.nama || '') + '! Mau pesan apa hari ini? 🍛', 5500);
    await par([tw({ pr: -150, hr: 6 }, 520, E.back)], my);
    for (var k = 0; k < 6; k++) { await pz({ pr: -126 }, 230, E.sine, my); await pz({ pr: -160 }, 230, E.sine, my); }
    await par([tw({ pr: 0, hr: 0, hp: 0, sm: 1 }, 600, E.io)], my);
    if (c.kabar) { say(c.kabar, 6000); await w(2500, my); }
    await w(1200, my); await netral(500, my);
  });
};

// ------------------------------------------------------------------ memberi makan
var FOOD = { '🍗': ['Nyam nyam! Ayam goreng kriuk 😻', 'ayam'], '🍤': ['Udang goreng! Gurih banget~ 😋', 'udang'], '🐟': ['Ikan! Favoritkuuu 🐟💕', 'ikan'],
  '🥩': ['Dagingnya empuk! 😍', 'daging'], '🥛': ['Slurp… susunya enak~ 🥛', 'susu'], '🍚': ['Nasi hangat… ngenyangin 🍚', 'nasi'] };
K.beriMakan = function (e, btn) {
  var r = btn ? btn.getBoundingClientRect() : { left: S.x, top: S.y + H + 20 };
  var mx = S.x + W / 2 - 8, my2 = S.y + S.jy + H * .42;
  var sx = r.left, sy = r.top; fx(e, sx, sy, mx - sx, my2 - sy, 700, 24);
  K.kenyang = (Date.now() - K.kenyangT > 120000) ? 1 : K.kenyang + 1; K.kenyangT = Date.now(); K.fedLast = Date.now();
  var info = FOOD[e] || ['Enak!', 'makanan'], penuh = K.kenyang >= 4;
  jalankan('makan', async function (my) {
    await par([tw({ dx: 0, hy: 4, mo: .1, hp: 0, sm: 0, pl: 0, pr: 0 }, 300)], my); await w(520, my);
    await par([tw({ mo: 1, hy: 2 }, 160, E.out)], my); await par([tw({ mo: .05, hy: 5, sq: .05 }, 160, E.in || E.io)], my);
    for (var i = 0; i < 5; i++) { await par([tw({ mo: .65, hy: 3, hr: i % 2 ? 4 : -4 }, 190, E.sine)], my); await par([tw({ mo: .06, hy: 6, hr: i % 2 ? -3 : 3 }, 190, E.sine)], my); }
    await par([tw({ mo: 0, hy: 0, hr: 0, sq: 0, hp: 1, sm: 1, bl: .9 }, 400, E.io)], my);
    say(penuh ? 'Huaah… kenyang! Makasih ya 🥰' : info[0], 3400); hati(4);
    await par([tw({ by: -3, tr: 20 }, 300, E.back)], my); await par([tw({ by: 0 }, 300)], my); await w(1800, my);
    await par([tw({ hp: 0, sm: 0 }, 300)], my); await netral(500, my);
  });
};

// ------------------------------------------------------------------ interaksi
root.addEventListener('click', function () {
  // pengendali ketukan halaman membuka jendela obrolan; di sini kucing bereaksi
  jalankan('sentuh', async function (my) {
    say('Meong! Mau tanya apa? 🐾', 2800); hati(3);
    await par([tw({ sm: 1, hp: 1, bl: .85, sq: .16, by: 4 }, 120, E.out)], my);
    await par([tw({ jy: -26, sq: -.06, by: -2 }, 260, E.out)], my); await par([tw({ jy: 0 }, 260, E.inn)], my);
    await par([tw({ sq: .12 }, 80)], my); await par([tw({ sq: 0, by: 0 }, 260, E.back)], my);
    await w(1200, my); await par([tw({ hp: 0, sm: 0 }, 300)], my);
  });
}, true);
D.addEventListener('pointerdown', function (e) {
  if (K.sembunyi || K.sibuk === 'sambut') return;
  var t = e.target; if (!t || !t.closest) return;
  if (t.closest('#uj-kucing,#uj-gelembung,button,a,input,select,textarea,label,table,[data-c],[role=dialog],[data-testid=stDialog],[data-baseweb],[data-testid=stExpander],iframe,svg')) return;
  var tx = e.clientX - W / 2, ty = e.clientY - H * .7;
  jalankan('panggil', async function (my) {
    say('Datang~ 🐾', 1600); var far = Math.hypot(tx - S.x, ty - S.y);
    if (far > 140) await lompatKe(tx, ty, Math.min(1100, 520 + far), 70, my); else await jalanKe(tx, ty, 900, my);
    await par([tw({ dx: 0, sm: 1, hp: .7 }, 300)], my); hati(2); await w(2400, my); await par([tw({ hp: 0 }, 300)], my);
  });
}, true);
P.addEventListener('resize', function () { if (!K.sibuk) { var h = home(); S.x = h.x; } });
D.addEventListener('visibilitychange', function () { lastT = 0; });

// ------------------------------------------------------------------ mulai
P.__ujKucing = K;
K.sambut2 = K.sambut;
var h0 = home(); S.x = h0.x; S.y = h0.y; lastX = S.x; lastY = S.y;
P.requestAnimationFrame(frame);
var reduce = P.matchMedia && P.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (CFG.sapa) K.sambut(CFG); else { mulaiGiliran(2500); if (CFG.kabar) setTimeout(function () { K.kabarBaru(CFG.kabar); }, 1500); }
