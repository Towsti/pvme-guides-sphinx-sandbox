# pvme-guides-sphinx-sandbox
Sandbox project for pvme-guides sphinx documentation that is hosted on Read the Docs or Github pages.

[github-pages](https://towsti.github.io/pvme-guides-sphinx-sandbox/#)

## Building locally

**Requirements**

- python 3.7
- `pip install sphinx`
- `pip install sphinx_rtd_theme`

**Steps**

1. clone the repository
2. from the root folder: `make html` or `make help`
3. open "sphinx/build/html/index.html"

## Generating Github-pages

*NOTE: Currently only supported on windows.*

### Windows

**Requirements**

- git
- local build requirements

**Steps**

1. clone the repository
2. from the root folder: `make github-pages`

