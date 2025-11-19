from pathlib import Path
from litellm import completion
import os
import json
import re

# returns a bible question with 4 choice answers (a, b, c, d)
def get_bible_question_from_llm(model = "gemini/gemini-2.5-flash", bible_text = ""):
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

def save_question_jsonl(question_obj, filepath="bible_questions.jsonl"):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(question_obj, ensure_ascii=False) + "\n")

def read_and_save_API_keys(api_keys_path):
    if api_keys_path := Path(api_keys_path):
        with api_keys_path.open("r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()

def main():
    read_and_save_API_keys("API_keys.txt")
    bible_path = Path(__file__).parent / "Bible" / "Pr1.txt"
    bible_chapter = "".join((bible_path).read_text(encoding="utf-8"))

    models = [
        "gemini/gemini-2.5-flash",
        "groq/llama-3.1-8b-instant",
        "openai/gpt-5-nano"
    ]

    for model in models:
        print(f"Main: Generuojamas klausimas naudojant modelį {model}...")
        raw_question = get_bible_question_from_llm(model=model, bible_text=bible_chapter)
        parsed = parse_question(raw_question)
        parsed.update({
        "model": model,
        "chapter": os.path.basename(bible_path).replace(".txt", "")
        })
        save_question_jsonl(parsed)
        print(f"Main: Klausimas išsaugotas.")

if __name__ == "__main__":
    main()