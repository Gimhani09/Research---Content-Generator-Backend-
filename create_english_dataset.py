"""
Filter dataset to English-only entries for initial GPT-2 fine-tuning
"""

import json

# Load full dataset
with open('dataset/marketing_content_template.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter English only
english_data = [entry for entry in data if entry['language'] == 'english']

print(f"Total entries: {len(data)}")
print(f"English entries: {len(english_data)} ({100*len(english_data)/len(data):.1f}%)")

# Save English-only dataset
with open('dataset/marketing_content_english_only.json', 'w', encoding='utf-8') as f:
    json.dump(english_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ English-only dataset saved to: dataset/marketing_content_english_only.json")
print(f"   Ready for GPT-2 fine-tuning!")

# Statistics
content_types = {}
for entry in english_data:
    ct = entry['content_type']
    content_types[ct] = content_types.get(ct, 0) + 1

print(f"\nContent type distribution:")
for ct, count in sorted(content_types.items()):
    print(f"  {ct}: {count}")
