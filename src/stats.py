# Sugeneruota su Gemini-2.5-flash

import json
from collections import defaultdict
from pathlib import Path

def get_stats():
    """Suskaičiuoja pagrindinę statistiką"""
    questions_dir = Path(__file__).parent.parent / "results/questions"
    evaluations_dir = Path(__file__).parent.parent / "results/evaluations"
    
    # Sugeneruoti klausimai pagal modelį
    generated_by_model = defaultdict(int)
    total_questions = 0
    models = set()
    
    for model_dir in questions_dir.iterdir():
        if model_dir.is_dir() and model_dir.name != "testing_questions":
            models.add(model_dir.name)
            model_name = model_dir.name
            for gospel_dir in model_dir.iterdir():
                if gospel_dir.is_dir():
                    for json_file in gospel_dir.glob("questions_*.json"):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                count = len(json.load(f))
                                generated_by_model[model_name] += count
                                total_questions += count
                        except:
                            pass
    
    # Įvertinimai pagal modelį (kiek gavo, ne kiek davė)
    grades_by_model = defaultdict(lambda: defaultdict(int))
    evaluated_by_model = defaultdict(int)
    
    # Sekti grade 5 skaičius iš kiekvieno vertintojo
    grade5_by_model_and_evaluator = defaultdict(lambda: defaultdict(int))
    
    for eval_dir in evaluations_dir.iterdir():
        if eval_dir.is_dir() and eval_dir.name != "testing_evaluations":
            parts = eval_dir.name.split("_vertina_")
            if len(parts) == 2:
                evaluator_model = parts[0]  # Modelis kuris vertina
                evaluated_model = parts[1]  # Modelis kurį vertino
                
                for gospel_dir in eval_dir.iterdir():
                    if gospel_dir.is_dir() and "_evaluations" in gospel_dir.name:
                        for json_file in gospel_dir.glob("*_evaluations.json"):
                            try:
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    if "results" in data:
                                        for result in data["results"]:
                                            grade = result.get("grade")
                                            question_id = result.get("id")
                                            grades_by_model[evaluated_model][grade] += 1
                                            evaluated_by_model[evaluated_model] += 1
                                            
                                            if grade == 5:
                                                grade5_by_model_and_evaluator[evaluated_model][question_id] += 1
                            except:
                                pass
    
    # Bendras įvertinimų skaičius
    total_grades = sum(sum(grades.values()) for grades in grades_by_model.values())
    
    # Suskaičiuoti klausimus, kurie gavo 5 iš abiejų vertintojų
    perfect_from_both = {}
    for model in grades_by_model.keys():
        count = sum(1 for question_id, count in grade5_by_model_and_evaluator[model].items() if count == 2)
        perfect_from_both[model] = count
    
    return len(models), total_questions, total_grades, grades_by_model, generated_by_model, evaluated_by_model, perfect_from_both

def print_statistics():
    num_models, total_questions, total_grades, grades_by_model, generated_by_model, evaluated_by_model, perfect_from_both = get_stats()
    
    print(f"Modelių skaičius: {num_models}")
    print(f"Bendra sugeneruotų klausimų suma: {total_questions}")
    print(f"Bendra vertintų klausimų suma: {total_grades}")
    print()
    
    for model in sorted(grades_by_model.keys()):
        generated = generated_by_model.get(model, 0)
        evaluated = evaluated_by_model.get(model, 0)
        grade_5_count = grades_by_model[model].get(5, 0)
        total_model_grades = sum(grades_by_model[model].values())
        percentage = (grade_5_count / total_model_grades * 100) if total_model_grades > 0 else 0
        perfect_both = perfect_from_both.get(model, 0)
        print(f"{model}:")
        print(f"  Sugeneravo: {generated} klausimų")
        print(f"  Įvertino: {evaluated} klausimų")
        print(f"  Gavo įvertinimą 5: {percentage:.1f}% ({grade_5_count}/{total_model_grades})")
        print(f"  Gavo 5 iš abiejų vertintojų: {perfect_both}")
        print()

if __name__ == "__main__":
    print_statistics()