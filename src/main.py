from pathlib import Path
import file_io 
import llm_calls as llm

def main():
    parent_folder = Path(__file__).parent.parent

    api_keys_path = parent_folder / "API_keys.txt"
    folder_path = parent_folder / "source_text" / "testiniai_skyriai"
    output_path = parent_folder / "results"


    file_io.read_and_save_API_keys(api_keys_path)
    
    models = [
        #"gemini/gemini-2.5-flash-lite",
        #"gemini/gemini-2.5-flash",
        "mistral/mistral-medium-2508",
        #"mistral/mistral-small-2506"
    ]
    
    llm.generate_questions_from_all_text_files(
        folder_path=folder_path,
        model=models[0],
        output_path=output_path)
    

if __name__ == "__main__":
    main()