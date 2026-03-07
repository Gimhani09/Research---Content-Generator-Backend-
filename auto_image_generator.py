"""
Automated Marketing Image Generator using FREE APIs
Generates professional images matching the marketing content
"""

import requests
import json
from urllib.parse import quote
import os
from pathlib import Path

class AutoImageGenerator:
    """Generate marketing images automatically based on content."""
    
    def __init__(self):
        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)
        
    def create_prompt_from_content(self, product_service, content_type, tone, content):
        """
        Create an image generation prompt based on marketing content.
        
        Maps content to visual elements like your example:
        - Hiring post → Person at desk, professional design
        - Product → Product photography with matching mood
        - Sale → Exciting colors, promotional elements
        """
        
        # Base style (professional marketing poster)
        base_style = "professional marketing poster design, high quality, vibrant colors, modern layout, "
        
        # Content type specific elements
        type_elements = {
            "Social Media Post": "social media friendly, eye-catching, bold typography, ",
            "Product Description": "product photography, clean background, professional lighting, ",
            "Email Marketing": "email header design, clean layout, call-to-action button, ",
            "Advertisement": "advertising banner, promotional design, attention-grabbing, "
        }
        
        # Tone-based mood
        tone_moods = {
            "exciting": "energetic colors, dynamic composition, exciting atmosphere, ",
            "professional": "corporate colors, clean design, professional look, ",
            "casual": "friendly vibe, warm colors, approachable design, ",
            "elegant": "sophisticated, luxury feel, elegant typography, ",
            "fun": "playful elements, bright colors, cheerful mood, "
        }
        
        # Product/service visual elements
        visual_elements = self._extract_visual_elements(product_service, content)
        
        # Combine all elements
        prompt = (
            base_style +
            type_elements.get(content_type, "") +
            tone_moods.get(tone, "") +
            visual_elements +
            "no text, no words, illustration style"  # Avoid text in generated images
        )
        
        return prompt
    
    def _extract_visual_elements(self, product_service, content):
        """Extract visual elements from product name and content."""
        
        combined = f"{product_service} {content}".lower()
        
        # Map keywords to visual elements
        element_map = {
            # Job/Hiring
            "hiring": "person working at computer desk, office setup, creative workspace, ",
            "job": "professional workspace, desk with laptop, modern office, ",
            "designer": "graphic design tools, creative studio, design sketches, ",
            
            # Food
            "food": "delicious food photography, appetizing presentation, ",
            "pizza": "pizza with toppings, Italian food, ",
            "burger": "gourmet burger, fast food styling, ",
            "coffee": "coffee cup, cafe atmosphere, ",
            "cake": "decorated cake, dessert presentation, ",
            
            # Fashion
            "clothing": "fashion photography, trendy outfit, ",
            "shoes": "stylish footwear, product shot, ",
            "bag": "handbag product photography, accessories, ",
            
            # Electronics
            "laptop": "modern laptop, tech gadget, ",
            "phone": "smartphone, mobile device, ",
            "watch": "smartwatch or luxury watch, ",
            
            # Sale/Offer
            "sale": "sale badge, discount tag, promotional elements, ",
            "discount": "percentage off symbol, deal highlight, ",
            "offer": "special offer badge, promotional banner, ",
            
            # Festive
            "christmas": "christmas decorations, festive atmosphere, ",
            "new year": "celebration elements, fireworks, festive mood, ",
            "avurudu": "sri lankan new year elements, traditional decorations, ",
        }
        
        elements = ""
        for keyword, visual in element_map.items():
            if keyword in combined:
                elements += visual
                
        return elements if elements else "modern marketing design, "
    
    def generate_with_pollinations(self, prompt, filename):
        """
        Generate image using Pollinations.ai (FREE, unlimited)
        API: https://pollinations.ai/
        """
        
        # Clean prompt for URL
        encoded_prompt = quote(prompt)
        
        # Pollinations API endpoint
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        # Add parameters for better quality
        params = {
            "width": 1024,
            "height": 1024,
            "seed": -1,  # Random seed
            "model": "flux",  # Best quality model
            "nologo": "true"
        }
        
        # Construct full URL
        full_url = url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        print(f"🎨 Generating image: {filename}")
        print(f"   Prompt: {prompt[:100]}...")
        
        try:
            response = requests.get(full_url, timeout=60)
            
            if response.status_code == 200:
                output_path = self.output_dir / filename
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Image saved: {output_path}")
                return str(output_path)
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error generating image: {e}")
            return None
    
    def generate_from_content(self, entry, index=0):
        """Generate image for a marketing content entry."""
        
        # Create prompt
        prompt = self.create_prompt_from_content(
            entry['product_service'],
            entry['content_type'],
            entry['tone'],
            entry['content']
        )
        
        # Generate filename
        safe_name = entry['product_service'].replace(' ', '_').replace('/', '_')[:30]
        filename = f"{index:03d}_{safe_name}.png"
        
        # Generate image
        return self.generate_with_pollinations(prompt, filename)


def main():
    """Demo: Generate images for sample marketing content."""
    
    generator = AutoImageGenerator()
    
    # Sample marketing content (like your hiring poster)
    sample_entries = [
        {
            "product_service": "Graphic Designer Position",
            "content_type": "Social Media Post",
            "target_audience": "Job Seekers",
            "tone": "professional",
            "language": "english",
            "content": "We Are Hiring! Graphic Designer - 1 Year Experience, Knowledge in Corel Draw & Photoshop. Apply Now!"
        },
        {
            "product_service": "Christmas Sale",
            "content_type": "Social Media Post",
            "target_audience": "General Public",
            "tone": "exciting",
            "language": "english",
            "content": "Mega Christmas Sale! Up to 60% OFF on selected items. Limited time only!"
        },
        {
            "product_service": "Laptop Promotion",
            "content_type": "Product Description",
            "target_audience": "Students",
            "tone": "professional",
            "language": "english",
            "content": "Premium laptops for students. Special discount with free backpack and mouse!"
        }
    ]
    
    print("🎨 Auto Image Generator - FREE API Demo")
    print("="*60)
    print(f"Output directory: {generator.output_dir}\n")
    
    for i, entry in enumerate(sample_entries, 1):
        print(f"\n[{i}/{len(sample_entries)}] {entry['product_service']}")
        print("-"*60)
        generator.generate_from_content(entry, i)
    
    print("\n" + "="*60)
    print("🎉 Image generation complete!")
    print(f"📁 Check images in: {generator.output_dir}/")


if __name__ == "__main__":
    main()
