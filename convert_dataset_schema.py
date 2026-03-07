"""
Convert dataset from old schema (6 fields) to new schema (5 fields).

Old Schema: category, product_name, description, tone, language, content
New Schema: product_service, content_type, target_audience, tone, language, content
"""

import json
import os

def infer_content_type(category, product_name, description, content):
    """Infer content_type from category and content."""
    content_lower = content.lower()
    
    # Check for social media indicators
    social_indicators = ['🍔', '🍕', '🍟', '☕', '🌮', '🍗', '🥑', '💄', '👠', '🧥', '🎮', '🎧', '⌚', '🎵', 
                         '🌸', '✨', '😎', '🧋', '🔥', '☀️', 'grab', 'tag', 'follow', 'share']
    
    # Check for email/newsletter indicators
    email_indicators = ['dear', 'subscribe', 'newsletter', 'inbox']
    
    # Check for product description indicators
    product_indicators = ['feature', 'specification', 'available', 'range', 'collection', 'quality']
    
    # Priority matching
    if any(indicator in content_lower for indicator in social_indicators):
        return "Social Media Post"
    elif any(indicator in content_lower for indicator in email_indicators):
        return "Email Marketing"
    elif any(indicator in content_lower for indicator in product_indicators):
        return "Product Description"
    elif 'sale' in category.lower() or 'offer' in product_name.lower() or 'discount' in description.lower():
        return "Social Media Post"
    elif category in ["Food", "Beverages", "Dessert"]:
        return "Social Media Post"
    else:
        return "Product Description"

def infer_target_audience(category, product_name, description, content):
    """Infer target_audience from context."""
    combined_text = f"{category} {product_name} {description} {content}".lower()
    
    # Age/demographic based
    if any(word in combined_text for word in ['kids', 'children', 'school', 'පොඩි', 'දරුව', 'සිගිති']):
        return "Parents with Kids"
    elif any(word in combined_text for word in ['student', 'assignment', 'college']):
        return "Students"
    elif any(word in combined_text for word in ['office', 'professional', 'executive', 'business', 'work']):
        return "Young Professionals"
    elif any(word in combined_text for word in ['wedding', 'party', 'saree', 'formal']):
        return "Event Attendees"
    elif any(word in combined_text for word in ['fitness', 'gym', 'workout', 'yoga', 'active']):
        return "Fitness Enthusiasts"
    elif any(word in combined_text for word in ['gamer', 'gaming', 'rgb']):
        return "Gamers"
    elif any(word in combined_text for word in ['family', 'පවුල', 'home', 'ගෙදර']):
        return "Families"
    elif any(word in combined_text for word in ['ladies', 'women', 'makeup', 'beauty']):
        return "Women"
    elif any(word in combined_text for word in ['men', 'gentleman', 'guy']):
        return "Men"
    elif any(word in combined_text for word in ['youth', 'youthful', 'trendy', 'වයසේ']):
        return "Youth"
    elif any(word in combined_text for word in ['diet', 'healthy', 'health', 'organic']):
        return "Health-conscious Consumers"
    elif any(word in combined_text for word in ['luxury', 'premium', 'elegant']):
        return "Affluent Customers"
    elif any(word in combined_text for word in ['budget', 'affordable', 'cheap', 'අඩු මිල']):
        return "Budget Shoppers"
    else:
        return "General Public"

def fix_empty_language(language, content):
    """Fix empty language field by detecting from content."""
    if language and language.strip():
        return language
    
    # Detect Sinhala characters
    has_sinhala = any('\u0D80' <= char <= '\u0DFF' for char in content)
    # Detect English (basic check)
    has_english = any(char.isalpha() and ord(char) < 128 for char in content)
    
    if has_sinhala and has_english:
        return "mixed"
    elif has_sinhala:
        return "sinhala"
    elif has_english:
        return "english"
    else:
        return "english"  # Default

def convert_entry(old_entry):
    """Convert a single entry from old schema to new schema."""
    # Extract old fields
    category = old_entry.get("category", "")
    product_name = old_entry.get("product_name", "")
    description = old_entry.get("description", "")
    tone = old_entry.get("tone", "casual")
    language = old_entry.get("language", "")
    content = old_entry.get("content", "")
    
    # Fix empty language
    language = fix_empty_language(language, content)
    
    # Infer new fields
    content_type = infer_content_type(category, product_name, description, content)
    target_audience = infer_target_audience(category, product_name, description, content)
    
    # Use product_name as product_service
    product_service = product_name if product_name else category
    
    # Create new entry
    new_entry = {
        "product_service": product_service,
        "content_type": content_type,
        "target_audience": target_audience,
        "tone": tone,
        "language": language,
        "content": content
    }
    
    return new_entry

def convert_dataset(input_file, output_file):
    """Convert entire dataset from old to new schema."""
    # Load old dataset
    with open(input_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    print(f"📂 Loaded {len(old_data)} entries from {input_file}")
    
    # Convert all entries
    new_data = []
    for i, old_entry in enumerate(old_data, 1):
        try:
            new_entry = convert_entry(old_entry)
            new_data.append(new_entry)
        except Exception as e:
            print(f"❌ Error converting entry {i}: {e}")
            print(f"   Entry: {old_entry}")
    
    # Save new dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Converted {len(new_data)} entries")
    print(f"💾 Saved to: {output_file}")
    
    # Statistics
    print("\n📊 Conversion Statistics:")
    print(f"   Total entries: {len(new_data)}")
    
    # Language distribution
    lang_dist = {}
    for entry in new_data:
        lang = entry['language']
        lang_dist[lang] = lang_dist.get(lang, 0) + 1
    
    print("\n   Language distribution:")
    for lang, count in sorted(lang_dist.items()):
        print(f"     {lang}: {count} ({100*count/len(new_data):.1f}%)")
    
    # Content type distribution
    content_type_dist = {}
    for entry in new_data:
        ct = entry['content_type']
        content_type_dist[ct] = content_type_dist.get(ct, 0) + 1
    
    print("\n   Content type distribution:")
    for ct, count in sorted(content_type_dist.items()):
        print(f"     {ct}: {count} ({100*count/len(new_data):.1f}%)")
    
    # Target audience distribution
    audience_dist = {}
    for entry in new_data:
        aud = entry['target_audience']
        audience_dist[aud] = audience_dist.get(aud, 0) + 1
    
    print("\n   Target audience distribution:")
    for aud, count in sorted(audience_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"     {aud}: {count} ({100*count/len(new_data):.1f}%)")
    
    return new_data

if __name__ == "__main__":
    # Paths
    input_file = "dataset/marketing_content_template.json"
    output_file = "dataset/marketing_content_template_new.json"
    backup_file = "dataset/marketing_content_template_backup.json"
    
    # Backup original file
    if os.path.exists(input_file):
        import shutil
        shutil.copy(input_file, backup_file)
        print(f"📦 Backup created: {backup_file}\n")
    
    # Convert
    new_data = convert_dataset(input_file, output_file)
    
    print("\n" + "="*60)
    print("🎉 Conversion complete!")
    print("="*60)
    print(f"\n📝 Next steps:")
    print(f"   1. Review the new file: {output_file}")
    print(f"   2. If satisfied, replace the old file:")
    print(f"      - Delete/rename: {input_file}")
    print(f"      - Rename: {output_file} → {input_file}")
    print(f"   3. Original backed up to: {backup_file}")
