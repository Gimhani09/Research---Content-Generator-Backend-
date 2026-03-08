"""
Gemini API-Based Content Generator
===================================
Direct marketing content generation using Google Gemini API.
Supports English, Sinhala (proper Unicode), and bilingual content.

This module exists ALONGSIDE the fine-tuned model pipeline:
  - When USE_GEMINI_GENERATION=true  → Uses this (API-based, no GPU needed)
  - When USE_GEMINI_GENERATION=false → Uses fine-tuned GPT-2/mT5 (local models)

The fine-tuned model code is preserved for future use when fine-tuning is ready.
"""
import google.generativeai as genai
import time
from config import config
from typing import Optional, Dict


class GeminiContentGenerator:
    """
    Generate marketing content directly using Google Gemini API.
    
    Research justification:
    - Modern multilingual LLMs generate acceptable Sinhala text without fine-tuning
    - Research novelty focuses on Unicode-aware shaping/rendering, not model training
    - API-based approach allows focusing on the Sinhala rendering pipeline
    """
    
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not set. Get your key from https://aistudio.google.com/app/apikey"
            )
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # All models to try in order — each has its own separate free-tier quota bucket
        all_model_names = [
            config.GEMINI_MODEL,        # gemini-3-flash-preview (primary)
            "gemini-2.5-flash",         # fallback 1 — stable, proven
            "gemini-2.0-flash",         # fallback 2
            "gemini-1.5-flash",         # fallback 3 — separate quota
        ]
        # Deduplicate while preserving order
        seen = set()
        self.model_names = []
        for m in all_model_names:
            if m not in seen:
                seen.add(m)
                self.model_names.append(m)
        
        self.primary_model_name = self.model_names[0]
        self.models = [genai.GenerativeModel(m) for m in self.model_names]
        
        # Keep legacy attributes for compatibility
        self.model = self.models[0]
        self.fallback_model_name = self.model_names[1] if len(self.model_names) > 1 else None
        self.fallback_model = self.models[1] if len(self.models) > 1 else None
        
        self.is_finetuned = False  # API-based, not fine-tuned
        self.generation_mode = "gemini_api"
        print(f"✅ Gemini Content Generator initialized ({self.primary_model_name})")
        print(f"   Fallback models: {', '.join(self.model_names[1:])}")
    
    def generate_english(
        self,
        product_name: str,
        description: str = "",
        tone: str = "professional",
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """Generate English marketing content via Gemini API"""
        prompt = self._build_generation_prompt(
            product_name, description, tone, "english", season, discount, tags
        )
        return self._call_gemini(prompt)
    
    def generate_sinhala(
        self,
        product_name: str,
        description: str = "",
        tone: str = "professional",
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """
        Generate Sinhala marketing content with proper Unicode.
        
        The generated text uses Unicode Sinhala block (U+0D80..U+0DFF)
        with proper virama (U+0DCA) and ZWJ (U+200D) sequences.
        """
        prompt = self._build_generation_prompt(
            product_name, description, tone, "sinhala", season, discount, tags
        )
        return self._call_gemini(prompt)
    
    def generate_bilingual(
        self,
        product_name: str,
        description: str = "",
        tone: str = "professional",
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """Generate bilingual Singlish (Sinhala + English) content"""
        prompt = self._build_generation_prompt(
            product_name, description, tone, "both", season, discount, tags
        )
        return self._call_gemini(prompt)
    
    def _call_gemini(self, prompt: str, max_retries: int = 3) -> str:
        """Call Gemini API with retry logic, model fallback, and quality validation"""
        gen_config = {
            "temperature": 0.65,
            "top_p": 0.85,
            "max_output_tokens": 2000
        }
        
        # Try primary model first, then fallback
        models_to_try = [(self.model, self.primary_model_name)]
        if self.fallback_model:
            models_to_try.append((self.fallback_model, self.fallback_model_name))
        
        for model, model_name in models_to_try:
            last_error = None
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt, generation_config=gen_config)
                    result = response.text.strip()
                    
                    # Clean up markdown formatting Gemini might add
                    result = result.replace("**", "").replace("*", "")
                    if result.startswith("```"):
                        lines = result.split("\n")
                        result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                    result = result.strip()
                    
                    # Quality validation: reject too-short content
                    if len(result) < 30:
                        print(f"⚠️ Content too short ({len(result)} chars), retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(2)
                        continue
                    
                    if model_name != self.primary_model_name:
                        print(f"✅ Generated via fallback model: {model_name}")
                    return result
                
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 5  # 5s, 10s, 15s (faster waits)
                            print(f"⏳ Rate limited on {model_name} (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            # Exhausted retries for this model, try fallback
                            print(f"⚠️ {model_name} quota exhausted, trying next model...")
                            break
                    else:
                        print(f"❌ Gemini generation failed: {e}")
                        raise
        
        # All models and retries exhausted
        print(f"❌ All Gemini models failed after retries: {last_error}")
        if last_error:
            raise last_error
        return ""
    
    def _build_generation_prompt(
        self,
        product_name: str,
        description: str,
        tone: str,
        language: str,
        season: str,
        discount: str,
        tags: str
    ) -> str:
        """Build poster-optimized content generation prompt — SHORT text for posters"""
        
        # Language-specific instructions for POSTER text
        language_instructions = {
            "english": """Write in ENGLISH.
Write like a PROFESSIONAL marketing copywriter — compelling, persuasive, and human.
Use punchy, impactful words with emotional appeal.
Do NOT include phone numbers or contact info.

EXAMPLE OUTPUT (follow this style and quality):
Unwrap the Ultimate Experience this Christmas!
Exclusive Holiday Deals for a Limited Time Only
Elevate Your Lifestyle with Premium Quality
Latest Designs, Unbeatable Value
Visit Our Showroom Today""",
            
            "sinhala": """Write ENTIRELY in Sinhala Unicode script (සිංහල) with strategic English product/tech terms.
Use proper Sinhala Unicode characters (U+0D80 to U+0DFF block).
DO NOT use romanized Sinhala.
Write like a PROFESSIONAL Sri Lankan marketing copywriter — humanized, emotional, persuasive.
Mix Sinhala sentences with English product terms naturally (like real Sri Lankan ads).
Each line should be meaningful and compelling — not just single generic words.
Do NOT include phone numbers or contact info.

EXAMPLE OUTPUT (follow this style and quality):
නත්තලේ අසිරිය සමඟින් නවීනතම අත්දැකීමක්!
සුවිශේෂී නත්තල් දීමනා සීමිත කාලයක් පමණි
නවීන පන්නයේ තාක්ෂණය අතැතිව සමරන්න
Premium Quality, Latest Designs
වටිනාකමට සරිලන මිල
දැන්ම පිවිසෙන්න අපගේ ප්‍රදර්ශනාගාර වෙත""",
            
            "both": """Mix SINHALA UNICODE script with English words — like real Sri Lankan ads.
Use Sinhala for emotional/persuasive sentences, English for product/tech terms.
Write like a PROFESSIONAL Sri Lankan marketing copywriter — humanized, bilingual, compelling.
Do NOT include phone numbers or contact info.

EXAMPLE OUTPUT (follow this style and quality):
නත්තලේ අසිරිය සමඟින් නවීනතම අත්දැකීමක්!
Exclusive Holiday Deals සීමිත කාලයක් පමණි
Premium Quality, Latest Designs
වටිනාකමට සරිලන මිල
දැන්ම පිවිසෙන්න අපගේ ප්‍රදර්ශනාගාර වෙත"""
        }
        
        # Build context info
        context_parts = []
        context_parts.append(f"PRODUCT: {product_name}")
        if description:
            context_parts.append(f"DESCRIPTION: {description}")
        if season and season.strip():
            context_parts.append(f"SEASON/FESTIVAL: {season}")
        if discount and discount.strip():
            context_parts.append(f"DISCOUNT: {discount}")
        if tags:
            context_parts.append(f"FEATURES/TAGS: {tags}")
        
        context_info = "\n".join(context_parts)
        
        # Season-specific hooks
        season_hook = ""
        if season and season.strip():
            season_hooks = {
                "christmas": "Christmas festive theme. Use holiday gifting angle.",
                "new year": "New Year theme. Fresh start, new beginnings.",
                "valentine": "Valentine's theme. Perfect gift, love.",
                "avurudu": "Sinhala/Tamil New Year theme. Cultural celebration.",
                "easter": "Easter celebration theme.",
                "ramadan": "Ramadan blessings theme.",
                "summer": "Summer deals theme. Beat the heat.",
                "black friday": "BLACK FRIDAY theme. Biggest discounts, mega sale energy. THIS IS BLACK FRIDAY — NOT Christmas or any other holiday.",
                "cyber monday": "Cyber Monday theme. Online exclusive deals.",
                "back to school": "Back to School theme. Student essentials."
            }
            for key, hook in season_hooks.items():
                if key in season.lower():
                    season_hook = f"\nSEASON: {hook}\nThe season is: {season}. Do NOT mention any other season."
                    break

        prompt = f"""You are an expert Sri Lankan marketing copywriter who creates compelling, humanized ad content.

TASK: Write ATTRACTIVE, PROFESSIONAL marketing poster text. Write like a real copywriter — emotional, persuasive, and human. NOT robotic or generic.

PRODUCT DETAILS:
{context_info}
{season_hook}

LANGUAGE:
{language_instructions.get(language, language_instructions['english'])}

FORMAT RULES (MUST FOLLOW):
1. Write 5-7 lines of compelling poster text, one per line
2. Each line should be concise but MEANINGFUL — not just single words
3. NO emojis, emoticons, no bullet symbols (no >, -, *, bullets)
4. Structure:
   Line 1: Emotional/festive hook that connects with the audience
   Line 2: Product positioned as aspirational (not just a name)
   Line 3-4: Unique selling points with emotional appeal
   Line 5: Value proposition (quality + affordability)
   Line 6-7: Urgency or invitation (warm, not pushy)
5. Use the product name "{product_name}" naturally in context
6. Sound PROFESSIONAL yet WARM — like talking to a valued customer
7. Do NOT include phone numbers, business names, or contact info
8. Do NOT include "Call now" or CTA text — that is added separately by the system
9. Do NOT repeat the discount "{discount}" — that is rendered separately in large text

QUALITY GUIDELINES:
- Be CREATIVE and ORIGINAL — avoid generic phrases like "best quality" or "special offer"
- Use culturally relevant language that resonates with Sri Lankan audiences
- For Sinhala: use rich, natural Sinhala with English tech/product terms mixed in naturally
- Make each line add NEW value — no filler or repetition
- Write like a HUMAN copywriter, not a template

DO NOT:
- Use emojis, emoticons, or symbols like > - * bullets
- Add labels like "Hook:" or "CTA:" or "Line 1:"
- Add explanations, commentary, or formatting notes
- Write generic filler content
- Include phone numbers, contact info, or business names
- Repeat the discount/price (already shown separately)

OUTPUT:
Return ONLY the poster text lines. Nothing else."""

        return prompt


# ============================================
# Singleton Management
# ============================================
_gemini_generator = None


def get_gemini_generator() -> Optional[GeminiContentGenerator]:
    """Get or create Gemini content generator"""
    global _gemini_generator
    
    if not config.USE_GEMINI_GENERATION:
        return None
    
    if _gemini_generator is None:
        try:
            _gemini_generator = GeminiContentGenerator()
        except ValueError as e:
            print(f"⚠️ {e}")
            print("Gemini content generation disabled. Falling back to fine-tuned models.")
            return None
    
    return _gemini_generator


# ============================================
# Test
# ============================================
if __name__ == "__main__":
    gen = GeminiContentGenerator()
    
    print("\n" + "=" * 60)
    print("SINHALA GENERATION TEST")
    print("=" * 60)
    result = gen.generate_sinhala(
        product_name="Robot Vacuum",
        description="Smart home cleaning",
        tone="exciting",
        season="Christmas",
        discount="20%"
    )
    print(f"\nGenerated:\n{result}")
    
    print("\n" + "=" * 60)
    print("ENGLISH GENERATION TEST")
    print("=" * 60)
    result = gen.generate_english(
        product_name="Smart TV",
        description="55 inch 4K display",
        tone="professional",
        discount="30%",
        tags="best-seller, free-delivery"
    )
    print(f"\nGenerated:\n{result}")
    
    print("\n" + "=" * 60)
    print("BILINGUAL (SINGLISH) GENERATION TEST")
    print("=" * 60)
    result = gen.generate_bilingual(
        product_name="Laptop",
        description="For students and professionals",
        tone="casual",
        season="Back to School",
        discount="15%"
    )
    print(f"\nGenerated:\n{result}")
