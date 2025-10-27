from pathlib import Path
from litellm import completion
import os

# returns a bible question with 4 choice answers (a, b, c, d)
def get_bible_question_from_llm(model = "gemini/gemini-2.5-flash", bible_text = ""):
    if model is not None and bible_text != "":
        message_content = "Sukurk vieną klausimą su keturiais a, b, c ir d atsakymų variantais " \
        "iš mano duoto Biblijos skyriaus. Tik vienas atsakymus turi būti teisingas. " + bible_text
        message = [{ "content": message_content,"role": "user"}]
        response = completion(model=model, messages=message)

        if response.choices:
            return response.choices[0].message["content"]
        else:
            print("Error: No choices found in the response.")
    else:
        raise ValueError("Model and bible_text must be provided")

def read_and_save_API_keys(api_keys_path):
    if api_keys_path := Path(api_keys_path):
        with api_keys_path.open("r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()

def main():
    read_and_save_API_keys("API_keys.txt")

    bible_pr1 = "".join((Path(__file__).parent / "Bible" / "Pr1.txt").read_text(encoding="utf-8"))

    print(get_bible_question_from_llm(model="gemini/gemini-2.5-flash", bible_text=bible_pr1))

if __name__ == "__main__":
    main()