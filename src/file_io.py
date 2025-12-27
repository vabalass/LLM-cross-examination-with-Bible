import json
from pathlib import Path
import os
import re

def add_important_parameters_to_evaluations(evaluations_json, model, source_text_path):
    updated_json = {
        "metadata": {
            "evaluator_model": model,
            "source": source_text_path.stem
        },
        "results": evaluations_json  # Čia įsideda jūsų originalus sąrašas
    }

    return updated_json

def save_json_file(json_obj, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_obj, f, ensure_ascii=False, indent=4)

def read_and_save_API_keys(api_keys_path):
    if api_keys_path := Path(api_keys_path):
        with api_keys_path.open("r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()

def calculate_questions_number(bible_text):
    verse_numbers = re.findall(r'\d+', bible_text)
    
    if verse_numbers:
        last_verse = int(verse_numbers[-1])
        questions_number = max(1, last_verse // 3)
    else:
        questions_number = 1
    
    print(f"file_io: apskaičiuotas klausimų skaičius: {questions_number}")
    return str(questions_number)

def load_questions(question_file):
    try:
        with open(question_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith('['):
                return json.loads(content)
            else:
                return [json.loads(line) for line in content.split('\n') if line.strip()]
    except FileNotFoundError:
        print(f"file_io klaida: įvesties failas '{question_file}' nerastas. Prašome sugeneruoti klausimus.")
        return []
    except json.JSONDecodeError as e:
        print(f"file_io klaida: nepavyko išparsinti '{question_file}': {e}")
        return []

def find_first_json_in_file(filepath):
    path = Path(filepath)

    first_json = next((f for f in path.rglob("*.json") if f.is_file()), None)
    if(first_json):
        return first_json
    else:
        print("file_io klaida: nepavyko rasti json failo.")
        return None

def paths_exist(paths):
    if not paths:
        print("file_io įspėjimas: tikrinimui nebuvo pateikta jokių kelių.")
        return False
    
    for path in paths:
        if path is None or not Path(path).exists():
            print(f"file_io klaida: neegzistuoja kelias {path}.")
            return False
        
    return True
    
