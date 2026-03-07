"""
Evaluation Metrics for Generated Content
Assess quality of marketing text generation
"""
from rouge_score import rouge_scorer
from evaluate import load
import json
from typing import List, Dict
from local_content_generator import get_generator

class ContentEvaluator:
    """Evaluate generated marketing content"""
    
    def __init__(self):
        print("📊 Initializing evaluators...")
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        try:
            self.bleu = load("bleu")
            print("✅ BLEU metric loaded")
        except Exception as e:
            print(f"⚠️  BLEU metric not available: {e}")
            self.bleu = None
    
    def calculate_rouge(self, generated: str, reference: str) -> Dict:
        """Calculate ROUGE scores (similarity to reference)"""
        scores = self.rouge_scorer.score(reference, generated)
        return {
            'rouge1': scores['rouge1'].fmeasure,
            'rouge2': scores['rouge2'].fmeasure,
            'rougeL': scores['rougeL'].fmeasure
        }
    
    def calculate_bleu(self, generated: str, reference: str) -> float:
        """Calculate BLEU score"""
        if self.bleu is None:
            return 0.0
        
        results = self.bleu.compute(
            predictions=[generated],
            references=[[reference]]
        )
        return results['bleu']
    
    def evaluate_quality(self, generated: str) -> Dict:
        """Evaluate quality metrics without reference"""
        
        words = generated.split()
        sentences = generated.split('.')
        
        return {
            'length': len(generated),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'unique_words_ratio': len(set(words)) / len(words) if words else 0
        }
    
    def evaluate_dataset(self, dataset_path: str, model_type: str = "english") -> Dict:
        """Evaluate model on a test dataset"""
        
        print(f"\n📊 Evaluating {model_type} model...")
        
        # Load dataset
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load generator
        generator = get_generator()
        
        rouge_scores = {'rouge1': [], 'rouge2': [], 'rougeL': []}
        bleu_scores = []
        quality_scores = []
        
        for i, item in enumerate(data[:10]):  # Evaluate first 10 samples
            print(f"Evaluating sample {i+1}/10...", end='\r')
            
            # Extract product info from prompt
            prompt_parts = item['prompt'].split('.')
            product_name = prompt_parts[0].replace('Write a professional marketing message for', '').strip()
            description = prompt_parts[1].strip() if len(prompt_parts) > 1 else ""
            
            # Generate
            if model_type == "english":
                generated = generator.generate_english(product_name, description)
            else:
                generated = generator.generate_sinhala(product_name, description)
            
            reference = item['completion']
            
            # Calculate metrics
            rouge = self.calculate_rouge(generated, reference)
            for key in rouge_scores:
                rouge_scores[key].append(rouge[key])
            
            if self.bleu:
                bleu = self.calculate_bleu(generated, reference)
                bleu_scores.append(bleu)
            
            quality = self.evaluate_quality(generated)
            quality_scores.append(quality)
        
        # Average scores
        results = {
            'rouge1': sum(rouge_scores['rouge1']) / len(rouge_scores['rouge1']),
            'rouge2': sum(rouge_scores['rouge2']) / len(rouge_scores['rouge2']),
            'rougeL': sum(rouge_scores['rougeL']) / len(rouge_scores['rougeL']),
            'avg_length': sum(q['length'] for q in quality_scores) / len(quality_scores),
            'avg_word_count': sum(q['word_count'] for q in quality_scores) / len(quality_scores),
            'avg_unique_ratio': sum(q['unique_words_ratio'] for q in quality_scores) / len(quality_scores)
        }
        
        if bleu_scores:
            results['bleu'] = sum(bleu_scores) / len(bleu_scores)
        
        print("\n")
        return results
    
    def print_results(self, results: Dict):
        """Pretty print evaluation results"""
        print("\n" + "="*60)
        print("📊 EVALUATION RESULTS")
        print("="*60)
        
        print(f"\n🎯 Similarity Scores (higher is better):")
        print(f"   ROUGE-1: {results.get('rouge1', 0):.4f}")
        print(f"   ROUGE-2: {results.get('rouge2', 0):.4f}")
        print(f"   ROUGE-L: {results.get('rougeL', 0):.4f}")
        
        if 'bleu' in results:
            print(f"   BLEU:    {results['bleu']:.4f}")
        
        print(f"\n📝 Quality Metrics:")
        print(f"   Avg Length: {results['avg_length']:.0f} characters")
        print(f"   Avg Words:  {results['avg_word_count']:.0f} words")
        print(f"   Vocabulary Diversity: {results['avg_unique_ratio']:.2%}")
        
        print("\n" + "="*60)

# Test evaluation
if __name__ == "__main__":
    import os
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         CONTENT EVALUATION TOOL                              ║
    ║  Measure quality of generated marketing content              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    evaluator = ContentEvaluator()
    
    # Check if test data exists
    if os.path.exists("training_data_english.json"):
        print("\n✅ Found English training data")
        results = evaluator.evaluate_dataset("training_data_english.json", "english")
        evaluator.print_results(results)
    else:
        print("\n⚠️  No training data found. Run prepare_dataset.py first!")
        
        # Demo with manual evaluation
        print("\n📝 Demo: Evaluating sample text...\n")
        
        generated = "Introducing Premium Milk Powder - your family's trusted choice for nutrition!"
        reference = "Introducing Premium Milk Powder – the ultimate nutrition solution for growing children!"
        
        rouge = evaluator.calculate_rouge(generated, reference)
        quality = evaluator.evaluate_quality(generated)
        
        print("Generated:", generated)
        print("Reference:", reference)
        print(f"\nROUGE-L Score: {rouge['rougeL']:.4f}")
        print("Word Count:", quality['word_count'])
        print(f"Unique Words Ratio: {quality['unique_words_ratio']:.2%}")
