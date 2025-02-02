import os
import glob
import json
import unicodedata
from fpdf import FPDF


class OperativePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")  # Portrait format
        self.set_auto_page_break(auto=True, margin=10)
        self.set_margins(10, 10, 10)

    def _encode_text(self, text):
        """Ensures text is safely encoded for FPDF by removing unsupported characters."""
        return text.encode("latin-1", "ignore").decode("latin-1")

    def strip_unicode(self, text):
        """Removes special Unicode characters, replacing them with closest ASCII equivalent."""
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    def add_operative(self, name, details):
        """Adds an operative's details to the PDF."""
        self.add_page()

        # ✅ Name & Stats on the same line (Smaller Font)
        self.set_font("Helvetica", "B", 12)
        operative_info = f"{self.strip_unicode(name)}  |  " + "  |  ".join(
            f"{key}: {value}" for key, value in details.get("stats", {}).items()
        )
        self.cell(0, 6, operative_info, ln=True, align="L")
        self.ln(2)

        # ✅ Keywords (Smaller Italic Font)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 5, f"Keywords: {self.strip_unicode(details.get('keywords', 'N/A'))}", ln=True)
        self.ln(3)

        # ✅ Weapons Table (100% width, Smaller Font)
        weapons = details.get("weapons", [])
        abilities = details.get("abilities", [])

        col_widths = [50, 20, 20, 20, 55]  # Adjust width of columns for Portrait
        headers = ["Name", "ATK", "HIT", "DMG", "WR"]

        # Table Headers
        self.set_font("Helvetica", "", 8)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 6, header, border=1, align="C")
        self.ln()

        # Table Data
        for weapon in weapons:
            self.cell(col_widths[0], 6, self.strip_unicode(weapon["NAME"]), border=1, align="L")
            self.cell(col_widths[1], 6, weapon["ATK"], border=1, align="C")
            self.cell(col_widths[2], 6, weapon["HIT"], border=1, align="C")
            self.cell(col_widths[3], 6, weapon["DMG"], border=1, align="C")
            self.cell(col_widths[4], 6, weapon["WR"], border=1, align="L")
            self.ln()

        # ✅ Abilities as Merged Table Rows (Smaller Font)
        if abilities:
            self.ln(1)  # Small space before abilities

            for ability in abilities:
                ability_text = f"**{self.strip_unicode(ability['name'])}**: {self.strip_unicode(ability['description'])}"

                # Merge across all columns
                total_width = sum(col_widths)  # Full table width
                self.set_font("Helvetica", "", 7)  # Smaller font for abilities
                self.multi_cell(total_width, 5, self._encode_text(ability_text), border=1, align="L")
                self.ln(1)  # Space between abilities

        # Move cursor down to avoid overlap
        self.ln(5)


if __name__ == "__main__":
    json_folder = "../data/"  # Change this to your JSON folder
    output_folder = "../data/pdfs/"  # Folder to save PDFs

    os.makedirs(output_folder, exist_ok=True)  # Ensure output directory exists

    json_files = glob.glob(os.path.join(json_folder, "*.json"))

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            team_name = data.get("name", "Unknown Team")
            operatives = data.get("operatives", {})

        if not operatives:
            print(f"Skipping {json_file}, no operatives found.")
            continue

        print(f"Processing team: {team_name} ({len(operatives)} operatives)")

        pdf = OperativePDF()

        for name, details in operatives.items():
            pdf.add_operative(name, details)

        pdf_filename = os.path.join(output_folder, f"{team_name}.pdf")
        pdf.output(pdf_filename, "F")
        print(f"✅ Saved PDF: {pdf_filename}")

    print("\n🎉 All PDFs have been generated successfully!")
