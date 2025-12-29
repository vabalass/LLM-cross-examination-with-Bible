
import json
from collections import defaultdict
from pathlib import Path

def get_stats():
    """Suskaičiuoja pagrindinę statistiką"""
    questions_dir = Path(__file__).parent.parent / "results/questions"
    evaluations_dir = Path(__file__).parent.parent / "results/evaluations"
    
    # Klausimų skaičius
    total_questions = 0
    models = set()
    
    for model_dir in questions_dir.iterdir():
        if model_dir.is_dir() and model_dir.name != "testing_questions":
            models.add(model_dir.name)
            for gospel_dir in model_dir.iterdir():
                if gospel_dir.is_dir():
                    for json_file in gospel_dir.glob("questions_*.json"):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                total_questions += len(json.load(f))
                        except:
                            pass
    
    # Įvertinimai pagal modelį
    grades_by_model = defaultdict(lambda: defaultdict(int))
    
    for eval_dir in evaluations_dir.iterdir():
        if eval_dir.is_dir() and eval_dir.name != "testing_evaluations":
            parts = eval_dir.name.split("_vertina_")
            if len(parts) == 2:
                evaluator_model = parts[0]
                
                for gospel_dir in eval_dir.iterdir():
                    if gospel_dir.is_dir() and "_evaluations" in gospel_dir.name:
                        for json_file in gospel_dir.glob("*_evaluations.json"):
                            try:
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    if "results" in data:
                                        for result in data["results"]:
                                            grade = result.get("grade")
                                            grades_by_model[evaluator_model][grade] += 1
                            except:
                                pass
    
    # Bendras įvertinimų skaičius
    total_grades = sum(sum(grades.values()) for grades in grades_by_model.values())
    
    return len(models), total_questions, total_grades, grades_by_model

def print_statistics():
    """Atspausdina supaprastintą statistiką"""
    num_models, total_questions, total_grades, grades_by_model = get_stats()
    
    print(f"Modelių skaičius: {num_models}")
    print(f"Bendra klausimų suma: {total_questions}")
    print(f"Bendra vertinimų suma: {total_grades}")
    print()
    
    for model in sorted(grades_by_model.keys()):
        grade_5_count = grades_by_model[model].get(5, 0)
        total_model_grades = sum(grades_by_model[model].values())
        percentage = (grade_5_count / total_model_grades * 100) if total_model_grades > 0 else 0
        print(f"{model}: {percentage:.1f}% gavo įvertinimą 5")

if __name__ == "__main__":
    print_statistics()