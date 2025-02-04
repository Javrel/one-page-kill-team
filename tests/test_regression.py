import os
import json
import pytest
import subprocess
from pathlib import Path
import fitz
from shutil import copy2
from one_page_kill_team.utils import extract_team_name# Assuming this exists in your project
from one_page_kill_team.parse import parse_folder

PDF_FOLDER = Path(r"C:\Users\harle\git\one-page-kill-team\tests\regression_data\pdf")
REFERENCE_FOLDER = Path(r"C:\Users\harle\git\one-page-kill-team\tests\regression_data\json")
PARSE_SCRIPT = Path(r"C:\Users\harle\git\one-page-kill-team\parse.py")

@pytest.fixture
def temp_output_dir(tmp_path):
    """Creates a temporary output directory for the test."""
    output_dir = tmp_path / "output_json"
    output_dir.mkdir()
    return output_dir

def run_parse_script(output_dir):
    """Runs parse.py and directs JSON output to the temporary directory."""
    try:
        subprocess.run(["python", str(PARSE_SCRIPT)], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"🚨 Failed to run parse.py: {e}")

def load_json_as_string(file_path):
    """Loads a JSON file, sorts keys, and returns a formatted string."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return json.dumps(data, indent=2, sort_keys=True)  # Convert to sorted JSON string

def compare_json_files(reference_path, output_path):
    """Loads JSON files as strings and compares them directly."""
    ref_str = load_json_as_string(reference_path)
    out_str = load_json_as_string(output_path)

    if ref_str != out_str:
        print("\n🚨 JSON MISMATCH FOUND! Full JSONs are different.\n")
        pytest.fail(f"❌ JSON mismatch detected in {reference_path}. Run a diff tool to investigate.")

    return True  # If they match, return True

def test_regression(temp_output_dir):
    """Runs parse.py, generates new JSON, and compares it against the reference."""
    parse_folder(PDF_FOLDER, temp_output_dir)  # ✅ Step 1: Generate JSONs

    pdf_files = list(PDF_FOLDER.glob("*.pdf"))
    if not pdf_files:
        pytest.fail(f"🚨 No PDFs found in: {PDF_FOLDER.resolve()}")

    for pdf_path in pdf_files:

        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc])
        team_name = extract_team_name(text)  # Extract team name
        assert team_name, f"❌ Could not extract team name from: {pdf_path}"

        ref_file = REFERENCE_FOLDER / f"{team_name}.json"
        out_file = temp_output_dir / f"{team_name}.json"

        if not ref_file.exists():
            pytest.fail(f"❌ Missing reference file for: {team_name} at {ref_file}")

        # ✅ Compare generated JSON with reference JSON
        compare_json_files(ref_file, out_file)
