from pathlib import Path
from litellm import completion
import pandas as pd
import os
import json
import re
import time

# returns n Bible questions with 4 choice answers (a, b, c, d)
def get_bible_question_from_llm(model, bible_text, max_retries=1, number_of_questions=1):
    for attempt in range(1, max_retries + 1):
        try:
            if model is not None and bible_text != "":
                message_content = (
                    "Sukurk " + number_of_questions +  " klausimus su keturiais atsakymų variantais (a, b, c, d) iš pateikto Biblijos teksto. " +
                    "Tik vienas atsakymas turi būti teisingas. " +
                    "Grąžink atsakymą IŠSKIRTINAI JSON formatu. JSON struktūra turi būti tokia:\n" +
                    "{\n" +
                    '  "questions": [\n' +
                    "    {\n" +
                    '      "question_text": "...",\n' +
                    '      "options": {"a": "...", "b": "...", "c": "...", "d": "..."},' +
                    '      "correct_answer": "a"\n' +
                    "    },\n" +
                    "    {... (antras klausimas) ...},\n" +
                    "    {... (trečias klausimas) ...}\n" +
                    "  ]\n" +
                    "}\n" +
                    "Neįtraukite jokių paaiškinimų ar papildamo teksto, tik JSON.\n\n" +
                    bible_text
                )
                message = [{ "content": message_content,"role": "user"}]
                response = completion(model=model, messages=message)
                print("Atsakymas gautas.")
                if response.choices:
                    return response.choices[0].message["content"]
                else:
                    print("Klaida: Atsakymo variantų nerasta.")
                    if attempt < max_retries:
                        print(f"Bandymas {attempt}/{max_retries-1}. Laukiu 5 sekundžių prieš pakartojimu...")
                        time.sleep(5)
                        continue
                    return None
            return None
        except Exception as e:
            print(f"Klaida: {e}")
            if attempt < max_retries:
                print(f"Bandymas {attempt}/{max_retries-1}...")
                time.sleep(5)
                continue
            return None

def parse_question(raw_text):
    if raw_text is None:
        print("Klaida: tuščias tekstas.")
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

        print("Klaida: JSON formatas neatitinka struktūros.")
        return []
    except Exception as e:
        print(f"Klaida: {e}")
        return []

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

def generate_evaluation_prompt(question_data, bible_text):        
    prompt = f"""
    BIBLIJOS IŠTRAUKA:
    {bible_text}

    Tu esi Šv. Rašto ekspertas.
    Atlikti klausimo teisingumo įvertinimą (grade) pagal šią skalę:
        0 - Nekorektiškas klausimas (Ydingas, neaiškus, neatitinka konteksto).
        1 - Akivaizdžiai Neteisingas atsakymas (Nurodyta raidė prieštarauja teksto faktams).
        2 - Iš dalies teisingas/Klaidinantis (Susijęs, bet per daug abstraktus ar nereikšmingas).
        3 - Tiesiogiai Netikslus (Faktas teisingas, bet netiksliai cituoja detales/eilės tvarką).
        4 - Teisingas, su Formuluotės Trūkumais (Faktas teisingas, bet formuluotė neaiški/per ilga).
        5 - Idealiai Teisingas ir Aiški Formuluotė (Nepriekaištingas atsakymas ir elegantiška formuluotė).

    KLAUSIMAS: {question_data['question']}

    a) {question_data['options']['a']}
    b) {question_data['options']['b']}
    c) {question_data['options']['c']}
    d) {question_data['options']['d']}

    Nurodytas TEISINGAS ATSAKYMAS (Raidė): {question_data['correct'].upper()}

    Pateikite savo įvertinimą TIK šiuo JSON formatu:
    {{
    "grade":,
    "comment": "[1-2 sakinių ilgio paaiškinimas dėl suteikto įvertinimo]"
    }}

    """
    return prompt

def evaluate_question_with_llm(model, prompt, max_retries=1):
    for attempt in range(1, max_retries + 1):
        try:
            message = [{ "content": prompt, "role": "user"}]
            response = completion(model=model, messages=message)
            
            if response and response.choices:
                return response.choices[0].message["content"]
            else:
                print("Klaida: nerasta atsakymo variantų atsakyme.")
                if attempt < max_retries:
                    print(f"Bandymas {attempt}/{max_retries-1}. Laukiu 5 sekundžių prieš pakartojimu...")
                    time.sleep(5)
                    continue
                return None
                
        except Exception as e:
            print(f"Klaida generuojant įvertinimą: {e}")
            if attempt < max_retries:
                print(f"Bandymas {attempt}/{max_retries-1}. Laukiu 5 sekundžių prieš pakartojimu...")
                time.sleep(5)
                continue
            return None

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

def calculate_questions_number(bible_text):
    # Find all verse numbers (numbers at the start of text or after punctuation)
    verse_numbers = re.findall(r'\d+', bible_text)
    
    if verse_numbers:
        # Get the last (highest) verse number
        last_verse = int(verse_numbers[-1])
        questions_number = max(1, last_verse // 3)
    else:
        questions_number = 1
    
    print(f"INFO: apskaičiuotas klausimų skaičius: {questions_number}")
    return str(questions_number)

def generate_questions(models, bible_text, chapter_name, question_file):
    all_questions = []
    question_counter = 1
    
    for model in models:
        print(f"INFO: Generuojami klausimai naudojant modelį {model}...")
        number_of_questions = calculate_questions_number(bible_text)
        raw_question = get_bible_question_from_llm(model=model, bible_text=bible_text, number_of_questions=number_of_questions)
        
        if raw_question is None:
            print("Klaida: tuščias tekstas iš modelio.")
            continue
        
        parsed_list = parse_question(raw_question)
        
        for parsed in parsed_list:
            if not parsed.get('question') or not parsed.get('options'):
                print(f"Klaida: praleistas nevalidus klausimas iš modelio {model}.")
                continue
            
            question_id = f"{chapter_name}_{question_counter:03d}"
            question_counter += 1
            
            question_obj = {
                "id": question_id,
                "question": parsed.get('question'),
                "options": parsed.get('options'),
                "correct": parsed.get('correct'),
                "model": model,
                "chapter": chapter_name
            }
            all_questions.append(question_obj)
    
    try:
        with open(question_file, "w", encoding="utf-8") as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)
        print(f"INFO: {len(all_questions)} klausimų įrašyta į '{question_file}'.")
    except Exception as e:
        print(f"Klaida: nepavyko išsaugoti: {e}")

def load_questions(question_file):
    try:
        with open(question_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith('['):
                return json.loads(content)
            else:
                return [json.loads(line) for line in content.split('\n') if line.strip()]
    except FileNotFoundError:
        print(f"Klaida: įvesties failas '{question_file}' nerastas. Prašome sugeneruoti klausimus.")
        return []
    except json.JSONDecodeError as e:
        print(f"Klaida: nepavyko išparsinti '{question_file}': {e}")
        return []

def evaluate_questions(questions, models, bible_text, evaluations_file):
    grouped = []
    
    for i, question in enumerate(questions):
        print(f"INFO: vertinamas klausimas {i+1}...")
        
        chapter = question.get("chapter")
        question_id = f"{chapter}_{i+1:03d}"
        
        entry = {
            "question_id": question_id,
            "chapter": chapter,
            "question_creator_model": question.get("model"),
            "question": question.get("question"),
            "options": question.get("options"),
            "correct_answer_key": question.get("correct"),
            "evaluations": []
        }

        for model in models:
            if model == question.get('model'):
                print(f"INFO: Modelis {model} praleidžiamas (sukūrė šį klausimą).")
                continue

            prompt = generate_evaluation_prompt(question, bible_text)
            evaluation_result = evaluate_question_with_llm(model, prompt)

            parsed_eval = extract_json_from_text(evaluation_result)
            if parsed_eval and isinstance(parsed_eval, dict):
                grade = parsed_eval.get('grade')
                comment = parsed_eval.get('comment')
            else:
                grade = None
                comment = None
                if evaluation_result:
                    m = re.search(r"\b([0-5])\b", evaluation_result)
                    if m:
                        try:
                            grade = int(m.group(1))
                        except Exception:
                            pass
                if grade is None:
                    print(f"Klaida: nepavyko išparsinti JSON įvertinimo.")

            eval_item = {
                "evaluator_model": model,
                "grade": grade,
                "comment": comment,
            }
            entry["evaluations"].append(eval_item)
            print(f"INFO: Įvertinimas gautas (grade={grade}).")

        grouped.append(entry)

    try:
        with open(evaluations_file, "w", encoding="utf-8") as ef:
            json.dump(grouped, ef, ensure_ascii=False, indent=2)
        print(f"INFO: Visi įvertinimai įrašyti į '{evaluations_file}'.")
    except Exception as e:
        print(f"Klaida: nepavyko išsaugoti '{evaluations_file}': {e}")

def json_to_csv(input_json_path: str, output_csv_path: str):
    print(f"INFO: pradedamas konvertavimas į csv...")
    
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Klaida: failas '{input_json_path}' nerastas.")
        return
    except json.JSONDecodeError:
        print(f"Klaida: Nepavyko dekoduoti JSON failo '{input_json_path}'.")
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

def main():
    read_and_save_API_keys("API_keys.txt")
    
    text_path = Path(__file__).parent / "Bible" / "morkaus_evangelija"
    
    models = [
        #"gemini/gemini-2.5-flash",
        #"gemini/gemini-2.5-flash-lite",
        #"groq/llama-3.3-70b-versatile",
        #"groq/llama-3.1-8b-instant",
        #"openai/gpt-5"
        "mistral/mistral-medium-2508"
    ]
    
    if not text_path.exists():
        print(f"Klaida: aplankalas '{text_path}' nerastas.")
        return

    bible_files = sorted(text_path.glob("*.txt"))
    
    if not bible_files:
        print(f"Klaida: jokių .txt failų nerasta '{text_path}'.")
        return
    
    print(f"INFO: Rasta {len(bible_files)} failų. Pradedamas apdorojimas...")
    
    for bible_path in bible_files:
        try:
            print(f"\n{'='*60}")
            print(f"Apdorojamas failas: {bible_path.name}")
            print(f"{'='*60}")
            
            # Read chapter text
            bible_chapter = bible_path.read_text(encoding="utf-8")
            chapter_name = bible_path.stem 
            
            # Define output files
            question_file = f"questions_{chapter_name}.json"
            evaluations_file = f"evaluations_{chapter_name}.json"
            
            # Generate questions
            generate_questions(models, bible_chapter, chapter_name, question_file)
            
            # Evaluate questions (commented out for now)
            #questions = load_questions(question_file)
            #if questions:
            #    evaluate_questions(questions, models, bible_chapter, evaluations_file)
            #    csv_path = f"evaluations_{chapter_name}.csv"
            #    json_to_csv(evaluations_file, csv_path)
            
            print(f"Failas {chapter_name} apdorotas sėkmingai.")
            
        except Exception as e:
            print(f"Klaida apdorojant {bible_path.name}: {e}")

if __name__ == "__main__":
    main()