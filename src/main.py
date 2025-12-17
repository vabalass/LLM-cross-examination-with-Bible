from pathlib import Path
import file_io 
import llm_calls as llm

def main():
    parent_folder = Path(__file__).parent.parent
    api_keys_path = parent_folder / "API_keys.txt"
    text_path = parent_folder / "source_text" / "test"
    bible_files = sorted(text_path.glob("*.txt"))
    print(f"main: Rasta {len(bible_files)} failų. Pradedamas apdorojimas...")

    file_io.read_and_save_API_keys(api_keys_path)
    
    models = [
        #"gemini/gemini-2.5-flash",
        #"gemini/gemini-2.5-flash-lite",
        #"groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-8b-instant",
        #"openrouter/meta-llama/llama-3.3-70b-instruct:free",
        #"openrouter/google/gemma-3-27b-it:free",
        #"mistral/mistral-medium-2508"
    ]
    
    for bible_path in bible_files:
        try:
            print(f"main: apdorojamas failas: {bible_path.name}")
            
            bible_chapter = bible_path.read_text(encoding="utf-8")
            chapter_name = bible_path.stem 
            
            question_file = parent_folder / "results" / f"questions_{chapter_name}.json"
            evaluations_file = parent_folder / "results" / f"evaluations_{chapter_name}.json"
            
            llm.generate_questions(models, bible_chapter, chapter_name, question_file)
        
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