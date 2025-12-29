from pathlib import Path
import file_io 
import llm_generation
import llm_evaluation

def main():
    parent_folder = Path(__file__).parent.parent

    klausimu_autorius = "mistral-small"
    vertintojas = "gemini-2.5-flash"
    evangelija = "mato_evangelija"
    rezultatai = "Mt_evaluations"
    klausimai = "klausimai_Mt"

    api_keys_path = parent_folder / "API_keys.txt"
    source_text_path = parent_folder / "source_text" / evangelija
    output_path = parent_folder / "results/evaluations" / f"{vertintojas}_vertina_{klausimu_autorius}" / rezultatai
    questions_path = parent_folder / "results/questions" / klausimu_autorius / klausimai


    file_io.read_and_save_API_keys(api_keys_path)
    
    models = [
        f"gemini/{vertintojas}",
        #f"mistral/{vertintojas}-2508"
        #f"mistral/{vertintojas}-2506"
    ]
    
    # llm_generation.generate_questions_from_all_text_files(
    #    folder_path=folder_path,
    #    model=models[0],
    #    output_path=output_path)

    # llm_generation.process_one_text_file(
    #     model="mistral/mistral-small-2506", 
    #     question_output_path= parent_folder / "results/questions/mistral-small/klausimai_Mk/questions_Mk_3.json",
    #     text_path= parent_folder / "source_text/morkaus_evangelija/Mk_3.txt"
    #     )
    
    llm_evaluation.evaluate_questions_with_one_model(
        folder_path=questions_path, 
        model=models[0], 
        output_path=output_path, 
        source_text_path=source_text_path
    )

    

if __name__ == "__main__":
    main()