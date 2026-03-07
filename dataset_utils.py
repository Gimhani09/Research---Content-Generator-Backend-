"""
Dataset Preparation Utilities
Tools for creating, validating, and managing training datasets
"""
import json
import csv
import pandas as pd
from typing import List, Dict, Any
import os

# Constants
JSON_EXTENSION = '.json'

class DatasetValidator:
    """Validate dataset format and content"""
    
    # NEW SCHEMA (correct for training)
    REQUIRED_COLUMNS = ['product_service', 'content_type', 'target_audience', 'tone', 'language', 'content']
    VALID_TONES = ['professional', 'casual', 'exciting', 'formal', 'elegant', 'romantic', 'energetic', 
                   'traditional', 'tempting', 'warm', 'confident', 'inspiring', 'soothing', 'modern',
                   'luxury', 'fun', 'dreamy', 'cozy', 'fresh', 'calm', 'cool', 'rugged', 'helpful',
                   'youthful', 'trendy', 'bold', 'cute', 'practical', 'chic', 'playful', 'sassy',
                   'retro', 'bubbly', 'thoughtful', 'motivational', 'savory', 'adventurous', 'sunny']
    VALID_LANGUAGES = ['english', 'sinhala', 'mixed']
    VALID_CONTENT_TYPES = ['Social Media Post', 'Product Description', 'Email Marketing', 'Blog Post', 'Advertisement']
    
    @staticmethod
    def validate_entry(entry: Dict, index: int = None) -> List[str]:
        """
        Validate a single dataset entry
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        entry_label = f"Entry {index}" if index is not None else "Entry"
        
        # Check required fields
        for field in DatasetValidator.REQUIRED_COLUMNS:
            if field not in entry:
                errors.append(f"{entry_label}: Missing required field '{field}'")
            elif not entry[field] or str(entry[field]).strip() == '':
                errors.append(f"{entry_label}: Field '{field}' is empty")
        
        # Validate tone
        if 'tone' in entry and entry['tone'] not in DatasetValidator.VALID_TONES:
            errors.append(
                f"{entry_label}: Invalid tone '{entry['tone']}'. "
                f"Must be one of: {', '.join(DatasetValidator.VALID_TONES)}"
            )
        
        # Validate language
        if 'language' in entry and entry['language'] not in DatasetValidator.VALID_LANGUAGES:
            errors.append(
                f"{entry_label}: Invalid language '{entry['language']}'. "
                f"Must be one of: {', '.join(DatasetValidator.VALID_LANGUAGES)}"
            )
        
        # Validate content_type
        if 'content_type' in entry and entry['content_type'] not in DatasetValidator.VALID_CONTENT_TYPES:
            errors.append(
                f"{entry_label}: Invalid content_type '{entry['content_type']}'. "
                f"Must be one of: {', '.join(DatasetValidator.VALID_CONTENT_TYPES)}"
            )
        
        # Check content length
        if 'content' in entry:
            content_length = len(str(entry['content']))
            if content_length < 20:
                errors.append(f"{entry_label}: Content too short ({content_length} chars). Minimum 20 chars.")
            elif content_length > 500:
                errors.append(f"{entry_label}: Content too long ({content_length} chars). Maximum 500 chars recommended.")
        
        return errors
    
    @staticmethod
    def _update_statistics(entry: Dict, lang_dist: Dict, tone_dist: Dict):
        """Update language and tone distribution statistics"""
        if 'language' in entry:
            lang_dist[entry['language']] = lang_dist.get(entry['language'], 0) + 1
        if 'tone' in entry:
            tone_dist[entry['tone']] = tone_dist.get(entry['tone'], 0) + 1
    
    @staticmethod
    def _check_language_balance(total_entries: int, lang_dist: Dict, warnings: List[str]):
        """Check for balanced language distribution"""
        if total_entries > 0:
            for lang, count in lang_dist.items():
                percentage = (count / total_entries) * 100
                if percentage < 10 and count > 0:
                    warnings.append(
                        f"Low representation of '{lang}' language ({count} entries, {percentage:.1f}%). "
                        f"Consider adding more examples for better model performance."
                    )
    
    @staticmethod
    def validate_dataset(data: List[Dict]) -> Dict:
        """
        Validate entire dataset
        
        Returns:
            {
                'is_valid': bool,
                'total_entries': int,
                'valid_entries': int,
                'errors': List[str],
                'warnings': List[str],
                'statistics': Dict
            }
        """
        total_entries = len(data)
        all_errors = []
        warnings = []
        valid_count = 0
        
        # Language distribution
        lang_dist = {'english': 0, 'sinhala': 0, 'mixed': 0}
        tone_dist = {'professional': 0, 'casual': 0, 'exciting': 0, 'formal': 0}
        
        for i, entry in enumerate(data, 1):
            entry_errors = DatasetValidator.validate_entry(entry, i)
            
            if not entry_errors:
                valid_count += 1
                DatasetValidator._update_statistics(entry, lang_dist, tone_dist)
            else:
                all_errors.extend(entry_errors)
        
        # Check for balanced dataset
        DatasetValidator._check_language_balance(total_entries, lang_dist, warnings)
        
        # Minimum dataset size warning
        if total_entries < 100:
            warnings.append(
                f"Dataset has only {total_entries} entries. "
                f"For research-quality results, aim for 200-500 examples."
            )
        
        return {
            'is_valid': len(all_errors) == 0,
            'total_entries': total_entries,
            'valid_entries': valid_count,
            'errors': all_errors,
            'warnings': warnings,
            'statistics': {
                'language_distribution': lang_dist,
                'tone_distribution': tone_dist
            }
        }


def create_dataset_template(output_path: str = "dataset/marketing_content_template.csv"):
    """Create a CSV template with example entries"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    examples = [
        {
            'product_name': 'Premium Milk Powder',
            'description': 'High calcium, vitamin enriched for children',
            'tone': 'professional',
            'language': 'english',
            'content': 'Introducing Premium Milk Powder - specially formulated for growing children. Enriched with essential vitamins and high calcium content to support healthy bone development. Trust the quality your family deserves. Available at leading supermarkets island-wide.'
        },
        {
            'product_name': 'ප්‍රිමියම් කිරිපිටි',
            'description': 'ළමුන් සඳහා විශේෂ කැල්සියම් බහුල',
            'tone': 'casual',
            'language': 'sinhala',
            'content': 'ඔබේ දරුවාට හොඳම පෝෂණය ලබා දෙන්න! ප්‍රිමියම් කිරිපිටි - කැල්සියම් හා විටමින් වලින් පොහොසත්. ළමයින්ගේ සෞඛ්‍ය සම්පන්න වර්ධනයට උපකාරී. දැන්ම ඔබේ ළඟම සුපිරි වෙළඳසැලෙන් ලබා ගන්න!'
        },
        {
            'product_name': 'Premium Milk එක',
            'description': 'Best for children, calcium වැඩියි',
            'tone': 'exciting',
            'language': 'mixed',
            'content': 'අපේ Premium Milk Powder එක try කරලා බලන්න! ළමයින්ට ඕනෑ හැම nutrition එකක්ම තියෙනවා. High calcium content එක bones වලට super good! දැන්ම online order කරන්න or ළඟම shop එකෙන් ගන්න. Limited time offer!'
        },
        {
            'product_name': 'Fashion Footwear Collection',
            'description': 'Trendy shoes for all occasions',
            'tone': 'professional',
            'language': 'english',
            'content': 'Step into style with our new Fashion Footwear Collection. Carefully curated designs for every occasion - from casual outings to formal events. Premium quality materials, exceptional comfort, and contemporary aesthetics. Visit our showrooms or shop online today.'
        },
        {
            'product_name': 'සුපිරි රස කෑම',
            'description': 'ගෙදර හැදූ වගේ රසවත්',
            'tone': 'casual',
            'language': 'sinhala',
            'content': 'අම්මා හදන එකට වඩා රස! අපේ සුපිරි රස කෑම ගෙදර හැදූ වගේම රසවත් හා සෞඛ්‍ය සම්පන්න. නැවුම් අමුද්‍රව්‍ය වලින් පමණක් සාදන ලද. දැන්ම අපේ outlet වලට පැමිණෙන්න හෝ home delivery සඳහා අමතන්න!'
        }
    ]
    
    # Save as CSV
    df = pd.DataFrame(examples)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')  # BOM for Excel compatibility
    
    print(f"✅ Template created at: {output_path}")
    print(f"📝 Contains {len(examples)} example entries")
    print("\nColumns:")
    for col in DatasetValidator.REQUIRED_COLUMNS:
        print(f"  - {col}")
    print("\nValid values:")
    print(f"  - tone: {', '.join(DatasetValidator.VALID_TONES)}")
    print(f"  - language: {', '.join(DatasetValidator.VALID_LANGUAGES)}")
    
    return output_path


def create_dataset_json_template(output_path: str = "dataset/marketing_content_template.json"):
    """Create a JSON template with example entries"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    examples = [
        {
            'product_name': 'Premium Milk Powder',
            'description': 'High calcium, vitamin enriched for children',
            'tone': 'professional',
            'language': 'english',
            'content': 'Introducing Premium Milk Powder - specially formulated for growing children. Enriched with essential vitamins and high calcium content to support healthy bone development. Trust the quality your family deserves. Available at leading supermarkets island-wide.'
        },
        {
            'product_name': 'ප්‍රිමියම් කිරිපිටි',
            'description': 'ළමුන් සඳහා විශේෂ කැල්සියම් බහුල',
            'tone': 'casual',
            'language': 'sinhala',
            'content': 'ඔබේ දරුවාට හොඳම පෝෂණය ලබා දෙන්න! ප්‍රිමියම් කිරිපිටි - කැල්සියම් හා විටමින් වලින් පොහොසත්. ළමයින්ගේ සෞඛ්‍ය සම්පන්න වර්ධනයට උපකාරී. දැන්ම ඔබේ ළඟම සුපිරි වෙළඳසැලෙන් ලබා ගන්න!'
        },
        {
            'product_name': 'Premium Milk එක',
            'description': 'Best for children, calcium වැඩියි',
            'tone': 'exciting',
            'language': 'mixed',
            'content': 'අපේ Premium Milk Powder එක try කරලා බලන්න! ළමයින්ට ඕනෑ හැම nutrition එකක්ම තියෙනවා. High calcium content එක bones වලට super good! දැන්ම online order කරන්න or ළඟම shop එකෙන් ගන්න. Limited time offer!'
        }
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON template created at: {output_path}")
    print(f"📝 Contains {len(examples)} example entries")
    
    return output_path


def _load_dataset_file(filepath: str) -> Any:
    """Load dataset from JSON or CSV file"""
    if filepath.endswith(JSON_EXTENSION):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
        return df.to_dict('records')
    return None

def _print_validation_header(filepath: str):
    """Print validation report header"""
    print(f"\n{'='*60}")
    print(f"VALIDATING DATASET: {filepath}")
    print(f"{'='*60}\n")

def validate_dataset_file(filepath: str):
    """Validate a dataset file and print report"""
    
    _print_validation_header(filepath)
    
    # Load dataset
    data = _load_dataset_file(filepath)
    if data is None:
        print("❌ Error: File must be .json or .csv")
        return False
    
    # Validate
    result = DatasetValidator.validate_dataset(data)
    
    # Print results
    print(f"📊 Total entries: {result['total_entries']}")
    print(f"✅ Valid entries: {result['valid_entries']}")
    print(f"❌ Invalid entries: {result['total_entries'] - result['valid_entries']}")
    
    if result['errors']:
        print(f"\n{'='*60}")
        print(f"❌ ERRORS ({len(result['errors'])})")
        print(f"{'='*60}")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result['warnings']:
        print(f"\n{'='*60}")
        print(f"⚠️  WARNINGS ({len(result['warnings'])})")
        print(f"{'='*60}")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    # Statistics
    print(f"\n{'='*60}")
    print("📈 DATASET STATISTICS")
    print(f"{'='*60}")
    
    print("\nLanguage Distribution:")
    for lang, count in result['statistics']['language_distribution'].items():
        percentage = (count / result['total_entries'] * 100) if result['total_entries'] > 0 else 0
        print(f"  - {lang}: {count} ({percentage:.1f}%)")
    
    print("\nTone Distribution:")
    for tone, count in result['statistics']['tone_distribution'].items():
        percentage = (count / result['total_entries'] * 100) if result['total_entries'] > 0 else 0
        print(f"  - {tone}: {count} ({percentage:.1f}%)")
    
    # Final verdict
    print(f"\n{'='*60}")
    if result['is_valid']:
        print("✅ DATASET IS VALID AND READY FOR TRAINING!")
    else:
        print("❌ DATASET HAS ERRORS - PLEASE FIX BEFORE TRAINING")
    print(f"{'='*60}\n")
    
    return result['is_valid']


def csv_to_json(csv_path: str, json_path: str = None):
    """Convert CSV dataset to JSON format"""
    if json_path is None:
        json_path = csv_path.replace('.csv', JSON_EXTENSION)
    
    df = pd.read_csv(csv_path)
    data = df.to_dict('records')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {csv_path} to {json_path}")
    return json_path


def json_to_csv(json_path: str, csv_path: str = None):
    """Convert JSON dataset to CSV format"""
    if csv_path is None:
        csv_path = json_path.replace(JSON_EXTENSION, '.csv')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ Converted {json_path} to {csv_path}")
    return csv_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dataset preparation utilities")
    parser.add_argument("--create-template", action="store_true", help="Create dataset template files")
    parser.add_argument("--validate", type=str, help="Validate a dataset file")
    parser.add_argument("--csv-to-json", type=str, help="Convert CSV to JSON")
    parser.add_argument("--json-to-csv", type=str, help="Convert JSON to CSV")
    
    args = parser.parse_args()
    
    if args.create_template:
        print("\n📝 Creating dataset templates...\n")
        create_dataset_template()
        print()
        create_dataset_json_template()
        print("\n✅ Templates created! Edit them to add your data, then validate before training.")
    
    elif args.validate:
        validate_dataset_file(args.validate)
    
    elif args.csv_to_json:
        csv_to_json(args.csv_to_json)
    
    elif args.json_to_csv:
        json_to_csv(args.json_to_csv)
    
    else:
        parser.print_help()
