"""
Clean training data - Fix repetitions and encoding issues
"""
import json
import re

def clean_completion(text):
    """Clean up completion text"""
    # Fix encoding issues (� to -)
    text = text.replace('�', '—')
    text = text.replace('â€"', '—')
    
    # Fix word repetitions (e.g., "now now" -> "now")
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up punctuation issues
    text = text.replace(' .', '.')
    text = text.replace(' !', '!')
    text = text.replace(' ,', ',')
    
    return text.strip()

def clean_dataset(input_file, output_file):
    """Clean the entire dataset"""
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Cleaning {len(data)} examples...")
    
    cleaned = []
    issues_fixed = 0
    
    for ex in data:
        original = ex['completion']
        cleaned_text = clean_completion(original)
        
        if original != cleaned_text:
            issues_fixed += 1
        
        ex['completion'] = cleaned_text
        cleaned.append(ex)
    
    print(f"Fixed {issues_fixed} examples with issues")
    
    # Save cleaned data
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Done! Saved {len(cleaned)} cleaned examples")

if __name__ == "__main__":
    # Clean both datasets
    clean_dataset('training_data_english_25k.json', 'training_data_english_25k_cleaned.json')
    clean_dataset('training_data_sinhala_25k.json', 'training_data_sinhala_25k_cleaned.json')
    print("\n✅ All datasets cleaned!")
