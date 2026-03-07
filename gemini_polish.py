"""
Gemini Content Polish Module
Refines GPT-2 generated content for better quality and cultural relevance
Generates hashtags for Sri Lankan context
"""
import os
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️ google-generativeai not available (requires Python 3.9+)")
from config import config
from typing import Dict, List, Optional

class GeminiPolisher:
    def __init__(self):
        """Initialize Gemini API for content polishing"""
        if not HAS_GEMINI:
            raise ValueError(
                "Google Generative AI not available. Requires Python 3.9+.\n"
                "Either upgrade Python or disable Gemini polish by setting USE_GEMINI_POLISH=false in .env"
            )
        
        if not config.GEMINI_API_KEY:
            raise ValueError(
                "Gemini API key not found. Please set GEMINI_API_KEY in .env file.\n"
                "Get your free API key from: https://aistudio.google.com/app/apikey"
            )
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        print(f"✅ Gemini {config.GEMINI_MODEL} initialized for content polishing")
    
    def polish_content(
        self, 
        content: str, 
        language: str = "english",
        tone: str = "professional",
        product_name: str = "",
        preserve_code_mixing: bool = True,
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """
        Polish and enhance generated content using Gemini
        
        Args:
            content: Original generated content from GPT-2
            language: "english", "sinhala", or "mixed"
            tone: Target tone (professional, casual, exciting, formal)
            product_name: Product name for context
            preserve_code_mixing: Keep Sinhala-English code-mixing if present
        
        Returns:
            Enhanced, culturally-relevant content
        """
        
        # Build context-aware prompt
        prompt = self._build_polish_prompt(
            content=content,
            language=language,
            tone=tone,
            product_name=product_name,
            preserve_code_mixing=preserve_code_mixing,
            season=season,
            discount=discount,
            tags=tags
        )
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.65,
                    "top_p": 0.85,
                    "max_output_tokens": 2000  # High for Sinhala (uses ~3x tokens of English)
                }
            )
            polished = response.text.strip()
            
            # Clean up any markdown formatting Gemini might add
            polished = polished.replace("**", "")
            polished = polished.replace("*", "")
            
            # SAFETY: If polished is extremely short, something went wrong
            if len(polished) < 30:
                print(f"⚠️ Polished content too short ({len(polished)} chars), keeping original")
                return content
            
            return polished
        
        except Exception as e:
            print(f"⚠️ Gemini polish failed: {e}")
            print("Returning original content")
            return content
    
    def generate_hashtags(
        self,
        content: str,
        product_name: str = "",
        num_hashtags: int = 5,
        include_sinhala: bool = True
    ) -> List[str]:
        """
        Generate relevant hashtags for Sri Lankan market
        
        Args:
            content: Marketing content
            product_name: Product name
            num_hashtags: Number of hashtags to generate
            include_sinhala: Include Sinhala hashtags
        
        Returns:
            List of hashtags
        """
        
        language_instruction = ""
        if include_sinhala:
            language_instruction = "Include both Sinhala and English hashtags (romanized Sinhala is acceptable). "
        
        prompt = f"""Generate {num_hashtags} relevant marketing hashtags for Sri Lankan social media.

Product: {product_name if product_name else "General"}
Content: {content}

Requirements:
- {language_instruction}
- Mix of popular and niche hashtags
- Culturally relevant to Sri Lanka
- Suitable for Facebook, Instagram, TikTok
- No spaces in hashtags (use camelCase or underscores)

Return ONLY the hashtags, one per line, starting with #. No explanations."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.8,
                    "top_p": 0.95,
                    "max_output_tokens": 100
                }
            )
            hashtags_text = response.text.strip()
            
            # Extract hashtags
            hashtags = []
            for line in hashtags_text.split('\n'):
                line = line.strip()
                if line.startswith('#'):
                    # Clean up and validate
                    tag = line.split()[0]  # Take first word if multiple
                    if len(tag) > 1:  # Must have content after #
                        hashtags.append(tag)
            
            return hashtags[:num_hashtags]
        
        except Exception as e:
            print(f"⚠️ Hashtag generation failed: {e}")
            # Return basic fallback hashtags
            return [f"#{product_name.replace(' ', '')}" if product_name else "#Marketing",
                    "#SriLanka", "#LK", "#Colombo", "#OnlineShopping"]
    
    def polish_with_hashtags(
        self,
        content: str,
        language: str = "english",
        tone: str = "professional",
        product_name: str = "",
        num_hashtags: int = 5,
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> Dict[str, any]:
        """
        Complete polish pipeline: enhance content + generate hashtags
        
        Returns:
            {
                "polished_content": str,
                "hashtags": List[str],
                "full_post": str  # content + hashtags combined
            }
        """
        
        # Step 1: Polish content
        polished = self.polish_content(
            content=content,
            language=language,
            tone=tone,
            product_name=product_name,
            preserve_code_mixing=True,
            season=season,
            discount=discount,
            tags=tags
        )
        
        # Step 2: Generate hashtags
        hashtags = self.generate_hashtags(
            content=polished,
            product_name=product_name,
            num_hashtags=num_hashtags,
            include_sinhala=(language in ["sinhala", "mixed"])
        )
        
        # Step 3: Combine
        hashtag_string = " ".join(hashtags)
        full_post = f"{polished}\n\n{hashtag_string}"
        
        return {
            "polished_content": polished,
            "hashtags": hashtags,
            "full_post": full_post
        }
    
    def _build_polish_prompt(
        self,
        content: str,
        language: str,
        tone: str,
        product_name: str,
        preserve_code_mixing: bool,
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """Build poster-optimized polish prompt"""
        
        # Build context
        context_parts = []
        if product_name:
            context_parts.append(f"PRODUCT: {product_name}")
        if season:
            context_parts.append(f"Season: {season}")
        if discount:
            context_parts.append(f"Discount: {discount}")
        if tags:
            context_parts.append(f"Features: {tags}")
        
        context_info = "\n".join(context_parts) if context_parts else "No context provided"
        
        # Season hook
        season_hook = ""
        if season:
            season_hook = f"\n- Season is: {season} — keep the season theme"
        
        # Discount hook
        discount_hook = ""
        if discount:
            discount_hook = f"\n- Discount '{discount}' must be prominent"
        
        # Tags hook
        tags_hook = ""
        if tags:
            tags_hook = f"\n- Highlight features: {tags}"
        
        prompt = f"""You are a professional poster copywriter for Sri Lankan marketing ads.

TASK: Polish this poster text. Keep it SHORT — this is for a POSTER, not social media.

USER CONTEXT:
{context_info}

DRAFT TEXT:
{content}

RULES:
- Keep each line SHORT (under 40 characters) but DO NOT cut words off
- Keep the SAME number of lines as the draft (do not remove lines)
- Fix grammar and improve impact/clarity
- Each line should be COMPLETE — do not truncate words or meaning
- Do NOT add new claims or features not in the draft
- Do NOT change product name: "{product_name}"
- Do NOT use any emojis or emoticons
- Do NOT convert to paragraphs — keep the line-by-line format
- Do NOT include phone numbers or contact information
- Do NOT add "Call now" or "Contact us" type lines
- Make each line punchy and impactful
- For Sinhala: Use proper Unicode with correct vowel signs
{season_hook}{discount_hook}{tags_hook}

OUTPUT:
Return ONLY the polished poster text. No explanations. No labels.
Keep it SHORT — this goes on a poster, not a blog."""

        return prompt


# Singleton instance
_polisher = None

def get_polisher() -> Optional[GeminiPolisher]:
    """Get or create Gemini polisher (returns None if API key not set)"""
    global _polisher
    
    if not config.USE_GEMINI_POLISH:
        return None
    
    if _polisher is None:
        try:
            _polisher = GeminiPolisher()
        except ValueError as e:
            print(f"⚠️ {e}")
            print("Gemini polishing disabled. Set GEMINI_API_KEY and USE_GEMINI_POLISH=true to enable.")
            return None
    
    return _polisher


# Test function
if __name__ == "__main__":
    # Test content polishing
    polisher = GeminiPolisher()
    
    test_content_english = "Premium milk powder for kids with calcium. Available now."
    test_content_sinhala = "ළමුන් සඳහා කැල්සියම් සමඟ ප්‍රිමියම් කිරිපිටි. දැන් ලබා ගත හැක."
    test_content_mixed = "අපේ new Premium Milk එක try කරලා බලන්න. Now available.!"
    
    print("\n" + "="*60)
    print("ENGLISH POLISH TEST")
    print("="*60)
    result = polisher.polish_with_hashtags(
        content=test_content_english,
        language="english",
        tone="exciting",
        product_name="Premium Milk Powder"
    )
    print(f"\nOriginal: {test_content_english}")
    print(f"\nPolished: {result['polished_content']}")
    print(f"\nHashtags: {' '.join(result['hashtags'])}")
    print(f"\nFull Post:\n{result['full_post']}")
    
    print("\n" + "="*60)
    print("SINHALA POLISH TEST")
    print("="*60)
    result = polisher.polish_with_hashtags(
        content=test_content_sinhala,
        language="sinhala",
        tone="professional",
        product_name="Premium Milk Powder"
    )
    print(f"\nOriginal: {test_content_sinhala}")
    print(f"\nPolished: {result['polished_content']}")
    print(f"\nHashtags: {' '.join(result['hashtags'])}")
    
    print("\n" + "="*60)
    print("CODE-MIXED POLISH TEST")
    print("="*60)
    result = polisher.polish_with_hashtags(
        content=test_content_mixed,
        language="mixed",
        tone="casual",
        product_name="Premium Milk"
    )
    print(f"\nOriginal: {test_content_mixed}")
    print(f"\nPolished: {result['polished_content']}")
    print(f"\nHashtags: {' '.join(result['hashtags'])}")
