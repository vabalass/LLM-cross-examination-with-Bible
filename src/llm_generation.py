from litellm import completion
import time
import json
import parser
import file_io
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
    
def generate_questions(model, bible_text, chapter_name, question_file):
    all_questions = []
    question_counter = 1
    
    print(f"llm_calls: generuojami klausimai naudojant modelį {model}...")
    number_of_questions = file_io.calculate_questions_number(bible_text)

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
                print(f"llm_calls: failas '{question_output_path}' jau egzistuoja. Praleidžiama...")
                continue

            process_one_text_file(text_path, model, question_output_path)

            print(f"llm_calls: failas {name} apdorotas sėkmingai.")
        except Exception as e:
            print(f"llm_calls: klaida apdorojant {text_path.name}: {e}")