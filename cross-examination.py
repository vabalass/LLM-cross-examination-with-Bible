from pathlib import Path
from litellm import completion
import os

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

    message_content = "Sukurk vieną klausimą su keturiais a, b, c ir d atsakymų variantais " \
    "iš mano duoto skyriaus. Tik vienas atsakymus turi būti teisingas. " + bible_pr1
    message = [{ "content": message_content,"role": "user"}]
    response = completion(model="gemini/gemini-2.5-flash", messages=message)
    print(response.choices[0].message["content"])

if __name__ == "__main__":
    main()