import os
import textwrap
import shutil
import time

from pvme_docs_generator.rules import *


# message end separator, this is generally a bot command that start with '.' like '.img'
MESSAGE_END_START = '.'

# order in which the message content is formatted.
# the order can affect the outcome (e.g. Sections can only be formatted before Bold/Underline)
CONTENT_FORMATTERS = [
    Emoji,
    TableOfContents,
    Section,
    CodeBlock,
    DiscordMarkdownHTML,
    InlineLiteral,
    LineBreak,
    ListSection,
    EmbedLink,
    PVMESpreadsheet,
    Cleanup
]

# default folder sequence is in alphabetical order, the folder sequence is used to customize this order.
# to enable/disable the fixed category sequence; set the generate_sphinx_rst(custom_list_sequence: bool)
CUSTOM_CATEGORY_SEQUENCE = [
    "information",
    "getting-started",
    "upgrading-info",
    "miscellaneous-information",
    "dpm-advice",
    "low-tier-pvm",
    "mid-tier-pvm",
    "high-tier-pvm"
]

# names (no '.txt' extension) of all the excluded categories
EXCLUDE_CATEGORIES = {
    "guide-writing"
}

# names (no '.txt' extension) of all the excluded channels
EXCLUDE_CHANNELS = {
}


class Message(object):
    def __init__(self, content, bot_command):
        self.content = content
        self.embeds = list()
        self.bot_command = bot_command


def get_messages(channel_file):
    messages = []
    try:
        with open(channel_file, "r", encoding="utf-8") as file:
            file_content = file.read()
    except IOError as e:
        print(e)
    else:
        file_lines = file_content.splitlines()
        prev_i = 0

        for i, line in enumerate(file_lines):
            if line.startswith(MESSAGE_END_START):
                messages.append(Message('\n\n'.join(file_lines[prev_i: i]), file_lines[i]))
                prev_i = i + 1

    return messages


def generate_channel(sphinx_source_dir, channel_dir, category_name, channel_name):
    doc_info = set()
    messages_formatted = []
    messages = get_messages(channel_dir)

    for message in messages:
        for formatter in CONTENT_FORMATTERS:
            formatter.format_sphinx_html(message, doc_info)

        messages_formatted.append(textwrap.dedent('''\
{}

{}
        
{}
        '''.format(message.content, ''.join(message.embeds), Bot.format_sphinx_html(message.bot_command, doc_info))))

    channel_formatted = textwrap.dedent('''\
{}
{}
{}

{}
    '''.format('\n'.join(doc_info), channel_name, len(channel_name) * '=', '\n'.join(messages_formatted)))

    try:
        with open("{}/pvme-guides/{}.{}.rst".format(sphinx_source_dir, category_name, channel_name), "w", encoding="utf-8") as file:
            file.write(channel_formatted)
    except IOError as e:
        print(e)


def generate_category(sphinx_source_dir, category_name, channel_names):
    channels_formatted = ''.join(["\n    {}.{}".format(category_name, channel_name) for channel_name in channel_names])

    category_formatted = textwrap.dedent('''\
{}
{}

.. toctree::
    :maxdepth: 2
{}
    '''.format(category_name, len(category_name) * '=', channels_formatted))

    try:
        with open("{}/pvme-guides/{}.rst".format(sphinx_source_dir, category_name), "w", encoding="utf-8") as file:
            file.write(category_formatted)
    except IOError as e:
        print(e)


def generate_index(sphinx_source_dir, category_names):
    # todo: appending to .. toctree instead of generating the entire index makes more sense but cba
    categories_formatted = ''.join(["\n    pvme-guides/{}".format(category_name) for category_name in category_names])

    index_formatted = textwrap.dedent('''\
PVME-Guides Documentation
=========================

The goal of this site is to make it easier to navigate the guides using a navigation menu and a search field.  

The content is generated from the pvme-guides repository and is therefore always up-to-date with the PVME discord.

The bottom of every page displays when the site was last updated. The site is updated every 4 days to update the perks prices.

**Theme**

- the site is build with Sphinx using the Read the Docs theme

    - support for mobile and desktop
  
- the dark-mode styling is created using the Dark Reader extension 

**Links**

- `PVME Discord <https://discord.com/invite/pvme>`_
- `pvme-guides Github <https://github.com/pvme/pvme-guides>`_

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
    '''.format(categories_formatted))

    try:
        with open("{}/index.rst".format(sphinx_source_dir), "w", encoding="utf-8") as file:
            file.write(index_formatted)
    except IOError as e:
        print(e)


def generate_sphinx_rst(pvme_guides_dir: str, sphinx_source_dir: str, custom_list_sequence: bool=True) -> bool:
    """Iterates the pvme-guides input folder and generates the following files:
        - sphinx_source_dir/index.rst
        - sphinx_source_dir/pvme-guides/category
        - sphinx_source_dir/pvme-guides/category/channel.rst
    
    :param pvme_guides_dir: folder to the pvme-guides (generally cloned from git repo beforehand)
    :param sphinx_source_dir: sphinx source directory.
    :param custom_list_sequence: enable or disable the category sequence in CUSTOM_CATEGORY_SEQUENCE.
    :return: the result of file generation (note: this result isn't strict and is not reliable for CI)
    """
    # guard clauses for ensuring the paths exist
    if not os.path.isdir(sphinx_source_dir):
        print("no {} found".format(sphinx_source_dir))
        return False

    if not os.path.isdir(pvme_guides_dir):
        print("no {} found".format(pvme_guides_dir))
        return False

    # (clear) + create the source/pvme-guides directory
    if os.path.isdir("{}/pvme-guides".format(sphinx_source_dir)):
        shutil.rmtree("{}/pvme-guides".format(sphinx_source_dir), ignore_errors=True)

    os.mkdir("{}/pvme-guides".format(sphinx_source_dir))

    index_categories = []

    if custom_list_sequence:
        categories = CUSTOM_CATEGORY_SEQUENCE
    else:
        categories = os.listdir(pvme_guides_dir)

    # iterate categories (dpm-advice, high-tier-pvm etc)
    for category_name in categories:
        category_dir = "{}/{}".format(pvme_guides_dir, category_name)

        # exclude non-directories like README.md and LICENSE
        if not os.path.isdir(category_dir):
            continue

        # exclude categories that should not be in the guide
        if category_name in EXCLUDE_CATEGORIES:
            continue

        category_channels = []

        # iterate channels (dpm-advice.dpm-advice-faq.txt etc)
        for channel_file in os.listdir(category_dir):
            channel_dir = "{}/{}".format(category_dir, channel_file)
            channel_name, ext = os.path.splitext(channel_file)

            if ext != ".txt":
                continue

            generate_channel(sphinx_source_dir, channel_dir, category_name, channel_name)
            category_channels.append(channel_name)

        generate_category(sphinx_source_dir, category_name, category_channels)
        index_categories.append(category_name)

    generate_index(sphinx_source_dir, index_categories)
    return True


if __name__ == "__main__":
    # For testing
    # generate_channel("../sphinx/source", "../pvme-guides/high-tier-pvm/araxxor-melee.txt", "high-tier-pvm", "araxxor-melee")
    # generate_channel("../sphinx/source", "../pvme-guides/getting-started/perks.txt", "getting-started", "perks")
    # generate_channel("../sphinx/source", "../pvme-guides/miscellaneous-information/ability-information.txt", "miscellaneous-information", "ability-information")


    start = time.time()
    generate_sphinx_rst("../pvme-guides", "../sphinx/source")
    print("format duration: {} seconds".format(time.time() - start))
