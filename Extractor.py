import pdfplumber
import pandas as pd
import os
import re
from datetime import datetime
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')


class FHFDataExtractor:
    def __init__(self, downloads_folder="downloads"):
        self.downloads_folder = downloads_folder
        self.report_summaries = []
        self.contributions = []
        self.expenditures = []

    def extract_all_data(self):
        """Main method to extract data from all PDFs"""
        pdf_files = [f for f in os.listdir(self.downloads_folder) if f.endswith('.pdf')]

        print(f"Found {len(pdf_files)} PDF files")

        # Process each PDF
        all_reports = {}  # For handling amendments

        for pdf_file in pdf_files:
            try:
                print(f"Processing {pdf_file}...")
                pdf_path = os.path.join(self.downloads_folder, pdf_file)
                report_data = self.extract_pdf_data(pdf_path, pdf_file)

                if report_data:
                    # Store for amendment handling
                    key = (report_data['report_type'], report_data['period_from'], report_data['period_through'])
                    if key not in all_reports or report_data['file_date'] > all_reports[key]['file_date']:
                        all_reports[key] = report_data

            except Exception as e:
                print(f"Error processing {pdf_file}: {str(e)}")
                continue

        # Process the latest versions only
        for report_data in all_reports.values():
            self.process_report_data(report_data)

        # Create CSV files
        self.create_csv_files()
        print("Extraction complete!")

    def extract_pdf_data(self, pdf_path, filename):
        """Extract data from a single PDF"""
        with pdfplumber.open(pdf_path) as pdf:
            report_data = {
                'filename': filename,
                'pages': [],
                'text_content': []
            }

            # Extract text from all pages
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    report_data['text_content'].append(text)
                    report_data['pages'].append(page_num + 1)

            # Parse report info from first page
            if report_data['text_content']:
                first_page = report_data['text_content'][0]

                # Extract basic report info
                report_data.update(self.parse_cover_page(first_page))

                # Extract financial data from all pages
                report_data['summary'] = self.extract_summary_data(report_data['text_content'])
                report_data['contributions'] = self.extract_contributions_data(report_data['text_content'])
                report_data['expenditures'] = self.extract_expenditures_data(report_data['text_content'])

                return report_data
        return None

    def parse_cover_page(self, text):
        """Parse basic info from cover page"""
        data = {}

        # Committee name
        name_match = re.search(r'Francis Howell Families', text, re.IGNORECASE)
        data['committee_name'] = 'Francis Howell Families' if name_match else 'Unknown'

        # Report date
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
        if date_match:
            try:
                data['file_date'] = datetime.strptime(date_match.group(1), '%m/%d/%Y')
            except:
                data['file_date'] = datetime.now()
        else:
            data['file_date'] = datetime.now()

        # Period covered - look for FROM/THROUGH pattern
        period_match = re.search(r'FROM\s+(\d{1,2}/\d{1,2}/\d{4})\s+THROUGH\s+(\d{1,2}/\d{1,2}/\d{4})', text)
        if period_match:
            data['period_from'] = period_match.group(1)
            data['period_through'] = period_match.group(2)
        else:
            data['period_from'] = ''
            data['period_through'] = ''

        # Report type
        if 'COMMITTEE QUARTERLY REPORT' in text:
            data['report_type'] = 'Quarterly'
        elif 'AMENDED' in text or 'AMENDING' in text:
            data['report_type'] = 'Quarterly (Amended)'
        else:
            data['report_type'] = 'Unknown'

        # Amendment status
        data['is_amendment'] = 'AMENDED' in text or 'AMENDING' in text

        return data

    def extract_summary_data(self, pages):
        """Extract financial summary data"""
        summary = {}

        for page_text in pages:
            if 'REPORT SUMMARY' in page_text:
                # Extract key financial figures using more flexible patterns

                # Money on hand at beginning
                beginning_patterns = [
                    r'Money On Hand at the beginning[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)',
                    r'beginning of\s+this reporting period[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)'
                ]
                for pattern in beginning_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        summary['money_on_hand_beginning'] = self.parse_amount(match.group(1))
                        break

                # Money on hand at close
                close_patterns = [
                    r'Money On Hand at the close[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)',
                    r'close of this\s+reporting period[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)'
                ]
                for pattern in close_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        summary['money_on_hand_ending'] = self.parse_amount(match.group(1))
                        break

                # Monetary contributions this period
                contrib_patterns = [
                    r'All Monetary Contributions Received\s+This Period[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)',
                    r'Monetary Contributions.*?This Period[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)'
                ]
                for pattern in contrib_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        summary['monetary_receipts_period'] = self.parse_amount(match.group(1))
                        break

                # Expenditures made this period
                expend_patterns = [
                    r'Expenditures made by cash or check\s+this period[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)',
                    r'Total All expenditures made this period[^$\d]*?(\d{1,3}(?:,\d{3})*\.?\d*)'
                ]
                for pattern in expend_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        summary['total_expenditures_period'] = self.parse_amount(match.group(1))
                        break

                break

        return summary

    def extract_contributions_data(self, pages):
        """Extract contributions data from CONTRIBUTIONS AND LOANS RECEIVED pages"""
        contributions = []

        for page_text in pages:
            if 'CONTRIBUTIONS AND LOANS RECEIVED' in page_text:
                print("Found contributions page, parsing...")
                contributions.extend(self.parse_contributions_table(page_text))

        return contributions

    def parse_contributions_table(self, text):
        """Parse the contributions table structure"""
        contributions = []

        # Split text into lines for easier parsing
        lines = text.split('\n')

        # Find contribution entries by looking for patterns
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for contributor name patterns (skip form field labels)
            if (line and
                    not line.startswith(
                        ('NAME:', 'ADDRESS:', 'CITY', 'EMPLOYER:', 'COMMITTEE:', '$', 'MONETARY', 'IN-KIND')) and
                    not 'SUBTOTAL' in line and
                    not 'TOTAL' in line and
                    len(line) < 100 and
                    len(line) > 2):

                # This might be a contributor name, look ahead for address and amount
                contributor_data = {'name': line}

                # Look ahead for address, date, and amount
                j = i + 1
                while j < min(i + 10, len(lines)):  # Look ahead max 10 lines
                    next_line = lines[j].strip()

                    # Look for address (has numbers and street indicators)
                    if (re.match(r'\d+.*(?:Dr|Rd|St|Ave|Lane|Circle|Court|Street)', next_line) and
                            'address' not in contributor_data):
                        contributor_data['address'] = next_line

                    # Look for city/state/zip
                    elif (re.search(r'[A-Za-z\s]+\s+[A-Z]{2}\s+\d{5}', next_line) and
                          'city_state' not in contributor_data):
                        contributor_data['city_state'] = next_line

                    # Look for employer/occupation (contains --)
                    elif (' -- ' in next_line and 'occupation' not in contributor_data):
                        parts = next_line.split(' -- ')
                        if len(parts) >= 2:
                            contributor_data['employer'] = parts[0].strip()
                            contributor_data['occupation'] = parts[1].strip()

                    # Look for date and amount pattern
                    elif re.search(r'(\d{1,2}/\d{1,2}/\d{4})', next_line):
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', next_line)
                        if date_match:
                            contributor_data['date'] = date_match.group(1)

                        # Look for amount in this line or nearby lines
                        amount_match = re.search(r'\$?\s*([\d,]+\.?\d*)', next_line)
                        if amount_match:
                            contributor_data['amount'] = self.parse_amount(amount_match.group(1))
                        else:
                            # Check the line before or after for amount
                            for check_line in [lines[j - 1] if j > 0 else '',
                                               lines[j + 1] if j + 1 < len(lines) else '']:
                                amount_match = re.search(r'\$?\s*([\d,]+\.?\d*)', check_line)
                                if amount_match and self.parse_amount(amount_match.group(1)) > 0:
                                    contributor_data['amount'] = self.parse_amount(amount_match.group(1))
                                    break

                    j += 1

                # If we found enough data, create a contribution record
                if ('name' in contributor_data and
                        'amount' in contributor_data and
                        contributor_data['amount'] > 0):

                    full_address = contributor_data.get('address', '')
                    if 'city_state' in contributor_data:
                        full_address += ', ' + contributor_data['city_state']

                    contributions.append({
                        'contributor_name': contributor_data['name'],
                        'contributor_address': full_address,
                        'date_received': contributor_data.get('date', ''),
                        'individual_amount': contributor_data['amount'],
                        'aggregate_amount': contributor_data['amount'],  # For now, same as individual
                        'contribution_type': 'Monetary',  # Default
                        'employer': contributor_data.get('employer', ''),
                        'occupation': contributor_data.get('occupation', '')
                    })

                    print(f"  Found contributor: {contributor_data['name']} - ${contributor_data['amount']}")

                # Skip ahead to avoid re-processing the same contributor
                i = j
            else:
                i += 1

        return contributions

    def extract_expenditures_data(self, pages):
        """Extract expenditures data"""
        expenditures = []

        for page_text in pages:
            if ('EXPENDITURES' in page_text and
                    ('ITEMIZED' in page_text or 'SUPPLEMENTAL' in page_text)):
                print("Found expenditures page, parsing...")
                expenditures.extend(self.parse_expenditures_table(page_text))

        return expenditures

    def parse_expenditures_table(self, text):
        """Parse the expenditures table structure"""
        expenditures = []

        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for vendor/recipient names (skip form labels)
            if (line and
                    not line.startswith(('NAME:', 'ADDRESS:', 'CITY', '$', 'PAID', 'INCURRED')) and
                    not 'SUBTOTAL' in line and
                    not 'TOTAL' in line and
                    not 'PURPOSE' in line and
                    len(line) < 100 and
                    len(line) > 2):

                expense_data = {'vendor': line}

                # Look ahead for address, purpose, amount, and date
                j = i + 1
                while j < min(i + 15, len(lines)):  # Look ahead max 15 lines
                    next_line = lines[j].strip()

                    # Look for address
                    if (re.match(r'\d+.*(?:Dr|Rd|St|Ave|Lane|Circle|Court|Street)', next_line) and
                            'address' not in expense_data):
                        expense_data['address'] = next_line

                    # Look for city/state/zip
                    elif (re.search(r'[A-Za-z\s]+\s+[A-Z]{2}\s+\d{5}', next_line) and
                          'city_state' not in expense_data):
                        expense_data['city_state'] = next_line

                    # Look for purpose/description with amount
                    elif re.search(r'^[a-zA-Z\s]+\s+([\d.]+)$', next_line):
                        purpose_match = re.search(r'^([a-zA-Z\s]+)\s+([\d.]+)$', next_line)
                        if purpose_match:
                            expense_data['purpose'] = purpose_match.group(1).strip()
                            expense_data['amount'] = self.parse_amount(purpose_match.group(2))

                    # Look for date
                    elif re.search(r'(\d{1,2}/\d{1,2}/\d{4})', next_line):
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', next_line)
                        if date_match:
                            expense_data['date'] = date_match.group(1)

                        # Also check for amount in same line if not found yet
                        if 'amount' not in expense_data:
                            amount_match = re.search(r'([\d,]+\.?\d*)', next_line)
                            if amount_match:
                                expense_data['amount'] = self.parse_amount(amount_match.group(1))

                    j += 1

                # If we found enough data, create an expenditure record
                if ('vendor' in expense_data and
                        'amount' in expense_data and
                        expense_data['amount'] > 0):

                    full_address = expense_data.get('address', '')
                    if 'city_state' in expense_data:
                        full_address += ', ' + expense_data['city_state']

                    expenditures.append({
                        'expense_category': expense_data.get('purpose', 'General'),
                        'amount': expense_data['amount'],
                        'recipient_name': expense_data['vendor'],
                        'recipient_address': full_address,
                        'purpose': expense_data.get('purpose', ''),
                        'date_paid': expense_data.get('date', '')
                    })

                    print(f"  Found expenditure: {expense_data['vendor']} - ${expense_data['amount']}")

                # Skip ahead to avoid re-processing
                i = j
            else:
                i += 1

        return expenditures

    def parse_amount(self, amount_str):
        """Parse amount string to float"""
        if not amount_str:
            return 0.0

        # Remove commas and dollar signs
        clean_amount = re.sub(r'[,$]', '', str(amount_str))

        try:
            return float(clean_amount)
        except:
            return 0.0

    def process_report_data(self, report_data):
        """Process a single report's data"""
        # Add to report summaries
        summary_row = {
            'filename': report_data['filename'],
            'committee_name': report_data.get('committee_name', ''),
            'report_type': report_data.get('report_type', ''),
            'period_from': report_data.get('period_from', ''),
            'period_through': report_data.get('period_through', ''),
            'file_date': report_data.get('file_date', ''),
            'is_amendment': report_data.get('is_amendment', False),
            'money_on_hand_beginning': report_data['summary'].get('money_on_hand_beginning', 0.0),
            'money_on_hand_ending': report_data['summary'].get('money_on_hand_ending', 0.0),
            'total_receipts_period': report_data['summary'].get('total_receipts_period', 0.0),
            'total_expenditures_period': report_data['summary'].get('total_expenditures_period', 0.0),
            'monetary_receipts_period': report_data['summary'].get('monetary_receipts_period', 0.0)
        }
        self.report_summaries.append(summary_row)

        # Add contributions
        for contrib in report_data['contributions']:
            contrib_row = contrib.copy()
            contrib_row['filename'] = report_data['filename']
            contrib_row['report_period_from'] = report_data.get('period_from', '')
            contrib_row['report_period_through'] = report_data.get('period_through', '')
            self.contributions.append(contrib_row)

        # Add expenditures
        period_start = report_data.get('period_from', '')
        for expense in report_data['expenditures']:
            expense_row = expense.copy()
            expense_row['filename'] = report_data['filename']
            expense_row['report_period_from'] = report_data.get('period_from', '')
            expense_row['report_period_through'] = report_data.get('period_through', '')
            # Use period start date if no specific date
            if not expense_row['date_paid']:
                expense_row['date_paid'] = period_start
            self.expenditures.append(expense_row)

    def create_csv_files(self):
        """Create the three CSV output files"""

        # Report Summaries
        if self.report_summaries:
            df_summaries = pd.DataFrame(self.report_summaries)
            df_summaries.to_csv('FHF_report_summaries.csv', index=False)
            print(f"Created FHF_report_summaries.csv with {len(df_summaries)} records")

        # Contributions
        if self.contributions:
            df_contributions = pd.DataFrame(self.contributions)
            df_contributions.to_csv('FHF_contributions_received.csv', index=False)
            print(f"Created FHF_contributions_received.csv with {len(df_contributions)} records")
        else:
            # Create empty file with headers
            df_contributions = pd.DataFrame(columns=[
                'filename', 'contributor_name', 'contributor_address', 'date_received',
                'individual_amount', 'aggregate_amount', 'contribution_type', 'employer',
                'occupation', 'report_period_from', 'report_period_through'
            ])
            df_contributions.to_csv('FHF_contributions_received.csv', index=False)
            print("Created empty FHF_contributions_received.csv with headers")

        # Expenditures
        if self.expenditures:
            df_expenditures = pd.DataFrame(self.expenditures)
            df_expenditures.to_csv('FHF_expenditures_made.csv', index=False)
            print(f"Created FHF_expenditures_made.csv with {len(df_expenditures)} records")
        else:
            # Create empty file with headers
            df_expenditures = pd.DataFrame(columns=[
                'filename', 'expense_category', 'amount', 'recipient_name', 'recipient_address',
                'purpose', 'date_paid', 'report_period_from', 'report_period_through'
            ])
            df_expenditures.to_csv('FHF_expenditures_made.csv', index=False)
            print("Created empty FHF_expenditures_made.csv with headers")


def main():
    """Main execution function"""
    # Create extractor instance
    extractor = FHFDataExtractor("downloads")

    # Check if downloads folder exists
    if not os.path.exists("downloads"):
        print("Error: 'downloads' folder not found!")
        print("Please ensure your PDF files are in a 'downloads' folder in the current directory.")
        return

    # Run extraction
    print("Starting Francis Howell Families PDF data extraction...")
    extractor.extract_all_data()

    print("\nExtraction Summary:")
    print(f"- Report Summaries: {len(extractor.report_summaries)} records")
    print(f"- Contributions: {len(extractor.contributions)} records")
    print(f"- Expenditures: {len(extractor.expenditures)} records")

    print("\nFiles created:")
    print("- FHF_report_summaries.csv")
    print("- FHF_contributions_received.csv")
    print("- FHF_expenditures_made.csv")


if __name__ == "__main__":
    main()