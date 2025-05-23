import re

from one_page_kill_team.utils import format_text, remove_quotes_and_anything_after

def extract_archetypes(text):
    match = re.search(r"ARCHETYPES\n(.+?)\nArchetypes", text, re.S)

    if not match:
        return []

    archetypes_text = match.group(1).strip()
    archetypes_text = re.sub(r'\s+', ' ', archetypes_text)

    keywords = ["RECON", "SEEK & DESTROY", "SECURITY", "INFILTRATION"]

    # Check which keywords exist in the text
    existing_keywords = [keyword for keyword in keywords if keyword in archetypes_text]

    return existing_keywords


def extract_faction_rules(text, team_name):
    """Extracts faction rules sections by identifying fully capitalized headers."""

    # Extract only the FACTION RULES section (stop at STRATEGY PLOYS)
    match = re.search(r"FACTION RULES\n(.+?)\nSTRATEGY PLOYS", text, re.S)
    if not match:
        return {}  # Return empty if no faction rules found

    faction_text = match.group(1).strip()  # Get only the relevant section
    faction_text = remove_quotes_and_anything_after(faction_text)

    # Find all section headers (fully capitalized lines without '»')
    section_pattern = re.compile(r"^(?!.*»)([A-Z’\s]+)$", re.M)

    sections = {}
    last_section = None
    content_lines = []

    # Iterate through each line in the text
    for line in faction_text.split("\n"):
        line = line.strip()

        # If line is a section header, store the previous section and start a new one
        if section_pattern.match(line):
            if last_section and content_lines:
                sections[last_section] = format_text("\n".join(content_lines).strip())
            last_section = line
            content_lines = []
        else:
            if not re.fullmatch(r"\d+", line):
                content_lines.append(line)

    # Store the last section
    if last_section and content_lines:
        sections[last_section] = format_text("\n".join(content_lines).strip())

    return sections


def extract_faction_equipment(text, team_name):
    """
    Extracts the Faction Equipment section, from 'FACTION EQUIPMENT' up to
    the next 'MARKER/TOKEN GUIDE' or 'UPDATE LOG' (or end of text).
    Returns the raw equipment text, or an empty string if none found.
    """

    pattern = re.compile(
        r"FACTION EQUIPMENT\s*\n"
        rf"(.*?)(?=\nMARKER/TOKEN GUIDE|{team_name}: UPDATE .?LOG|$)",
        flags=re.DOTALL
    )


    match = re.search(pattern, text)
    if match:
        equipment_text = match.group(1).strip()
        return parse_equipment_to_list(equipment_text)
    else:
        return print("No equipment match...")


import re


def parse_equipment_to_list(equipment_text):
    """
    Splits equipment text by fully uppercase headings, excluding specific unwanted headers,
    returning a list of dicts: [ {"name": "BRASS ADORNMENTS", "description": "..."},
                                 {"name": "GORE MARKS",       "description": "..."},
                                 ... ]
    """

    # Regex for lines that are ALL CAPS (and can contain spaces), e.g. BRASS ADORNMENTS
    heading_pattern = re.compile(r"^[A-Z][A-Z\s]+$", re.MULTILINE)

    # Define headers to ignore
    ignored_headers = {"ATK\t HIT\t DMG", "WR", "NAME"}

    equipment_entries = []
    current_heading = None
    description_buffer = []

    lines = equipment_text.splitlines()
    for line in lines:
        line_stripped = line.strip()

        # If this line is a new uppercase heading...
        if heading_pattern.match(line_stripped) and line_stripped not in ignored_headers:
            # If we already have a heading & buffer, store the previous equipment piece
            if current_heading and description_buffer:
                equipment_entries.append({
                    "name": current_heading,
                    "description": " ".join(description_buffer).strip()
                })
            # Reset for new heading
            current_heading = line_stripped
            description_buffer = []
        else:
            # Accumulate description text for the current heading
            if not re.fullmatch(r"\d+", line):
                description_buffer.append(line_stripped)

    # Store the last heading found (if any)
    if current_heading and description_buffer:
        equipment_entries.append({
            "name": current_heading,
            "description": " ".join(description_buffer).strip()
        })

    return equipment_entries
