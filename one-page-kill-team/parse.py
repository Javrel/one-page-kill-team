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


def extract_operative_details(text, operatives):
    """Extracts operative stats, weapons, abilities, and keywords from the data section."""

    for operative in operatives.keys():
        print(f"\n🔍 Searching details for operative: {operative}")

        # ✅ Keep the original regex as-is
        pattern = re.search(fr"\nNAME\s*\nATK\s*\nHIT\s*\nDMG\s*\nWR\s*\n(.+?){operative}", text, re.S)

        if not pattern:
            print(f"⚠️ No match found for {operative}")
            continue  # Skip if no match found

        section_text = pattern.group(1).strip()  # Extract everything between `NAME` and operative
        lines = section_text.split("\n")

        print(f"✅ Extracted section for {operative}:\n{'-' * 40}\n{section_text}\n{'-' * 40}\n")

        weapons = []
        abilities = []
        is_weapon_section = True  # Start by assuming it's in the weapons section

        # 📌 **Extract Keywords (Last Line)**
        keywords = lines[-1].strip()
        lines = lines[:-1]  # Remove keywords from the main section

        # 📌 **NEW: Detect and extract weapon stats by grouping every 5 lines together**
        weapon_buffer = []

        for i, line in enumerate(lines):
            line = line.strip()

            if re.match(r"^[A-Za-z\s]+:.*$", line):  # Detects ability names followed by a colon
                is_weapon_section = False  # Switch from weapon parsing to ability parsing

                # Split ability into name and description
                ability_parts = line.split(":", 1)  # Split on first colon
                ability_name = ability_parts[0].strip()
                ability_desc = ability_parts[1].strip() if len(ability_parts) > 1 else ""

                # Store ability as a dictionary
                abilities.append({"name": ability_name, "description": ability_desc})

                print(f"🛡️ Ability Found: {ability_name} -> {ability_desc}")
                continue
            # If we're still in the ability section, continue appending text to the last ability
            elif not is_weapon_section and abilities:
                print(abilities)
                abilities[-1]["description"] += " " + line.strip()

            # 📌 **Collect 5 lines together for weapons**
            if is_weapon_section:
                weapon_buffer.append(line)

                if len(weapon_buffer) == 5:  # Ensure it's a full row
                    weapon = {
                        "NAME": weapon_buffer[0].strip(),
                        "ATK": weapon_buffer[1].strip(),
                        "HIT": weapon_buffer[2].strip(),
                        "DMG": weapon_buffer[3].strip(),
                        "WR": weapon_buffer[4].strip(),
                    }
                    print(f"🛠️ Weapon Found: {weapon_buffer[0].strip()}")
                    weapons.append(weapon)
                    weapon_buffer = []  # Reset buffer for the next weapon
                continue


        # Store extracted data in the operatives list
        operatives[operative]["weapons"] = weapons
        operatives[operative]["abilities"] = abilities
        operatives[operative]["keywords"] = keywords

    return operatives


# Example Usage
if __name__ == "__main__":
    test_doc = "../data/pdfs/killteam_teamrules_angelsofdeath_eng_02.10.24.pdf"

    doc = fitz.open(test_doc)
    text = "\n".join([page.get_text() for page in doc])
    team_name = extract_team_name(text)

    # Remove unwanted footers like "ANGELS OF DEATH » FACTION RULES"
    cleaned_lines = [line for line in text.split("\n") if f"{team_name} »" not in line and len(line)>1]  # Ignore lines with `»`
    text = "\n".join(cleaned_lines)


    output = {"name": team_name}
    output["faction_rules"] = extract_faction_rules(text, team_name)
    output["strategy_ploys"] = extract_strategy_ploys(text)
    output["firefight_ploys"] = extract_firefight_ploys(text)
    operatives_list = extract_operatives_list(text)
    operatives = extract_operative_details(text, operatives_list)
    output["operatives"] = operatives
    with open("../data/killteam_data.txt", "w", encoding="utf-8") as text_file:
        text_file.write(text)

    # Output the structured JSON file
    with open("../data/killteam_data.json", "w", encoding="utf-8") as json_file:
        json.dump(output, json_file, indent=4, ensure_ascii=False)

    print("Kill Team data extracted and saved as 'killteam_data.json'.")
