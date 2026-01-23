# Sugeneruota su Gemini-2.5-flash

import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

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
    
    # Statistika: kiek kokių įvertinimų gavo modelis iš kiekvieno vertintojo
    grades_by_evaluated_and_evaluator = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
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
                                            grades_by_evaluated_and_evaluator[evaluated_model][evaluator_model][grade] += 1
                            except:
                                pass
    
    return len(models), total_questions, total_grades, grades_by_model, generated_by_model, evaluated_by_model, perfect_from_both, grades_by_evaluated_and_evaluator

def print_statistics():
    num_models, total_questions, total_grades, grades_by_model, generated_by_model, evaluated_by_model, perfect_from_both, grades_by_evaluated_and_evaluator = get_stats()
    
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

def print_cross_evaluation_statistics():
    """Spausdina detalizuotą statistiką: kiek kokių įvertinimų gavo modelis iš kiekvieno vertintojo"""
    num_models, total_questions, total_grades, grades_by_model, generated_by_model, evaluated_by_model, perfect_from_both, grades_by_evaluated_and_evaluator = get_stats()
    
    print("=" * 80)
    print("DETALIZUOTA MODELIŲ VERTINIMO STATISTIKA")
    print("=" * 80)
    print()
    
    for evaluated_model in sorted(grades_by_evaluated_and_evaluator.keys()):
        print(f"\n{evaluated_model} - GAUTAS VERTINIMAS:")
        print("-" * 80)
        
        evaluator_data = grades_by_evaluated_and_evaluator[evaluated_model]
        
        for evaluator_model in sorted(evaluator_data.keys()):
            grades_distribution = evaluator_data[evaluator_model]
            total_grades_from_evaluator = sum(grades_distribution.values())
            
            print(f"\n  Iš {evaluator_model}:")
            print(f"    Iš viso vertintų: {total_grades_from_evaluator}")
            
            # Spausdinti įvertinimus nuo 5 iki 1
            for grade in range(5, 0, -1):
                count = grades_distribution.get(grade, 0)
                percentage = (count / total_grades_from_evaluator * 100) if total_grades_from_evaluator > 0 else 0
                print(f"      Įvertinimas {grade}: {count} ({percentage:.1f}%)")
        
        # Bendras šio modelio vertinimas
        print(f"\n  IŠ VISO:")
        total_for_model = sum(sum(evaluator_data[e].values()) for e in evaluator_data)
        all_grades_dist = defaultdict(int)
        for grades_dist in evaluator_data.values():
            for grade, count in grades_dist.items():
                all_grades_dist[grade] += count
        
        for grade in range(5, 0, -1):
            count = all_grades_dist.get(grade, 0)
            percentage = (count / total_for_model * 100) if total_for_model > 0 else 0
            print(f"    Įvertinimas {grade}: {count} ({percentage:.1f}%)")
        print()

def plot_cross_evaluation_charts():
    """Sukuria 3 atskiras stulpelines diagramas, rodančias kaip kiekvienas modelis buvo vertas"""
    num_models, total_questions, total_grades, grades_by_model, generated_by_model, evaluated_by_model, perfect_from_both, grades_by_evaluated_and_evaluator = get_stats()
    
    # Spalvos kiekvienam įvertinimui
    grade_colors = {5: '#2ecc71', 4: '#3498db', 3: '#f39c12', 2: '#e74c3c', 1: '#c0392b'}
    grade_labels = {5: 'Puiku (5)', 4: 'Gerai (4)', 3: 'Vidutiniškai (3)', 2: 'Blogai (2)', 1: 'Labai blogai (1)'}
    
    models_list = sorted(grades_by_evaluated_and_evaluator.keys())
    
    for idx, evaluated_model in enumerate(models_list):
        # Sukurti atskirą figūrą kiekvienai diagramai
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.suptitle(f'{evaluated_model}', fontsize=14, fontweight='bold')
        
        evaluator_data = grades_by_evaluated_and_evaluator[evaluated_model]
        evaluators = sorted(evaluator_data.keys())
        
        # Pasiruošti duomenis
        grades_data = {evaluator: [] for evaluator in evaluators}
        
        for evaluator in evaluators:
            grades_dist = evaluator_data[evaluator]
            for grade in range(1, 6):
                grades_data[evaluator].append(grades_dist.get(grade, 0))
        
        # Sukurti diagramą
        x = np.arange(1, 6)
        width = 0.35
        
        for i, evaluator in enumerate(evaluators):
            offset = width * (i - (len(evaluators) - 1) / 2)
            colors = [grade_colors[grade] for grade in range(1, 6)]
            bars = ax.bar(x + offset, grades_data[evaluator], width, label=evaluator, alpha=0.8)
            # Pridėti skaičius prie stulpelių
            ax.bar_label(bars, fmt='%d', fontsize=10)
        
        ax.set_xlabel('Įvertinimas', fontsize=12, fontweight='bold')
        ax.set_ylabel('Įvertinių kiekis', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(['1', '2', '3', '4', '5'])
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # Išsaugoti atskirą diagramą
        output_dir = Path(__file__).parent.parent / "results" / "evaluation_charts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"evaluation_{evaluated_model}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Diagrama išsaugota: {output_path}")
        plt.close()

if __name__ == "__main__":
    print_statistics()
    print("\n")
    print_cross_evaluation_statistics()
    print("\n")
    plot_cross_evaluation_charts()