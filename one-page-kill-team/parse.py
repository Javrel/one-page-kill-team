import fitz  # PyMuPDF
import re
import json


def extract_team_name(text):
    """Extracts the team name from the first line of the text."""
    first_line = text.strip().split("\n")[0]  # Get the first line
    return first_line.strip()  # Remove extra spaces


def format_text(content):
    """
    Splits text around `.\n` but removes `\n` that is NOT preceded by a `.`
    Returns a list of sentences.
    """
    # Replace newline characters that are NOT preceded by a dot (.) with a space
    formatted_content = re.sub(r"(?<!\.)\n", " ", content)

    # Split sentences where a dot is followed by a newline
    sentences = re.split(r"\.\s*\n", formatted_content)

    return [sentence.strip() for sentence in sentences if sentence.strip()]


def extract_faction_rules(text, team_name):
    """Extracts faction rules sections by identifying fully capitalized headers."""

    # Extract only the FACTION RULES section (stop at STRATEGY PLOYS)
    match = re.search(r"FACTION RULES\n(.+?)\nSTRATEGY PLOYS", text, re.S)
    if not match:
        return {}  # Return empty if no faction rules found

    faction_text = match.group(1).strip()  # Get only the relevant section

    # Remove unwanted footers like "ANGELS OF DEATH » FACTION RULES" and page numbers
    cleaned_text = re.sub(fr"{team_name} » FACTION RULES\n\d+", "", faction_text)

    # Find all section headers (fully capitalized lines without '»')
    section_pattern = re.compile(r"^(?!.*»)([A-Z\s]+)$", re.M)

    sections = {}
    last_section = None
    content_lines = []

    # Iterate through each line in the text
    for line in cleaned_text.split("\n"):
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


# Example Usage
if __name__ == "__main__":
    test_doc = "../data/pdfs/killteam_teamrules_angelsofdeath_eng_02.10.24.pdf"

    doc = fitz.open(test_doc)
    text = "\n".join([page.get_text() for page in doc])
    team_name = extract_team_name(text)
    output = {"name": team_name}
    output["faction_rules"] = extract_faction_rules(text, team_name)

    with open("../data/killteam_data.txt", "w", encoding="utf-8") as text_file:
        text_file.write(text)

    # Output the structured JSON file
    with open("../data/killteam_data.json", "w", encoding="utf-8") as json_file:
        json.dump(output, json_file, indent=4, ensure_ascii=False)

    print("Kill Team data extracted and saved as 'killteam_data.json'.")
