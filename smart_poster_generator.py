"""
Smart Poster Generator with Contextual Backgrounds
Combines AI-generated backgrounds with HTML template overlay
"""
import os
import requests
import json
from datetime import datetime
from pathlib import Path

class SmartPosterGenerator:
    """Generate marketing posters with context-aware backgrounds"""
    
    # API Options (choose one)
    APIS = {
        "bannerbear": {
            "url": "https://api.bannerbear.com/v2/images",
            "free_tier": True,
            "best_for": "Marketing posters with templates"
        },
        "leonardo": {
            "url": "https://cloud.leonardo.ai/api/rest/v1/generations",
            "free_tier": True,  # 150 credits/day
            "best_for": "High-quality contextual backgrounds"
        },
        "stability": {
            "url": "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            "free_tier": False,
            "best_for": "Professional quality images"
        },
        "dalle3": {
            "url": "https://api.openai.com/v1/images/generations",
            "free_tier": False,
            "best_for": "Complete posters with text"
        }
    }
    
    def __init__(self, api_choice="leonardo"):
        """
        Initialize with your preferred API
        
        Args:
            api_choice: 'bannerbear', 'leonardo', 'stability', or 'dalle3'
        """
        self.api_choice = api_choice
        self.api_key = os.getenv(f"{api_choice.upper()}_API_KEY", "")
        
    def detect_content_context(self, content, product_name, user_season=None):
        """
        Detect context from content for background generation
        
        Args:
            content: Marketing content
            product_name: Product name
            user_season: User-selected season (overrides auto-detection)
        
        Returns: theme, season, mood
        """
        content_lower = (content + " " + product_name).lower()
        
        # Use user-selected season if provided, otherwise auto-detect
        if user_season:
            # Normalize: lowercase, collapse spaces/underscores, strip punctuation
            import re as _re
            norm = _re.sub(r"[^a-z0-9 ]", "", user_season.lower()).strip()

            # Map frontend season display strings → internal keys
            # Handles full readable strings sent by the frontend (e.g. "Sinhala & Tamil New Year")
            season_mapping = {
                # Exact normalized matches
                "sinhala  tamil new year": "avurudu",   # & stripped → double space
                "sinhala tamil new year":  "avurudu",
                "avurudu":                 "avurudu",
                "christmas":               "christmas",
                "new year":                "new_year",
                "year end":                "new_year",
                "valentines day":          "valentine",
                "valentine":               "valentine",
                "easter":                  "easter",
                "vesak":                   "vesak",
                "poson":                   "poson",
                "deepavali":               "deepavali",
                "diwali":                  "deepavali",
                "ramadan":                 "ramadan",
                "thai pongal":             "thai_pongal",
                "pongal":                  "thai_pongal",
                "summer sale":             "summer",
                "summer":                  "summer",
                "black friday":            "black_friday",
                "cyber monday":            "cyber_monday",
                "back to school":          "back_to_school",
            }
            # Also try substring matching as fallback
            detected_season = season_mapping.get(norm, None)
            if detected_season is None:
                for key, val in season_mapping.items():
                    if key in norm or norm in key:
                        detected_season = val
                        break
                else:
                    detected_season = "general"
        else:
            # Auto-detect from content — only triggered when no season is selected
            # Keep keywords conservative: avoid words that appear in non-seasonal contexts
            seasons = {
                "christmas": ["christmas", "xmas", "festive season", "santa", "holly"],
                "new_year": ["new year", "new year's", "resolution", "2025", "2026"],
                "valentine": ["valentine", "valentines", "romance", "romantic gift"],
                "avurudu": ["avurudu", "aluth avurudu", "sinhala new year", "tamil new year"],
                "summer": ["summer sale", "beach party", "sunshine deal"],
                "back_to_school": ["back to school", "school season", "students back"],
                "black_friday": ["black friday", "blackfriday", "cyber monday"],
            }
            
            detected_season = "general"
            for season, keywords in seasons.items():
                if any(keyword in content_lower for keyword in keywords):
                    detected_season = season
                    break
        
        # Product category detection
        categories = {
            "food": ["kottu", "ribs", "cake", "coffee", "tea", "pudding", "restaurant",
                     "rice", "food", "eat", "drink", "juice", "burger", "pizza", "curry",
                     "porridge", "noodle", "soup", "bread", "snack", "fruit", "vegetable",
                     "cucumber", "mango", "coconut", "spice", "bakery", "cafe", "meal",
                     "beverage", "milk", "dairy", "chocolate", "sweet", "dessert"],
            "fashion": ["dress", "jeans", "wear", "lipstick", "frocks", "clothing",
                        "saree", "shirt", "trouser", "shoe", "bag", "handbag", "jewellery",
                        "jewelry", "accessories", "fashion", "apparel", "outfit"],
            "tech": ["smartphone", "laptop", "speaker", "watch", "vacuum", "robot",
                     "computer", "tablet", "phone", "mobile", "camera", "gadget",
                     "appliance", "electronic", "smart", "wifi", "bluetooth", "charger"],
            "home": ["sofa", "furniture", "cookware", "washing machine", "gym",
                     "bed", "chair", "table", "cabinet", "curtain", "mattress",
                     "pillow", "lamp", "decor", "interior", "kitchen", "bathroom",
                     "fridge", "refrigerator", "microwave", "fan", "air conditioner"],
            "beauty": ["skin care", "skincare", "lipstick", "shampoo", "cosmetics",
                       "cream", "serum", "moisturizer", "perfume", "makeup", "beauty",
                       "hair care", "body wash", "lotion", "sunscreen"]
        }
        
        detected_category = "general"
        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_category = category
                break
        
        # Mood detection
        mood = "professional"
        if any(word in content_lower for word in ["exciting", "wow", "amazing", "incredible"]):
            mood = "exciting"
        elif any(word in content_lower for word in ["limited", "hurry", "now", "urgent"]):
            mood = "urgent"
        elif any(word in content_lower for word in ["luxury", "premium", "exclusive"]):
            mood = "luxury"
        
        return {
            "season": detected_season,
            "category": detected_category,
            "mood": mood
        }
    
    def generate_background_prompt(self, context, product_name):
        """
        Create AI prompt for background generation
        """
        season_elements = {
            "christmas":       "Christmas decorations, snowflakes, red and green colors, festive lights, holly leaves, Christmas tree",
            "new_year":        "fireworks, champagne, gold confetti, celebratory atmosphere, midnight blue sky, sparkles",
            "valentine":       "red roses, hearts, pink and red colors, romantic soft lighting, rose petals",
            "avurudu":         "traditional Sri Lankan oil lamps, marigold flowers, nelum flowers, orange and gold tones, traditional clay pots, vibrant cultural motifs",
            "easter":          "spring flowers, pastel colors, Easter eggs, blooming garden, soft pink and yellow tones",
            "vesak":           "glowing paper lanterns, lotus flowers, Buddhist temple lights, white and golden tones, peaceful atmosphere",
            "poson":           "stupa silhouette, white lotus flowers, Mihintale hills, soft white and golden glow, sacred atmosphere",
            "deepavali":       "oil lamps (diyas), rangoli patterns, golden and orange tones, fireworks, marigold garlands, festive lights",
            "ramadan":         "crescent moon, star and lantern motifs, golden and teal tones, Arabic geometric patterns, night sky",
            "thai_pongal":     "sugarcane, kolam patterns, clay pot (pongal pot), yellow and orange tones, harvest celebration",
            "summer":          "sunshine, tropical beach vibes, bright turquoise tones, palm leaves, clear blue sky",
            "black_friday":    "bold black background, neon sale lights, modern tech design, dynamic energy, high contrast",
            "cyber_monday":    "digital tech grid, glowing blue and purple tones, futuristic modern design, circuit patterns",
            "back_to_school":  "colorful notebooks, pencils, school backpack, bright youthful colors, educational theme",
            "general":         "clean modern gradient background, professional atmosphere, subtle geometric shapes",
        }
        
        category_elements = {
            "food": "appetizing food presentation, warm kitchen tones, fresh ingredients, delicious atmosphere, natural food photography style",
            "fashion": "stylish setting, fashion photography, elegant background, trendy vibes",
            "tech": "modern minimalist, tech-inspired, sleek design, futuristic elements",
            "home": "cozy home setting, comfortable living room atmosphere, lifestyle photography, warm interior design",
            "beauty": "soft lighting, elegant presentation, spa-like atmosphere, beauty product style",
            "general": "product photography style, professional lighting"
        }
        
        mood_styles = {
            "exciting": "vibrant, energetic, dynamic composition, eye-catching",
            "urgent": "bold, attention-grabbing, high contrast, dramatic",
            "luxury": "premium, sophisticated, elegant, high-end photography",
            "professional": "clean, professional, trustworthy, polished"
        }
        
        # When no season is selected, build a product-category-driven background
        # instead of a plain generic gradient
        season_key = context['season']
        if season_key == "general":
            product_category_style = category_elements.get(context['category'], category_elements['general'])
            prompt = f"""Professional marketing poster background for {product_name}.
        Create a visually rich background that perfectly matches a {context['category']} product advertisement.
        Style: {product_category_style}.
        Mood: {mood_styles.get(context['mood'], mood_styles['professional'])}.
        Layout: Clean open space in the center for text overlay, subtle product-related imagery around the edges.
        1200x630px, high quality, suitable for social media marketing.
        IMPORTANT: Pure visual background only — absolutely no text, words, letters, numbers, price tags, sale signs, banners, watermarks, typography, or any writing anywhere in the image. Text-free, clean background."""
        else:
            season_theme = season_elements.get(season_key, season_elements['general'])
            product_category_style = category_elements.get(context['category'], category_elements['general'])
            season_label = season_key.replace("_", " ")
            category = context['category']

            # Build a blended prompt: product category is VISUALLY DOMINANT,
            # season provides the color palette and decorative accents only.
            # This prevents a food ad from looking like a school supply ad etc.
            if category == "general":
                # No strong product category — let season dominate
                prompt = f"""Professional marketing poster background for {product_name}.
        Theme: {season_theme}.
        Mood: {mood_styles.get(context['mood'], mood_styles['professional'])}.
        Layout: Clean open space for text overlay.
        1200x630px, high quality, suitable for social media marketing.
        IMPORTANT: Pure visual background only — absolutely no text, words, letters, numbers, price tags, sale signs, banners, watermarks, typography, or any writing anywhere in the image. Text-free, clean background."""
            else:
                # Strong product category — make it primary, season is accent only
                prompt = f"""Professional marketing poster background for {product_name} — a {category} product promoted during {season_label}.
        PRIMARY visual: {product_category_style}. The background must clearly look like a {category} product advertisement.
        SECONDARY accent: Subtly incorporate {season_label} decorative elements ({season_theme}) around the edges or as a color palette — do NOT let seasonal items dominate the scene.
        The product category ({category}) must be immediately recognizable. A food product must look like food, a tech product must look like tech, etc.
        Mood: {mood_styles.get(context['mood'], mood_styles['professional'])}.
        Layout: Clean open space in the center for text overlay, product-relevant imagery visible around the frame.
        1200x630px, high quality, suitable for social media marketing.
        IMPORTANT: Pure visual background only — absolutely no text, words, letters, numbers, price tags, sale signs, banners, watermarks, typography, or any writing anywhere in the image. Text-free, clean background."""
        
        return prompt
    
    def generate_with_leonardo(self, prompt):
        """Generate background using Leonardo.ai (150 free credits/day)"""
        if not self.api_key:
            return {"error": "LEONARDO_API_KEY not set"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "num_images": 1,
            "width": 1200,
            "height": 630,
            "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",  # Leonardo Diffusion XL
            "guidance_scale": 7,
            "public": False
        }
        
        response = requests.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers=headers,
            json=payload
        )
        
        return response.json()
    
    def generate_with_dalle3(self, prompt):
        """Generate complete poster using DALL-E 3"""
        if not self.api_key:
            return {"error": "DALLE3_API_KEY not set (use OPENAI_API_KEY)"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard"
        }
        
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload
        )
        
        return response.json()
    
    # SDXL-supported sizes closest to each poster aspect ratio
    _SDXL_SIZE_MAP = {
        "facebook":  {"gen_w": 1216, "gen_h": 832,  "out_w": 1200, "out_h": 630},   # ~1.93:1
        "instagram": {"gen_w": 1024, "gen_h": 1024, "out_w": 1080, "out_h": 1080},  # 1:1
        "story":     {"gen_w": 832,  "gen_h": 1216, "out_w": 1080, "out_h": 1920},  # 9:16 portrait
        "twitter":   {"gen_w": 1344, "gen_h": 768,  "out_w": 1200, "out_h": 675},   # 16:9
    }

    def generate_with_stability(self, prompt, size="facebook"):
        """Generate background using Stability AI at the correct dimensions for `size`"""
        if not self.api_key:
            return {"error": "STABILITY_API_KEY not set"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        sz = self._SDXL_SIZE_MAP.get(size, self._SDXL_SIZE_MAP["facebook"])
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                },
                {
                    "text": "text, words, letters, numbers, typography, writing, signage, labels, watermark, signature, caption, title, heading, font, alphabet, characters, price tag, sale sign, banner text, overlay text, speech bubble, blurry, low quality",
                    "weight": -2.0
                }
            ],
            "cfg_scale": 7,
            "width": sz["gen_w"],
            "height": sz["gen_h"],
            "samples": 1,
            "steps": 30
        }
        
        try:
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Save the image
                import base64
                from PIL import Image
                import io
                
                for i, image in enumerate(data.get("artifacts", [])):
                    img_data = base64.b64decode(image["base64"])
                    
                    # Resize to exact target dimensions for this platform
                    img = Image.open(io.BytesIO(img_data))
                    out_w, out_h = sz["out_w"], sz["out_h"]
                    img_resized = img.resize((out_w, out_h), Image.Resampling.LANCZOS)
                    
                    output_path = f"generated_backgrounds/poster_bg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    Path("generated_backgrounds").mkdir(exist_ok=True)
                    img_resized.save(output_path, "PNG")
                    
                    return {
                        "success": True,
                        "image_path": output_path,
                        "prompt": prompt,
                        "original_size": f"{img.width}x{img.height}",
                        "final_size": f"{out_w}x{out_h}"
                    }
            else:
                error_msg = response.text
                print(f"❌ Stability API Error {response.status_code}: {error_msg}")
                
                # Check for insufficient balance
                if "insufficient_balance" in error_msg.lower() or response.status_code == 429:
                    print("⚠️ Stability AI account out of credits - falling back to free Pollinations.AI")
                    return self.generate_with_pollinations(prompt, size=size)
                
                return {"error": error_msg, "status": response.status_code}
        except Exception as e:
            print(f"❌ Stability API Exception: {str(e)}")
            print("⚠️ Falling back to free Pollinations.AI")
            return self.generate_with_pollinations(prompt, size=size)
    
    def generate_with_pollinations(self, prompt, size="facebook"):
        """Generate background using Pollinations.AI (FREE - no API key needed)"""
        try:
            # Pollinations.AI - completely free text-to-image API
            # Clean prompt for URL
            import urllib.parse
            clean_prompt = urllib.parse.quote(prompt[:500])  # Limit to 500 chars
            
            # Request image generation
            sz = self._SDXL_SIZE_MAP.get(size, self._SDXL_SIZE_MAP["facebook"])
            out_w, out_h = sz["out_w"], sz["out_h"]
            image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width={out_w}&height={out_h}&nologo=true&model=flux&negative=text,words,letters,numbers,typography,writing,signage,labels,watermark,signature,caption,title,heading,price+tag,sale+sign,banner+text,overlay+text"
            
            print(f"📡 Requesting from Pollinations.AI...")
            response = requests.get(image_url, timeout=30)
            
            if response.status_code == 200:
                from PIL import Image
                import io
                
                # Save the image
                img = Image.open(io.BytesIO(response.content))
                
                output_path = f"generated_backgrounds/pollinations_bg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                Path("generated_backgrounds").mkdir(exist_ok=True)
                img.save(output_path, "PNG")
                
                print(f"✅ FREE image generated via Pollinations.AI")
                
                return {
                    "success": True,
                    "image_path": output_path,
                    "prompt": prompt,
                    "original_size": f"{img.width}x{img.height}",
                    "final_size": f"{img.width}x{img.height}",
                    "api_used": "pollinations_free"
                }
            else:
                return {"error": f"Pollinations API returned {response.status_code}", "status": response.status_code}
        except Exception as e:
            return {"error": f"Pollinations API error: {str(e)}"}
    
    def generate_with_bannerbear(self, template_id, modifications):
        """Generate poster using Bannerbear templates"""
        if not self.api_key:
            return {"error": "BANNERBEAR_API_KEY not set"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "template": template_id,
            "modifications": modifications,
            "webhook_url": None  # Or set your webhook
        }
        
        response = requests.post(
            "https://api.bannerbear.com/v2/images",
            headers=headers,
            json=payload
        )
        
        return response.json()
    
    def generate_poster(self, content, product_name, template_id=None, season=None):
        """
        Main method: Generate contextual poster
        
        Args:
            content: AI-generated marketing text
            product_name: Product name
            template_id: Required for Bannerbear
            season: User-selected season/festival (optional)
            
        Returns:
            dict with image_url or file_path
        """
        # Detect context (use user-selected season if provided)
        context = self.detect_content_context(content, product_name, season)
        print(f"📊 Detected context: {context}")
        
        # Generate appropriate background prompt
        bg_prompt = self.generate_background_prompt(context, product_name)
        print(f"🎨 Background prompt: {bg_prompt[:100]}...")
        
        # Call appropriate API
        if self.api_choice == "leonardo":
            result = self.generate_with_leonardo(bg_prompt)
        elif self.api_choice == "stability":
            result = self.generate_with_stability(bg_prompt)
        elif self.api_choice == "dalle3":
            # For DALL-E, include text in prompt
            full_prompt = f"{bg_prompt}\n\nInclude text: '{content}'"
            result = self.generate_with_dalle3(full_prompt)
        elif self.api_choice == "bannerbear":
            if not template_id:
                return {"error": "template_id required for Bannerbear"}
            modifications = [
                {"name": "headline", "text": product_name},
                {"name": "body_text", "text": content},
                {"name": "theme", "text": context['season']}
            ]
            result = self.generate_with_bannerbear(template_id, modifications)
        else:
            result = {"error": f"Unsupported API: {self.api_choice}"}
        
        return {
            "result": result,
            "context": context,
            "prompt": bg_prompt
        }


# Example usage
if __name__ == "__main__":
    # Example with Leonardo.ai (FREE - 150 credits/day)
    generator = SmartPosterGenerator(api_choice="leonardo")
    
    # Your AI-generated content
    content = "Christmas craving sorted! Get an EXCLUSIVE discount on our Kottu! Don't miss out. Visit store!"
    product = "Kottu Promotion"
    
    result = generator.generate_poster(content, product)
    print("\n✅ Result:")
    print(json.dumps(result, indent=2))
    
    # Example API comparison
    print("\n\n📋 API Comparison for Your Use Case:")
    print("=" * 60)
    for api_name, api_info in SmartPosterGenerator.APIS.items():
        print(f"\n{api_name.upper()}:")
        print(f"  Free tier: {'✅ Yes' if api_info['free_tier'] else '❌ No'}")
        print(f"  Best for: {api_info['best_for']}")
