import re
import textwrap
from urllib.parse import urlparse
from functools import lru_cache
import pathlib
import requests

import gspread
from gspread.utils import a1_to_rowcol


__all__ = ['Bot', 'TableOfContents', 'Section', 'InlineLiteral', 'PVMESpreadsheet',
           'LineBreak', 'ListSection', 'Emoji', 'EmbedLink', 'DiscordMarkdownHTML', 'Cleanup', 'CodeBlock']

# set the credentials.json file path, by default, the file is searched in the pvme_docs_generator/ folder
module_path = pathlib.Path(__file__).parent.absolute()
CREDENTIALS_FILE = "{}/credentials.json".format(module_path)

# set the PVME price spreadsheet link (full link)
PVME_SPREADSHEET = "https://docs.google.com/spreadsheets/d/1nFepmgXBFh1Juc0Qh5nd1HLk50iiFTt3DHapILozuIM/edit#gid=0"


def align_inline_substitution(msg_content, substitution, start, end):
    if start > 0:
        if msg_content[start-1] not in (' ', '\t', '\n'):
            substitution = " {}".format(substitution)

    if end < len(msg_content):
        if msg_content[end] not in (' ', '\t', '\n'):
            substitution = "{} ".format(substitution)

    return substitution


class SphinxRstMixIn(object):

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        pass


class Bot:
    @staticmethod
    def format_sphinx_html(line, doc_info):
        if line == '.':
            formatted_line = ''

        elif line.startswith(".img:"):
            # todo: use embed parser since images can also be gifs/mp4 etc
            image_link = line[len(".img:"):]
            formatted_line = "|{}|".format(image_link)
            doc_info.add(textwrap.dedent('''\
.. |{}| image:: {}
            '''.format(image_link, image_link)))

        elif line.startswith(".tag:"):
            formatted_line = ''

        elif line.startswith(".pin:"):
            formatted_line = ''

        elif line.startswith(".."):
            formatted_line = '.'

        else:
            formatted_line = ''

        return formatted_line





class Section(SphinxRstMixIn):
    # todo: possibly more precise pattern matching instead of startswith("> ")
    # PATTERN = re.compile(r"^> [_*]*([a-zA-Z0-9<>@ ]+)")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        content_lines = msg.content.splitlines()
        for i, line in enumerate(content_lines):
            if line.startswith("> "):
                # remove markdown html tags and spaces before emojis (e.g. "> ** |melee| Melee**" > "Melee"
                section_name = re.sub(r"[*_~`]", '', line[len("> "):]).lstrip()

                content_lines[i] = textwrap.dedent('''\
{}  
{}
                '''.format(section_name, len(section_name) * '-'))

        msg.content = '\n'.join(content_lines)


class TableOfContents(SphinxRstMixIn):

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        content_lines = msg.content.splitlines()
        for i, line in enumerate(content_lines):
            if line.startswith("> "):
                section_name = re.sub(r"[*_~`]", '', line[len("> "):])
                if section_name.lower() == "table of contents":
                    msg.content = '\n'.join(content_lines[:i])
                    break


class Emoji(SphinxRstMixIn):
    PATTERNS = [(re.compile(r"<:([^:]{2,}):([0-9]+)>"), ".png"),
                (re.compile(r"<:a:([^:]+):([0-9]+)>"), ".gif")]

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        for pattern, extension in Emoji.PATTERNS:
            matches = [match for match in re.finditer(pattern, msg.content)]
            for match in reversed(matches):
                substitution = "|{}{}|".format(match.group(2), extension)
                substitution_aligned = align_inline_substitution(msg.content, substitution, match.start(), match.end())
                msg.content = msg.content[:match.start()] + substitution_aligned + msg.content[match.end():]

                doc_info.add(textwrap.dedent('''\
.. {} image:: https://cdn.discordapp.com/emojis/{}{}?v=1
    :width: 1.375em
    :height: 1.375em
                '''.format(substitution, match.group(2), extension)))


class PVMESpreadsheet(SphinxRstMixIn):
    # $data_pvme:Perks!H11$
    PATTERN = re.compile(r"\$data_pvme:([^!]+)!([^$]+)\$")

    @staticmethod
    @lru_cache(maxsize=None)
    def obtain_pvme_spreadsheet_data(worksheet):

        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open_by_url(PVME_SPREADSHEET)

        worksheet = sh.worksheet(worksheet)
        return worksheet.get_all_values()

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        matches = [match for match in re.finditer(PVMESpreadsheet.PATTERN, msg.content)]
        for match in reversed(matches):
            worksheet_data = PVMESpreadsheet.obtain_pvme_spreadsheet_data(match.group(1))
            row, column = a1_to_rowcol(match.group(2))
            price_formatted = "{}".format(worksheet_data[row-1][column-1])
            msg.content = msg.content[:match.start()] + price_formatted + msg.content[match.end():]


class InlineLiteral(SphinxRstMixIn):
    PATTERN = re.compile(r"`")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        msg.content = re.sub(InlineLiteral.PATTERN, "``", msg.content)


class CodeBlock(SphinxRstMixIn):
    """
    NOTE: alternatively, discord markdown html formatting can be used for code blocks.
          the rst style code blocks are limited in styling (e.g. no bold/underline code blocks)
          they also do not allow for the line after the code block to start with a tab.
          That said the styling looks a lot better and it is advised to use rst styling wherever possible

    """
    PATTERN = re.compile(r"```")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        matches = [match for match in re.finditer(CodeBlock.PATTERN, msg.content)]

        if len(matches) % 2 == 1:
            matches = matches[:-1]

        end = None
        for index, match in enumerate(reversed(matches)):
            if index % 2:
                start = match
                code_block_lines = msg.content[start.start()+len("```"):end.end()-len("```")].splitlines()
                formatted_codeblock = textwrap.dedent('''\

.. code:: none

    {}
           
                '''.format('\n    '.join(code_block_lines)))
                msg.content = msg.content[:start.start()] + formatted_codeblock + msg.content[end.end():]
            else:
                end = match


class LineBreak(SphinxRstMixIn):
    PATTERN = re.compile(r"_ _")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        msg.content = re.sub(LineBreak.PATTERN, '', msg.content)


class ListSection(SphinxRstMixIn):
    # todo: better approach to remove the weirdchamp symbol (lstrip doesn't work)
    WEIRDCHAMP_PATTERN = re.compile(r"︎")
    PATTERN = re.compile(r"[⬥•▪]")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        msg.content = re.sub(ListSection.WEIRDCHAMP_PATTERN, ' ', msg.content)
        msg.content = re.sub(ListSection.PATTERN, '-', msg.content)


def generate_embed(link):
    """Obtain the html embed link from a raw (unparsed) link

    :param link: raw unparsed link
    :return: html formatted embed link or None (link cannot be parsed)
    """
    # todo: clips.twitch and twitch/videos are not formatted correctly
    # youtu.be
    match = re.match(r"https?://youtu\.be/([a-zA-Z0-9_\-]+)", link)
    if match:
        return "<iframe class=\"media\" width=\"560\" height=\"315\" src=\"https://www.youtube.com/embed/{}\" frameborder=\"0\" allow=\"accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture\" allowfullscreen></iframe>".format(match.group(1))

    # youtube.com
    match = re.match(r"https?://(www\.)?youtube\.[a-z0-9.]*?/watch\?([0-9a-zA-Z$\-_.+!*'(),;/?:@=&#]*&)?v=([a-zA-Z0-9_\-]+)", link)
    if match:
        return "<iframe class=\"media\" width=\"560\" height=\"315\" src=\"https://www.youtube.com/embed/{}\" frameborder=\"0\" allow=\"accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture\" allowfullscreen></iframe>".format(match.group(3))

    # clips.twitch.tv
    match = re.match(r"https?://clips\.twitch\.tv/([a-zA-Z]+)", link)
    if match:
        return "<iframe class=\"media\" src=\"https://clips.twitch.tv/embed?autoplay=false&clip={}\" frameborder=\"0\" allowfullscreen=\"true\" scrolling=\"no\" height=\"315\" width=\"560\"></iframe>".format(match.group(1))

    # twitch.tv/videos
    match = re.match(r"https?://www\.twitch\.tv/videos/([0-9a-zA-Z]+)", link)
    if match:
        return "<iframe class=\"media\" src=\"https://player.twitch.tv/?autoplay=false&video=v{}\" frameborder=\"0\" allowfullscreen=\"true\" scrolling=\"no\" height=\"335\" width=\"550\"></iframe>".format(match.group(1))

    # streamable
    match = re.match(r"https?://streamable.com/([a-zA-Z0-9]+)", link)
    if match:
        return "<iframe class=\"media\" src=\"https://streamable.com/o/{}\" frameborder=\"0\" scrolling=\"no\" width=\"560\" height=\"315\" allowfullscreen></iframe>".format(match.group(1))


class EmbedLink(SphinxRstMixIn):
    PATTERN = re.compile(
        r'(?:[^<])' # check for valid embed links (don't start with '<')
        r'((?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)'
        r'(?:[^ \n\t\r]*))', re.IGNORECASE)    # anything at the end of the link

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        for link in re.findall(EmbedLink.PATTERN, msg.content):
            html_embed = generate_embed(link)

            if html_embed:
                substitution = "|{}|".format(link)
                msg.embeds.append(substitution)

                doc_info.add(textwrap.dedent('''\
.. {} raw:: html
    
    {}
                '''.format(substitution, html_embed)))


class DiscordMarkdownHTML(SphinxRstMixIn):
    """(Experimental) support for full discord markdown style html output.
    This formatting is a WiP and is generally not advised according to the RST documentation:
    https://docutils.sourceforge.io/docs/ref/rst/roles.html#raw

    Example:
    .. |<u>| raw:: html

        <u>

    .. |</u>| raw:: html

        </u>

    .. |<b>| raw:: html

        <b>

    .. |</b>| raw:: html

        </b>

    hello |<b>| bold |<u>| bold-underline ``bold-underline-mono`` |</b>| underline |</u>| end
    """
    PATTERNS = [
        (re.compile(r"\*\*"), "|<b>|", "|</b>|", {
            textwrap.dedent('''\
.. |<b>| raw:: html

    <b>
            '''),
            textwrap.dedent('''\
.. |</b>| raw:: html

    </b>
            ''')
         }),
        (re.compile(r"__"), "|<u>|", "|</u>|", {
            textwrap.dedent('''\
.. |<u>| raw:: html

    <u>
            '''),
            textwrap.dedent('''\
.. |</u>| raw:: html

    </u>
            ''')
        }),
        (re.compile(r"\*"), "|<i>|", "|</i>|", {
            textwrap.dedent('''\
.. |<i>| raw:: html

    <i>
            '''),
            textwrap.dedent('''\
.. |</i>| raw:: html

    </i>
            ''')
         }),
        (re.compile(r"```"), "|<code>|", "|</code>|", {
            textwrap.dedent('''\
.. |<s>| raw:: html

    <s>
            '''),
            textwrap.dedent('''\
.. |</s>| raw:: html

    </s>
            ''')
        }),
    ]

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        for pattern, start_substitution, end_substitution, doc_info_substitutions in DiscordMarkdownHTML.PATTERNS:
            matches = [match for match in re.finditer(pattern, msg.content)]
            if len(matches) % 2 == 1:
                # note: this will "break" dpm-advice.dpm-advice.melee.rst line 624
                #       reason: Inline emphasis start-string without end-string.
                #       fix: formatting step that replaces trailing * with \*
                matches = matches[:-1]

            for index, match in enumerate(reversed(matches)):
                # set <b> or </b> based on if the match is even or uneven
                if index % 2:
                    substitution = align_inline_substitution(msg.content, start_substitution, match.start(), match.end())
                else:
                    substitution = align_inline_substitution(msg.content, end_substitution, match.start(), match.end())

                msg.content = msg.content[:match.start()] + substitution + msg.content[match.end():]

                # ensures that there are no duplicates or unused substitutions, that said it's very inefficient
                for doc_info_substitution in doc_info_substitutions:
                    doc_info.add(doc_info_substitution)


class Cleanup(SphinxRstMixIn):
    """Remove left-over common sphinx warnings like "*Note:" to "\*Note:".
    """
    @staticmethod
    def format_sphinx_html(msg, doc_info):
        msg.content = re.sub("\*", r"\*", msg.content)
