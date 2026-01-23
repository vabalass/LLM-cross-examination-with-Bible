"""
Script to filter questions that received grade 5 from both other models
and save them organized by gospel name in a separate folder.
"""

import json
from pathlib import Path
from collections import defaultdict


def get_all_models():
    """Get list of all models from questions directory"""
    questions_dir = Path(__file__).parent.parent / "results/questions"
    models = [d.name for d in questions_dir.iterdir() if d.is_dir()]
    return sorted(models)


def get_evaluations_for_model(evaluated_model):
    """
    Get all grades for a specific evaluated model from both other models.
    Returns: {gospel: {question_id: [grades_from_other_models]}}
    """
    evaluations_dir = Path(__file__).parent.parent / "results/evaluations"
    all_models = get_all_models()
    other_models = [m for m in all_models if m != evaluated_model]
    
    # Structure: {gospel: {question_id: [list of grades from each evaluator]}}
    grades_by_question = defaultdict(lambda: defaultdict(list))
    
    for eval_folder in evaluations_dir.iterdir():
        if not eval_folder.is_dir() or eval_folder.name == "testing_evaluations":
            continue
        
        parts = eval_folder.name.split("_vertina_")
        if len(parts) != 2:
            continue
        
        evaluator_model, target_model = parts
        
        # Only process evaluations where evaluated_model is the target
        if target_model != evaluated_model:
            continue
        
        # Read evaluations for each gospel
        for gospel_dir in eval_folder.iterdir():
            if not gospel_dir.is_dir() or "_evaluations" not in gospel_dir.name:
                continue
            
            gospel_name = gospel_dir.name.replace("_evaluations", "")
            
            for eval_file in gospel_dir.glob("*_evaluations.json"):
                try:
                    with open(eval_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if "results" in data:
                            for result in data["results"]:
                                question_id = result.get("id")
                                grade = result.get("grade")
                                if question_id and grade:
                                    grades_by_question[gospel_name][question_id].append(grade)
                except Exception as e:
                    print(f"Error reading {eval_file}: {e}")
    
    return grades_by_question


def get_questions_for_model(model, gospel):
    """Get questions for a specific model and gospel"""
    questions_file = Path(__file__).parent.parent / f"results/questions/{model}/klausimai_{gospel}/questions_{gospel}_*.json"
    questions = []
    
    for file in Path(questions_file).parent.glob(f"questions_{gospel}_*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                questions.extend(json.load(f))
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    return questions


def filter_perfect_questions():
    """Filter questions that received grade 5 from both other models"""
    all_models = get_all_models()
    output_base_dir = Path(__file__).parent.parent / "results" / "perfect_questions"
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("FILTERING QUESTIONS WITH PERFECT GRADE 5 FROM BOTH OTHER MODELS")
    print("=" * 80)
    print()
    
    for model in all_models:
        print(f"\nProcessing {model}...")
        
        # Get grades for this model from both other evaluators
        grades_by_question = get_evaluations_for_model(model)
        
        # Find questions with grade 5 from both other models
        perfect_questions = defaultdict(list)
        
        for gospel, questions_grades in grades_by_question.items():
            for question_id, grades in questions_grades.items():
                # We need exactly 2 grades (from 2 other models) and both should be 5
                if len(grades) == 2 and all(g == 5 for g in grades):
                    perfect_questions[gospel].append(question_id)
        
        # Get actual question data and save
        model_output_dir = output_base_dir / model
        model_output_dir.mkdir(parents=True, exist_ok=True)
        
        total_perfect = 0
        
        for gospel in sorted(perfect_questions.keys()):
            question_ids = perfect_questions[gospel]
            
            if not question_ids:
                continue
            
            # Get all questions for this gospel
            all_questions = get_questions_for_model(model, gospel)
            
            # Filter to only perfect ones
            perfect_q = [q for q in all_questions if q.get("id") in question_ids]
            
            if perfect_q:
                # Save to file
                output_file = model_output_dir / f"{gospel}_perfect_questions.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(perfect_q, f, ensure_ascii=False, indent=2)
                
                print(f"  {gospel}: {len(perfect_q)} perfect questions saved to {output_file.name}")
                total_perfect += len(perfect_q)
        
        print(f"  Total perfect questions: {total_perfect}")
    
    print()
    print("=" * 80)
    print(f"Perfect questions saved to: {output_base_dir}")
    print("=" * 80)


if __name__ == "__main__":
    filter_perfect_questions()
