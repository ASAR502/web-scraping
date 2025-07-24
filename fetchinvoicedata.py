import os
import re
import pandas as pd
import pdfplumber
from collections import namedtuple

# Define the namedtuple structure for parsed lines
Line = namedtuple(
    'Line',
    'company_id company_name doctype reference currency voucher inv_date due_date open_amt_tc open_amt_bc current months1 months2 months3'
)

# Regular expressions
company_re = re.compile(r'(V\d+) (.*) Phone:')
line_re = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}/\d{2}/\d{4}')

lines = []

with pdfplumber.open('pdfs/samplereport.pdf') as pdf:
    for page in pdf.pages:
        print(f"Processing page {page.page_number}...")
        text = page.extract_text()

        # Extract company/vendor info
        comp = company_re.search(text)
        if comp:
            vend_no, vend_name = comp.group(1), comp.group(2)

        # Process each line of text
        for line in text.splitlines():
            if line.startswith('INVOICES'):
                doctype = 'INVOICE'

            elif line.startswith('CREDITNOTES'):
                doctype = 'CREDITNOTE'

            elif line_re.search(line):
                items = line.split()
                # Add parsed line to list
                lines.append(Line(vend_no, vend_name, doctype, *items))

            elif line.startswith('Supplier total'):
                total_check = float(line.split()[2].replace(',', ''))
                # Do something with total_check if required

# Convert list of namedtuples to DataFrame
df = pd.DataFrame(lines)
df.head()

print(df)

    