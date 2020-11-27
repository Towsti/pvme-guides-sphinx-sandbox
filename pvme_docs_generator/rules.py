import re
import textwrap
from urllib.parse import urlparse

__all__ = ['Bot', 'TableOfContents', 'Section', 'InlineLiteral', 'BoldUnderline', 'Bold', 'Underline',
           'LineBreak', 'ListSection', 'Emoji', 'EmbedLink']


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
                section_name = re.sub(r"[*_~`]", '', line[len("> "):])
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
            emoji_formatted = " |{}| ".format(match.group(1))
            msg.content = msg.content[:match.start()] + emoji_formatted + msg.content[match.end():]

            doc_info.add(textwrap.dedent('''\
.. |{}| image:: https://cdn.discordapp.com/emojis/{}.png?v=1
    :width: 1.375em
    :height: 1.375em
            '''.format(match.group(1), match.group(2))))


class InlineLiteral(SphinxRstMixIn):
    PATTERN = re.compile(r"[`]")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        msg.content = re.sub(InlineLiteral.PATTERN, "``", msg.content)


class BoldUnderline(SphinxRstMixIn):
    # todo: optimize pattern and ensure order is correct (currently __**bold underline__** is allowed)
    # todo: currently bugged when there are multiple bold-underline words in a single line
    PATTERN = re.compile(r"(?<=(__\*\*|\*\*__))(.+?)(?=(\*\*__|__\*\*))")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        matches = [match for match in re.finditer(BoldUnderline.PATTERN, msg.content)]
        for match in reversed(matches):
            text_formatted = ":bold-underline:`{}`".format(match.group(2))
            msg.content = msg.content[:match.start()-len(match.group(1))] + text_formatted + msg.content[match.end() + len(match.group(3)):]
            doc_info.add(textwrap.dedent('''\
.. role:: bold-underline
    :class: bold-underline
            '''))


class Underline(SphinxRstMixIn):
    # todo: add spacing ONLY if the surrounding characters isn't empty/new line
    PATTERN = re.compile(r"(?<=(__))(.+?)(?=(__))")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        matches = [match for match in re.finditer(Underline.PATTERN, msg.content)]
        for match in reversed(matches):
            text_formatted = ":underline:`{}`".format(match.group(2))
            msg.content = msg.content[:match.start() - len(match.group(1))] + text_formatted + msg.content[match.end() + len(match.group(3)):]
            doc_info.add(textwrap.dedent('''\
.. role:: underline
    :class: underline
            '''))


class Bold(SphinxRstMixIn):
    # todo: add spacing ONLY if the surrounding characters isn't empty/new line
    PATTERN = re.compile(r"(?<=(\*\*))(.+?)(?=(\*\*))")

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        matches = [match for match in re.finditer(Bold.PATTERN, msg.content)]
        for match in reversed(matches):
            text_formatted = ":bold:`{}`".format(match.group(2))
            msg.content = msg.content[:match.start() - len(match.group(1))] + text_formatted + msg.content[match.end() + len(match.group(3)):]
            doc_info.add(textwrap.dedent('''\
.. role:: bold
    :class: bold
            '''))


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
        # print(re.findall(EmbedLink.PATTERN_YOUTUBE_FULL, msg.content))

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
    """Experimental support for full discord markdown style html output.
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

    @staticmethod
    def format_sphinx_html(msg, doc_info):
        pass
