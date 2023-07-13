# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'BattleShip MP'
copyright = '2023 Karlsruhe Institute of Technology'
author = 'CSD Dozenten'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.imgmath',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

intersphinx_mapping = {
    "python": ('https://docs.python.org/3', None),
    "websockets": ('https://websockets.readthedocs.io/en/stable/', None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_theme_options = {
    "description": "Battleship server/client",
    'github_user': 'kit-colsoftdes',
    'github_repo': 'battleship_mp',
    "fixed_sidebar": True,
}

# -- Options for Extensions -------------------------------------------------
# autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

autodoc_member_order = "bysource"
