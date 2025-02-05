import os
from glob import glob


import fitz  # PyMuPDF
import json

from one_page_kill_team.faction import extract_faction_rules, extract_faction_equipment, extract_archetypes
from one_page_kill_team.operatives import extract_operative_blocks
from one_page_kill_team.ploys import extract_strategy_ploys, extract_firefight_ploys
from one_page_kill_team.utils import extract_team_name
import os


def parse_folder(input_path, output_path):

    pdf_files = glob(os.path.join(input_path, "*.pdf"))  # Get all PDFs

    for pdf_path in pdf_files:
        print(f"\n📂 Processing: {pdf_path}")


        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc])
        team_name = extract_team_name(text)

        print(f"🛡️Saving txt for : {team_name}")
        # ✅ Save raw text (optional)
        text_output_path = os.path.join(output_path, "{team_name}.txt")
        with open(text_output_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)

        # ✅ Remove unwanted footers like "ANGELS OF DEATH » FACTION RULES"
        cleaned_lines = [line for line in text.split("\n") if f"{team_name} »" not in line]
        text = "\n".join(cleaned_lines)

        # ✅ Extract Data
        output = {"name": team_name}
        output["archetypes"] = extract_archetypes(text)
        output["faction_rules"] = extract_faction_rules(text, team_name)
        output["strategy_ploys"] = extract_strategy_ploys(text)
        output["firefight_ploys"] = extract_firefight_ploys(text)
        output["operatives"] = extract_operative_blocks(text)
        output["faction_equipment"] = extract_faction_equipment(text)

        # ✅ Save JSON output
        json_output_path = os.path.join(output_path, f"{team_name}.json")
        with open(json_output_path, "w", encoding="utf-8") as json_file:
            json.dump(output, json_file, indent=4, ensure_ascii=False)

        print(f"✅ Saved {team_name} json: {json_output_path}")


# Example Usage
if __name__ == "__main__":
    pdf_folder = "./data/input_pdfs/"
    pdf_files = glob(os.path.join(pdf_folder, "*.pdf"))  # Get all PDFs

    # 📌 **Process each PDF**
    for pdf_path in pdf_files:
        print(f"\n📂 Processing: {pdf_path}")

        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc])
        team_name = extract_team_name(text)

        print(f"🛡️Saving txt for : {team_name}")
        # ✅ Save raw text (optional)
        text_output_path = os.path.join("./data/text", f"{team_name}.txt")
        with open(text_output_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)

        # ✅ Remove unwanted footers like "ANGELS OF DEATH » FACTION RULES"
        cleaned_lines = [line for line in text.split("\n") if f"{team_name} »" not in line]
        text = "\n".join(cleaned_lines)

        # ✅ Extract Data
        output = {"name": team_name}
        output["archetypes"] = extract_archetypes(text)
        output["faction_rules"] = extract_faction_rules(text, team_name)
        output["strategy_ploys"] = extract_strategy_ploys(text)
        output["firefight_ploys"] = extract_firefight_ploys(text)
        output["operatives"] = extract_operative_blocks(text)
        output["faction_equipment"] = extract_faction_equipment(text)


        # ✅ Save JSON output
        json_output_path = os.path.join("./data/json", f"{team_name}.json")
        with open(json_output_path, "w", encoding="utf-8") as json_file:
            json.dump(output, json_file, indent=4, ensure_ascii=False)

        print(f"✅ Saved {team_name} json: {json_output_path}")

    print("\n🎯 All PDFs processed successfully!")
