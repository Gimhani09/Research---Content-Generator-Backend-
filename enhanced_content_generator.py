"""
Enhanced Content Generator - Ensures user inputs are properly integrated
Hybrid approach: Template-based with GPT-2 enhancement
"""
import re
from typing import Optional

class EnhancedContentGenerator:
    """Wrapper that ensures perfect content generation with user inputs"""
    
    def __init__(self, base_generator):
        """
        Args:
            base_generator: LocalContentGenerator instance
        """
        self.base_generator = base_generator
    
    def generate_english_enhanced(
        self, 
        product_name: str, 
        description: str = "", 
        tone: str = "professional",
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """
        Generate perfect English content with guaranteed user input integration
        
        Args:
            product_name: Product name
            description: Product description/features
            tone: Marketing tone
            season: Festival/season (e.g., "Cyber Monday", "Christmas")
            discount: Discount offer (e.g., "20%", "50% OFF")
            tags: User-selected tags (comma-separated)
        
        Returns:
            Perfectly formatted marketing content
        """
        
        # Strategy: Use smart template that integrates all user inputs
        # This ensures 100% accuracy with user requirements
        
        content_parts = []
        
        # 1. SEASON/FESTIVAL INTEGRATION
        if season and season.strip():
            # Format: "{Festival} Special Offer!!"
            season_text = f"{season} Special Offer!!"
            content_parts.append(season_text)
        
        # 2. MAIN PRODUCT + DISCOUNT
        if discount and discount.strip():
            # Ensure exact discount is used
            discount_clean = discount.strip()
            # Format: "Get {discount} on {product}!"
            product_text = f"Get {discount_clean} on {product_name}!"
        else:
            # No discount
            product_text = f"Get our {product_name}!"
        
        content_parts.append(product_text)
        
        # 3. URGENCY/FEATURES from description or tags
        urgency_added = False
        if description:
            desc_lower = description.lower()
            if "limited time" in desc_lower or "limited stock" in desc_lower:
                content_parts.append("Limited time offer!")
                urgency_added = True
            elif "great value" in desc_lower:
                content_parts.append("Unbeatable value!")
                urgency_added = True
        
        # 4. CALL-TO-ACTION from tags
        cta = self._get_cta_from_tags(tags)
        content_parts.append(f"{cta}!")
        
        # Join all parts
        final_content = " ".join(content_parts)
        
        # Validate and fix common issues
        final_content = self._validate_and_fix(
            final_content, 
            product_name, 
            season, 
            discount
        )
        
        return final_content
    
    def _get_cta_from_tags(self, tags: str) -> str:
        """Extract appropriate CTA from user-selected tags"""
        if not tags:
            return "Shop Now"
        
        tags_lower = tags.lower()
        
        # Map tags to CTAs
        cta_mapping = {
            "limited time offer": "Order Today",
            "limited stock": "Shop Before It's Gone",
            "special offer": "Get Yours Now",
            "new arrival": "Check It Out",
            "best seller": "Don't Miss Out",
            "free delivery": "Order Now with Free Delivery",
            "great value": "Save Big Today",
            "top-rated": "Experience Top Quality",
            "easy installments": "Shop Now, Pay Later"
        }
        
        # Find matching CTA
        for tag, cta in cta_mapping.items():
            if tag in tags_lower:
                return cta
        
        return "Shop Now"
    
    def _validate_and_fix(self, content: str, product_name: str, season: str, discount: str) -> str:
        """Validate content has all required user inputs"""
        
        # Check 1: Season must be present if provided
        if season and season.lower() not in content.lower():
            content = f"{season} Special! {content}"
        
        # Check 2: Exact discount must be present if provided
        if discount:
            discount_clean = discount.strip()
            if discount_clean not in content:
                # Find any percentage and replace
                percentage_match = re.search(r'\d+\s*(?:percent|%|OFF)', content, re.IGNORECASE)
                if percentage_match:
                    content = content.replace(percentage_match.group(0), discount_clean)
                else:
                    # Insert discount after product name
                    content = content.replace(
                        product_name, 
                        f"{product_name} with {discount_clean}", 
                        1
                    )
        
        # Clean up spacing and punctuation
        content = re.sub(r'\s+', ' ', content).strip()
        content = re.sub(r'([.!?])\s*([.!?])', r'\1', content)  # Remove double punctuation
        
        # Ensure proper ending
        if not content.endswith(('!', '.')):
            content += '!'
        
        return content
    
    def generate_with_gpt2_fallback(
        self,
        product_name: str,
        description: str = "",
        tone: str = "professional", 
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """
        Try GPT-2 generation first, fallback to enhanced template if quality is poor
        """
        
        # Try base GPT-2 generation
        try:
            gpt2_output = self.base_generator.generate_english(
                product_name=product_name,
                description=description,
                tone=tone
            )
            
            # Validate GPT-2 output quality
            quality_score = self._assess_quality(gpt2_output, product_name, season, discount)
            
            if quality_score >= 7:  # Good quality
                # Post-process to ensure user inputs
                return self._post_process_gpt2(
                    gpt2_output,
                    product_name,
                    season,
                    discount,
                    tags
                )
            else:
                print(f"⚠️ GPT-2 quality score: {quality_score}/10 - Using enhanced template")
                return self.generate_english_enhanced(
                    product_name, description, tone, season, discount, tags
                )
        
        except Exception as e:
            print(f"⚠️ GPT-2 generation failed: {e}")
            return self.generate_english_enhanced(
                product_name, description, tone, season, discount, tags
            )
    
    def _assess_quality(self, text: str, product_name: str, season: str, discount: str) -> int:
        """
        Assess content quality (0-10 scale)
        """
        score = 10
        
        # Deduct points for issues
        if product_name.lower() not in text.lower():
            score -= 3  # Product name missing
        
        if season and season.lower() not in text.lower():
            score -= 2  # Season missing
        
        if discount and discount not in text:
            score -= 2  # Exact discount missing
        
        # Check for hallucinations (random brand names)
        brand_hallucinations = ["nowa", "singer", "daraz", "abans"]
        text_lower = text.lower()
        if any(brand in text_lower for brand in brand_hallucinations):
            score -= 2  # Hallucinated brand
        
        # Check for repetition
        words = text.split()
        if len(words) != len(set(words)):  # Has duplicate words
            score -= 1
        
        return max(0, score)
    
    def _post_process_gpt2(
        self,
        gpt2_text: str,
        product_name: str,
        season: str,
        discount: str,
        tags: str
    ) -> str:
        """
        Post-process GPT-2 output to enforce user inputs
        """
        
        # Remove hallucinated brands
        hallucinations = ["nowa special", "singer", "abans", "softlogic"]
        for hal in hallucinations:
            if hal.lower() in gpt2_text.lower():
                # Remove the hallucination
                gpt2_text = re.sub(hal, "", gpt2_text, flags=re.IGNORECASE).strip()
                gpt2_text = re.sub(r'\s+', ' ', gpt2_text)
        
        # Fix discount mismatch
        if discount:
            # Find any percentage in text
            percentage_match = re.search(r'\d+\s*(?:percent|%)', gpt2_text, re.IGNORECASE)
            if percentage_match:
                # Replace with correct discount
                gpt2_text = gpt2_text.replace(percentage_match.group(0), discount)
        
        # Add season if missing
        if season and season.lower() not in gpt2_text.lower():
            gpt2_text = f"{season} Special! {gpt2_text}"
        
        return gpt2_text
    
    def generate_sinhala_enhanced(
        self, 
        product_name: str, 
        description: str = "", 
        tone: str = "professional",
        season: str = "",
        discount: str = "",
        tags: str = ""
    ) -> str:
        """
        Generate perfect Sinhala content with guaranteed user input integration
        
        Args:
            product_name: Product name
            description: Product description/features
            tone: Marketing tone
            season: Festival/season (e.g., "Christmas", "Avurudu")
            discount: Discount offer (e.g., "20%", "50% OFF")
            tags: User-selected tags (comma-separated)
        
        Returns:
            Perfectly formatted Sinhala marketing content
        """
        
        content_parts = []
        
        # 1. SEASON/FESTIVAL INTEGRATION (Sinhala)
        season_sinhala_map = {
            "Christmas": "නත්තල් සමය ",
    "New Year": "අලුත් අවුරුදු සමය",
    "Avurudu": " අවුරුදු සමය",
    "Vesak": "වෙසක් ",
    "Ramadan": "රාමදාන් ",
    "Poya": "පොහෝ දිනය",
    "Black Friday": "බ්ලැක් ෆ්‍රයිඩේ ",
    "Cyber Monday": "සයිබර් මන්ඩේ",
    "Summer": "ගිම්හාන කාලය",
    "Winter": "ශීත කාලය",
    "Valentine": "වැලන්ටයින්"
        }
        
        if season and season.strip():
            # Get Sinhala translation or use original
            season_si = season_sinhala_map.get(season, season)
            season_text = f"{season_si} විශේෂ දීමනාව!"
            content_parts.append(season_text)
        
        # 2. MAIN PRODUCT + DISCOUNT
        if discount and discount.strip():
            discount_clean = discount.strip()
            # Format: "{product} සඳහා {discount} වට්ටම!"
            product_text = f"{product_name} සඳහා {discount_clean} වට්ටම!"
        else:
            product_text = f"{product_name} දැන් ලබා ගන්න!"
        
        content_parts.append(product_text)
        
        # 3. URGENCY/VALUE PHRASES
        urgency_added = False
        if description:
            desc_lower = description.lower()
            if "limited time" in desc_lower:
                content_parts.append("සීමිත කාලයක් පමණයි!")
                urgency_added = True
            elif "great value" in desc_lower:
                content_parts.append("විශේෂ දීමනාවක්!")
                urgency_added = True
        
        if not urgency_added:
            # Add value phrase based on tone
            if tone == "exciting":
                content_parts.append("මාරම chance එකක්!")
            elif tone == "professional":
                content_parts.append("ඉහළ තත්ත්වයේ!")
        
        # 4. CALL-TO-ACTION (Sinhala)
        cta = self._get_sinhala_cta_from_tags(tags)
        content_parts.append(cta)
        
        # Join all parts
        final_content = " ".join(content_parts)
        
        return final_content
    
    def _get_sinhala_cta_from_tags(self, tags: str) -> str:
        """Extract appropriate Sinhala CTA from user-selected tags"""
        if not tags:
            return "දැන් ඇණවුම් කරන්න!"
        
        tags_lower = tags.lower()
        
        # Map tags to Sinhala CTAs
        cta_mapping = {
"limited time": "කාලය සීමිතයි! අදම ඇණවුම් කරන්න",
    "limited-time": "මෙය මඟහැරගන්න එපා! අදම ඇණවුම් කරන්න",

    "special offer": "විශේෂ offer එක අදම අත්විඳින්න",
    "special-offer": "මෙන්න විශේෂ වට්ටමක් ! දැන්ම ලබාගන්න",

    "new arrival": "අලුත්ම ආපු නිෂ්පාදන දැකලා බලන්න",
    "new-arrival": "නවතම items දැන් available ! බලන්න",

    "best seller": "හැමෝම කැමති best seller එක ! ඔබත් අත්විඳින්න",
    "best-seller": "මේක අතපසු කරගන්න බැරි එකක්",

    "free delivery": "නොමිලේ බෙදාහැරීම සමඟ ගෙදරටම",
    "free-delivery": "Delivery charge නැතුව අදම ඇණවුම් කරන්න",

    "great value": "මුදල් වලට වටිනාම deal එක",
    "great-value": "වැඩි වටිනාකමක් ! අඩු මිලකට",

    "top-rated": "Top rated quality ! විශ්වාසයෙන් මිලදී ගන්න",
    "top-rated": "ඉහළම rating ලැබූ quality එක",

    "easy installments": "පහසු වාරික වලට ලබාගන්න පුළුවන්",
    "easy-installments": "ගෙවීම පහසුයි ! installments available"
        }
        
        # Find matching CTA
        for tag, cta in cta_mapping.items():
            if tag in tags_lower:
                return cta
        
        return "දැන් ඇණවුම් කරන්න!"

# Singleton instance
_enhanced_generator = None

def get_enhanced_generator(base_generator):
    """Get or create enhanced generator"""
    global _enhanced_generator
    if _enhanced_generator is None:
        _enhanced_generator = EnhancedContentGenerator(base_generator)
    return _enhanced_generator
