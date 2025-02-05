import re

from one_page_kill_team.utils import strip_control_chars, remove_quotes_and_anything_after, is_keyword_line


def extract_operatives_list(text):
    """Extracts operatives and their descriptions from the OPERATIVES section."""

    match = re.search(r"OPERATIVES\n(.+?)\u0007", text, re.S)
    if not match:
        return {}

    operatives_text = match.group(1).strip()
    section_pattern = re.compile(r"^([A-Z\s]+)$", re.M)
    operatives = {}
    last_operative = None
    content_lines = []

    for line in operatives_text.split("\n"):
        line = line.strip()
        if section_pattern.match(line):
            if last_operative and content_lines:
                operatives[last_operative] = {"description": " ".join(content_lines).strip()}
            last_operative = line
            content_lines = []
        else:
            content_lines.append(line)

    if last_operative and content_lines:
        operatives[last_operative] = {"description": " ".join(content_lines).strip()}

    return operatives


def extract_operative_name_keywords_and_stats(operative_block):
    """Extracts the operative's name, keywords, and stats (APL, WOUNDS, SAVE, MOVE)."""
    lines = [line.strip() for line in operative_block.splitlines() if line.strip()]

    keyword_index, apl_index = None, None
    for i, line in enumerate(lines):
        if is_keyword_line(line):
            keyword_index = i
        elif line == "APL":
            apl_index = i
            break

    if keyword_index is None or apl_index is None:
        print(f"⚠️ No keyword or APL line found in block! Block:\n{operative_block}\n{'-' * 40}")
        return None, None, None

    operative_name = " ".join(lines[keyword_index + 1: apl_index -1]).strip()
    keywords = lines[keyword_index].strip()

    stats = {
        "APL": lines[apl_index - 1].strip(),
        "WOUNDS": lines[apl_index + 6].strip(),
        "SAVE": lines[apl_index + 5].strip(),
        "MOVE": lines[apl_index + 4].strip(),
    }

    return operative_name, keywords, stats


def clean_quotes_from_blocks(operative_blocks):
    cleaned_blocks = []
    for block in operative_blocks:
        # Remove quotes formatted like the example
        cleaned_block = remove_quotes_and_anything_after(block)

        if cleaned_block != block:
            print("🛠️ Removed a quote from an operative block.")

        cleaned_blocks.append(cleaned_block)

    return cleaned_blocks

def extract_operative_blocks(text):
    """Extract full operative data blocks, including stats, weapons, and abilities."""

    match = re.search(r"(\nNAME.*?)(?=FACTION EQUIPMENT)", text, re.S)
    if not match:
        print("⚠️ No operative section found!")
        return []

    operative_section = match.group(1).strip()
    operative_blocks = [block.strip() for block in re.split(r"(?=\nNAME\t)", operative_section)]
    operative_blocks = clean_quotes_from_blocks(operative_blocks)

    all_operatives = []

    for operative_block in operative_blocks:
        name, keywords, stats = extract_operative_name_keywords_and_stats(operative_block)
        if not name:
            continue

        operative = {"name": name, "keywords": keywords, "stats": stats, "weapons": [], "abilities": []}
        lines = operative_block.splitlines()
        lines = [l.strip() for l in lines if l.strip()]

        parse_idx = 0
        if len(lines) >= 5 and [ln.upper() for ln in lines[:5]] == ["NAME", "ATK", "HIT", "DMG", "WR"]:
            parse_idx = 5

        weapons = []
        while parse_idx + 4 < len(lines):
            chunk = lines[parse_idx: parse_idx + 5]
            if (re.match(r"^\*?[A-Za-z].*?:", chunk[0])
                    or (re.match(r"^[A-Z ,\-]+$", chunk[0]) and "," in chunk[0]))\
                    or re.match(r"^[A-Z]+", chunk[0]):
                break
            weapons.append({"NAME": chunk[0], "ATK": chunk[1], "HIT": chunk[2], "DMG": chunk[3], "WR": chunk[4]})
            parse_idx += 5

        operative["weapons"] = weapons
        abilities = []
        current_ability = None


        for line in lines[parse_idx:]:
            if is_keyword_line(line):
                break
            if re.match(r"^\*?[A-Z][A-Za-z*\- ]+[:]", line):  # Ensure ability names start with a capital letter
                ability_name, ability_desc = map(str.strip, re.split(r"[:]", line, 1))
                current_ability = {"name": ability_name, "description": ability_desc}
                abilities.append(current_ability)
            elif current_ability:
                # Append to the previous ability description instead of treating as a new one
                current_ability["description"] += " " + line.strip()

        operative["abilities"] = postprocess_ap_abilities(abilities)
        all_operatives.append(operative)

    return all_operatives


def postprocess_ap_abilities(abilities):
    """Extracts AP-based abilities and organizes them separately."""
    new_abilities = []
    pattern = re.compile(r'([A-Z\s]+)\s+(\d+AP)\s+(.*?)(?=[A-Z\s]+\d+AP|$)', flags=re.DOTALL)

    for ability in abilities:
        desc = strip_control_chars(ability["description"])
        ap_subabilities = []

        for match in pattern.finditer(desc):
            sub_ability = {"name": match.group(1).strip(), "cost": match.group(2).strip(),
                           "description": match.group(3).strip()}
            ap_subabilities.append(sub_ability)

        if ap_subabilities:
            desc_cleaned = pattern.sub('', desc).strip()
            ability["description"] = desc_cleaned
            new_abilities.extend(ap_subabilities)

        new_abilities.append(ability)

    return new_abilities
