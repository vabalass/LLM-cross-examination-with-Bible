from litellm import completion
import time
import json
import parser
from file_io import calculate_questions_number
import re
import sys

def get_bible_questions_from_llm(model, bible_text, number_of_questions=1):
    try:
        if model is not None and bible_text != "":
            system_prompt = (
                "Naudok taisyklingą lietuvių kalbą. Niekada nepraleisk raidžių."
            )
            user_prompt = (
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
            message = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            response = completion(
                model=model, 
                messages=message)
            
            print(response)
            
            if response.choices:
                return response.choices[0].message["content"]
        return None
    except Exception as e:
        print(f"llm_calls klaida: {e}")
        return None
        
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
                print("llm_calls klaida: nerasta atsakymo variantų atsakyme.")
                if attempt < max_retries:
                    print(f"Bandymas {attempt}/{max_retries-1}. Laukiu 5 sekundžių prieš pakartojimu...")
                    time.sleep(5)
                    continue
                return None
                
        except Exception as e:
            print(f"llm_calls klaida generuojant įvertinimą: {e}")
            if attempt < max_retries:
                print(f"llm_calls: bandymas {attempt}/{max_retries-1}. Laukiu 5 sekundžių prieš pakartojimu...")
                time.sleep(5)
                continue
            return None
        
def generate_questions(model, bible_text, chapter_name, question_file):
    all_questions = []
    question_counter = 1
    
    print(f"llm_calls: generuojami klausimai naudojant modelį {model}...")
    number_of_questions = calculate_questions_number(bible_text)

    max_retries = 3
    raw_question = None
    for attempt in range(max_retries):
        raw_question = get_bible_questions_from_llm(
            model=model, 
            bible_text=bible_text, 
            number_of_questions=number_of_questions
        )
        if raw_question is not None: 
            break

        if attempt < max_retries - 1:
            print(f"llm_calls: bandymas {attempt + 1} nepavyko. Po 5 sek. kartojimas...")
            time.sleep(5)
    else:
        print(f"llm_calls klaida: nepavyko gauti klausimų iš modelio {model}.")
        sys.exit("llm_calls: programa sustabdyta.")
        
    parsed_list = parser.parse_questions_to_json(raw_question)
        
    for parsed in parsed_list:
        if not parsed.get('question') or not parsed.get('options'):
            print(f"llm_calls klaida: praleistas nevalidus klausimas iš modelio {model}.")
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
        print(f"llm_calls: {len(all_questions)} klausimų įrašyta į '{question_file}'.")
    except Exception as e:
        print(f"llm_calls klaida: nepavyko išsaugoti: {e}")

def evaluate_questions(questions, models, bible_text, evaluations_file):
    grouped = []
    
    for i, question in enumerate(questions):
        print(f"llm_calls: vertinamas klausimas {i+1}...")
        
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
                print(f"llm_calls: Modelis {model} praleidžiamas (sukūrė šį klausimą).")
                continue

            prompt = generate_evaluation_prompt(question, bible_text)
            evaluation_result = evaluate_question_with_llm(model, prompt)

            parsed_eval = parser.extract_json_from_text(evaluation_result)
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
                    print(f"llm_calls klaida: nepavyko išparsinti JSON įvertinimo.")

            eval_item = {
                "evaluator_model": model,
                "grade": grade,
                "comment": comment,
            }
            entry["evaluations"].append(eval_item)
            print(f"llm_calls: Įvertinimas gautas (grade={grade}).")

        grouped.append(entry)

    try:
        with open(evaluations_file, "w", encoding="utf-8") as ef:
            json.dump(grouped, ef, ensure_ascii=False, indent=2)
        print(f"llm_calls: Visi įvertinimai įrašyti į '{evaluations_file}'.")
    except Exception as e:
        print(f"llm_calls klaida: nepavyko išsaugoti '{evaluations_file}': {e}")

def process_one_text_file(text_path, model, question_output_path):
    print(f"llm_calls: apdorojamas failas: {text_path.name}")

    text = text_path.read_text(encoding="utf-8")
    name = text_path.stem
    
    generate_questions(model, text, name, question_output_path)
    
    print(f"llm_calls: {name} apdorotas sėkmingai.")

def generate_questions_from_all_text_files(folder_path, model, output_path):
    if folder_path.exists() is False:
        print(f"llm_calls klaida: nurodytas aplankas '{folder_path}' neegzistuoja.")
        return
    
    text_files_paths = list(folder_path.glob("*.txt"))
    print(f"main: Rasta {len(text_files_paths)} failų. Pradedamas apdorojimas...")

    for text_path in text_files_paths:
        try:
            name = text_path.stem 
            question_output_path = output_path / f"questions_{name}.json"

            if question_output_path.exists():
                print(f"main: failas '{question_output_path}' jau egzistuoja. Praleidžiama...")
                continue

            process_one_text_file(text_path, model, question_output_path)

            print(f"llm_calls: failas {name} apdorotas sėkmingai.")
        except Exception as e:
            print(f"llm_calls: klaida apdorojant {text_path.name}: {e}")