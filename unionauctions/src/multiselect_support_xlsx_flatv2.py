##Union Aucitons working :  Main version as on 26/07/2025.

import pandas as pd
import json
from collections import defaultdict

def parse_inputs(row, count_col, label1_col, value1_col, label2_col, value2_col, label3_col, value3_col):
    inputs = []
    count = row.get(count_col)
    # FIX: Check for None and valid integer before conversion
    if count is not None and str(count).strip() and str(count).strip().isdigit():
        count = int(count)
        for i in range(1, count+1):
            label = row.get(f"{label1_col} ({i})", row.get(label1_col)) or f"P{i}"
            value_type = row.get(f"{value1_col} ({i})", row.get(value1_col)) or "Numeric"
            inputs.append({"label": str(label), "type": str(value_type), "value": None})
    else:
        # Handle up to 3 labels/values
        for label_col, value_col in [
            (label1_col, value1_col),
            (label2_col, value2_col),
            (label3_col, value3_col)
        ]:
            label = row.get(label_col)
            value_type = row.get(value_col)
            if label is not None and str(label).strip() and value_type is not None and str(value_type).strip():
                inputs.append({"label": str(label), "type": str(value_type), "value": None})
    return inputs

def parse_options(row, label_col):
    options_raw = row.get(label_col)
    options = []
    if options_raw is not None and str(options_raw).strip():
        # Support "/" or "," separated
        if "/" in str(options_raw):
            opts = [opt.strip() for opt in str(options_raw).replace("/", ",").split(",")]
        elif "," in str(options_raw):
            opts = [opt.strip() for opt in str(options_raw).split(",")]
        else:
            opts = [str(options_raw).strip()]
        for o in opts:
            options.append({"label": o, "selected": False})
    return options

def get_option_labels(option_raw):
    if option_raw is not None and str(option_raw).strip():
        if "/" in str(option_raw):
            return [opt.strip() for opt in str(option_raw).replace("/", ",").split(",")]
        elif "," in str(option_raw):
            return [opt.strip() for opt in str(option_raw).split(",")]
        else:
            return [str(option_raw).strip()]
    return []

def get_response_type(input_type):
    # Map inputType to responseType
    if not input_type:
        return ""
    input_type = str(input_type).lower()
    if "image" in input_type:
        return "image"
    if "video" in input_type:
        return "video"
    if "number" in input_type or "numeric" in input_type:
        return "number"
    if "singleselect" in input_type:
        return "singleselect"
    if "multiselect" in input_type:
        return "multiselect"
    return input_type

def excel_to_json(filepath):
    #df = pd.read_excel(filepath)
    # Check if first line starts with '#', and skip it if so
    with open(filepath, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        skiprows = 1 if first_line.lstrip().startswith('#') else 0
    df = pd.read_csv(filepath, skiprows=skiprows)
    print("Loaded columns:", list(df.columns))
    if 'SectionId' not in df.columns:
        raise KeyError("'SectionId' column not found in CSV. Please check the column names: " + str(list(df.columns)))
    df = df.fillna("")
    sections = defaultdict(list)
    for _, row in df.iterrows():
        section_id = int(row["SectionId"])
        section_label = row["Section"]
        question_id = int(row["MainQuestionId"])
        question_label = row.get("List itemsSQ1") or row.get("questionLabel") or ""
        subquestions = []

        # Subquestion 2 (Number/Other)
        if row.get("subquestion2Id") is not None and str(row.get("subquestion2Id")).strip():
            input_type2 = row.get("InputTypeSQ2", "")
            response_type2 = get_response_type(input_type2)
            validations2_raw = row.get("validationsSQ2", "")
            validations2_obj = {}
            if validations2_raw:
                for v in str(validations2_raw).split(";"):
                    if '=' in v:
                        k, val = v.split('=', 1)
                        validations2_obj[k.strip()] = val.strip()
            # If number, use a/b/c fields as inputs, else use parse_inputs
            if response_type2 == "number":
                label_value_pairs = [
                    (row.get("TextLabelSQ2a", ""), row.get("Input ValueSQ2a", "")),
                    (row.get("TextLabelSQ2b", ""), row.get("InputValueSQ2b", "")),
                    (row.get("TextLabelSQ2c", ""), row.get("Input ValueSQ2c", ""))
                ]
                inputs = []
                for label, value_type in label_value_pairs:
                    if label and str(label).strip():
                        inputs.append({
                            "label": label,
                            "type": value_type or "Numeric",
                            "value": None
                        })
                subq = {
                    "subquestionId": int(row["subquestion2Id"]),
                    "label": row.get("Text LabelSQ2", ""),
                    "inputType": input_type2,
                    "responseType": response_type2,
                    "validations": validations2_obj,
                    "inputs": inputs,
                    "options": []
                }
                subquestions.append(subq)
            else:
                subq = {
                    "subquestionId": int(row["subquestion2Id"]),
                    "label": row.get("Text LabelSQ2", ""),
                    "inputType": input_type2,
                    "responseType": response_type2,
                    "validations": validations2_obj,
                    "inputs": parse_inputs(row, "Input CountSQ2", "TextLabelSQ2a", "Input ValueSQ2a", "TextLabelSQ2b", "InputValueSQ2b", "TextLabelSQ2c", "Input ValueSQ2c"),
                    "options": []
                }
                subquestions.append(subq)
        # Subquestion 1 (Image/Video)
        if row.get("subquestion1Id") is not None and str(row.get("subquestion1Id")).strip():
            input_type = row.get("InputTypeSQ1", "")
            validations1_raw = row.get("validationsSQ1", "")
            validations1_obj = {}
            if validations1_raw:
                for v in str(validations1_raw).split(";"):
                    if '=' in v:
                        k, val = v.split('=', 1)
                        validations1_obj[k.strip()] = val.strip()
            subq = {
                "subquestionId": int(row["subquestion1Id"]),
                "label": row.get("List itemsSQ1", ""),
                "inputType": input_type,
                "responseType": get_response_type(input_type),
                "validations": validations1_obj,
                "photo": row.get("PhotoSQ1", ""),
                "video": row.get("VideoSQ1", ""),
                "response": {
                    "imageURL": "",
                    "aiimageURL": ""
                }
            }
            subquestions.append(subq)

        # Subquestion 4 (Singeselect/Multiselect)
        if row.get("subquestion4Id") is not None and str(row.get("subquestion4Id")).strip():
            input_type4 = row.get("InputType4", "")
            response_type4 = get_response_type(input_type4)
            validations4_raw = row.get("validations4", "")
            validations4_obj = {}
            if validations4_raw:
                for v in str(validations4_raw).split(";"):
                    if '=' in v:
                        k, val = v.split('=', 1)
                        validations4_obj[k.strip()] = val.strip()
            options = []
            selected_value = None
            selected_values = []
            option_labels = []
            input_value4 = row.get("InputValue4", "")
            if input_value4:
                option_labels = [opt.strip() for opt in str(input_value4).split("/") if opt.strip()]
            # For singleselect, use SelectedValue4; for multiselect, use SelectedValues4 (comma-separated)
            if response_type4 == "singleselect":
                selected_raw = row.get("SelectedValue4", "") if "SelectedValue4" in row else None
                for opt in option_labels:
                    selected = False
                    if selected_raw:
                        if str(opt) == str(selected_raw):
                            selected = False
                            selected_value = opt
                    elif not selected_value:
                        selected = False
                        selected_value = opt
                    options.append({"label": opt, "selected": selected})
            elif response_type4 == "multiselect":
                selected_raw = row.get("SelectedValues4", "") if "SelectedValues4" in row else None
                selected_set = set()
                if selected_raw:
                    selected_set = set([s.strip() for s in str(selected_raw).split(",") if s.strip()])
                for opt in option_labels:
                    selected = opt in selected_set
                    if selected:
                        selected_values.append(opt)
                    options.append({"label": opt, "selected": selected})
            subq = {
                "subquestionId": int(row["subquestion4Id"]),
                "label": row.get("TextLabel4", ""),
                "inputType": input_type4,
                "responseType": response_type4,
                "validations": validations4_obj,
                "inputs": [],
                "options": options
            }
            if response_type4 == "singleselect" and selected_value:
                subq["selectedValue"] = selected_value
            if response_type4 == "multiselect" and selected_values:
                subq["selectedValues"] = selected_values
            subquestions.append(subq)

        # Subquestion 3 (Number/Other)
        if row.get("subquestion3Id") is not None and str(row.get("subquestion3Id")).strip():
            input_type3 = row.get("InputType3", "")
            response_type3 = get_response_type(input_type3)
            validations3_raw = row.get("validations3", "")
            validations3_obj = {}
            if validations3_raw:
                for v in str(validations3_raw).split(";"):
                    if '=' in v:
                        k, val = v.split('=', 1)
                        validations3_obj[k.strip()] = val.strip()
            if response_type3 == "number":
                # For subquestion3Id, use label from 'TextLabel3', and inputs from 'TextLabel3a'/'InputValue3a' and 'TextLabel3b'/'InputValue3b'
                label_value_pairs = [
                    (row.get("TextLabel3a", ""), row.get("InputValue3a", "")),
                    (row.get("TextLabel3b", ""), row.get("InputValue3b", ""))
                ]
                inputs = []
                for label, value_type in label_value_pairs:
                    if label and str(label).strip():
                        inputs.append({
                            "label": label,
                            "type": value_type or "Numeric",
                            "value": None
                        })
                subq = {
                    "subquestionId": int(row["subquestion3Id"]),
                    "label": row.get("TextLabel3", ""),
                    "inputType": input_type3,
                    "responseType": response_type3,
                    "validations": validations3_obj,
                    "inputs": inputs,
                    "options": []
                }
                subquestions.append(subq)
            else:
                # Use original parse_inputs for other types
                subq = {
                    "subquestionId": int(row["subquestion3Id"]),
                    "label": row.get("TextLabel3a", ""),
                    "inputType": input_type3,
                    "responseType": response_type3,
                    "validations": validations3_obj,
                    "inputs": parse_inputs(row, "", "TextLabel3b", "InputValue3b", "TextLabel3c", "InputValue3c", "", ""),
                    "options": []
                }
                subquestions.append(subq)

        # Sort subquestions by subquestionId
        subquestions_sorted = sorted(subquestions, key=lambda sq: sq["subquestionId"])
        question = {
            "questionId": question_id,
            "questionLabel": question_label,
            "subquestions": subquestions_sorted
        }
        key = (section_id, section_label)
        sections[key].append(question)

    json_sections = []
    for (section_id, section_label), questions in sections.items():
        # Sort questions by questionId
        questions_sorted = sorted(questions, key=lambda q: q["questionId"])
        json_sections.append({
            "sectionId": section_id,
            "section": section_label,
            "totalQuestions": len(questions_sorted),
            "answeredQuestions": 0,
            "questions": questions_sorted
        })
    return json_sections

if __name__ == "__main__":
    inputpath = r"UnionAuctionQA2_CSV.csv"
    output = r"output.json"
    json_data = excel_to_json(inputpath)
    print(json.dumps(json_data, indent=2, ensure_ascii=False))
    with open(output, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)