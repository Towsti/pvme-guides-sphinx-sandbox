import pathlib
import os
import re
import textwrap


class Metadata(object):

    def __init__(self):
        self.emojis = dict()
        self.underline = False
        self.bold_underline = False
        self.bold_italic = False

    def format(self):
        metadata_formatted = ""

        # format emojis
        for name, id in self.emojis.items():
            metadata_formatted += textwrap.dedent('''\
.. |{}| image:: https://cdn.discordapp.com/emojis/{}.png?v=1
    :width: 1.375em
    :height: 1.375em

            '''.format(name, id))

        return metadata_formatted


class Channel(object):

    def __init__(self, category_name, channel_name):
        self.name = channel_name
        self.full_name = "{}.{}".format(category_name, channel_name)
        self.file_content = ""

    def write(self, source_dir):
        channel_content = textwrap.dedent('''\
{}
{}

{}
        '''.format(
            self.name, len(self.name) * '=', self.file_content
        ))

        source_file = "{}/pvme-guides/{}.rst".format(source_dir, self.full_name)
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(channel_content)

    @staticmethod
    def format_line(line, metadata):
        modified_line = None
        line_formatted = True

        if line == "":
            modified_line = ""

        elif line == ".":
            modified_line = ""

        elif line.startswith(".tag:"):
            modified_line = ""

        elif line.startswith("> "):
            modified_line = line[len("> "):]  # todo: add to regex
            section_name = re.sub('[>*_]', '', modified_line)  # remove ** and __ to get the section name
            modified_line = "{}\n{}".format(section_name, len(section_name) * '^')

        elif line.startswith(".img:"):
            image_splitted = line.split(".img:", 1)
            modified_line = ".. image:: {}".format(image_splitted[1])

        else:
            line_formatted = False

        return line_formatted, modified_line

    @staticmethod
    def format_words(line, metadata):
        modified_line = line

        # todo: add in css because RST does not support underline and bold italic by default
        modified_line = modified_line.replace("__", '', -1)

        modified_line = modified_line.replace('⬥', '-', -1)

        # format emojis
        emojis = re.findall('<:(.*?)>', line)

        for emoji in emojis:
            emoji_splitted = emoji.split(':')
            metadata.emojis[emoji_splitted[0]] = emoji_splitted[1]

            # todo: find more efficient approach than replacing characters every time
            modified_line = modified_line.replace(
                "<:{}:{}>".format(emoji_splitted[0], emoji_splitted[1]), " |{}| ".format(emoji_splitted[0]), 1)

        return modified_line

    def format_guide_content(self, file):
        with open(file, "r", encoding="utf-8") as f:
            file_lines = f.read().split('\n')  # can't seem to get formatting correct with file.readlines()

        metadata = Metadata()

        for i, line in enumerate(file_lines):
            line_formatted, modified_line = self.format_line(line, metadata)

            if line.lower().startswith("> **__table of contents__**"):
                file_lines = file_lines[0:i]
                break

            if line_formatted:
                # format entire lines
                file_lines[i] = modified_line
            else:
                # format words
                file_lines[i] = self.format_words(line, metadata)

        # format metadata
        metadata_formatted = metadata.format()

        self.file_content = metadata_formatted + "\n\n".join(file_lines)


class Category(object):

    def __init__(self, category_name):
        self.name = category_name
        self.channels = list()

    def add_channel(self, channel):
        if len(self.channels) == 0:
            self.channels = [channel]
        else:
            self.channels.append(channel)

    def write(self, source_dir):
        channel_names = [channel.full_name for channel in self.channels]
        category_content = textwrap.dedent('''\
{}
{}

.. toctree::
    :maxdepth: 2

    {}  
        '''.format(self.name, len(self.name) * '=', "\n    ".join(channel_names)))

        source_file = "{}/pvme-guides/{}.rst".format(source_dir, self.name)
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(category_content)


class Index(object):

    def __init__(self):
        self.categories = list()

    def write(self, source_dir):
        category_names = ["pvme-guides/{}".format(category.name) for category in self.categories]

        index_content = textwrap.dedent('''\
Table Of Contents
=================

.. toctree::
    :maxdepth: 2

    {}

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
            '''.format("\n    ".join(category_names)))

        source_file = "{}/index.rst".format(source_dir)
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(index_content)


def format_pvme_guides():
    # get the path to pvme_guides_formatter.py
    module_path = pathlib.Path(__file__).parent.absolute()
    source_dir = "{}/sphinx/source".format(module_path)
    pvme_guides_dir = "{}/pvme-guides".format(module_path)

    if not os.path.isdir(pvme_guides_dir):
        print("no {} found".format(pvme_guides_dir))
        return False

    if not os.path.isdir(source_dir):
        print("no {} found".format(source_dir))
        return False

    index = Index()

    # iterate categories (dpm-advice, high-tier-pvm etc)
    for category_name in os.listdir(pvme_guides_dir):
        category_dir = "{}/{}".format(pvme_guides_dir, category_name)

        # exclude non-directories like README.md and LICENSE as well as guide-writing dir
        if os.path.isdir(category_dir) and category_name != "guide-writing":
            category = Category(category_name)

            # iterate channels (dpm-advice.dpm-advice-faq.txt etc)
            for channel_file in os.listdir(category_dir):
                channel_path = "{}/{}".format(category_dir, channel_file)
                channel_name, _ext = os.path.splitext(channel_file)

                channel = Channel(category.name, channel_name)

                channel.format_guide_content(channel_path)
                category.channels.append(channel)

            index.categories.append(category)

    if not os.path.isdir("{}/pvme-guides".format(source_dir)):
        os.mkdir("{}/pvme-guides".format(source_dir))

    try:
        # create/overwrite the index.rst file
        index.write(source_dir)

        # create/overwrite the category files
        for category in index.categories:
            category.write(source_dir)

            # create/overwrite the channel files
            for channel in category.channels:
                channel.write(source_dir)

    except IOError as e:
        print("file write error: {}".format(e))
        write_status = False
    else:
        write_status = True

    return write_status
