import re


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


def strip_control_chars(s: str) -> str:
    # remove ASCII control chars (below 32 plus 127)
    clean = re.sub(r"[\x00-\x1F\x7F]", "", s)
    # optionally collapse multiple spaces
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def remove_quotes_and_anything_after(text):
    """Removes quotes in all caps, along with all lines after it."""
    return re.sub(r"‘..[A-Z0-9:! ,.\n-].*", "", text, flags=re.S)


def is_keyword_line(line):
    return re.match(r"^(?![\'’])[A-Z ‑,\-’']+$", line) and "," in line
