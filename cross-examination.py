from pathlib import Path
from litellm import completion
import os
import json
import re

# returns a 3 Bible questions with 4 choice answers (a, b, c, d)
def get_bible_question_from_llm(model, bible_text):
    try:
        if model is not None and bible_text != "":
            message_content = (
                "Sukurk tris klausimus su keturiais atsakymų variantais (a, b, c, d) iš pateikto Biblijos teksto. " +
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
                "Neįtraukite jokių paaiškinimų ar papildomo teksto, tik JSON.\n\n" +
                bible_text
            )
            message = [{ "content": message_content,"role": "user"}]
            response = completion(model=model, messages=message)
            print("Atsakymas gautas.")
            if response.choices:
                return response.choices[0].message["content"]
            else:
                print("Klaida: Atsakymo variantų nerasta.")
                return None
        return None
    except Exception as e:
        print(f"Klaida: {e}")
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

    Tu esi Šv. Rašo ekspertas.
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

def evaluate_question_with_llm(model, prompt):
    message = [{ "content": prompt, "role": "user"}]
    try:
        response = completion(model=model, messages=message)
        
        if response and response.choices:
            return response.choices[0].message["content"]
        else:
            print("Klaida: nerasta atsakymo variantų atsakyme.")
            return None
            
    except Exception as e:
        print(f"Klaida generuojant įvertinimą: {e}")
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

def generate_questions(models, bible_text, chapter_name, question_file):
    all_questions = []
    
    for model in models:
        print(f"INFO: Generuojami klausimai naudojant modelį {model}...")
        raw_question = get_bible_question_from_llm(model=model, bible_text=bible_text)
        
        if raw_question is None:
            print("Klaida: tuščias tekstas iš modelio.")
            continue
        
        parsed_list = parse_question(raw_question)
        
        for parsed in parsed_list:
            if not parsed.get('question') or not parsed.get('options'):
                print(f"Klaida: praleistas nevalidus klausimas iš modelio {model}.")
                continue
            
            parsed.update({
                "model": model,
                "chapter": chapter_name
            })
            all_questions.append(parsed)
            print(f"INFO: Klausimas išsaugotas iš modelio {model}.")
    
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
        entry = {
            "question_index": i,
            "question": question.get("question"),
            "options": question.get("options"),
            "correct_answer": question.get("correct"),
            "question_creator_model": question.get("model"),
            "evaluations": []
        }

        for model in models:
            if model == question['model']:
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

def main():
    read_and_save_API_keys("API_keys.txt")
    bible_path = Path(__file__).parent / "Bible" / "1Sam17.txt"
    bible_chapter = "".join((bible_path).read_text(encoding="utf-8"))
    question_file = "bible_questions.json"
    evaluations_file = "evaluations.json"

    models = [
        "gemini/gemini-2.5-flash",
        "groq/llama-3.3-70b-versatile",
        #"openai/gpt-5"
    ]

    chapter_name = os.path.basename(bible_path).replace(".txt", "")
    generate_questions(models, bible_chapter, chapter_name, question_file)

    questions = load_questions(question_file)
    if not questions:
        return

    evaluate_questions(questions, models, bible_chapter, evaluations_file)

if __name__ == "__main__":
    main()