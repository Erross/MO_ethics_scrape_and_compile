import pdfplumber
import os


def scan_all_pdf_content():
    downloads_folder = "downloads"
    pdf_files = [f for f in os.listdir(downloads_folder) if f.endswith('.pdf')]

    # Look at the first PDF
    if pdf_files:
        pdf_path = os.path.join(downloads_folder, pdf_files[0])
        print(f"Scanning all pages of: {pdf_files[0]}")
        print("=" * 60)

        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")

            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    print(f"\n{'=' * 20} PAGE {page_num + 1} {'=' * 20}")

                    # Check for key sections
                    key_phrases = [
                        'CONTRIBUTIONS AND LOANS RECEIVED',
                        'CONTRIBUTIONS RECEIVED',
                        'EXPENDITURES AND CONTRIBUTIONS MADE',
                        'EXPENDITURES',
                        'REPORT SUMMARY',
                        'Wolf',
                        'Penny',
                        'Annette'
                    ]

                    found_key_phrases = [phrase for phrase in key_phrases if phrase in text]

                    if found_key_phrases:
                        print(f"*** FOUND: {', '.join(found_key_phrases)} ***")
                        print("\nFull page content:")
                        print(text)
                        print("\n" + "=" * 60)
                    else:
                        # Just show a snippet of pages without key phrases
                        print("No key phrases found. Page content preview:")
                        print(text[:200] + "...")

                        # But still check for dollar signs (might indicate financial data)
                        if '$' in text:
                            print("*** PAGE CONTAINS DOLLAR AMOUNTS ***")
                            # Show lines with dollar signs
                            lines_with_dollars = [line for line in text.split('\n') if '$' in line]
                            for line in lines_with_dollars[:5]:  # First 5 lines with $
                                print(f"  ${line}")


if __name__ == "__main__":
    scan_all_pdf_content()