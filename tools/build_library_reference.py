#!/usr/bin/env python
"""Build the library reference page, docs/library/index.html, from the code in python/.

The page is generated, never hand-edited: it lists every module of the `goldpan` package with its
docstring, its classes and its public functions (signature, summary, `@status` tag and note),
read from the code itself. Only the standard library is used, besides the library's own
dependencies (numpy, h5py), so it runs wherever the tests run.

    python tools/build_library_reference.py          # write docs/library/index.html
    python tools/build_library_reference.py check    # exit 1 if the page is out of date

`check` runs in the library tests (python/tests/test_library_reference.py), so a pull request
that changes a function without rebuilding the page fails CI.
"""
import ast
import html
import importlib
import inspect
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PYTHON_DIR = REPO / "python"
OUT = REPO / "docs" / "library" / "index.html"

# Documented in this order; any other module of the package is appended alphabetically. `goldpan.legacy` (the old flat
# names) and the package's `__init__` are not documented here.
ORDER = ["goldpan.io", "goldpan.config", "goldpan.operations", "goldpan.quantities", "goldpan.cuts",
         "goldpan.archive", "goldpan.channels", "goldpan.status"]


def esc(text):
    return html.escape(text, quote=False)


def inline(text):
    """Escape; turn `code` into <code>, **bold** into <strong> and *italic* into <em>."""
    out = []
    for part in re.split(r"(``[^`]+``|`[^`]+`)", text):
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append("<code>" + esc(part.strip("`")) + "</code>")
        else:
            part = esc(part)
            part = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", part)
            part = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])", r"<em>\1</em>", part)
            out.append(part)
    return "".join(out)


def blocks(doc):
    """Docstring -> HTML: paragraphs, and indented blocks as <pre>."""
    if not doc:
        return ""
    out = []
    for para in re.split(r"\n\s*\n", inspect.cleandoc(doc)):
        lines = para.split("\n")
        if all(line.startswith("    ") or not line.strip() for line in lines) and lines[0].startswith("    "):
            out.append("<pre>" + esc(inspect.cleandoc("\n".join(lines))) + "</pre>")
        elif all(re.match(r"\s*[*-] ", line) or line.startswith("  ") for line in lines) and re.match(r"\s*[*-] ", lines[0]):
            items = re.split(r"\n(?=\s*[*-] )", para)
            out.append("<ul>" + "".join("<li>" + inline(" ".join(re.sub(r"^\s*[*-] ", "", i).split())) + "</li>" for i in items) + "</ul>")
        else:
            text = " ".join(para.split())
            out.append("<p>" + inline(text[:-1] if text.endswith("::") else text) + "</p>")
    return "\n".join(out)


def summary(doc):
    """First paragraph of a docstring, on one line."""
    if not doc:
        return ""
    return " ".join(inspect.cleandoc(doc).split("\n\n")[0].split())


def signature(obj):
    """Signature as text, with module prefixes dropped."""
    return re.sub(r"\bgoldpan\.[a-z]+\.", "", str(inspect.signature(obj)))


def status_cell(func):
    level = getattr(func, "status", None)
    note = getattr(func, "status_note", None)
    if level == "done":
        return '<span class="status done">done</span>'
    if level == "under_development":
        out = '<span class="status under-dev">under development</span>'
        return out + (f"<br><small>{inline(note)}</small>" if note else "")
    return "&mdash;"


def class_attribute_docs(module, cls):
    """{field: docstring} for string literals that follow a class attribute, read with ast."""
    tree = ast.parse(inspect.getsource(module))
    docs = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
            body = node.body
            for prev, nxt in zip(body, body[1:]):
                if isinstance(prev, ast.AnnAssign) and isinstance(nxt, ast.Expr) \
                        and isinstance(nxt.value, ast.Constant) and isinstance(nxt.value.value, str):
                    docs[prev.target.id] = " ".join(inspect.cleandoc(nxt.value.value).split())
    return docs


def module_names():
    found = sorted("goldpan." + p.stem for p in (PYTHON_DIR / "goldpan").glob("*.py")
                   if p.stem not in {"__init__", "legacy"})
    found += sorted("goldpan.adapters." + p.stem for p in (PYTHON_DIR / "goldpan" / "adapters").glob("*.py")
                    if p.stem != "__init__")
    return [m for m in ORDER if m in found] + [m for m in found if m not in ORDER]


def render_module(modname):
    module = importlib.import_module(modname)
    funcs = [(n, f) for n, f in inspect.getmembers(module, inspect.isfunction)
             if not n.startswith("_") and f.__module__ == module.__name__]
    funcs.sort(key=lambda nf: nf[1].__code__.co_firstlineno)      # in source order
    classes = [(n, c) for n, c in inspect.getmembers(module, inspect.isclass)
               if not n.startswith("_") and c.__module__ == module.__name__]
    out = [f'<h2 id="{modname}">{modname}</h2>', blocks(module.__doc__)]
    for name, cls in classes:
        out.append(f"<h3><code>{name}{esc(signature(cls))}</code></h3>")
        if cls.__doc__ and not cls.__doc__.startswith(name + "("):    # skip the auto-made dataclass doc
            out.append(blocks(cls.__doc__))
        fields = class_attribute_docs(module, cls)
        if fields:
            out.append('<div class="table-scroll"><table><thead><tr><th>Field</th><th>Meaning</th></tr></thead><tbody>')
            out += [f"<tr><td><code>{n}</code></td><td>{inline(d)}</td></tr>" for n, d in fields.items()]
            out.append("</tbody></table></div>")
    if funcs:
        out.append('<div class="table-scroll"><table><thead><tr><th>Function</th><th>Summary</th><th>Status</th></tr></thead><tbody>')
        for name, f in funcs:
            sig = esc(signature(f))
            rest = inspect.cleandoc(f.__doc__ or "").split("\n\n")[1:]
            more = ""
            if rest:
                more = "<details><summary>details</summary>" + blocks("\n\n".join(rest)) + "</details>"
            out.append(f'<tr id="{modname}.{name}"><td><code>{name}</code><br><small><code>{sig}</code></small></td>'
                       f"<td>{inline(summary(f.__doc__))}{more}</td><td>{status_cell(f)}</td></tr>")
        out.append("</tbody></table></div>")
    return "\n".join(out), funcs


def render():
    sys.path.insert(0, str(PYTHON_DIR))
    sections, overview = [], []
    for modname in module_names():
        text, funcs = render_module(modname)
        sections.append(text)
        done = sum(getattr(f, "status", None) == "done" for _, f in funcs)
        dev = sum(getattr(f, "status", None) == "under_development" for _, f in funcs)
        first = summary(importlib.import_module(modname).__doc__).split(". ")[0].rstrip(".")
        overview.append(f'<tr><td><a href="#{modname}"><code>{modname}</code></a></td><td>{inline(first)}</td>'
                        f"<td>{len(funcs)}</td><td>{done}</td><td>{dev}</td></tr>")
    return PAGE.format(overview="\n".join(overview), sections="\n\n".join(sections))


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Library reference: python/</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="wrap note">

<header class="site"><nav><a href="../index.html">&larr; All notes</a></nav></header>

<h1>Library reference: <code>python/</code></h1>
<p class="meta">Generated from the code by <code>tools/build_library_reference.py</code>; do not edit by hand. Rebuild it after changing a function.</p>

<p>The pulse-analysis library, the Python package <code>goldpan</code> (in <code>python/</code>). Background and history: <a href="../notes/note-01a-pulse-library-structure.html">Note 1a</a> and <a href="../notes/note-04-pulse-library.html">Note 4</a>. Import a module as <code>from goldpan import cuts</code>; the library is installed by <code>requirements.txt</code> (see <code>python/README.md</code>). The old flat names (<code>pulse_cuts</code> and the others) are aliases of these modules with the Run 76 readout as the default <code>config</code>, kept for the existing notebooks. In this package <strong>every function takes a readout (<code>config</code>) and has no default for it</strong>: name your data's readout with <code>goldpan.config.DCRC_RUN76</code>, <code>goldpan.config.Z7</code> or your own <code>PulseConfig</code>. Samples are on the last axis, so every function takes one pulse or a whole batch. A function marked <span class="status under-dev">under development</span> still runs but emits a <code>UserWarning</code> on every call.</p>

<div class="table-scroll"><table>
<thead><tr><th>Module</th><th>What it is</th><th>Functions</th><th>Done</th><th>Under development</th></tr></thead>
<tbody>
{overview}
</tbody></table></div>

{sections}

</div>
</body>
</html>
"""


def main(argv):
    page = render()
    if argv[1:] == ["check"]:
        have = OUT.read_text(encoding="utf-8").replace("\r\n", "\n") if OUT.exists() else ""
        if have != page:
            print(f"{OUT.relative_to(REPO)} is out of date: run  python tools/build_library_reference.py")
            return 1
        print(f"{OUT.relative_to(REPO)} is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)} ({len(page.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
