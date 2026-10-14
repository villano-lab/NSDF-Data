/* Copy buttons for the guides and quick-sheets (docs/students, docs/developers).

   Every command block gets a Copy button on each command line, and a Copy all button when it has
   more than one command. A trailing "# comment" is left out of what is copied, because Windows
   cmd does not treat # as a comment. A Python block is one piece of code, so it gets one Copy
   button for the whole block. Without JavaScript the page still reads fine; it just has no buttons.
   Generated pages load this file; edit it here, not in the HTML. */
(function () {
  'use strict';

  var live = null;

  function announce(message) {
    if (!live) {
      live = document.createElement('div');
      live.className = 'sr-only';
      live.setAttribute('role', 'status');
      live.setAttribute('aria-live', 'polite');
      document.body.appendChild(live);
    }
    live.textContent = '';
    setTimeout(function () { live.textContent = message; }, 30);
  }

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

  function flash(button, ok, idleLabel) {
    button.textContent = ok ? 'Copied' : 'Select, then Ctrl+C';
    button.classList.toggle('done', ok);
    announce(ok ? 'Copied to the clipboard.' : 'Could not copy. Select the text and press Control C.');
    setTimeout(function () {
      button.textContent = idleLabel;
      button.classList.remove('done');
    }, 1600);
  }

  function makeButton(label, ariaLabel, getText, extraClass) {
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy ' + (extraClass || '');
    button.textContent = label;
    button.setAttribute('aria-label', ariaLabel);
    button.addEventListener('click', function () {
      copy(getText()).then(function (ok) { flash(button, ok, label); });
    });
    return button;
  }

  /* "git status   # only your note?" -> "git status" */
  function commandOf(line) {
    return line.replace(/\s+#(\s.*)?$/, '').replace(/\s+$/, '');
  }

  function isCommentOnly(line) {
    return /^\s*#/.test(line);
  }

  function enhance(pre) {
    var code = pre.querySelector('code') || pre;
    var text = code.textContent.replace(/\n+$/, '');
    var isPython = /\bpython\b/.test(pre.className + ' ' + code.className);

    var wrap = document.createElement('div');
    wrap.className = 'codeblock';
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);

    if (isPython) {
      var bar = document.createElement('div');
      bar.className = 'codebar';
      bar.appendChild(document.createElement('span')).textContent = 'Python';
      bar.appendChild(makeButton('Copy', 'Copy this code', function () { return text; }));
      wrap.insertBefore(bar, pre);
      return;
    }

    var commands = [];
    code.textContent = '';
    text.split('\n').forEach(function (line) {
      var row = document.createElement('span');
      row.className = 'cl';
      var shown = document.createElement('span');
      shown.className = 'ct';
      shown.textContent = line.length ? line : ' ';
      row.appendChild(shown);
      var command = commandOf(line);
      if (command && !isCommentOnly(line)) {
        commands.push(command);
        row.appendChild(makeButton('Copy', 'Copy this line: ' + command, function () { return command; }, 'copy-line'));
      } else {
        row.classList.add('nocopy');
      }
      code.appendChild(row);
    });

    if (commands.length > 1) {
      var head = document.createElement('div');
      head.className = 'codebar';
      head.appendChild(document.createElement('span')).textContent = commands.length + ' commands';
      head.appendChild(makeButton('Copy all', 'Copy all ' + commands.length + ' commands',
        function () { return commands.join('\n'); }));
      wrap.insertBefore(head, pre);
    }
  }

  /* The text of a quote block, with its numbered steps written out as "1. ...", for pasting. */
  function quoteText(quote) {
    var parts = [];
    for (var i = 0; i < quote.children.length; i++) {
      var el = quote.children[i];
      var tag = el.tagName;
      if (tag === 'OL' || tag === 'UL') {
        var lines = [];
        for (var j = 0; j < el.children.length; j++) {
          lines.push((tag === 'OL' ? (j + 1) + '. ' : '- ') + el.children[j].textContent.replace(/\s+/g, ' ').trim());
        }
        parts.push(lines.join('\n'));
      } else {
        parts.push(el.textContent.replace(/\s+/g, ' ').trim());
      }
    }
    return parts.join('\n\n');
  }

  function enhanceQuote(quote) {
    var bar = document.createElement('div');
    bar.className = 'codebar';
    bar.appendChild(document.createElement('span')).textContent = 'Text to paste';
    bar.appendChild(makeButton('Copy', 'Copy this text', function () { return quoteText(quote); }));
    quote.parentNode.insertBefore(bar, quote);
  }

  /* A guide with a version for each computer (Windows, macOS, Linux) is one page with a switch.
     The page picks the visitor's system from the browser; the visitor can change it, and the choice is
     remembered in this browser (never sent anywhere). A link such as setup.html?os=macos picks one
     directly, and so does a link to a heading that lives in one of the versions. Without JavaScript the
     page shows all three versions, one after the other. */
  function osSwitch() {
    var bar = document.querySelector('.os-switch');
    if (!bar) { return; }
    var systems = ['windows', 'macos', 'linux'];
    var names = { windows: 'Windows', macos: 'macOS', linux: 'Linux' };
    var variants = document.querySelectorAll('.os-variant');
    var buttons = bar.querySelectorAll('button[data-os]');
    var pdf = bar.querySelector('.os-pdf');
    var prompt = document.querySelector('.os-prompt');
    var KEY = 'nsdf-os';

    function valid(v) { return systems.indexOf(v) !== -1 ? v : null; }

    function fromUrl() {
      var m = /[?&]os=([a-z]+)/i.exec(location.search);
      return m ? valid(m[1].toLowerCase()) : null;
    }

    function fromHash() {
      if (!location.hash) { return null; }
      var target = null;
      try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (e) { return null; }
      var variant = target && target.closest ? target.closest('.os-variant') : null;
      return variant ? valid(variant.getAttribute('data-os')) : null;
    }

    function stored() {
      try { return valid(localStorage.getItem(KEY)); } catch (e) { return null; }
    }

    /* Best guess at the visitor's computer; null when it is not one of the three (a phone, a tablet, a Chromebook). */
    function detect() {
      var ua = navigator.userAgent || '';
      var p = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || '';
      if (/iPhone|iPad|iPod|Android|CrOS/i.test(ua)) { return null; }
      if (/^Win/i.test(p)) { return 'windows'; }
      if (/^Mac/i.test(p)) { return navigator.maxTouchPoints > 1 ? null : 'macos'; }
      if (/Linux/i.test(p)) { return 'linux'; }
      return null;
    }

    function show(os) {
      for (var i = 0; i < variants.length; i++) {
        var on = variants[i].getAttribute('data-os') === os;
        if (on) { variants[i].classList.add('active'); } else { variants[i].classList.remove('active'); }
      }
      for (var j = 0; j < buttons.length; j++) {
        buttons[j].setAttribute('aria-pressed', buttons[j].getAttribute('data-os') === os ? 'true' : 'false');
      }
      if (pdf) {
        var base = pdf.getAttribute('data-base');
        if (os) {
          pdf.href = base + '-' + os + '.pdf';
          pdf.textContent = 'PDF for ' + names[os] + ' (download or print)';
          pdf.hidden = false;
        } else {
          pdf.hidden = true;
        }
      }
      if (prompt) { prompt.hidden = !!os; }
    }

    for (var b = 0; b < buttons.length; b++) {
      buttons[b].addEventListener('click', function () {
        var os = this.getAttribute('data-os');
        try { localStorage.setItem(KEY, os); } catch (e) { /* private mode: ignore */ }
        try { history.replaceState(null, '', location.pathname + '?os=' + os); } catch (e) { /* ignore */ }
        show(os);
      });
    }

    /* A link that names a system (?os=macos) is a deliberate choice, so remember it: the guides link to each
       other without naming a system, and the next page then opens on the same one. */
    var urlOs = fromUrl();
    if (urlOs) { try { localStorage.setItem(KEY, urlOs); } catch (e) { /* private mode: ignore */ } }
    var chosen = urlOs || fromHash() || stored() || detect();
    show(chosen);
    if (location.hash && chosen) {
      var el = null;
      try { el = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (e) { el = null; }
      if (el && el.scrollIntoView) { el.scrollIntoView(); }
    }
  }

  function init() {
    osSwitch();
    var blocks = document.querySelectorAll('.guide pre');
    for (var i = 0; i < blocks.length; i++) { enhance(blocks[i]); }
    var quotes = document.querySelectorAll('.guide blockquote');
    for (var k = 0; k < quotes.length; k++) { enhanceQuote(quotes[k]); }
    var inline = document.querySelectorAll('.guide code.cmd');
    for (var m = 0; m < inline.length; m++) { enhanceInline(inline[m]); }
    rememberTicks();
  }

  /* A command written inside a sentence (a "type this" step, or an item of a checklist) gets a small
     Copy button after it. The source marks such commands with the class "cmd". */
  function enhanceInline(code) {
    var command = code.textContent.trim();
    code.parentNode.insertBefore(
      makeButton('Copy', 'Copy this command: ' + command, function () { return command; }, 'copy-inline'),
      code.nextSibling
    );
  }

  /* The checklists ("You are done when") are meant to be ticked. The ticks are remembered in this
     browser, per page, so they are still there after a reload. They are never sent anywhere. */
  function rememberTicks() {
    var boxes = document.querySelectorAll('.guide input[type="checkbox"]');
    if (!boxes.length) { return; }
    var key = 'nsdf-guide-ticks:' + location.pathname;
    var saved = [];
    try { saved = JSON.parse(localStorage.getItem(key) || '[]'); } catch (e) { saved = []; }
    function save() {
      var ticked = [];
      for (var b = 0; b < boxes.length; b++) { if (boxes[b].checked) { ticked.push(b); } }
      try { localStorage.setItem(key, JSON.stringify(ticked)); } catch (e) { /* private mode: ignore */ }
    }
    for (var j = 0; j < boxes.length; j++) {
      boxes[j].removeAttribute('disabled');
      if (saved.indexOf(j) !== -1) { boxes[j].checked = true; }
      boxes[j].addEventListener('change', save);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
