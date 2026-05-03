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

EXAMPLE OUTPUT (follow this EXACT structure):
[HEADING]
Unwrap the Ultimate Christmas Experience!
[BODY]
Exclusive holiday deals on premium products. Elevate your lifestyle with unbeatable value.
[FEATURES]
Latest Designs & Premium Quality
Island-wide Delivery Available
Limited Time Holiday Pricing
[CTA]
Visit Our Showroom Today""",
            
            "sinhala": """Write ENTIRELY AND ONLY in Sinhala Unicode script (සිංහල). NO English words anywhere — including the product name, brand name, or any other term.
Use proper Sinhala Unicode characters (U+0D80 to U+0DFF block) exclusively.
DO NOT use romanized Sinhala.
DO NOT write any English word at all — translate EVERYTHING into natural, meaningful Sinhala.
The product name given may be in English — you MUST translate it to natural Sinhala for [PRODUCT_SI].
Write like a PROFESSIONAL Sri Lankan marketing copywriter — humanized, emotional, persuasive.
Each line should be meaningful and compelling — not just single generic words.
Do NOT include phone numbers or contact info.

STRICTLY AVOID:
- Any English words (e.g. "Kottu", "Promotion", "Quality", "Premium", "Free Delivery", "Natural", "Special offer")
- "අති විශේෂයි", "මහා පිස්සුව", "විශේෂ දීමනාව"
- Single-word lines, slang words

EXAMPLE OUTPUT (follow this EXACT structure — [PRODUCT_SI] MUST be first):
[PRODUCT_SI]
කොත්තු ප්‍රවර්ධනය
[HEADING]
නත්තලේ රසකිරීමට හොඳම රස අත්දැකීම!
[BODY]
අවන්හලේ සුවිශේෂී ප්‍රවර්ධන මිලදී ගන්නේ සීමිත කාලයක් පමණි. රසවත් ශ්‍රී ලාංකික ආහාර ඔබ වෙත.
[FEATURES]
දෛනිකව නැවුම් ලෙස සකසන ලද
සාම්ප්‍රදායික රෙසිපි, නවීන රස
අඩු මිලට රසවත් රාත්‍රී භෝජනය
[CTA]
දැන්ම ඇණවුම් කරන්න""",
            
            "both": """Mix SINHALA UNICODE script with English words — like real Sri Lankan ads.
Use Sinhala for emotional/persuasive sentences, English for product/tech terms.
Write like a PROFESSIONAL Sri Lankan marketing copywriter — humanized, bilingual, compelling.
Do NOT include phone numbers or contact info.

EXAMPLE OUTPUT (follow this EXACT structure):
[HEADING]
නත්තලේ අසිරිය සමඟින් නවීනතම අත්දැකීමක්!
[BODY]
Exclusive Holiday Deals සීමිත කාලයක් පමණි. Premium quality at unbeatable prices.
[FEATURES]
Latest Designs, නවතම නිර්මාණ
දිවයින පුරා Delivery Available
වටිනාකමට සරිලන මිල
[CTA]
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
            # Convert raw slug IDs to readable labels for Gemini
            # e.g. "great-value, free-delivery" → "Great Deal, Free Delivery"
            slug_to_label = {
                "great-value":        "Great Deal — emphasize value for money",
                "special-offer":      "Special Offer — highlight a promotion",
                "limited-time":       "Limited Time Only — create urgency",
                "new-arrival":        "New Arrival — latest product",
                "best-seller":        "Best Seller — customer favourite",
                "top-rated":          "Top Rated — quality & reviews",
                "free-delivery":      "Free Delivery — island-wide",
                "easy-installments":  "Pay in Installments — easy payment plan",
            }
            readable_tags = ", ".join(
                slug_to_label.get(t.strip(), t.strip().replace("-", " ").title())
                for t in tags.split(",")
                if t.strip()
            )
            context_parts.append(f"MARKETING HIGHLIGHTS (must be reflected in content): {readable_tags}")
        
        # Tone instruction
        tone_instructions = {
            "urgent":     "TONE: URGENT — create strong urgency and FOMO. Use time-sensitive language.",
            "luxurious":  "TONE: LUXURIOUS — premium, sophisticated, exclusive feel. Use elevated language.",
            "friendly":   "TONE: FRIENDLY & WARM — approachable, accessible, community feel.",
            "casual":     "TONE: CASUAL — relaxed, conversational, everyday language.",
            "professional": "",  # default — no special instruction needed
        }
        tone_line = tone_instructions.get(tone, "")
        if tone_line:
            context_parts.append(tone_line)
        
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

FORMAT RULES (MUST FOLLOW EXACTLY):
1. For SINHALA: Use these EXACT section markers in this order: [PRODUCT_SI], [HEADING], [BODY], [FEATURES], [CTA]
   For ENGLISH/BILINGUAL: Use these EXACT section markers in this order: [HEADING], [BODY], [FEATURES], [CTA]
2. [PRODUCT_SI] = (SINHALA ONLY — MANDATORY FIRST SECTION) The natural Sinhala translation of the product name "{product_name}". 1 line only, pure Sinhala script, NO English at all. Even if the product name is in English, translate it to its Sinhala equivalent.
3. [HEADING] = 1 short powerful headline (max 8-10 words). Emotional hook that grabs attention.
4. [BODY] = 1-2 SHORT sentences (max 2 lines). Key value proposition, persuasive and concise.
5. [FEATURES] = exactly 3 short feature lines (each max 5-6 words). Key selling points.
6. [CTA] = 1 action line. Warm invitation, not pushy.
7. NO emojis, emoticons, no bullet symbols (no >, -, *, bullets)
8. Sound PROFESSIONAL yet WARM — like talking to a valued customer
9. Do NOT include phone numbers, business names, or contact info
10. Do NOT repeat the discount "{discount}" — that is rendered separately in large text

QUALITY GUIDELINES:
- Be CREATIVE and ORIGINAL — avoid generic phrases like "best quality" or "special offer"
- Use culturally relevant language that resonates with Sri Lankan audiences
- Reflect the MARKETING HIGHLIGHTS naturally in the copy — don't just list them, weave them in
- For Sinhala: write pure Sinhala throughout — no English words at all
- Make each section add NEW value — no filler or repetition
- Keep it SHORT and PUNCHY — this is a poster, not a paragraph
- Write like a HUMAN copywriter, not a template
- If TONE is urgent: use words that create FOMO and time pressure
- If TONE is luxurious: use premium, refined language throughout

DO NOT:
- Use emojis, emoticons, or symbols like > - * bullets
- Add explanations, commentary, or formatting notes
- Write generic filler content
- Include phone numbers, contact info, or business names
- Repeat the discount/price (already shown separately)
- For SINHALA: skip [PRODUCT_SI] — it is REQUIRED and must be first
- Skip or rename section markers — for Sinhala use [PRODUCT_SI], [HEADING], [BODY], [FEATURES], [CTA] exactly; for English/bilingual use [HEADING], [BODY], [FEATURES], [CTA] exactly

OUTPUT:
Return ONLY the section-marked poster text. Nothing else."""

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
