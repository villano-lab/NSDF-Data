/* Small extras for a published student note: a Copy button on every code block (copies the whole block),
   and a click on a picture opens it in its own browser tab, where it can be zoomed. Without JavaScript the
   page reads the same, just without these. Edit this file, not the pages. */
(function () {
  'use strict';

  function fallbackCopy(text) {
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(
        function () { return true; },
        function () { return fallbackCopy(text); }
      );
    }
    return Promise.resolve(fallbackCopy(text));
  }

  function linkPictures() {
    var pics = document.querySelectorAll('.note img');
    for (var i = 0; i < pics.length; i++) {
      var img = pics[i];
      if (img.closest('a')) { continue; }
      var a = document.createElement('a');
      a.href = img.currentSrc || img.src;
      a.target = '_blank';
      a.rel = 'noopener';
      a.title = 'Open the picture in its own tab';
      img.parentNode.insertBefore(a, img);
      a.appendChild(img);
    }
  }

  function init() {
    linkPictures();
    var blocks = document.querySelectorAll('.note pre');
    for (var i = 0; i < blocks.length; i++) {
      var pre = blocks[i];
      if (pre.classList.contains('jupyter-warning') || pre.parentNode.classList.contains('code-wrap')) { continue; }
      var wrap = document.createElement('div');
      wrap.className = 'code-wrap';
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-btn';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy this code block');
      button.addEventListener('click', (function (block, b) {
        return function () {
          copy(block.innerText.replace(/\n$/, '')).then(function (ok) {
            b.textContent = ok ? 'Copied' : 'Select, then Ctrl+C';
            setTimeout(function () { b.textContent = 'Copy'; }, 1600);
          });
        };
      })(pre, button));
      wrap.appendChild(button);
    }
  }

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }
})();
