"""Sphinx configuration for TripleModel (Read the Docs and local builds)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

project = "TripleModel"
author = "TripleModel contributors"
copyright = f"{datetime.now().year}, {author}"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]

autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "special-members": "__init__",
}

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "README.md",
    "guides/README.md",
]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "logo_only": False,
}

pygments_style = "sphinx"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
    "tasklist",
]
myst_heading_anchors = 4
myst_fence_as_directive = ["mermaid"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "rdflib": ("https://rdflib.readthedocs.io/en/stable/", None),
}

# Signatures reference pyoxigraph types and internal TypeVars without intersphinx entries.
nitpick_ignore = [
    ("py:class", "TripleModel"),
    ("py:class", "Lang"),
    ("py:attr", "RdfConfig.instance_of"),
    ("py:data", "default_registry"),
    ("py:data", "default_resolver"),
    ("py:data", "typing.Union"),
    ("py:class", "typing_extensions.Unpack"),
    ("py:class", "types.EllipsisType"),
]
nitpick_ignore_regex = [
    (r"py:class", r"pyoxigraph\..*"),
    (r"py:class", r"triplemodel\.store\.(graph|dataset)\.Rdf\w+"),
    (r"py:class", r"triplemodel\.store\.sparql_result\.\w+"),
    (r"py:class", r"triplemodel\.(io|fields|metadata|plugins|namespaces|_typing)\..+"),
]

# Linkcheck: localhost is local-only; W3C/xmlns IRIs are often not retrievable as HTML.
linkcheck_ignore = [
    r"http://localhost:8000/?",
    r"http://www\.w3\.org/.*",
    r"http://xmlns\.com/.*",
]

linkcheck_allowed_redirects = {
    "https://docs.pydantic.dev/": r"https://pydantic\.dev/.*",
    "https://rdflib.readthedocs.io/": r"https://rdflib\.readthedocs\.io/en/stable/.*",
    "https://pypi.org/manage/account/token/": r"https://pypi\.org/account/login/.*",
    "https://readthedocs.org/": r"https://about\.readthedocs\.com/.*",
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_special_with_doc = True

# Import package so autodoc and version stay in sync.
import triplemodel  # noqa: E402

version = triplemodel.__version__
release = version
