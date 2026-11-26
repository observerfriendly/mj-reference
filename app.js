'use strict';

var PAGE = 48;
var THUMB_W = 320;

var DB = null;      // {prefix, cats, vers, rows}
var PARAMS = null;
var filtered = [];
var shown = 0;
var activeCat = null;
var query = '';

var el = {
  q: document.getElementById('q'),
  clear: document.getElementById('clear'),
  chips: document.getElementById('chips'),
  grid: document.getElementById('grid'),
  count: document.getElementById('count'),
  empty: document.getElementById('empty'),
  sentinel: document.getElementById('sentinel'),
  codelist: document.getElementById('codelist'),
  toast: document.getElementById('toast'),
  searchwrap: document.getElementById('searchwrap')
};

/* ---------- thumbnails ----------
   Resize proxy first, raw GitHub as the fallback. If wsrv is down or
   blocked, onerror swaps in the full-size original so the app still works. */
function thumbUrl(path) {
  var raw = DB.prefix + path;
  return 'https://wsrv.nl/?url=' + encodeURIComponent(raw.replace(/^https?:\/\//, '')) +
         '&w=' + THUMB_W + '&output=webp&q=72';
}
function rawUrl(path) { return DB.prefix + path; }

/* ---------- clipboard ---------- */
function toast(msg) {
  el.toast.textContent = msg;
  el.toast.classList.add('on');
  clearTimeout(toast._t);
  toast._t = setTimeout(function () { el.toast.classList.remove('on'); }, 1400);
}

function copy(text, label) {
  var done = function () { toast(label || ('Copied  ' + text)); };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text, done); });
  } else {
    fallbackCopy(text, done);
  }
}

function fallbackCopy(text, done) {
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.setAttribute('readonly', '');
  ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0';
  document.body.appendChild(ta);
  ta.select();
  ta.setSelectionRange(0, text.length);
  try { document.execCommand('copy'); done(); } catch (e) { toast('Could not copy'); }
  document.body.removeChild(ta);
}

/* ---------- search ---------- */
function applyFilter() {
  var q = query.trim().toLowerCase();
  var rows = DB.rows;
  var out = [];
  var i, r;
  for (i = 0; i < rows.length; i++) {
    r = rows[i];
    if (activeCat !== null && r[1] !== activeCat) continue;
    if (q && r[0].toLowerCase().indexOf(q) === -1) continue;
    out.push(r);
  }
  filtered = out;
  shown = 0;
  el.grid.textContent = '';
  el.empty.hidden = out.length > 0;
  el.count.textContent = out.length.toLocaleString() +
    (out.length === 1 ? ' keyword' : ' keywords') +
    (activeCat !== null ? '  ·  ' + DB.cats[activeCat] : '');
  renderMore();
}

function renderMore() {
  if (shown >= filtered.length) return;
  var frag = document.createDocumentFragment();
  var end = Math.min(shown + PAGE, filtered.length);
  for (var i = shown; i < end; i++) frag.appendChild(cardFor(filtered[i]));
  el.grid.appendChild(frag);
  shown = end;
}

function cardFor(r) {
  var kw = r[0], path = r[2];

  var card = document.createElement('div');
  card.className = 'card';
  card.setAttribute('role', 'button');
  card.tabIndex = 0;

  var img = document.createElement('img');
  img.className = 'thumb';
  img.loading = 'lazy';
  img.decoding = 'async';
  img.alt = kw;
  img.src = thumbUrl(path);
  img.addEventListener('error', function onerr() {
    img.removeEventListener('error', onerr);
    img.src = rawUrl(path);          // proxy failed — serve the original
  });

  var cap = document.createElement('div');
  cap.className = 'cap';
  var kwEl = document.createElement('div');
  kwEl.className = 'kw';
  kwEl.textContent = kw;
  var catEl = document.createElement('div');
  catEl.className = 'cat';
  catEl.textContent = DB.cats[r[1]];
  cap.appendChild(kwEl);
  cap.appendChild(catEl);

  card.appendChild(img);
  card.appendChild(cap);

  var hit = function (e) { e.preventDefault(); copy(kw); };
  card.addEventListener('click', hit);
  card.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') hit(e);
  });
  return card;
}

/* ---------- chips ---------- */
function buildChips() {
  var all = document.createElement('button');
  all.className = 'chip on';
  all.textContent = 'All';
  all.addEventListener('click', function () { pickCat(null, all); });
  el.chips.appendChild(all);

  DB.cats.forEach(function (c, ix) {
    var b = document.createElement('button');
    b.className = 'chip';
    b.textContent = c;
    b.addEventListener('click', function () { pickCat(ix, b); });
    el.chips.appendChild(b);
  });
}

function pickCat(ix, btn) {
  activeCat = ix;
  Array.prototype.forEach.call(el.chips.children, function (c) { c.classList.remove('on'); });
  btn.classList.add('on');
  window.scrollTo(0, 0);
  applyFilter();
}

/* ---------- codes ---------- */
function buildCodes() {
  var groups = {};
  var order = [];
  PARAMS.parameters.forEach(function (p) {
    if (!groups[p.group]) { groups[p.group] = []; order.push(p.group); }
    groups[p.group].push(p);
  });

  order.forEach(function (g) {
    var wrap = document.createElement('div');
    wrap.className = 'cgroup';
    var h = document.createElement('h2');
    h.textContent = g;
    wrap.appendChild(h);

    groups[g].forEach(function (p) {
      var row = document.createElement('div');
      row.className = 'prow';

      var top = document.createElement('div');
      top.className = 'ptop';

      var flag = document.createElement('button');
      flag.className = 'flag';
      flag.textContent = p.flag;
      flag.addEventListener('click', function () { copy(p.flag); });
      top.appendChild(flag);

      if (p.alias) {
        var al = document.createElement('span');
        al.className = 'alias';
        al.textContent = p.alias;
        top.appendChild(al);
      }
      var nm = document.createElement('span');
      nm.className = 'pname';
      nm.textContent = p.name;
      top.appendChild(nm);
      row.appendChild(top);

      var d = document.createElement('p');
      d.className = 'pdesc';
      d.textContent = p.desc;
      row.appendChild(d);

      var meta = document.createElement('div');
      meta.className = 'meta';
      if (p.values) meta.appendChild(metaBit('Values', p.values));
      if (p.default) meta.appendChild(metaBit('Default', p.default));
      if (meta.children.length) row.appendChild(meta);

      if (p.example) {
        var ex = document.createElement('div');
        ex.className = 'ex';
        ex.textContent = p.example;
        ex.title = 'Tap to copy';
        ex.addEventListener('click', function () { copy(p.example, 'Copied the example'); });
        row.appendChild(ex);
      }

      if (p.note) {
        var n = document.createElement('p');
        n.className = 'note';
        n.textContent = p.note;
        row.appendChild(n);
      }

      wrap.appendChild(row);
    });

    el.codelist.appendChild(wrap);
  });
}

function metaBit(label, val) {
  var s = document.createElement('span');
  s.textContent = label + '  ';
  var b = document.createElement('b');
  b.textContent = val;
  s.appendChild(b);
  return s;
}

/* ---------- tabs ---------- */
Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (t) {
  t.addEventListener('click', function () {
    var view = t.dataset.view;
    Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (x) {
      var on = x === t;
      x.classList.toggle('on', on);
      x.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    document.getElementById('styles').hidden = view !== 'styles';
    document.getElementById('codes').hidden = view !== 'codes';
    el.searchwrap.hidden = view !== 'styles';
    el.chips.hidden = view !== 'styles';
    window.scrollTo(0, 0);
  });
});

/* ---------- search input ---------- */
var deb;
el.q.addEventListener('input', function () {
  query = el.q.value;
  el.clear.hidden = !query;
  clearTimeout(deb);
  deb = setTimeout(applyFilter, 110);
});
el.clear.addEventListener('click', function () {
  el.q.value = ''; query = ''; el.clear.hidden = true; applyFilter(); el.q.focus();
});

/* ---------- infinite scroll ---------- */
if ('IntersectionObserver' in window) {
  new IntersectionObserver(function (es) {
    if (es[0].isIntersecting) renderMore();
  }, { rootMargin: '600px' }).observe(el.sentinel);
} else {
  window.addEventListener('scroll', function () {
    if (window.innerHeight + window.scrollY > document.body.offsetHeight - 700) renderMore();
  });
}

/* ---------- boot ---------- */
Promise.all([
  fetch('data/index.json').then(function (r) { return r.json(); }),
  fetch('data/params.json').then(function (r) { return r.json(); })
]).then(function (res) {
  DB = res[0];
  PARAMS = res[1];
  el.q.placeholder = 'Search ' + DB.rows.length.toLocaleString() + ' keywords';
  buildChips();
  buildCodes();
  applyFilter();
}).catch(function () {
  el.count.textContent = 'Could not load the reference data.';
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  });
}
