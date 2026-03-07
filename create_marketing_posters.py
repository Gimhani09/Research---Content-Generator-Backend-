"""
Add Marketing Text Overlay to Generated Images
Creates professional marketing posters like your examples with proper text placement
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import textwrap
from pathlib import Path
import requests
from io import BytesIO

class MarketingPosterCreator:
    """Add professional text overlays to generated images."""
    
    def __init__(self):
        self.output_dir = Path("final_posters")
        self.output_dir.mkdir(exist_ok=True)
        
        # Try to use system fonts, fallback to PIL default
        self.fonts = self._load_fonts()
    
    def _load_fonts(self):
        """Load fonts for different text elements."""
        fonts = {}
        
        # Common Windows font paths
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/comic.ttf",
        ]
        
        try:
            # Title font (large, bold)
            fonts['title_large'] = ImageFont.truetype(font_paths[2], 120)  # Impact
            fonts['title'] = ImageFont.truetype(font_paths[1], 80)  # Arial Bold
            fonts['subtitle'] = ImageFont.truetype(font_paths[1], 50)  # Arial Bold
            fonts['body'] = ImageFont.truetype(font_paths[0], 35)  # Arial
            fonts['small'] = ImageFont.truetype(font_paths[0], 25)  # Arial
        except:
            print("⚠️ Using default fonts (install Arial/Impact for better quality)")
            fonts['title_large'] = ImageFont.load_default()
            fonts['title'] = ImageFont.load_default()
            fonts['subtitle'] = ImageFont.load_default()
            fonts['body'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()
        
        return fonts
    
    def create_gradient_overlay(self, image, direction='top', opacity=0.6):
        """Create gradient overlay for better text visibility."""
        width, height = image.size
        gradient = Image.new('RGBA', (width, height), color=0)
        draw = ImageDraw.Draw(gradient)
        
        if direction == 'top':
            # Dark gradient from top
            for y in range(height // 2):
                alpha = int(255 * opacity * (1 - y / (height // 2)))
                draw.rectangle([(0, y), (width, y+1)], fill=(0, 0, 0, alpha))
        elif direction == 'bottom':
            # Dark gradient from bottom
            for y in range(height // 2, height):
                alpha = int(255 * opacity * ((y - height // 2) / (height // 2)))
                draw.rectangle([(0, y), (width, y+1)], fill=(0, 0, 0, alpha))
        
        return gradient
    
    def add_text_with_stroke(self, draw, position, text, font, fill_color, stroke_color, stroke_width=3):
        """Add text with outline/stroke for better visibility."""
        x, y = position
        
        # Draw stroke
        for adj_x in range(-stroke_width, stroke_width + 1):
            for adj_y in range(-stroke_width, stroke_width + 1):
                draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=fill_color)
    
    def create_marketing_poster(self, image_path, entry, style="professional"):
        """
        Create professional marketing poster with text overlay.
        
        Styles:
        - professional: Clean, corporate (like Image 1)
        - exciting: Bold, colorful (like Image 2 - Christmas sale)
        - product: Product focused (like Image 3 - Laptops)
        """
        
        # Load background image
        bg_image = Image.open(image_path).convert('RGBA')
        
        # Resize to standard poster size (1024x1024)
        bg_image = bg_image.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        # Create overlay layer
        overlay = Image.new('RGBA', bg_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Add gradient for text visibility
        if style == "exciting":
            gradient = self.create_gradient_overlay(bg_image, 'top', 0.3)
        else:
            gradient = self.create_gradient_overlay(bg_image, 'top', 0.5)
        
        bg_image.paste(gradient, (0, 0), gradient)
        
        # Extract text elements
        product = entry['product_service']
        content = entry['content']
        tone = entry['tone']
        
        # Style-specific layouts
        if style == "professional":
            self._add_professional_layout(draw, product, content, tone)
        elif style == "exciting":
            self._add_exciting_layout(draw, product, content, tone)
        elif style == "product":
            self._add_product_layout(draw, product, content, tone)
        
        # Composite overlay onto background
        final_image = Image.alpha_composite(bg_image, overlay)
        
        return final_image.convert('RGB')
    
    def _add_professional_layout(self, draw, product, content, tone):
        """Clean layout - ONLY your generated content text."""
        
        # Just display the content text (what you generated)
        # Wrapped for readability
        wrapped_content = textwrap.wrap(content, width=35)
        
        # Center the text block
        y_start = 400  # Middle of image
        
        for line in wrapped_content:
            # Add each line with stroke for visibility
            self.add_text_with_stroke(
                draw, (100, y_start), line,
                self.fonts['body'], (255, 255, 255), (0, 0, 0), 2
            )
            y_start += 50
    
    def _add_exciting_layout(self, draw, product, content, tone):
        """Clean layout - ONLY your generated content text."""
        
        # Just display the content text (what you generated)
        wrapped_content = textwrap.wrap(content, width=35)
        
        # Center the text block
        y_start = 400  # Middle of image
        
        for line in wrapped_content:
            # Add each line with stroke for visibility
            self.add_text_with_stroke(
                draw, (100, y_start), line,
                self.fonts['body'], (255, 255, 255), (0, 0, 0), 2
            )
            y_start += 50
    
    def _add_product_layout(self, draw, product, content, tone):
        """Clean layout - ONLY your generated content text."""
        
        # Just display the content text (what you generated)
        wrapped_content = textwrap.wrap(content, width=35)
        
        # Center the text block
        y_start = 400  # Middle of image
        
        for line in wrapped_content:
            # Add each line with stroke for visibility
            self.add_text_with_stroke(
                draw, (100, y_start), line,
                self.fonts['body'], (255, 255, 255), (0, 0, 0), 2
            )
            y_start += 50
    
    def process_content_entry(self, image_path, entry, index=0):
        """Process a single content entry and create final poster."""
        
        # Determine style based on tone and content type
        tone = entry.get('tone', 'professional')
        content_type = entry.get('content_type', 'Social Media Post')
        
        if tone in ['exciting', 'fun', 'energetic']:
            style = "exciting"
        elif 'Product' in content_type:
            style = "product"
        else:
            style = "professional"
        
        # Create poster
        poster = self.create_marketing_poster(image_path, entry, style)
        
        # Save
        safe_name = entry['product_service'].replace(' ', '_').replace('/', '_')[:30]
        output_path = self.output_dir / f"poster_{index:03d}_{safe_name}.jpg"
        poster.save(output_path, quality=95)
        
        print(f"✅ Created poster: {output_path}")
        return str(output_path)


def demo():
    """Demo: Create marketing posters with text overlay."""
    
    creator = MarketingPosterCreator()
    
    # Sample entries (matching your examples)
    samples = [
        {
            "product_service": "Graphic Designer",
            "content_type": "Social Media Post",
            "tone": "professional",
            "content": "We Are Hiring! 1 Year Experience Required. Knowledge in Corel Draw & Photoshop. Apply Now!"
        },
        {
            "product_service": "Christmas Sale",
            "content_type": "Social Media Post",
            "tone": "exciting",
            "content": "Mega Sale Up To 50% OFF! Limited Time Only. Shop Now!"
        },
        {
            "product_service": "Laptop Sale",
            "content_type": "Product Description",
            "tone": "professional",
            "content": "Premium Laptops - Special Discount 59% OFF! Best Price Guaranteed."
        }
    ]
    
    print("🎨 Marketing Poster Creator - Adding Text Overlays")
    print("="*60)
    
    # Check if images exist
    image_dir = Path("generated_images")
    if not image_dir.exists() or not list(image_dir.glob("*.png")):
        print("⚠️ No generated images found!")
        print("   Run 'python auto_image_generator.py' first to generate background images.")
        return
    
    # Process each image
    for i, image_path in enumerate(sorted(image_dir.glob("*.png"))[:3], 1):
        if i <= len(samples):
            print(f"\n[{i}] Processing: {image_path.name}")
            creator.process_content_entry(image_path, samples[i-1], i)
    
    print("\n" + "="*60)
    print(f"🎉 Posters created successfully!")
    print(f"📁 Check: {creator.output_dir}/")


if __name__ == "__main__":
    demo()
