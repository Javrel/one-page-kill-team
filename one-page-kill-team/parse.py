import os
from glob import glob

import fitz  # PyMuPDF
import re
import json


def extract_team_name(text):
    """Extracts the team name from the first line of the text."""
    first_line = text.strip().split("\n")[0]  # Get the first line
    return first_line.strip()  # Remove extra spaces


def format_text(content):
    """
    - Splits text at `.\n` to ensure proper sentence separation.
    - Splits at `\n•` while keeping `•` at the start of the new list item.
    - Cleans extra spaces and ensures structured list output.
    """

    # Replace `\u0007` with a newline so it acts as a separator
    content = content.replace("\u0007", "\n")

    # Ensure bullet points `•` that start mid-line get a newline before them
    content = re.sub(r"\n\s*•", "\n•", content)  # Normalize bullet points with no space before them

    # Split properly at:
    #   1. `.\n` (End of sentences)
    #   2. `\n•` (Bullet points start a new list item)
    split_pattern = r"\.\s*\n|\n(?=•)"
    sentences = re.split(split_pattern, content)

    # Clean and remove empty entries
    sentences = [sentence.strip().replace("\n", " ") for sentence in sentences if sentence.strip()]

    return sentences


def extract_faction_rules(text, team_name):
    """Extracts faction rules sections by identifying fully capitalized headers."""

    # Extract only the FACTION RULES section (stop at STRATEGY PLOYS)
    match = re.search(r"FACTION RULES\n(.+?)\nSTRATEGY PLOYS", text, re.S)
    if not match:
        return {}  # Return empty if no faction rules found

    faction_text = match.group(1).strip()  # Get only the relevant section

    # Find all section headers (fully capitalized lines without '»')
    section_pattern = re.compile(r"^(?!.*»)([A-Z\s]+)$", re.M)

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
            content_lines.append(line)

    # Store the last section
    if last_section and content_lines:
        sections[last_section] = format_text("\n".join(content_lines).strip())

    return sections


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


def extract_operatives_list(text):
    """Extracts operatives and their descriptions from the OPERATIVES section."""

    # Find the OPERATIVES section (stop at the special character `\u0007`)
    match = re.search(r"OPERATIVES\n(.+?)\u0007", text, re.S)
    if not match:
        return {}  # Return empty if no operatives found

    operatives_text = match.group(1).strip()

    # Find all operative names (fully capitalized lines)
    section_pattern = re.compile(r"^([A-Z\s]+)$", re.M)

    operatives = {}
    last_operative = None
    content_lines = []

    for line in operatives_text.split("\n"):
        line = line.strip()

        # If line is a new operative (all uppercase), store the last operative's details
        if section_pattern.match(line):
            if last_operative and content_lines:
                operatives[last_operative] = {"description": " ".join(content_lines).strip()}
            last_operative = line
            content_lines = []
        else:
            content_lines.append(line)

    # Store the last operative
    if last_operative and content_lines:
        operatives[last_operative] = {"description": " ".join(content_lines).strip()}

    return operatives


def extract_operative_name_and_keywords(operative_block):
    """
    Extracts the operative's name from a block of text.
    - The keywords (uppercase, comma-separated) appear before the name.
    - The name is between keywords and 'APL', but can span multiple lines.
    """

    # ✅ Normalize newlines and remove extra spaces
    lines = [line.strip() for line in operative_block.splitlines() if line.strip()]

    # ✅ Find the Keywords Line (uppercase, comma-separated)
    keyword_index = None
    for i, line in enumerate(lines):
        if re.match(r"^[A-Z ,\-]+$", line) and "," in line:  # Ensure it contains uppercase keywords
            keyword_index = i

    if keyword_index is None:
        print("⚠️ No keyword line found in block!")
        return None

    # ✅ Find the APL Line (Ensure we match it correctly)
    apl_index = None
    for i in range(keyword_index, len(lines)):
        if re.search(r"APL", lines[i], re.IGNORECASE):  # Ensure "APL" is an exact matc
            print("found an apl")
            apl_index = i
            break
        else:
            print(lines[i])

    if apl_index is None:
        print(f"⚠️ No 'APL' line found in block! Block:\n{operative_block}\n{'-'*40}")
        return None

    # ✅ Extract the Operative Name (All lines between keywords and APL)
    operative_name_lines = lines[keyword_index + 1 : apl_index]
    operative_name = " ".join(operative_name_lines).strip()

    # ✅ Extract Keywords
    keywords = lines[keyword_index].strip()

    return operative_name, keywords



def extract_operative_blocks(text):
    """
    Extract full operative data blocks, splitting them into individual operatives
    with name, keywords, weapons, and abilities.
    """

    # 1) Extract text between "NAME" (start) and "FACTION EQUIPMENT" (end)
    match = re.search(r"(\nNAME.*?)(?=FACTION EQUIPMENT)", text, re.S)
    if not match:
        print("⚠️ No operative section found!")
        return []

    operative_section = match.group(1).strip()
    print(f"✅ Extracted operative section ({len(operative_section.splitlines())} lines)")

    # 2) Split by "NAME" to separate operatives
    operative_blocks = [block.strip() for block in re.split(r"(?=\nNAME\t)", operative_section)]

    all_operatives = []

    for operative_block in operative_blocks:
        lines = operative_block.splitlines()
        # Clean up empty lines/spaces
        lines = [l.strip() for l in lines if l.strip()]

        # (A) Extract name & keywords however you do
        name, keywords = extract_operative_name_and_keywords(operative_block)
        operative = {
            "name": name,
            "keywords": keywords,
            "weapons": [],
            "abilities": []
        }

        #
        # ─────────────────────────────────────────────────────────────
        #  B) Detect the "header" lines if present
        # ─────────────────────────────────────────────────────────────
        if len(lines) >= 5:
            # Compare the first 5 lines to "NAME", "ATK", "HIT", "DMG", "WR"
            header_lines = [ln.upper() for ln in lines[:5]]
            expected_header = ["NAME", "ATK", "HIT", "DMG", "WR"]

            if header_lines == expected_header:
                # Skip these 5 lines
                parse_idx = 5
            else:
                # We didn’t find a 5-line header
                parse_idx = 0
        else:
            parse_idx = 0

        # ─────────────────────────────────────────────────────────────
        # C) Parse Weapons in 5-line chunks
        # ─────────────────────────────────────────────────────────────
        weapons = []
        while parse_idx + 4 < len(lines):
            chunk = lines[parse_idx: parse_idx + 5]

            # Stop if the first line looks like “AbilityName: Something”
            # so we don't accidentally read an ability as a weapon.
            if re.match(r"^[A-Za-z].*?:", chunk[0]):
                break

            # Build the weapon object
            weapon = {
                "NAME": chunk[0],
                "ATK": chunk[1],
                "HIT": chunk[2],
                "DMG": chunk[3],
                "WR": chunk[4],
            }
            weapons.append(weapon)
            parse_idx += 5

        operative["weapons"] = weapons

        # ─────────────────────────────────────────────────────────────
        # D) Parse Abilities from whatever remains
        # ─────────────────────────────────────────────────────────────
        abilities = []
        current_ability = None

        for line in lines[parse_idx:]:
            if ":" in line:
                # Start a new ability
                ability_name, ability_desc = map(str.strip, line.split(":", 1))
                current_ability = {
                    "name": ability_name,
                    "description": ability_desc
                }
                abilities.append(current_ability)
            elif current_ability:
                # Subsequent lines belong to the current ability
                current_ability["description"] += " " + line

        operative["abilities"] = postprocess_ap_abilities(abilities)
        all_operatives.append(operative)

    return all_operatives

def strip_control_chars(s: str) -> str:
    # remove ASCII control chars (below 32 plus 127)
    clean = re.sub(r"[\x00-\x1F\x7F]", "", s)
    # optionally collapse multiple spaces
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()

def postprocess_ap_abilities(abilities):
    """
    Given a list of abilities (each is { 'name': str, 'description': str }),
    look for any text that matches a pattern like:
       ABILITY_NAME 1AP ...
    and split that chunk out as a separate ability with its own "cost" key.
    """
    new_abilities = []

    # A regex that allows multiple uppercase words (like "ANGEL OF DEATH"),
    # followed by an AP cost, then captures text until next AP-based action or string end.
    # e.g. "OPTICS 1AP" or "ANGEL OF DEATH 2AP"
    pattern = re.compile(
        r'([A-Z\s]+)\s+(\d+AP)\s+(.*?)(?=[A-Z\s]+\d+AP|$)',
        flags=re.DOTALL
    )

    for ability in abilities:
        # 1) Clean the description to remove weird control chars or backspaces
        desc = strip_control_chars(ability["description"])

        ap_subabilities = []
        # 2) Scan for 'ABILITY_NAME 1AP <text>'
        for match in pattern.finditer(desc):
            action_name = match.group(1).strip()  # e.g. "OPTICS" or "ANGEL OF DEATH"
            ap_cost     = match.group(2).strip()  # e.g. "1AP"
            action_text = match.group(3).strip()  # text until next AP-based action

            sub_ability = {
                "name":        action_name,
                "cost":        ap_cost,      # store "1AP" here
                "description": action_text
            }
            ap_subabilities.append(sub_ability)

        if ap_subabilities:
            # Remove the matched text from the original ability's description
            # so we don't see it twice.
            desc_cleaned = pattern.sub('', desc).strip()
            ability["description"] = desc_cleaned

            # Add the newly extracted sub-abilities
            new_abilities.extend(ap_subabilities)

        # Keep the original (possibly shortened) ability as well
        new_abilities.append(ability)

    return new_abilities

def extract_faction_equipment(text):
    """
    Extracts the Faction Equipment section, from 'FACTION EQUIPMENT' up to
    the next 'MARKER/TOKEN GUIDE' or 'UPDATE LOG' (or end of text).
    Returns the raw equipment text, or an empty string if none found.
    """
    # Regex explanation:
    #   1. Look for 'FACTION EQUIPMENT' literally.
    #   2. Capture everything lazily (.*?) until
    #   3. We see either:
    #         - A line with 'MARKER/TOKEN GUIDE'
    #         - A line with 'UPDATE LOG' (in case your file uses 'FELLGOR RAVAGERS: UPDATE LOG' or similar)
    #         - OR the end of the entire text ($)

    print("********************************************")
    for idx, line in enumerate(text.splitlines()):
        if 685 <= idx <= 716:
            print(idx, repr(line), len(line))

    pattern = re.compile(
        r"FACTION EQUIPMENT\s*\n"
        r"(.*?)(?=\nMARKER/TOKEN GUIDE|\nUPDATE LOG|$)",
        flags=re.DOTALL
    )

    match = re.search(pattern, text)
    if match:
        equipment_text = match.group(1).strip()
        print(f"equip: {equipment_text}")
        return parse_equipment_to_list(equipment_text)
    else:
        return print("No equipment match...")


def parse_equipment_to_list(equipment_text):
    """
    Splits equipment text by fully uppercase headings, returning a list of
    dicts: [ {"name": "BRASS ADORNMENTS", "description": "..."},
             {"name": "GORE MARKS",       "description": "..."},
             ... ]
    """

    # Regex for lines that are ALL CAPS (and can contain spaces), e.g. BRASS ADORNMENTS
    heading_pattern = re.compile(r"^[A-Z][A-Z\s]+$", re.MULTILINE)

    equipment_entries = []
    current_heading = None
    description_buffer = []

    lines = equipment_text.splitlines()
    for line in lines:
        line_stripped = line.strip()

        # If this line is a new uppercase heading...
        if heading_pattern.match(line_stripped):
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
            description_buffer.append(line_stripped)

    # Store the last heading found (if any)
    if current_heading and description_buffer:
        equipment_entries.append({
            "name": current_heading,
            "description": " ".join(description_buffer).strip()
        })

    return equipment_entries


# Example Usage
if __name__ == "__main__":
    pdf_folder = "../data/input_pdfs/"
    pdf_files = glob(os.path.join(pdf_folder, "*.pdf"))  # Get all PDFs

    # 📌 **Process each PDF**
    for pdf_path in pdf_files:
        print(f"\n📂 Processing: {pdf_path}")

        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc])
        team_name = extract_team_name(text)

        print(f"🛡️ Team Name: {team_name}")

        # ✅ Remove unwanted footers like "ANGELS OF DEATH » FACTION RULES"
        cleaned_lines = [line for line in text.split("\n") if f"{team_name} »" not in line and len(line) > 1]
        text = "\n".join(cleaned_lines)

        # ✅ Extract Data
        output = {"name": team_name}
        output["faction_rules"] = extract_faction_rules(text, team_name)
        output["strategy_ploys"] = extract_strategy_ploys(text)
        output["firefight_ploys"] = extract_firefight_ploys(text)
        output["operatives"] = extract_operative_blocks(text)
        output["faction_equipment"] = extract_faction_equipment(text)

        # ✅ Save raw text (optional)
        text_output_path = os.path.join("../data", f"{team_name}.txt")
        with open(text_output_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)

        # ✅ Save JSON output
        json_output_path = os.path.join("../data", f"{team_name}.json")
        with open(json_output_path, "w", encoding="utf-8") as json_file:
            json.dump(output, json_file, indent=4, ensure_ascii=False)

        print(f"✅ Saved: {json_output_path}")

    print("\n🎯 All PDFs processed successfully!")
