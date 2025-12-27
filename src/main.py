from pathlib import Path
import file_io 
import llm_generation
import llm_evaluation

def main():
    parent_folder = Path(__file__).parent.parent

    klausimu_autorius = "gemini-2.5-flash"
    vertintojas = "mistral-medium"

    api_keys_path = parent_folder / "API_keys.txt"
    source_text_path = parent_folder / "source_text" / "jono_evangelija"
    output_path = parent_folder / "results/evaluations" / "mistral-medium_vertina_gemini-2.5-flash"
    questions_path = parent_folder / "results/questions" / "" / "klausimai_Jn"


    file_io.read_and_save_API_keys(api_keys_path)
    
    models = [
        #"gemini/gemini-2.5-flash-lite",
        "gemini/gemini-2.5-flash",
        #"mistral/mistral-medium-2508",
        #"mistral/mistral-small-2506"
    ]
    
    # llm.generate_questions_from_all_text_files(
    #    folder_path=folder_path,
    #    model=models[0],
    #    output_path=output_path)
    
    llm_evaluation.evaluate_questions_with_one_model(questions_path, models[0], output_path, source_text_path)

    

if __name__ == "__main__":
    main()