"""
FREE LOCAL Content Generation
Supports English and Sinhala without API keys
Uses: GPT-2 Medium (English) + mT5 (Multilingual including Sinhala)
"""
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    pipeline
)
import torch
from config import config
import os

class LocalContentGenerator:
    def __init__(self, use_finetuned: bool = None):
        """
        Initialize content generator
        
        Args:
            use_finetuned: Whether to use fine-tuned model (overrides config)
        """
        self.device = "cuda" if config.USE_GPU and torch.cuda.is_available() else "cpu"
        print(f"🖥️  Using device: {self.device}")
        
        # Create cache directory
        os.makedirs(config.MODEL_CACHE_DIR, exist_ok=True)
        
        # Determine which model to use
        if use_finetuned is None:
            use_finetuned = config.USE_FINETUNED
        
        # Load English/Bilingual model (GPT-2 Medium - Base or Fine-tuned)
        if use_finetuned and os.path.exists(config.FINETUNED_MODEL_PATH):
            print(f"📥 Loading FINE-TUNED LoRA model from {config.FINETUNED_MODEL_PATH}...")
            self.is_finetuned = True
            
            try:
                # LoRA adapters need PEFT library
                try:
                    from peft import PeftModel, PeftConfig
                    HAS_PEFT = True
                except ImportError:
                    HAS_PEFT = False
                    raise ImportError("peft library required for fine-tuned model")
                
                # Load base model first
                base_model_name = config.ENGLISH_MODEL  # gpt2-medium
                self.english_tokenizer = AutoTokenizer.from_pretrained(
                    base_model_name,
                    cache_dir=config.MODEL_CACHE_DIR
                )
                if self.english_tokenizer.pad_token is None:
                    self.english_tokenizer.pad_token = self.english_tokenizer.eos_token
                
                base_model = AutoModelForCausalLM.from_pretrained(
                    base_model_name,
                    cache_dir=config.MODEL_CACHE_DIR,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                
                # Load LoRA adapters on top of base model
                self.english_model = PeftModel.from_pretrained(
                    base_model,
                    config.FINETUNED_MODEL_PATH,
                    is_trainable=False  # Inference mode
                ).to(self.device)
                
                print("✅ Fine-tuned LoRA model loaded successfully!")
                
            except Exception as e:
                print(f"⚠️ Failed to load fine-tuned model: {e}")
                print("⏳ Falling back to base model (GPT-2 Medium)...")
                self.is_finetuned = False
                
                self.english_tokenizer = AutoTokenizer.from_pretrained(
                    config.ENGLISH_MODEL,
                    cache_dir=config.MODEL_CACHE_DIR
                )
                if self.english_tokenizer.pad_token is None:
                    self.english_tokenizer.pad_token = self.english_tokenizer.eos_token
                
                self.english_model = AutoModelForCausalLM.from_pretrained(
                    config.ENGLISH_MODEL,
                    cache_dir=config.MODEL_CACHE_DIR,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                ).to(self.device)
        else:
            print("📥 Loading BASE English model (GPT-2 Medium)...")
            model_path = config.ENGLISH_MODEL
            self.is_finetuned = False
            if use_finetuned:
                print(f"⚠️ Fine-tuned model not found at {config.FINETUNED_MODEL_PATH}")
                print("Using base model instead. Train a model using finetune_gpt2.py")
            
            self.english_tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                cache_dir=config.MODEL_CACHE_DIR
            )
            # Set padding token if not set
            if self.english_tokenizer.pad_token is None:
                self.english_tokenizer.pad_token = self.english_tokenizer.eos_token
            
            self.english_model = AutoModelForCausalLM.from_pretrained(
                model_path,
                cache_dir=config.MODEL_CACHE_DIR,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
        
        # Load Sinhala/Multilingual model (mT5 - Base or Fine-tuned)
        use_finetuned_sinhala = config.USE_FINETUNED_SINHALA if hasattr(config, 'USE_FINETUNED_SINHALA') else False
        
        if use_finetuned_sinhala and os.path.exists(config.FINETUNED_SINHALA_MODEL_PATH):
            print(f"📥 Loading FINE-TUNED Sinhala LoRA model from {config.FINETUNED_SINHALA_MODEL_PATH}...")
            self.is_sinhala_finetuned = True
            
            try:
                # LoRA adapters need PEFT library
                try:
                    from peft import PeftModel, PeftConfig
                    HAS_PEFT = True
                except ImportError:
                    HAS_PEFT = False
                    raise ImportError("peft library required for fine-tuned model")
                
                # Load base model first
                self.sinhala_tokenizer = AutoTokenizer.from_pretrained(
                    config.SINHALA_MODEL,
                    cache_dir=config.MODEL_CACHE_DIR,
                    use_fast=True
                )
                
                base_model = AutoModelForSeq2SeqLM.from_pretrained(
                    config.SINHALA_MODEL,
                    cache_dir=config.MODEL_CACHE_DIR,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                
                # Load LoRA adapters on top of base model
                self.sinhala_model = PeftModel.from_pretrained(
                    base_model,
                    config.FINETUNED_SINHALA_MODEL_PATH,
                    is_trainable=False
                ).to(self.device)
                
                print("✅ Fine-tuned Sinhala LoRA model loaded successfully!")
                self.sinhala_available = True
                
            except Exception as e:
                print(f"⚠️ Failed to load fine-tuned Sinhala model: {e}")
                print("⏳ Falling back to base mT5 model...")
                self.is_sinhala_finetuned = False
                
                try:
                    self.sinhala_tokenizer = AutoTokenizer.from_pretrained(
                        config.SINHALA_MODEL,
                        cache_dir=config.MODEL_CACHE_DIR,
                        use_fast=True
                    )
                    self.sinhala_model = AutoModelForSeq2SeqLM.from_pretrained(
                        config.SINHALA_MODEL,
                        cache_dir=config.MODEL_CACHE_DIR,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                    ).to(self.device)
                    print("✅ Base Sinhala model loaded successfully!")
                    self.sinhala_available = True
                except Exception as e2:
                    print(f"⚠️ Failed to load Sinhala model: {e2}")
                    print("⚠️ Sinhala content generation will be disabled.")
                    self.sinhala_tokenizer = None
                    self.sinhala_model = None
                    self.sinhala_available = False
        else:
            # Load base mT5 model
            print("📥 Loading BASE Sinhala model (mT5-base)...")
            self.is_sinhala_finetuned = False
            if use_finetuned_sinhala:
                print(f"⚠️ Fine-tuned Sinhala model not found at {config.FINETUNED_SINHALA_MODEL_PATH}")
                print("Using base model instead. Train using: python finetune.py --model sinhala")
            
            try:
                self.sinhala_tokenizer = AutoTokenizer.from_pretrained(
                    config.SINHALA_MODEL,
                    cache_dir=config.MODEL_CACHE_DIR,
                    use_fast=True
                )
                self.sinhala_model = AutoModelForSeq2SeqLM.from_pretrained(
                    config.SINHALA_MODEL,
                    cache_dir=config.MODEL_CACHE_DIR,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                ).to(self.device)
                print("✅ Sinhala model loaded successfully!")
                self.sinhala_available = True
            except Exception as e:
                print(f"⚠️ Failed to load Sinhala model: {e}")
                print("⚠️ Sinhala content generation will be disabled.")
                self.sinhala_tokenizer = None
                self.sinhala_model = None
                self.sinhala_available = False
        
        print("✅ Models loaded successfully!")
    
    def generate_english(self, product_name: str, description: str, tone: str = "professional") -> str:
        """Generate English marketing content using GPT-2 or templates"""
        
        # If using base model (not fine-tuned), use templates for better quality
        # Fine-tuned model will generate directly
        if not self.is_finetuned:
            return self._generate_template_english(product_name, description, tone)
        
        # Use EXACT format from training data
        # Training format: "Write a {tone} marketing message for {product}. {description}"
        prompt = f"Write a {tone} marketing message for {product_name}. {description}"
        
        inputs = self.english_tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.english_model.generate(
                **inputs,
                max_new_tokens=70,   # Longer for complete marketing messages
                # min_new_tokens not supported in older transformers
                do_sample=True,
                top_k=50,            # Balanced vocabulary selection
                top_p=0.9,           # Focused sampling for coherent output
                temperature=0.85,    # Balanced creativity and coherence
                repetition_penalty=2.0,  # Strong penalty to prevent repetitions
                no_repeat_ngram_size=3,  # Prevent 3-word repetitions
                num_return_sequences=1,
                pad_token_id=self.english_tokenizer.eos_token_id,
                eos_token_id=self.english_tokenizer.eos_token_id,
                early_stopping=False  # Let it complete naturally
            )
        
        generated = self.english_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"\n🔍 DEBUG - RAW GPT-2 OUTPUT:")
        print(f"   Prompt: {prompt}")
        print(f"   Raw output: '{generated}'")
        print(f"   Length: {len(generated)} chars")
        
        # Extract only the completion part (after the prompt)
        if prompt in generated:
            generated = generated.replace(prompt, "").strip()
        
        print(f"\n🔍 DEBUG - AFTER PROMPT REMOVAL:")
        print(f"   Content: '{generated}'")
        print(f"   Length: {len(generated)} chars")
        
        # Clean and format the output
        generated = self._format_marketing_content(generated, product_name)
        
        print(f"\n🔍 DEBUG - AFTER FORMATTING:")
        print(f"   Final: '{generated}'")
        print(f"   Length: {len(generated)} chars\n")
        
        return generated
    
    def _format_marketing_content(self, text: str, product_name: str) -> str:
        """Format marketing content - clean and return only completion"""
        import re
        text = text.strip()
        
        print(f"   📝 Formatting input: '{text}'")
        
        # Remove prompt fragments
        if text.lower().startswith('write'):
            parts = text.split('!', 1)
            if len(parts) > 1:
                text = parts[1].strip()
                print(f"   ✂️  Removed 'write' prefix, now: '{text}'")
        
        # Fix common issues
        text = re.sub(r'\s+', ' ', text)  # Fix multiple spaces
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Fix merged words
        text = re.sub(r'(\w)(now!)', r'\1 \2', text)  # Fix "todaynow!"
        
        # Split sentences properly
        sentences = re.split(r'(?<=[.!?])\s+', text)
        print(f"   📋 Split into {len(sentences)} sentences")
        
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 8]
        print(f"   ✅ After filtering (>8 chars): {len(sentences)} sentences")
        
        if sentences:
            print(f"   📄 Sentences: {sentences}")
        
        if not sentences:
            fallback = f"Get {product_name} now!"
            print(f"   ⚠️  No valid sentences! Using fallback: '{fallback}'")
            return fallback
        
        # Take first 2-3 complete sentences for richer content (not just first)
        # This gives better marketing messages while avoiding repetitive tail
        max_sentences = min(3, len(sentences))
        result_sentences = sentences[:max_sentences]
        result = ' '.join(result_sentences)
        
        # Limit total length to ~150 chars to avoid overly long messages
        if len(result) > 150:
            # Take first 2 sentences if too long
            result = ' '.join(sentences[:2])
        
        # Ensure proper ending
        if not result.endswith(('!', '.', '?')):
            result += '!'
        
        return result
    
    def _generate_template_english(self, product_name: str, description: str, tone: str) -> str:
        """Generate template-based English content (for base model)"""
        templates = {
            "professional": f"Introducing {product_name} - {description}. Experience quality and reliability. Contact us today for more information.",
            "casual": f"Check out our {product_name}! {description}. Perfect for you. Get yours now!",
            "exciting": f"Amazing news! {product_name} is here! {description}. Don't miss out - grab yours today!",
            "formal": f"We are pleased to present {product_name}. {description}. For inquiries, please contact our team."
        }
        return templates.get(tone, templates["professional"])
    
    def generate_sinhala(self, product_name: str, description: str, tone: str = "professional") -> str:
        """Generate Sinhala marketing content using mT5 (direct generation if fine-tuned, translation otherwise)"""
        
        # Check if Sinhala model is available
        if not self.sinhala_available or self.sinhala_model is None:
            print("⚠️ Sinhala model not available, using template-based generation")
            return self._generate_template_sinhala(product_name, description, tone)
        
        # If using fine-tuned Sinhala model, generate directly (no translation)
        if self.is_sinhala_finetuned:
            print("🇱🇰 Generating Sinhala content with FINE-TUNED mT5...")
            
            # Match training data format EXACTLY
            prompt = f"Write a {tone} marketing message for {product_name}. {description}"
            
            try:
                inputs = self.sinhala_tokenizer(
                    prompt, 
                    return_tensors="pt", 
                    max_length=512, 
                    truncation=True,
                    padding=False
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.sinhala_model.generate(
                        **inputs,
                        max_new_tokens=128,
                        do_sample=True,
                        top_k=50,
                        top_p=0.9,
                        temperature=0.8,
                        repetition_penalty=1.1,
                        no_repeat_ngram_size=2,
                        early_stopping=True
                    )
                
                generated = self.sinhala_tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Remove the prompt from output if it was included
                if prompt in generated:
                    generated = generated.replace(prompt, '').strip()
                
                # Clean up any artifacts
                import re
                generated = re.sub(r'<extra_id_\d+>', '', generated)
                generated = re.sub(r'<[^>]*>', '', generated)
                generated = re.sub(r'\s+', ' ', generated)
                generated = generated.strip()
                
                print(f"🔍 DEBUG - FINE-TUNED Sinhala OUTPUT: '{generated}' ({len(generated)} chars)")
                
                # Validate output - check for actual Sinhala characters
                has_sinhala = any('\u0D80' <= c <= '\u0DFF' for c in generated)
                if len(generated) < 15 or not has_sinhala:
                    print(f"⚠️ Invalid output (too short or no Sinhala): '{generated}'")
                    print(f"🔄 Fallback to template generation")
                    return self._generate_template_sinhala(product_name, description, tone)
                
                return generated
                
            except Exception as e:
                print(f"⚠️ Fine-tuned Sinhala generation failed: {e}")
                import traceback
                traceback.print_exc()
                return self._generate_template_sinhala(product_name, description, tone)
        
        # Base mT5: Use translation approach
        else:
            print("🔄 Translating English to Sinhala with base mT5...")
            
            # First, generate English content
            english_content = self.generate_english(product_name, description, tone)
            
            # Then translate to Sinhala using mT5 (which is good at translation)
            translation_prompt = f"translate English to Sinhala: {english_content}"
            
            try:
                inputs = self.sinhala_tokenizer(translation_prompt, return_tensors="pt", max_length=512, truncation=True).to(self.device)
                
                with torch.no_grad():
                    outputs = self.sinhala_model.generate(
                        **inputs,
                        max_length=300,
                        do_sample=True,
                        top_k=50,
                        top_p=0.95,
                        temperature=0.7,
                        num_beams=4,
                        num_return_sequences=1,
                        early_stopping=True
                    )
                
                generated = self.sinhala_tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Clean up any remaining artifacts
                import re
                # Remove extra_id tokens and similar artifacts
                generated = re.sub(r'<extra_id_\d+>', '', generated)
                generated = re.sub(r'<[^>]*>', '', generated)  # Remove any other XML-like tags
                generated = re.sub(r'\s+', ' ', generated)  # Normalize whitespace
                generated = generated.strip()
                
                # If translation failed or produced garbage, create a template-based Sinhala message
                if len(generated) < 10 or not any(ord(c) >= 0x0D80 and ord(c) <= 0x0DFF for c in generated):
                    return self._generate_template_sinhala(product_name, description, tone)
                
                return generated
            except Exception as e:
                print(f"⚠️ Sinhala generation failed: {e}")
                return self._generate_template_sinhala(product_name, description, tone)
    
    def _generate_template_sinhala(self, product_name: str, description: str, tone: str) -> str:
        """Generate template-based Sinhala/code-mixed content as fallback
        
        Uses realistic code-mixing patterns from training data
        """
        import random
        
        # Code-mixed templates based on actual training data patterns
        if tone == "excited":
            templates = [
                f"{product_name} එනවා! {description}. විශේෂ offers! Don't wait - ඇණවුම් කරන්න දැන්!",
                f"අලුත් {product_name}! {description} එකක්! Grab yours now! මග හරින්න එපා!",
                f"{product_name} එනවා special වලින්! {description}. Order දැන්ම! Limited time!",
                f"Wow! {product_name} - {description}. මේ deal එක ආයේ නෑ! Call now!",
                f"{product_name} sale එක! {description}. අදම ඇණවුම් කරන්න! Special price!",
            ]
        elif tone == "professional":
            templates = [
                f"{product_name} - {description}. වැඩි විස්තර සඳහා අප අමතන්න. Quality guaranteed.",
                f"Introducing {product_name}. {description}. අදම දැනගන්න. Professional service.",
                f"{product_name}: {description}. Contact us දැන්ම. ඉහළ තත්ත්වයේ සේවාව.",
                f"විශ්වාසනීය {product_name}. {description}. Call today. We deliver.",
            ]
        elif tone == "casual":
            templates = [
                f"{product_name}! {description}. ඔබටත් ඕනද? Get yours today!",
                f"Check out {product_name}! {description} එකක්! දැන්ම ලබාගන්න!",
                f"{product_name} බලන්නකෝ! {description}. Super cool! Order කරන්න!",
                f"අනේ! {product_name} - {description}. මේක නම් ලස්සනයි! Try කරලා බලන්නකෝ!",
            ]
        else:  # friendly/formal
            templates = [
                f"{product_name} - {description}. වැඩි විස්තර සඳහා කරුණාකර අප අමතන්න.",
                f"Discover {product_name}. {description}. අදම අප අමතන්න.",
                f"{product_name}: {description}. We're here to help. Contact us.",
            ]
        
        return random.choice(templates)
    
    def generate_mixed(self, product_name: str, description: str, tone: str = "professional") -> str:
        """Generate natural Sinhala-English code-mixed content using fine-tuned English + Sinhala CTA"""
        
        print(f"\n🌍 GENERATING MIXED CONTENT (English + Sinhala)")
        print(f"   Product: {product_name}")
        print(f"   Tone: {tone}\n")
        
        # Use fine-tuned English content as the main message
        english_content = self.generate_english(product_name, description, tone)
        
        print(f"\n🇬🇧 English content generated: '{english_content}'")
        print(f"   Length: {len(english_content)} chars")
        
        # Add Sinhala call-to-action based on tone
        sinhala_ctas = {
            "professional": "වැඩි විස්තර සඳහා අප අමතන්න.",
            "casual": "ඔබටත් අවශ්‍යද? දැන්ම ඇණවුම් කරන්න!",
            "exciting": "මග හරින්න එපා! දැන්ම ලබා ගන්න!",
            "formal": "වැඩි විස්තර සඳහා කරුණාකර සම්බන්ධ වන්න."
        }
        
        sinhala_cta = sinhala_ctas.get(tone, sinhala_ctas["professional"])
        
        print(f"🇱🇰 Sinhala CTA: '{sinhala_cta}'\n")
        
        # Combine: English content from fine-tuned model + Sinhala CTA
        combined = f"{english_content} {sinhala_cta}"
        
        print(f"🌍 FINAL MIXED OUTPUT: '{combined}'")
        print(f"   Total length: {len(combined)} chars")
        print("=" * 70 + "\n")
        
        return combined
    
    def generate_bilingual(self, product_name: str, description: str, tone: str = "professional") -> dict:
        """Generate content in both languages"""
        
        # For mixed language, use dedicated mixed generator
        mixed = self.generate_mixed(product_name, description, tone)
        
        return {
            "english": self.generate_english(product_name, description, tone),
            "sinhala": self.generate_sinhala(product_name, description, tone),
            "combined": mixed
        }

# Singleton instance
_generator = None

def get_generator():
    """Get or create the content generator"""
    global _generator
    if _generator is None:
        _generator = LocalContentGenerator()
    return _generator

# Test function
if __name__ == "__main__":
    # Test constants
    TEST_PRODUCT = "Premium Milk Powder"
    TEST_DESCRIPTION = "High calcium, vitamin enriched for children"
    TEST_TONE = "professional"
    
    gen = LocalContentGenerator()
    
    print("\n" + "="*60)
    print("🇬🇧 ENGLISH CONTENT")
    print("="*60)
    english = gen.generate_english(
        product_name=TEST_PRODUCT,
        description=TEST_DESCRIPTION,
        tone=TEST_TONE
    )
    print(english)
    
    print("\n" + "="*60)
    print("🇱🇰 SINHALA CONTENT")
    print("="*60)
    sinhala = gen.generate_sinhala(
        product_name=TEST_PRODUCT,
        description=TEST_DESCRIPTION,
        tone=TEST_TONE
    )
    print(sinhala)
    
    print("\n" + "="*60)
    print("🌍 BILINGUAL CONTENT")
    print("="*60)
    bilingual = gen.generate_bilingual(
        product_name=TEST_PRODUCT,
        description=TEST_DESCRIPTION
    )
    print(bilingual["combined"])
