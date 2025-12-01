#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

def fix_question_ids(folder_path):
    """
    Fix all question IDs in JSON files.
    Changes IDs like "Jn_1_002", "Jn_1_003" to "Jn_1_001", "Jn_1_002", etc.
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Klaida: Folder '{folder}' nerastas.")
        return
    
    # Get all questions_*.json files
    json_files = sorted(folder.glob("questions_*.json"))
    
    if not json_files:
        print(f"Klaida: Jokių questions_*.json failų nerasta '{folder}'.")
        return
    
    print(f"INFO: Rasta {len(json_files)} failų. Pradedamas apdorojimas...\n")
    
    total_fixed = 0
    
    for json_file in json_files:
        try:
            print(f"Apdorojamas failas: {json_file.name}")
            
            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            # Fix IDs for each question
            questions_fixed = 0
            for i, question in enumerate(questions, 1):
                if "id" in question:
                    # Extract chapter name and create new ID
                    chapter = question.get("chapter", "unknown")
                    old_id = question["id"]
                    new_id = f"{chapter}_{i:03d}"
                    question["id"] = new_id
                    questions_fixed += 1
                    
                    if i <= 3 or i == len(questions):  # Show first 3 and last
                        print(f"  {old_id} -> {new_id}")
            
            # Write back to file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            
            print(f"✓ {json_file.name}: {questions_fixed} IDs fixed.\n")
            total_fixed += questions_fixed
            
        except Exception as e:
            print(f"✗ Klaida apdorojant {json_file.name}: {e}\n")
    
    print(f"{'='*60}")
    print(f"Iš viso pataisyta IDs: {total_fixed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Folder containing your question JSON files
    questions_folder = Path(__file__).parent / "questions" / "testing_questions" / "klausimai_Jn"
    fix_question_ids(questions_folder)
