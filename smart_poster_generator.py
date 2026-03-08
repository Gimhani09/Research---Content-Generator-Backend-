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
            # Map frontend season names to internal names
            season_mapping = {
                "christmas": "christmas",
                "new_year": "new_year",
                "valentine": "valentine",
                "avurudu": "avurudu",
                "year_end": "new_year",
                "black_friday": "black_friday",
                "blackfriday": "black_friday",
                "summer": "summer",
                "back_to_school": "back_to_school",
                "backtoschool": "back_to_school"
            }
            detected_season = season_mapping.get(user_season.lower().replace(" ", "_"), "general")
        else:
            # Auto-detect from content
            seasons = {
                "christmas": ["christmas", "xmas", "festive", "holiday", "santa"],
                "new_year": ["new year", "2024", "2025", "resolution"],
                "valentine": ["valentine", "love", "romance", "heart"],
                "avurudu": ["avurudu", "sinhala", "tamil new year"],
                "summer": ["summer", "beach", "sunshine", "hot"],
                "back_to_school": ["school", "education", "students"],
                "black_friday": ["black friday", "cyber monday", "sale"]
            }
            
            detected_season = "general"
            for season, keywords in seasons.items():
                if any(keyword in content_lower for keyword in keywords):
                    detected_season = season
                    break
        
        # Product category detection
        categories = {
            "food": ["kottu", "ribs", "cake", "coffee", "tea", "pudding", "restaurant"],
            "fashion": ["dress", "jeans", "wear", "lipstick", "frocks", "clothing"],
            "tech": ["smartphone", "laptop", "speaker", "watch", "vacuum", "robot"],
            "home": ["sofa", "furniture", "cookware", "washing machine", "gym"],
            "beauty": ["skin care", "lipstick", "shampoo", "cosmetics"]
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
            "christmas": "Christmas decorations, snowflakes, red and green colors, festive lights, holly leaves",
            "new_year": "fireworks, champagne, gold confetti, celebratory atmosphere, midnight blue",
            "valentine": "hearts, roses, pink and red colors, romantic atmosphere, soft lighting",
            "avurudu": "traditional Sri Lankan elements, oil lamps, flowers, vibrant colors, cultural motifs",
            "summer": "sunshine, beach vibes, bright colors, tropical elements, palm leaves",
            "back_to_school": "notebooks, pencils, school elements, youthful colors, educational theme",
            "black_friday": "bold black background, neon lights, modern design, sale tags, dynamic",
            "general": "clean modern background, gradient, professional atmosphere"
        }
        
        category_elements = {
            "food": "appetizing presentation, food photography style, warm tones, delicious atmosphere",
            "fashion": "stylish setting, fashion photography, elegant background, trendy vibes",
            "tech": "modern minimalist, tech-inspired, sleek design, futuristic elements",
            "home": "cozy home setting, comfortable atmosphere, lifestyle photography",
            "beauty": "soft lighting, elegant presentation, spa-like atmosphere, beauty product style",
            "general": "product photography style, professional lighting"
        }
        
        mood_styles = {
            "exciting": "vibrant, energetic, dynamic composition, eye-catching",
            "urgent": "bold, attention-grabbing, high contrast, dramatic",
            "luxury": "premium, sophisticated, elegant, high-end photography",
            "professional": "clean, professional, trustworthy, polished"
        }
        
        prompt = f"""Professional marketing poster background for {product_name}.
        Theme: {season_elements.get(context['season'], season_elements['general'])}.
        Style: {category_elements.get(context['category'], category_elements['general'])}.
        Mood: {mood_styles.get(context['mood'], mood_styles['professional'])}.
        Layout: Clean open space for text overlay, subtle product-related imagery.
        1200x630px, high quality, suitable for social media marketing.
        IMPORTANT: Absolutely no text, no words, no letters, no numbers, no typography, no writing, no signage, no labels, no watermarks anywhere in the image. Pure visual background only."""
        
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
    
    def generate_with_stability(self, prompt):
        """Generate background using Stability AI"""
        if not self.api_key:
            return {"error": "STABILITY_API_KEY not set"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                },
                {
                    "text": "text, words, letters, numbers, typography, writing, signage, labels, watermark, signature, caption, title, heading, font, alphabet, characters, blurry, low quality",
                    "weight": -1.5
                }
            ],
            "cfg_scale": 7,
            "width": 1216,  # Closest to 1200x630 ratio (1.93:1) - SDXL supported
            "height": 832,  # Aspect ratio 1.46:1 (will crop to 1200x630)
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
                    
                    # Resize to exact 1200x630 for poster template
                    img = Image.open(io.BytesIO(img_data))
                    img_resized = img.resize((1200, 630), Image.Resampling.LANCZOS)
                    
                    output_path = f"generated_backgrounds/poster_bg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    Path("generated_backgrounds").mkdir(exist_ok=True)
                    img_resized.save(output_path, "PNG")
                    
                    return {
                        "success": True,
                        "image_path": output_path,
                        "prompt": prompt,
                        "original_size": f"{img.width}x{img.height}",
                        "final_size": "1200x630"
                    }
            else:
                error_msg = response.text
                print(f"❌ Stability API Error {response.status_code}: {error_msg}")
                
                # Check for insufficient balance
                if "insufficient_balance" in error_msg.lower() or response.status_code == 429:
                    print("⚠️ Stability AI account out of credits - falling back to free Pollinations.AI")
                    return self.generate_with_pollinations(prompt)
                
                return {"error": error_msg, "status": response.status_code}
        except Exception as e:
            print(f"❌ Stability API Exception: {str(e)}")
            print("⚠️ Falling back to free Pollinations.AI")
            return self.generate_with_pollinations(prompt)
    
    def generate_with_pollinations(self, prompt):
        """Generate background using Pollinations.AI (FREE - no API key needed)"""
        try:
            # Pollinations.AI - completely free text-to-image API
            # Clean prompt for URL
            import urllib.parse
            clean_prompt = urllib.parse.quote(prompt[:500])  # Limit to 500 chars
            
            # Request image generation
            image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1200&height=630&nologo=true&model=flux&negative=text,words,letters,numbers,typography,writing,signage,labels,watermark,signature"
            
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
