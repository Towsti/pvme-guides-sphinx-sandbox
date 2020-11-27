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

### Linux

todo

## LaTeX PDF

PDF generation using LaTeX has limited support. To build and experiment with LaTeX pdf generation, use the following command: `make latexpdf`. Most likely, a separate formatting ruleset for latex has to be implemented due to css styling for text not being supported. 

## Progress

overview of all the current bugs that need to be resolved and new features.

| description                                                  | status             |
| ------------------------------------------------------------ | ------------------ |
| `.img` not always shown on a new line (e.g. solak-7s presets) | :white_check_mark: |
| `_ _` character not yet removed                              | :white_check_mark: |
| add GE prices to perks                                       | :red_circle:       |
| image max-height should be relative                          | :red_circle:       |
| support for ***bold italic*** text                           | :red_circle:       |
| support for <u>underline</u> text                            | :warning:          |
| support for <u>**bold underline**</u> text                   | :warning:          |
| support for <u>*italic underline*</u> text                   | :red_circle:       |
| support for <u>***bold italic underline***</u> text          | :red_circle:       |
| add logo to the top of navigation bar                        | :red_circle:       |
| minor style change to `l2` navigation (background should contrast more with `l1`) | :red_circle:       |
| improve section identification*                              | :red_circle:       |
| add "generated on: DD/MM/YY" to the top of the navigation bar | :red_circle:       |
| hyperlink support (according the pvme style-guide)           | :red_circle:       |
| embed Youtube/Twitch and other links                         | :warning:          |
| automatically display images that don't start with `.img` at the end of a message | :red_circle:       |
| categories are not sorted correctly                          | :red_circle:       |

*currently the `> __**` format is used to identify sections. This format is not consistently used across all sections and certain sections are not suited for displaying in the navigation bar.