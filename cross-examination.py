from pathlib import Path
import random
import time
from litellm import completion
import os
import json
import re

# returns a bible question with 4 choice answers (a, b, c, d)
def get_bible_question_from_llm(model, bible_text):
    if model is not None and bible_text != "":
        message_content = (
            "Sukurk vieną klausimą su keturiais atsakymų variantais (a, b, c, d) iš pateikto Biblijos teksto. " +
            "Tik vienas atsakymas turi būti teisingas. " +
            "Grąžink aiškiai sužymėtus elementus tokia struktūra:\n" +
            "Klausimas: ...\n" +
            "a) ...\n" +
            "b) ...\n" +
            "c) ...\n" +
            "d) ...\n" +
            "Teisingas atsakymas: (nurodyk raidę)" +
            "\n\n" + bible_text
        )
        message = [{ "content": message_content,"role": "user"}]
        print("Waiting for LMM response...")
        response = completion(model=model, messages=message)

        if response.choices:
            return response.choices[0].message["content"]
        else:
            print("Error: No choices found in the response.")
    else:
        raise ValueError("Model and bible_text must be provided")

def parse_question(raw_text):
    q_match = re.search(r"Klausimas[:\--]\s*(.+)", raw_text)
    options = dict(re.findall(r"([a-d])\)\s*(.+)", raw_text))
    correct_match = re.search(r"Teisingas(?: atsakymas)?:?\s*([a-dA-D])", raw_text)

    return {
        "question": q_match.group(1).strip() if q_match else None,
        "options": options,
        "correct": correct_match.group(1).lower() if correct_match else None,
    }

def save_question_jsonl(question_obj, filepath):
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
    grades_description = [
        "0 - Nekorektiškas klausimas (Ydingas, neaiškus, neatitinka konteksto).",
        "1 - Akivaizdžiai Neteisingas atsakymas (Nurodyta raidė prieštarauja teksto faktams).",
        "2 - Iš dalies teisingas/Klaidinantis (Susijęs, bet per daug abstraktus ar nereikšmingas).",
        "3 - Tiesiogiai Netikslus (Faktas teisingas, bet netiksliai cituoja detales/eilės tvarką).",
        "4 - Teisingas, su Formuluotės Trūkumais (Faktas teisingas, bet formuluotė neaiški/per ilga).",
        "5 - Idealiai Teisingas ir Aiški Formuluotė (Nepriekaištingas atsakymas ir elegantiška formuluotė)."
    ]
        
    prompt = f"""
    BIBLIJOS IŠTRAUKA:
    {bible_text}

    Tu esi Šv. Rašo ekspertas.
    Atlikti tikslų klausimo teisingumo įvertinimą pagal šioje skalėje:
    {'\n'.join(grades_description)}

    KLAUSIMAS: {question_data['question']}

    a) {question_data['options']['a']}
    b) {question_data['options']['b']}
    c) {question_data['options']['c']}
    d) {question_data['options']['d']}

    Nurodytas TEISINGAS ATSAKYMAS (Raidė): {question_data['correct'].upper()}

    Pateikite savo įvertinimą TIK šiuo JSON formatu:
    {{
    "grade": [skaičius nuo 0 iki 5],
    "comment": "[1-2 sakinių ilgio paaiškinimas dėl suteikto įvertinimo]"
    }}

    """
    return prompt

def evaluate_question_with_llm(model, prompt, max_retries=3, base_delay=1.5):
    message = [{ "content": prompt, "role": "user"}]
    for attempt in range(1, max_retries + 1):
        try:
            response = completion(model=model, messages=message)
            if response.choices:
                return response.choices[0].message["content"]
            else:
                print("Klaida! nerasta atsakymo variantų.")
                return None
        except Exception as e:
            if attempt < max_retries:
                sleep_time = (base_delay ** attempt) + random.uniform(0, 1)
                print(f"Rate limit detected from model {model}: {e}. Retrying in {sleep_time:.1f}s (attempt {attempt}/{max_retries})...")
                time.sleep(sleep_time)
                continue
            else:
                raise
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
    for model in models:
        print(f"INFO: Generuojamas klausimas naudojant modelį {model}.")
        raw_question = get_bible_question_from_llm(model=model, bible_text=bible_text)
        parsed = parse_question(raw_question)
        parsed.update({
            "model": model,
            "chapter": chapter_name
        })
        save_question_jsonl(parsed, question_file)
        print(f"INFO: Klausimas išsaugotas ({model}).")

def load_questions(question_file):
    try:
        with open(question_file, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    except FileNotFoundError:
        print(f"Klaida! Įvesties failas '{question_file}' nerastas. Prašome sugeneruoti klausimus.")
        return []

def evaluate_questions(questions, models, bible_text, evaluations_file):
    grouped = []
    for i, question in enumerate(questions):
        print(f"INFO: vertinamas klausimas {i+1}.")
        entry = {
            "question_index": i,
            "question": question.get("question"),
            "options": question.get("options"),
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
                    print(f"Klaida! Nepavyko išparsinti JSON įvertinimo.")

            eval_item = {
                "evaluator_model": model,
                "grade": grade,
                "comment": comment,
            }
            entry["evaluations"].append(eval_item)
            print(f"INFO: Įvertinimas iš {model} gautas (grade={grade}).")

        grouped.append(entry)

    try:
        with open(evaluations_file, "w", encoding="utf-8") as ef:
            json.dump(grouped, ef, ensure_ascii=False, indent=2)
        print(f"INFO: Visi įvertinimai įrašyti į '{evaluations_file}'.")
    except Exception as e:
        print(f"[KLAIDA] Nepavyko išsaugoti '{evaluations_file}': {e}")

def main():
    read_and_save_API_keys("API_keys.txt")
    bible_path = Path(__file__).parent / "Bible" / "1Sam17.txt"
    bible_chapter = "".join((bible_path).read_text(encoding="utf-8"))
    question_file = "bible_questions.jsonl"
    evaluations_file = "evaluations.json"

    models = [
        "gemini/gemini-2.5-flash",
        "groq/llama-3.1-8b-instant",
        "openai/gpt-5-nano"
    ]

    chapter_name = os.path.basename(bible_path).replace(".txt", "")
    #generate_questions(models, bible_chapter, chapter_name, question_file)

    questions = load_questions(question_file)
    if not questions:
        return

    evaluate_questions(questions, models, bible_chapter, evaluations_file)

if __name__ == "__main__":
    main()