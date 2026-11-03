"""Sphinx configuration of the documentation of goldpan and goldsluice (built into docs/api/ by tools/build_docs.py).

The two packages are documented together while they live in this repository. When they get their own repositories each takes its
own copy of this folder: nothing here depends on the rest of the repository except the paths below.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "python"))                  # goldpan
sys.path.insert(0, str(ROOT / "goldsluice" / "python"))   # goldsluice (its compiled part is not needed to document it)

project = "goldpan and goldsluice"
author = "NSDF-Data maintainers"
copyright = "the NSDF-Data authors"
language = "en"

extensions = [
    "myst_parser",             # the pages are Markdown
    "sphinx.ext.autodoc",      # the reference is read from the docstrings
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",     # accepts NumPy / Google style sections if a docstring uses them
    "sphinx.ext.intersphinx",  # links into numpy, awkward, pyarrow, Python
    "sphinx.ext.viewcode",
    "sphinx_copybutton",       # a copy button on every code block, as on the guides
]

source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
exclude_patterns = ["_build", "requirements.txt"]
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3
myst_all_links_external = True                           # the guides link to pages of the project site, not to Sphinx documents

# The docstrings of this repository put names in single backticks: show them as code, not as emphasis.
default_role = "code"

autosummary_generate = True
autodoc_default_options = {"members": True, "undoc-members": False, "show-inheritance": True}
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_mock_imports = ["goldsluice._core"]               # the Rust extension: not needed to read the docstrings
napoleon_use_param = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "awkward": ("https://awkward-array.org/doc/stable/", None),
    "pyarrow": ("https://arrow.apache.org/docs/", None),
}
intersphinx_timeout = 10

html_theme = "furo"
html_title = "goldpan and goldsluice"
html_static_path = []
html_theme_options = {
    "source_repository": "https://github.com/villano-lab/NSDF-Data/",
    "source_branch": "develop",
    "source_directory": "sphinx/",
}


def _status_note(app, what, name, obj, options, lines):
    """Show the development status of a function (`goldpan.status`) at the top of its entry when it is not settled."""
    if getattr(obj, "status", None) == "under_development":
        note = getattr(obj, "status_note", None)
        lines[0:0] = [".. warning::", "", "   **Under development**" + (f": {note}" if note else "."), ""]


def setup(app):
    app.connect("autodoc-process-docstring", _status_note)

html_copy_source = False
html_show_sourcelink = False
