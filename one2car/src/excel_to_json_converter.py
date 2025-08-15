import openpyxl
import json
from collections import defaultdict

excel_path = 'C:\\WiseDrive\\python_code\\inspection_excelTOjson\\one2car\\output\\eng_v3_flat.xlsx'
json_path = 'C:\\WiseDrive\\python_code\\inspection_excelTOjson\\one2car\\output\\One2Car_SYSTEMGENERATED_Fixed_eng_v3.json'

def parse_plaintext_dict(s):
    if not s or not isinstance(s, str):
        return {}
    d = {}
    for pair in s.split(';'):
        if '=' in pair:
            k, v = pair.split('=', 1)
            v = v.strip()
            # Try to convert to bool or int if possible
            if v.lower() == 'true':
                v = True
            elif v.lower() == 'false':
                v = False
            else:
                try:
                    v = int(v)
                except ValueError:
                    pass
            d[k.strip()] = v
    return d

def group_by(items, keys):
    grouped = defaultdict(list)
    for item in items:
        key = tuple(item[k] for k in keys)
        grouped[key].append(item)
    return grouped

wb = openpyxl.load_workbook(excel_path)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
header = rows[0]
data_rows = [dict(zip(header, row)) for row in rows[1:]]

# Group by sectionId, sectionTitle
grouped_sections = group_by(data_rows, ['sectionId', 'sectionTitle'])
sections = []
for (sectionId, sectionTitle), section_rows in grouped_sections.items():
    # Group by questionId
    grouped_questions = group_by(section_rows, ['questionId'])
    questions = []
    for questionId, question_rows in grouped_questions.items():
        q = question_rows[0]
        question = {
            'questionId': q['questionId'],
            'questionText': q['questionText'],
            'questionType': q['questionType'],
            'globalValidations': parse_plaintext_dict(q['globalValidations']) if q['globalValidations'] else {},
            'options': []
        }
        for opt in question_rows:
            option = {
                'optionId': opt['optionId'],
                'label': opt['optionLabel'],
                'suffix': opt['optionSuffix'] if opt['optionSuffix'] else None,
                'thumbnailImage': opt['thumbnailImage'] if opt.get('thumbnailImage') else None,
                'validations': parse_plaintext_dict(opt['optionValidations']) if opt['optionValidations'] else None,
                'response': parse_plaintext_dict(opt['optionResponse']) if opt['optionResponse'] else None
            }
            # Remove suffix if None for cleaner JSON
            if option['thumbnailImage'] is None:
                del option['thumbnailImage']
            question['options'].append(option)
        questions.append(question)
    sections.append({
        'sectionId': sectionId,
        'sectionTitle': sectionTitle,
        'answeredQuestions':0,
        'questions': questions
    })

output = {
    'sections': sections
}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

print(f'JSON file created at: {json_path}')
