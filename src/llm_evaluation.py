from litellm import completion
import json
import file_io
from pathlib import Path
import sys

        
def formulate_evaluation_message(questions_list, text):
    if not questions_list or not text:
        return None
    
    questions_json_str = json.dumps(questions_list, indent=2, ensure_ascii=False)

    system_prompt = (
        "Tu esi Šv. Rašto ekspertas. Tavo užduotis - įvertinti klausimų ir atsakymų kokybę (grade).\n"
        "Vertinimo skalė:\n"
        "0 - Visiškai netinkamas (neaiškus arba kliedesinis)\n"
        "1 - Aiškus, bet faktiškai klaidingas (prieštarauja šaltiniui).\n"
        "2 - Faktiškai teisingas, bet turi didelių turinio trūkumų (neteisingi atsakymai, klaidinanti logika).\n"
        "3 - Teisingas, bet yra techninių/formos klaidų (gramatika, citavimo tikslumas)\n"
        "4 - Puikus turinys ir technika, bet stilius/formuluotė galėtų būti geresni.\n"
        "5 - Idealus visais aspektais (turinys, logika, gramatika, didaktinė vertė)\n"

        "Vertink griežtai hierarchiškai: jei klausimas faktiškai neteisingas, jis negali gauti daugiau nei 1 balo,\n"
        "net jei jo gramatika ideali. Jei klausimas teisingas, bet neaiškus, jis negali gauti daugiau nei 4 balų.\n"

        "Atsakymą pateik tik JSON formatu kaip sąrašą objektų, atitinkančių šią struktūrą:\n"
        "[\n"
        "  {\n"
        "    \"id\": \"klausimo_id\",\n"
        "    \"grade\": įvertinimas\n"
        "    \"comment\": \"1-2 sakinių vertinimo paaiškinimas\"\n"
        "  }\n"
        "]"
    )
    
    user_prompt = user_prompt = f"Biblijos ištrauka:\n{text}\n\nKlausimai vertinimui:\n{questions_json_str}" 
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def evaluate_questions_with_llm(model, message):
    try:
        response = completion(
            model=model, 
            messages=message,
            response_format={"type": "json_object"}
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print("llm_evaluation klaida: Modelis grąžino nevalidų JSON formatą.")
                return None
        else:
            print("llm_evaluation klaida: nerasta atsakymo variantų atsakyme.")
            return None
            
    except Exception as e:
        print(f"llm_evaluation klaida generuojant įvertinimą su modelius {model}: {e}")
        return None

def evaluate_questions(questions_path, model, source_text_path):
    # check paths
    if not file_io.paths_exist([questions_path, source_text_path]):
        return
    # check if the Bible chapter match questions chapter
    if not chapters_match(questions_path, source_text_path):
        return
    
    # generate prompt with all questions
    with open(questions_path, "r", encoding="utf-8") as f:
        questions_list = json.load(f)
    with open(source_text_path, "r", encoding="utf-8") as f:
        source_text = f.read()
    message = formulate_evaluation_message(questions_list, source_text)
    # generate evaluation
    evaluations_json = evaluate_questions_with_llm(model, message)
    
    if evaluations_json is not None:
        return file_io.add_important_parameters_to_evaluations(evaluations_json, model, source_text_path)
    else:
        print("llm_evaluations klaida: nepavyko gauti JSON klausimų įvertinimų.")
        return

def get_model_from_question_file(question_file):
    try:
        with open(question_file, "r", encoding="utf-8") as qf:
            questions = json.load(qf)
            if questions and isinstance(questions, list):
                first_question = questions[0]
                model = first_question.get("model")
                return model
        return None
    except Exception as e:
        print(f"llm_calls klaida: nepavyko nuskaityti modelio iš '{question_file}': {e}")
        return None
    
def chapters_match(questions_path, source_text_path):
    try:
        with open(questions_path, "r", encoding="utf-8") as questions_json:
            questions = json.load(questions_json)
            question_chapter = str(questions[0].get("chapter")).strip()
        source_chapter = Path(source_text_path).stem
        if (question_chapter!= source_chapter):
            print(f"llm_evaluations klaida: klausimo skyrius ({question_chapter}) nesutampa su šaltinio skyriumi ({source_chapter}).")
            return False
        
        return True
    except Exception as e:
        print(f"llm_evaluations klaida lyginant skyrius: {e}")
        return False

def evaluate_questions_with_one_model(folder_path, model, output_path, source_text_path):
    # error checks
    if not file_io.paths_exist([folder_path, output_path, source_text_path]): 
        return

    first_json_file = file_io.find_first_json_in_file(folder_path)
    if first_json_file is None:
        print(f"llm_calls klaida: {folder_path} neturi JSON failų.")
        return

    question_model = get_model_from_question_file(first_json_file)
    if(question_model is None or question_model == model):
        print("llm_calls klaida: nerastas modelis klausimų faile arba modelis autorius sutampa su vertintoju.")
        return

    question_files_paths = sorted(folder_path.glob("*.json"))
    source_text_files_paths = sorted(source_text_path.glob("*.txt"))
    if (len(question_files_paths) != len(source_text_files_paths)):
        print("llm_evaluations klaida: šaltinių failų kiekis nesutampa su klausimų failų kiekiu.")
        return

    # execution
    print(f"llm_evaluations: pradedamas {question_model} klausimų įvertinimas su {model}...")

    for questions_path, text_path in zip(question_files_paths, source_text_files_paths):
        evalutions_path = output_path / f"{text_path.stem}_evaluations.json"
        if Path(evalutions_path).exists():
            print(f"llm_evaluations: failas {evalutions_path.stem} jau egzistuoja.")
            continue

        print(f"llm_evaluations: vertinami {text_path.stem} skyriaus klausimai...")

        evaluations_json = evaluate_questions(questions_path, model, text_path)

        if evaluations_json is not None:
            file_io.save_json_file(evaluations_json, evalutions_path)
            print("llm_evaluations: įvertinimai sėkmingai išsaugoti!")
        else:
            print("llm_evaluations klaida: gautas JSON None failas. Programa stabdoma.")
            sys.exit()

    print("llm_evaluations: visi įvertinimai sėkmingai išsaugoti!")

