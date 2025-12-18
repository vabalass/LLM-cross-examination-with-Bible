import json
import re
import os
import pandas as pd

def parse_questions_to_json(raw_text):
    if raw_text is None:
        print("Parser klaida: tuščias tekstas.")
        return []

    try:
        cleaned_text = re.sub(r'^\s*```json\s*|\s*```\s*$', '', raw_text, flags=re.DOTALL)
        
        data = json.loads(cleaned_text)
        
        if "questions" in data and isinstance(data["questions"], list):
            
            parsed_questions = []
            for item in data["questions"]:
                if all(key in item for key in ["question_text", "options", "correct_answer"]):
                    parsed_questions.append({
                        "question": item["question_text"],
                        "options": item["options"],
                        "correct": item["correct_answer"].lower(),
                    })
            return parsed_questions

        print("Parser klaida: JSON formatas neatitinka struktūros.")
        return ""
    except Exception as e:
        print(f"Parser klaida: {e}")
        return ""
    
def json_to_csv(input_json_path: str, output_csv_path: str):
    print(f"Parser: pradedamas konvertavimas į csv...")
    
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Parser klaida: failas '{input_json_path}' nerastas.")
        return
    except json.JSONDecodeError:
        print(f"Parser klaida: Nepavyko dekoduoti JSON failo '{input_json_path}'.")
        return

    records = []
    for question in data:
        common_data = {
            'Klausimo ID': question.get('question_id'),
            'Skyrius': question.get('chapter'),
            'Autorius': question.get('question_creator_model'),
            'Klausimas': question.get('question'),
            'Teisingas': question.get('correct_answer_key'),
        }

        options_str = ""
        options = question.get('options', {})
        for key, value in options.items():
            options_str += f"{key}: {value}; "
        common_data['Variantai'] = options_str.strip()

        evaluations = question.get('evaluations', [])
        
        if not evaluations:
            records.append(common_data)
            continue

        for evaluation in evaluations:
            record = common_data.copy()
            record.update({
                'Vertintojas': evaluation.get('evaluator_model'),
                'Įvertinimas': evaluation.get('grade'),
                'Komentaras': evaluation.get('comment')
            })
            records.append(record)

    if not records:
        print("Ispėjimas: nėra jokių įrašų.")
        return
        
    df = pd.DataFrame(records)
    
    try:
        os.makedirs(os.path.dirname(output_csv_path) or '.', exist_ok=True)
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"INFO: failas {output_csv_path} sėkmingai išsaugotas.")
    except Exception as e:
        print(f"Klaida: {e}")

def extract_json_from_text(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"(\{[\s\S]*\})", text)
    if m:
        candidate = m.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            return None

    return None