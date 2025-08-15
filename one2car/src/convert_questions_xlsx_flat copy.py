import pandas as pd
import openpyxl
import re
import numpy as np
import os
import logging
import json
import ast

# File paths
source_file = 'input/One2Car Questions_V2.xlsx'
dest_file = 'output/TEST_questoinary_flat3.xlsx'

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

logging.info(f"Reading from: {source_file}")
logging.info(f"Current working directory: {os.getcwd()}")  # Print current working directory
# Exit to prevent further execution in this example
# Read the source Excel file
try:
    df = pd.read_excel(source_file)
    print(df.head(10))  # Print first few rows for debugging
    logging.info(f"Loaded {len(df)} rows from source Excel file.")
except Exception as e:
    logging.error(f"Error reading {source_file}: {e}")
    exit(1)

def get_section_id(val):
    if pd.isnull(val):
        return None
    m = re.match(r'^(\d+)$', str(val).strip())
    return m.group(1) if m else None

def get_question_id(val):
    if pd.isnull(val):
        return None
    # Accept both int and float-like strings, but always return int
    s = str(val).strip()
    # If it's a float string like '1001.0', convert to int
    if re.match(r'^\d+\.0$', s):
        return int(float(s))
    # If it's an int string
    if re.match(r'^\d+$', s):
        return int(s)
    # If it's a float string like '1001.5', keep as float
    if re.match(r'^\d+\.\d+$', s):
        return float(s)
    return None

def safe_get(row, col):
    return row[col] if col in row and pd.notnull(row[col]) else None

def parse_type_from_validations(val):
    # If val is a string like 'type=prefix_suffix,min=1', parse it
    if not val or not isinstance(val, str):
        return None
    for part in val.split(';'):
        if '=' in part:
            k, v = part.split('=', 1)
            if k.strip() == 'type':
                return v.strip()
    return None


rows = []
current_section_id = 0  # Will start at 10 for first section
current_section_title = None
for idx, row in df.iterrows():
    sid_val = row.get('sectionId', None)
    question_text = safe_get(row, 'Question')
    if sid_val is None or pd.isnull(sid_val):
        # New section starts
        current_section_id += 10
        # If question_text is present, use it as the section title
        if question_text and isinstance(question_text, str) and question_text.strip():
            current_section_title = question_text.strip()
            logging.info(f"Section {current_section_id} title set to: {current_section_title}")
        else:
            current_section_title = None
        logging.info(f"Found section: {current_section_id} - {current_section_title}")
        continue  # skip section header row
    # For all rows, use the last found section title
    qid = get_question_id(row.get('sectionId', None))
    if qid is not None:
        # Always use int for questionId if possible
        question_id = int(qid) if isinstance(qid, (int, float)) and float(qid).is_integer() else qid
        question_type = safe_get(row, 'QuestionType')
        global_validations = safe_get(row, 'globalValidations')
        options_str = safe_get(row, 'options_seperated_by_comma')
        option_suffix = safe_get(row, 'optionSuffix')
        option_validations = safe_get(row, 'optionValidations')
        option_response = safe_get(row, 'optionResponse')
        logging.info(f"Processing question: {question_id} - {question_text}")
        # Split options and create a row for each
        if options_str and isinstance(options_str, str):
            options = [opt.strip() for opt in options_str.split(',') if opt.strip()]
        else:
            options = [None]
        # Only assign suffixes if globalValidations has type=prefix_suffix
        use_suffix = False
        suffixes = []
        if parse_type_from_validations(global_validations) == 'prefix_suffix':
            use_suffix = True
        if use_suffix and option_suffix and isinstance(option_suffix, str):
            suffixes = [s.strip() for s in option_suffix.split(',')]
        # Assign suffixes to options in order, fill with None if missing
        for i, opt in enumerate(options, 1):
            suffix = suffixes[i-1] if use_suffix and i-1 < len(suffixes) else None
            logging.info(f"  Adding option {i}: {opt}, suffix: {suffix}")
            # optionId = questionId*10 + i
            opt_id = None
            if question_id is not None and isinstance(question_id, int):
                opt_id = question_id * 10 + i
            rows.append({
                'sectionId': current_section_id,
                'sectionTitle': current_section_title,
                'questionId': question_id,
                'questionText': question_text,
                'questionType': question_type,
                'globalValidations': global_validations,
                'optionId': opt_id,
                'optionLabel': opt,
                'optionSuffix': suffix,
                'optionValidations': option_validations,
                'optionResponse': option_response
            })

# Create DataFrame and write to Excel
out_df = pd.DataFrame(rows)
logging.info(f"Writing {len(out_df)} rows to Excel file: {dest_file}")
# Ensure all columns are present
columns = [
    'sectionId', 'sectionTitle', 'questionId', 'questionText', 'questionType',
    'globalValidations', 'optionId', 'optionLabel', 'optionSuffix', 'optionValidations', 'optionResponse'
]
out_df = out_df.reindex(columns=columns)
out_df.replace({np.nan: None}, inplace=True)
out_df.to_excel(dest_file, index=False)
logging.info(f"Excel file created at: {dest_file}")
