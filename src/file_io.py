import json
from pathlib import Path
import os
import re

def save_question_json(question_obj, filepath):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(question_obj, ensure_ascii=False) + "\n")

def read_and_save_API_keys(api_keys_path):
    if api_keys_path := Path(api_keys_path):
        with api_keys_path.open("r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()

def calculate_questions_number(bible_text):
    # Find all verse numbers (numbers at the start of text or after punctuation)
    verse_numbers = re.findall(r'\d+', bible_text)
    
    if verse_numbers:
        # Get the last (highest) verse number
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
    