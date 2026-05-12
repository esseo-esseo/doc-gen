/* doc-gen template library — shared deck behavior
 * - 16:9 resize lock
 * - slide-body 자동 wrap
 * - 화살표/점 네비게이션
 * - 테마 토글
 * - PDF 저장(window.print)
 */

(function () {
  // wrap content after .sh into a scrollable .slide-body
  document.querySelectorAll('.slide').forEach(slide => {
    const sh = slide.querySelector('.sh');
    if (!sh || slide.querySelector('.slide-body')) return;
    const body = document.createElement('div');
    body.className = 'slide-body';
    const children = Array.from(slide.children);
    const afterSh = children.slice(children.indexOf(sh) + 1)
      .filter(el => !el.classList.contains('author-foot'));
    afterSh.forEach(el => body.appendChild(el));
    const foot = slide.querySelector('.author-foot');
    if (foot) slide.insertBefore(body, foot);
    else slide.appendChild(body);
  });

  const slides = document.querySelectorAll('.slide');
  const dotsEl = document.getElementById('dots');
  const ctr = document.getElementById('ctr');
  let cur = 0;

  function resize() {
    const deck = document.getElementById('deck');
    if (!deck) return;
    const vw = window.innerWidth, vh = window.innerHeight;
    let w = vw, h = vw * 9 / 16;
    if (h > vh) { h = vh; w = vh * 16 / 9; }
    deck.style.width = w + 'px';
    deck.style.height = h + 'px';
    document.documentElement.style.setProperty('--dw', w + 'px');
  }
  window.addEventListener('resize', resize);
  resize();

  if (dotsEl && slides.length > 1) {
    slides.forEach((_, i) => {
      const d = document.createElement('div');
      d.className = 'dot' + (i === 0 ? ' active' : '');
      d.onclick = () => show(i);
      dotsEl.appendChild(d);
    });
  }

  function show(n) {
    if (slides.length === 0) return;
    slides[cur].classList.remove('active');
    if (dotsEl && dotsEl.children[cur]) dotsEl.children[cur].classList.remove('active');
    cur = (n + slides.length) % slides.length;
    slides[cur].classList.add('active');
    if (dotsEl && dotsEl.children[cur]) dotsEl.children[cur].classList.add('active');
    if (ctr) ctr.textContent = (cur + 1) + ' / ' + slides.length;
  }
  window.show = show;
  window.go = function (d) { show(cur + d); };

  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') window.go(1);
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') window.go(-1);
  });

  window.toggleTheme = function () { document.body.classList.toggle('dark'); };
  window.savePDF = function () { window.print(); };

  window.addEventListener('beforeprint', () => {
    slides.forEach(s => s.classList.add('active'));
  });
  window.addEventListener('afterprint', () => {
    slides.forEach((s, i) => s.classList.toggle('active', i === cur));
  });
})();
