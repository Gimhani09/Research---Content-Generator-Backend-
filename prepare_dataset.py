"""
Dataset Preparation Tool
Helps you create training datasets for fine-tuning
"""
import json
import os
from typing import List, Dict

class DatasetBuilder:
    """Build training datasets for content generation"""
    
    def __init__(self):
        self.english_data = []
        self.sinhala_data = []
    
    def add_english_sample(self, product_name: str, description: str, 
                          marketing_text: str, tone: str = "professional"):
        """Add an English training sample"""
        prompt = f"Write a {tone} marketing message for {product_name}. {description}."
        
        self.english_data.append({
            "prompt": prompt,
            "completion": marketing_text,
            "metadata": {
                "product_name": product_name,
                "tone": tone,
                "language": "english"
            }
        })
    
    def add_sinhala_sample(self, product_name: str, description: str,
                          marketing_text: str, tone: str = "වෘත්තීය"):
        """Add a Sinhala training sample"""
        prompt = f"නිෂ්පාදනය: {product_name}. විස්තරය: {description}. {tone} ප්‍රචාරණ පණිවිඩයක් ලියන්න:"
        
        self.sinhala_data.append({
            "prompt": prompt,
            "completion": marketing_text,
            "metadata": {
                "product_name": product_name,
                "tone": tone,
                "language": "sinhala"
            }
        })
    
    def save_english(self, filename: str = "training_data_english.json"):
        """Save English dataset"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.english_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(self.english_data)} English samples to {filename}")
    
    def save_sinhala(self, filename: str = "training_data_sinhala.json"):
        """Save Sinhala dataset"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.sinhala_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(self.sinhala_data)} Sinhala samples to {filename}")
    
    def load_from_csv(self, csv_file: str, language: str = "english"):
        """Load data from CSV file
        CSV format: product_name,description,marketing_text,tone
        """
        import csv
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if language == "english":
                    self.add_english_sample(
                        row['product_name'],
                        row['description'],
                        row['marketing_text'],
                        row.get('tone', 'professional')
                    )
                else:
                    self.add_sinhala_sample(
                        row['product_name'],
                        row['description'],
                        row['marketing_text'],
                        row.get('tone', 'වෘත්තීය')
                    )
        
        print(f"✅ Loaded {len(self.english_data + self.sinhala_data)} samples from {csv_file}")

# Example usage and templates
if __name__ == "__main__":
    builder = DatasetBuilder()
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         DATASET PREPARATION TOOL                             ║
    ║  Create training data for fine-tuning your models            ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Example English samples
    print("\n📝 Adding example English samples...")
    
    builder.add_english_sample(
        product_name="Premium Milk Powder",
        description="High calcium, vitamin D enriched, suitable for children",
        marketing_text="Introducing Premium Milk Powder – the ultimate nutrition solution for growing children! Packed with high calcium and essential vitamin D, our scientifically formulated milk powder supports strong bones and healthy development. Give your children the gift of optimal nutrition. Available now at leading supermarkets!",
        tone="professional"
    )
    
    builder.add_english_sample(
        product_name="Running Shoes Pro",
        description="Lightweight design, breathable mesh, perfect for marathon runners",
        marketing_text="Unleash your inner athlete with Running Shoes Pro! Engineered with cutting-edge lightweight technology and breathable mesh fabric, these shoes are built for champions. Whether you're training for a marathon or enjoying a morning jog, experience unmatched comfort with every stride. Your feet will thank you!",
        tone="exciting"
    )
    
    builder.add_english_sample(
        product_name="Organic Green Tea",
        description="100% organic, antioxidant-rich, imported from premium estates",
        marketing_text="Discover the pure essence of wellness with our Organic Green Tea. Sourced from the finest organic estates, each cup delivers powerful antioxidants and natural goodness. Start your day with a refreshing boost of health and vitality. Pure. Organic. Perfect.",
        tone="professional"
    )
    
    # Example Sinhala samples
    print("📝 Adding example Sinhala samples...")
    
    builder.add_sinhala_sample(
        product_name="ප්‍රිමියම් කිරිපිටි",
        description="ඉහළ කැල්සියම්, විටමින් D සහිත, ළමුන් සඳහා සුදුසු",
        marketing_text="ප්‍රිමියම් කිරිපිටි හඳුන්වා දෙමු - වර්ධනය වන ළමුන් සඳහා පරිපූර්ණ පෝෂණ විසඳුම! ඉහළ කැල්සියම් සහ අත්‍යවශ්‍ය විටමින් D වලින් පොහොසත්, අපගේ විද්‍යාත්මකව සකස් කළ කිරිපිටි ශක්තිමත් ඇටකටු සහ සෞඛ්‍ය සම්පන්න වර්ධනයට සහාය වේ. ඔබේ දරුවන්ට උසස් පෝෂණයේ තෑග්ග ලබා දෙන්න. ප්‍රමුඛ සුපිරි වෙළඳසැල්වල දැන් ලබා ගත හැක!",
        tone="වෘත්තීය"
    )
    
    builder.add_sinhala_sample(
        product_name="ධාවන පාදුකා ප්‍රෝ",
        description="සැහැල්ලු නිර්මාණය, හුස්ම ගත හැකි දැල්, මැරතන් ධාවකයන් සඳහා පරිපූර්ණ",
        marketing_text="ධාවන පාදුකා ප්‍රෝ සමඟ ඔබේ අභ්‍යන්තර මලල ක්‍රීඩකයා මුදා හරින්න! අති නවීන සැහැල්ලු තාක්ෂණයෙන් සහ හුස්ම ගත හැකි දැල් රෙදිවලින් නිර්මාණය කර ඇති මෙම පාදුකා ශූරයන් සඳහා ගොඩනගා ඇත. ඔබ මැරතන් තරඟයක් සඳහා පුහුණු වන්නේ නම් හෝ උදෑසන ජෝගිං එකක් රස විඳින්නේ නම්, සෑම පියවරකම අසමසම සුවපහසුව අත්විඳින්න. ඔබේ පාද ඔබට ස්තූති කරනු ඇත!",
        tone="උද්යෝගිමත්"
    )
    
    # Save datasets
    builder.save_english()
    builder.save_sinhala()
    
    print(f"""
    ✅ Sample datasets created!
    
    📁 Files created:
       - training_data_english.json ({len(builder.english_data)} samples)
       - training_data_sinhala.json ({len(builder.sinhala_data)} samples)
    
    📝 To add more data:
       1. Edit the JSON files directly, OR
       2. Create a CSV file with columns: product_name,description,marketing_text,tone
       3. Run: builder.load_from_csv('your_file.csv', 'english')
    
    🚀 Next step: Run fine-tuning!
       python finetune.py
    """)
    
    # Create a sample CSV template
    import csv
    with open('dataset_template.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['product_name', 'description', 'marketing_text', 'tone'])
        writer.writerow(['Your Product', 'Product description here', 'Your marketing message here', 'professional'])
    
    print("📄 CSV template created: dataset_template.csv")
