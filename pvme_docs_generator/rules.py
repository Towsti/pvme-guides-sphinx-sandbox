import re
import textwrap
from urllib.parse import urlparse

__all__ = ['Bot', 'TableOfContents', 'Section', 'InlineLiteral',
           'LineBreak', 'ListSection', 'Emoji', 'EmbedLink', 'DiscordMarkdownHTML', 'Cleanup', 'CodeBlock']


def align_inline_substitution(msg_content, substitution, start, end):
    if start > 0:
        if msg_content[start-1] not in (' ', '\t', '\n'):
            substitution = " {}".format(substitution)

    if end < len(msg_content):
        if msg_content[end] not in (' ', '\t', '\n'):
            substitution = "{} ".format(substitution)

    return substitution


class Bot:
    @staticmethod
    def format_sphinx_html(line, doc_info):
        if line == '.':
            formatted_line = ''

        elif line.startswith(".img:"):
            # note: extra enter mandatory for RST formatting
            image_link = line[len(".img:"):]
            formatted_line = "|{}|".format(image_link)
            doc_info.add(textwrap.dedent('''\
.. |{}| image:: {}
            '''.format(image_link, image_link)))

        elif line.startswith(".tag:"):
            formatted_line = ''

        elif line.startswith(".pin:"):
            formatted_line = ''

        else:
            formatted_line = ''

        return formatted_line


class SphinxRstMixIn(object):

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        pass


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
    # todo: add spacing ONLY if the surrounding characters isn't empty/new line
    PATTERN = re.compile(r"<:([^:]+):([0-9]+)>")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        matches = [match for match in re.finditer(Emoji.PATTERN, msg.content)]
        for match in reversed(matches):
            substitution = "|{}+{}|".format(match.group(1), match.group(2))
            emoji_formatted = align_inline_substitution(msg.content, substitution, match.start(), match.end())
            msg.content = msg.content[:match.start()] + emoji_formatted + msg.content[match.end():]

            doc_info.add(textwrap.dedent('''\
.. |{}+{}| image:: https://cdn.discordapp.com/emojis/{}.png?v=1
    :width: 1.375em
    :height: 1.375em
            '''.format(match.group(1), match.group(2), match.group(2))))


class InlineLiteral(SphinxRstMixIn):
    PATTERN = re.compile(r"`")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        msg.content = re.sub(InlineLiteral.PATTERN, "``", msg.content)


class CodeBlock(SphinxRstMixIn):
    PATTERN = re.compile(r"```")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        # res = re.findall(r"(?<=(```))([a-z A-Z0-9\n\t]+?)(?=(```))", msg.content)
        # res = re.findall(r"```", msg.content)
        # # print(res)
        #
        # matches = [match for match in re.finditer(CodeBlock.PATTERN, msg.content)]
        # if len(matches) % 2 == 1:
        #     matches = matches[:-1]
        #
        # for match in matches:
        pass



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


class EmbedLink(SphinxRstMixIn):
    PATTERN = re.compile(r"[\n ]\b((?:https?://)?(?:(?:www\.)?(?:[\da-z.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w.-]*)*/?)\b(?#[ \n])")

    @staticmethod
    def format_sphinx_html(msg, doc_info):

        for link in re.findall(EmbedLink.PATTERN, msg.content):
            embed_formatted = "|{}|".format(link)

            link_components = urlparse(link)

            if link_components.netloc == "youtu.be":
                msg.embeds.append(embed_formatted)
                doc_info.add(textwrap.dedent('''\
.. |{}| raw:: html

    <iframe class="media" width="560" height="315" src="https://www.youtube.com/embed{}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                '''.format(link, link_components.path)))


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
        (re.compile(r"\*\*\*"), "|<i>| |<b>|", "|</b>| |</i>|", {
            textwrap.dedent('''\
.. |<b>| raw:: html

    <b>
            '''),
            textwrap.dedent('''\
.. |<i>| raw:: html

    <i>
            '''),
            textwrap.dedent('''\
.. |</b>| raw:: html

    </b>
            '''),
            textwrap.dedent('''\
.. |</i>| raw:: html

    </i>
            ''')
        }),
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
.. |<code>| raw:: html

    <code style="display:block; white-space:pre-wrap">
            '''),
            textwrap.dedent('''\
.. |</code>| raw:: html

    </code>
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
