import re

from utils import format_text


def extract_strategy_ploys(text):
    """Extracts strategy ploys between STRATEGY PLOYS and FIREFIGHT PLOYS."""
    match = re.search(r"STRATEGY PLOYS\n(.+?)\nFIREFIGHT PLOYS\n", text, re.S)
    if not match:
        return {}  # Return empty if no strategy ploys found

    strategy_text = match.group(1).strip()

    # Find all section headers (fully capitalized lines without '»')
    section_pattern = re.compile(r"^(?!.*»)([A-Z\s]+)$", re.M)

    strategy_ploys = {}
    last_section = None
    content_lines = []

    # Iterate through each line in the text
    for line in strategy_text.split("\n"):
        line = line.strip()

        # If line is a section header, store the previous section and start a new one
        if section_pattern.match(line):
            if last_section and content_lines:
                strategy_ploys[last_section] = format_text("\n".join(content_lines).strip())
            last_section = line
            content_lines = []
        else:
            content_lines.append(line)

    # Store the last section
    if last_section and content_lines:
        strategy_ploys[last_section] = format_text("\n".join(content_lines).strip())

    return strategy_ploys


def extract_firefight_ploys(text):
    """Extracts firefight ploys between FIREFIGHT PLOYS and the first standalone 'NAME'."""

    match = re.search(r"FIREFIGHT PLOYS\n(.+?)\nNAME", text, re.S)
    if not match:
        print("firefight section not found")
        return {}  # Return empty if no firefight ploys found

    firefight_text = match.group(1).strip()
    # Find all section headers (fully capitalized lines without '»')
    section_pattern = re.compile(r"^(?!.*»)([A-Z\s]+)$", re.M)

    firefight_ploys = {}
    last_section = None
    content_lines = []

    # Iterate through each line in the text
    for line in firefight_text.split("\n"):
        line = line.strip()

        # If line is a section header, store the previous section and start a new one
        if section_pattern.match(line):
            if last_section and content_lines:
                firefight_ploys[last_section] = format_text("\n".join(content_lines).strip())
            last_section = line
            content_lines = []
        else:
            content_lines.append(line)

    # Store the last section
    if last_section and content_lines:
        firefight_ploys[last_section] = format_text("\n".join(content_lines).strip())

    return firefight_ploys
