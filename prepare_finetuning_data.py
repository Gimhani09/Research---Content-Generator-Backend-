"""
Convert Excel dataset to fine-tuning JSON format
Prepares marketing_dataset_25000.xlsx for GPT-2 fine-tuning
"""
import pandas as pd
import json

def get_tone(description):
    """Determine tone from description text"""
    desc_lower = str(description).lower()
    if 'professional' in desc_lower or 'formal' in desc_lower:
        return 'professional'
    if 'exciting' in desc_lower or 'limited time' in desc_lower:
        return 'exciting'
    if 'casual' in desc_lower or 'friendly' in desc_lower:
        return 'casual'
    return 'professional'  # default

def get_language_code(language):
    """Convert language string to standard code"""
    if language == 'code_mix':
        return 'sinhala'  # Code-mixed content
    if language == 'english':
        return 'english'
    return 'english'  # default

def create_training_example(row):
    """Create a single training example from a row"""
    # Extract fields
    product_name = str(row['product_name'])
    description = str(row['description'])
    content = str(row['content'])
    language = str(row['language'])
    category = str(row['category'])
    platform = str(row.get('platform', 'general'))
    cta = str(row.get('cta', 'Learn more'))
    
    # Determine tone and language
    tone = get_tone(description)
    lang = get_language_code(language)
    
    # Create prompt
    prompt = f"Write a {tone} marketing message for {product_name}. {description}"
    
    # Create training example
    return {
        "prompt": prompt,
        "completion": content,
        "metadata": {
            "product_name": product_name,
            "tone": tone,
            "language": lang,
            "category": category,
            "platform": platform,
            "cta": cta
        }
    }

def print_statistics(training_data):
    """Print dataset statistics"""
    categories = {}
    tones = {}
    for ex in training_data:
        cat = ex['metadata']['category']
        tone = ex['metadata']['tone']
        categories[cat] = categories.get(cat, 0) + 1
        tones[tone] = tones.get(tone, 0) + 1
    
    print("\n  Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"    {cat}: {count}")
    
    print("\n  Tones:")
    for tone, count in sorted(tones.items(), key=lambda x: x[1], reverse=True):
        print(f"    {tone}: {count}")

def save_datasets(training_data, english_data, sinhala_data):
    """Save datasets to JSON files"""
    # Save full dataset
    full_output = 'training_data_full_25k.json'
    with open(full_output, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved full dataset: {full_output}")
    
    # Save English dataset
    english_output = 'training_data_english_25k.json'
    with open(english_output, 'w', encoding='utf-8') as f:
        json.dump(english_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved English dataset: {english_output}")
    
    # Save Sinhala dataset
    sinhala_output = 'training_data_sinhala_25k.json'
    with open(sinhala_output, 'w', encoding='utf-8') as f:
        json.dump(sinhala_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved Sinhala dataset: {sinhala_output}")

def convert_excel_to_finetuning_json():
    """Convert Excel dataset to prompt-completion format for fine-tuning"""
    
    print("🔄 Loading Excel dataset...")
    df = pd.read_excel('dataset/marketing_dataset_25000.xlsx')
    
    print(f"✅ Loaded {len(df)} examples")
    print(f"📊 Columns: {list(df.columns)}")
    
    # Prepare training data
    training_data = []
    
    print("\n🔧 Converting to fine-tuning format...")
    
    for idx, row in df.iterrows():
        # Create training example
        example = create_training_example(row)
        training_data.append(example)
        
        # Progress indicator
        if (idx + 1) % 5000 == 0:
            print(f"  Processed {idx + 1}/{len(df)} examples...")
    
    print(f"✅ Converted {len(training_data)} examples")
    
    # Split into English and Sinhala datasets
    english_data = [ex for ex in training_data if ex['metadata']['language'] == 'english']
    sinhala_data = [ex for ex in training_data if ex['metadata']['language'] == 'sinhala']
    
    print("\n📝 Dataset Split:")
    print(f"  English: {len(english_data)} examples")
    print(f"  Sinhala/Code-mix: {len(sinhala_data)} examples")
    
    # Save datasets
    save_datasets(training_data, english_data, sinhala_data)
    
    # Show sample
    print("\n📄 Sample converted data:")
    print("=" * 80)
    sample = training_data[0]
    print(f"Prompt: {sample['prompt']}")
    print(f"Completion: {sample['completion'][:200]}...")
    print(f"Metadata: {sample['metadata']}")
    print("=" * 80)
    
    # Statistics
    print("\n📊 Dataset Statistics:")
    print_statistics(training_data)
    
    print("\n✅ Dataset preparation complete!")
    print("\n🎯 Next steps:")
    print("  1. Review the generated files")
    print("  2. Run fine-tuning for English:")
    print("     python finetune.py --model english --dataset training_data_english_25k.json")
    print("  3. Run fine-tuning for Sinhala:")
    print("     python finetune.py --model sinhala --dataset training_data_sinhala_25k.json")
    
    return training_data

if __name__ == "__main__":
    convert_excel_to_finetuning_json()
