from pathlib import Path
from litellm import completion
import os

os.environ["OPENAI_API_KEY"] = "your-openai-key"

def main():
    bible_text = "".join((Path(__file__).parent / "Bible" / "Pr1.txt").read_text(encoding="utf-8"))
    print(bible_text)             

if __name__ == "__main__":
    main()