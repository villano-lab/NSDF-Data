/* "Latest" links next to the pinned links of a note (issue 51).

   A note links to files at an exact commit, for example .../blob/322b1b8/python/pulse_cuts.py, so the note keeps
   showing the version of the file that produced its numbers. That version may be older than the file today, and the
   file may have moved. After each such link this script adds a small "[latest]" link to the same file on the develop
   branch. When the file has moved or been removed, docs/notes/pin-moves.json (written by
   tools/check_note_pins.py report --write-moves) says where it went. Without JavaScript, or without that file,
   nothing changes: the pinned links work as before. Edit this file, not the pages. */
(function () {
  'use strict';

  var PIN = /^https:\/\/github\.com\/villano-lab\/NSDF-Data\/(blob|tree)\/([0-9a-f]{7,40})\/([^#?]*)(#.*)?$/;
  var BASE = 'https://github.com/villano-lab/NSDF-Data/';

  function annotate(moves) {
    var links = document.querySelectorAll('a[href^="' + BASE + '"]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      var m = PIN.exec(a.getAttribute('href') || '');
      if (!m || a.getAttribute('data-pin-done')) { continue; }
      a.setAttribute('data-pin-done', '1');
      var kind = m[1], sha = m[2], path = m[3].replace(/\/$/, '');
      var key = sha + '/' + decodeURIComponent(path);
      var span = document.createElement('span');
      span.className = 'pin-note';
      var title = 'The link above is pinned to commit ' + sha.slice(0, 7) + ', the version this note used. ';
      if (Object.prototype.hasOwnProperty.call(moves, key)) {
        var target = moves[key];
        if (target) {
          span.appendChild(document.createTextNode('['));
          span.appendChild(latestLink(kind, encodeURI(target), 'latest, moved', title + 'The file has moved: this is where it is now.'));
          span.appendChild(document.createTextNode(']'));
        } else {
          span.textContent = '[latest: no longer in the repository]';
          span.title = title + 'The file has been removed; the pinned link still shows it.';
        }
      } else {
        span.appendChild(document.createTextNode('['));
        span.appendChild(latestLink(kind, path, 'latest', title + 'This is the file on the develop branch today, which may differ.'));
        span.appendChild(document.createTextNode(']'));
      }
      a.parentNode.insertBefore(span, a.nextSibling);
    }
  }

  function latestLink(kind, path, label, title) {
    var l = document.createElement('a');
    l.href = BASE + kind + '/develop/' + path;
    l.textContent = label;
    l.title = title;
    l.className = 'pin-latest';
    return l;
  }

  function start(moves) {
    try { annotate(moves || {}); } catch (e) { /* decoration only: leave the page as it is */ }
  }

  function init() {
    if (!window.fetch) { start({}); return; }
    fetch('pin-moves.json').then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; })
      .then(start);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
