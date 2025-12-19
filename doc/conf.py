# -*- coding: utf-8 -*-
import sys, os
from packaging.version import parse as version_parse
import epics

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.mathjax',
              'sphinx.ext.napoleon', 'sphinx_copybutton',
              'numpydoc']
templates_path = ['_templates']


project = "PyEpics"
copyright = "2025, Matthew Newville, The University of Chicago"

html_title = "Epics Channel Access for Python"
html_short_title = "PyEpics"

release = version_parse(epics.__version__).base_version

source_suffix = {'.rst': 'restructuredtext'}
exclude_trees = ['_build']
default_role = None
source_encoding = 'utf-8'

add_function_parentheses = True
add_module_names = True
pygments_style = 'sphinx'
master_doc = 'index'

html_theme_path = ['sphinx_theme']
html_theme = 'bizstyle'

html_static_path = ['_static']
html_sidebars = {
  'index': ["indexsidebar.html",  "sourcelink.html", "searchbox.html"],
  "**": [ "localtoc.html",  "relations.html", "sourcelink.html", "searchbox.html"]
}

html_domain_indices = False
html_use_index = True
html_show_sourcelink = True
