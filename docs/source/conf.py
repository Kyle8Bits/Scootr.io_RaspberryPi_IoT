# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------
import os
import sys

# Add the root of the project and master_pi itself to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../master_pi')))


# -- Project information -----------------------------------------------------

project = 'COSC2790 Assignment2 Group 7'
copyright = '2025, Shirin, Thao, Khoa'
author = 'Shirin, Thao, Khoa'
release = '1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',      # for Google-style and NumPy-style docstrings
    'sphinx.ext.autosummary',   # for autosummary generation
]

autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for LaTeX (PDF export) ------------------------------------------

latex_engine = 'pdflatex'
latex_documents = [
    ('index', 'COSC2790Group7.tex', 'COSC2790 Assignment2 Group 7 Documentation',
     'Shirin, Thao, Khoa', 'manual'),
]
