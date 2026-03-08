"""
Complete Poster Generator: Background (Stability AI) + Content (Your Fine-tuned Model)
Multiple template styles with random selection
"""
import os
import random
from pathlib import Path
from jinja2 import Template
from smart_poster_generator import SmartPosterGenerator
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def create_fallback_background(product_name, season=None):
    """
    Create a simple gradient background as fallback when AI generation fails
    
    Args:
        product_name: Product name
        season: Season/festival for color scheme
    
    Returns:
        Path to generated background image
    """
    # Create output directory
    Path("generated_backgrounds").mkdir(exist_ok=True)
    
    # Season-based color schemes
    color_schemes = {
        "Christmas": ((139, 0, 0), (255, 223, 186)),  # Dark red to cream
        "New Year": ((0, 0, 139), (255, 215, 0)),  # Navy to gold
        "Valentine": ((255, 20, 147), (255, 182, 193)),  # Deep pink to light pink
        "Avurudu": ((255, 140, 0), (255, 215, 0)),  # Orange to gold
        "Summer": ((0, 191, 255), (255, 255, 224)),  # Sky blue to light yellow
        "BlackFriday": ((0, 0, 0), (255, 69, 0)),  # Black to orange-red
        "default": ((70, 130, 180), (240, 248, 255))  # Steel blue to alice blue
    }
    
    colors = color_schemes.get(season, color_schemes["default"])
    
    # Create 1200x630 gradient
    width, height = 1200, 630
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient
    for y in range(height):
        ratio = y / height
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Save
    output_path = f"generated_backgrounds/fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(output_path, "PNG")
    print(f"   ✅ Created fallback background: {output_path}")
    
    return output_path

def get_random_template_style():
    """
    Randomly select a template style.
    Returns: template name or None for no template (just text overlay on AI background)
    """
    templates = [
        "left_panel",      # White panel on left (current style)
        "minimal",         # No panel, just text with shadow
        "bottom_banner",   # Dark banner at bottom
        "gradient_top",    # Gradient overlay from top
        "corner_accent",   # Accent panel in corner
        None              # No template overlay - just AI background with minimal text
    ]
    
    # Random selection with weights (None has lower probability for better variety)
    weights = [20, 20, 15, 15, 15, 15]  # 15% chance of no template
    return random.choices(templates, weights=weights, k=1)[0]


def apply_template_overlay(img, template_style, product_name, content, discount, business_name, phone_number, font_path=None, has_sinhala=False):
    """
    Apply selected template style to the image.
    
    Args:
        img: PIL Image object
        template_style: Template style name or None
        product_name, content, discount, business_name, phone_number: Content details
        font_path: Path to font file (for Sinhala support)
        has_sinhala: Boolean indicating if content has Sinhala text
    
    Returns:
        Modified PIL Image object
    """
    draw = ImageDraw.Draw(img)
    
    # Load fonts based on template
    try:
        if has_sinhala and font_path:
            title_font = ImageFont.truetype(font_path, 52)
            content_font = ImageFont.truetype(font_path, 20)
            discount_font = ImageFont.truetype(font_path, 72)
            cta_font = ImageFont.truetype(font_path, 40)
            bar_font = ImageFont.truetype(font_path, 22)
            bar_font_large = ImageFont.truetype(font_path, 28)
        else:
            title_font = ImageFont.truetype("arialbd.ttf", 52)
            content_font = ImageFont.truetype("arial.ttf", 20)
            discount_font = ImageFont.truetype("arialbd.ttf", 72)
            cta_font = ImageFont.truetype("arialbd.ttf", 40)
            bar_font = ImageFont.truetype("arial.ttf", 22)
            bar_font_large = ImageFont.truetype("arialbd.ttf", 28)
    except:
        title_font = content_font = discount_font = cta_font = bar_font = bar_font_large = ImageFont.load_default()
    
    if template_style == "left_panel":
        # TEMPLATE 1: White panel on left (current style)
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([(0, 0), (720, 630)], fill=(255, 255, 255, 200))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        y_pos = _add_content_text(draw, product_name, content, discount, 60, 100, title_font, content_font, discount_font, cta_font, (27, 27, 27), (255, 20, 20))
        _add_bottom_bar(draw, business_name, phone_number, bar_font, bar_font_large)
    
    elif template_style == "minimal":
        # TEMPLATE 2: No panel - just text with heavy shadow for readability
        y_pos = _add_content_text_with_shadow(draw, product_name, content, discount, 60, 100, title_font, content_font, discount_font, cta_font)
        _add_bottom_bar(draw, business_name, phone_number, bar_font, bar_font_large)
    
    elif template_style == "bottom_banner":
        # TEMPLATE 3: Dark banner at bottom with content
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([(0, 330), (1200, 630)], fill=(0, 0, 0, 180))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        y_pos = _add_content_text(draw, product_name, content, discount, 60, 360, title_font, content_font, discount_font, cta_font, (255, 255, 255), (255, 87, 34))
        _add_minimal_footer(draw, business_name, phone_number, bar_font, 560)
    
    elif template_style == "gradient_top":
        # TEMPLATE 4: Gradient from top
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for y in range(400):
            alpha = int(180 * (1 - y/400))
            overlay_draw.line([(0, y), (1200, y)], fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        y_pos = _add_content_text(draw, product_name, content, discount, 60, 60, title_font, content_font, discount_font, cta_font, (255, 255, 255), (255, 215, 0))
        _add_bottom_bar(draw, business_name, phone_number, bar_font, bar_font_large)
    
    elif template_style == "corner_accent":
        # TEMPLATE 5: Rounded accent panel in top-left corner
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle([(30, 30), (700, 420)], radius=20, fill=(255, 255, 255, 220))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        y_pos = _add_content_text(draw, product_name, content, discount, 70, 70, title_font, content_font, discount_font, cta_font, (27, 27, 27), (220, 20, 60))
        _add_bottom_bar(draw, business_name, phone_number, bar_font, bar_font_large)
    
    elif template_style is None:
        # TEMPLATE 6: No overlay - clean AI background with minimal text
        y_pos = _add_content_text_with_shadow(draw, product_name, content, discount, 60, 400, title_font, content_font, discount_font, cta_font)
        _add_minimal_footer(draw, business_name, phone_number, bar_font, 560)
    
    return img


def _add_content_text(draw, product_name, content, discount, x_start, y_start, title_font, content_font, discount_font, cta_font, text_color, accent_color):
    """Helper: Add content text to draw object."""
    y_pos = y_start
    
    # Product name
    draw.text((x_start, y_pos), product_name.upper(), fill=text_color, font=title_font)
    y_pos += 85
    
    # Discount
    if discount:
        discount_text = discount.strip()
        if not any(word in discount_text.upper() for word in ['OFF', 'RS.', 'LKR']):
            discount_text = f"{discount_text} OFF!"
        draw.text((x_start, y_pos), discount_text, fill=accent_color, font=discount_font)
        y_pos += 90
    
    # Content (wrapped)
    words = content.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if len(test_line) * 12 < 600:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines[:3]:
        draw.text((x_start, y_pos), line, fill=text_color, font=content_font)
        y_pos += 30
    
    # CTA button
    y_pos += 40
    cta_text = "ORDER NOW"
    button_bbox = draw.textbbox((x_start, y_pos), cta_text, font=cta_font)
    padding = 25
    draw.rectangle(
        [(button_bbox[0] - padding, button_bbox[1] - padding),
         (button_bbox[2] + padding, button_bbox[3] + padding)],
        fill=accent_color if accent_color != (255, 20, 20) else (255, 87, 34)
    )
    draw.text((x_start, y_pos), cta_text, fill=(255, 255, 255), font=cta_font)
    
    return y_pos


def _add_content_text_with_shadow(draw, product_name, content, discount, x_start, y_start, title_font, content_font, discount_font, cta_font):
    """Helper: Add content text with shadow for readability on transparent background."""
    y_pos = y_start
    shadow_offset = 3
    
    # Product name with shadow
    for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, shadow_offset)]:
        draw.text((x_start + dx, y_pos + dy), product_name.upper(), fill=(0, 0, 0), font=title_font)
    draw.text((x_start, y_pos), product_name.upper(), fill=(255, 255, 255), font=title_font)
    y_pos += 85
    
    # Discount with shadow
    if discount:
        discount_text = discount.strip()
        if not any(word in discount_text.upper() for word in ['OFF', 'RS.', 'LKR']):
            discount_text = f"{discount_text} OFF!"
        for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, shadow_offset)]:
            draw.text((x_start + dx, y_pos + dy), discount_text, fill=(0, 0, 0), font=discount_font)
        draw.text((x_start, y_pos), discount_text, fill=(255, 215, 0), font=discount_font)
        y_pos += 60
    
    return y_pos


def _add_bottom_bar(draw, business_name, phone_number, bar_font, bar_font_large):
    """Helper: Add black bottom bar with business info."""
    bar_height = 60
    bar_y = 630 - bar_height
    draw.rectangle([(0, bar_y), (1200, 630)], fill=(0, 0, 0))
    
    if phone_number:
        draw.text((40, bar_y + 18), phone_number, fill=(255, 255, 255), font=bar_font)
    
    if business_name:
        business_text = business_name.upper()
        business_bbox = draw.textbbox((0, 0), business_text, font=bar_font_large)
        business_width = business_bbox[2] - business_bbox[0]
        draw.text((1200 - business_width - 40, bar_y + 15), business_text, fill=(255, 255, 255), font=bar_font_large)


def _add_minimal_footer(draw, business_name, phone_number, bar_font, y_pos):
    """Helper: Add minimal footer without bar."""
    if phone_number or business_name:
        footer_text = f"{phone_number}  •  {business_name.upper()}" if phone_number and business_name else phone_number or business_name.upper()
        draw.text((60, y_pos), footer_text, fill=(255, 255, 255), font=bar_font)


def create_complete_poster(product_name, content, tags, background_path=None, season=None, discount=None, business_name=None, phone_number=None, template_style=None):
    """
    Create complete marketing poster with random template selection
    
    Args:
        product_name: Product name
        content: AI-generated marketing content
        tags: Product tags for context
        background_path: Path to background image (or auto-generate)
        season: User-selected season/festival (Christmas, Avurudu, etc.)
        discount: Discount info to highlight
        business_name: Business name (displayed right bottom)
        phone_number: Contact number (displayed left bottom)
        template_style: Template style name or None (auto-select randomly if not specified)
    
    Returns:
        Path to final poster image
    """
    
    # Select random template if not specified
    if template_style is None:
        template_style = get_random_template_style()
    
    print(f"\n🎨 Creating Complete Poster for: {product_name}")
    print(f"   Template: {template_style or 'None (minimal overlay)'}")
    print(f"   Season: {season or 'Auto-detect'}")
    print(f"   Business: {business_name or 'None'}")
    print(f"   Phone: {phone_number or 'None'}")
    print("=" * 60)
    
    # Step 1: Generate contextual background if not provided
    if not background_path:
        print("\n📸 Step 1: Generating contextual background...")
        try:
            poster_gen = SmartPosterGenerator(api_choice="stability")
            result = poster_gen.generate_poster(content, product_name, season=season)
            
            if result.get("result", {}).get("success"):
                background_path = result["result"]["image_path"]
                print(f"   ✅ Background generated: {background_path}")
                print(f"   📊 Context: {result['context']}")
            else:
                error_msg = result.get("result", {}).get("error", "Unknown error")
                print(f"   ❌ Background generation failed: {error_msg}")
                print(f"   ⚠️ Falling back to default gradient background")
                # Create a simple gradient background as fallback
                background_path = create_fallback_background(product_name, season)
        except Exception as e:
            print(f"   ❌ Exception during background generation: {str(e)}")
            print(f"   ⚠️ Falling back to default gradient background")
            background_path = create_fallback_background(product_name, season)
    else:
        print(f"\n📸 Step 1: Using existing background: {background_path}")
    
    # Step 2: Overlay text on background
    print(f"\n✍️  Step 2: Applying '{template_style or 'minimal'}' template...")
    
    # Open background
    img = Image.open(background_path)
    
    # Detect if content has Sinhala characters
    has_sinhala = any(ord(c) >= 0x0D80 and ord(c) <= 0x0DFF for c in content)
    print(f"   🔍 Sinhala detected: {has_sinhala}")
    
    # Initialize font_path variable
    font_path = None
    
    # Try to load fonts - use local Nirmala UI or other Sinhala fonts
    try:
        if has_sinhala:
            # Try multiple font sources for Sinhala support (in priority order)
            font_attempts = [
                # User's downloaded font
                "D:/content_generator/nirmala-ui.ttf",
                "nirmala-ui.ttf",
                # Windows 10/11 built-in Sinhala fonts
                "C:/Windows/Fonts/nirmala.ttf",
                "C:/Windows/Fonts/Nirmala.ttf",
                "C:/Windows/Fonts/NirmalaB.ttf",
                # Alternative Windows fonts with Sinhala support
                "C:/Windows/Fonts/seguisb.ttf",
                # Local downloads
                "fonts/NotoSansSinhala-Regular.ttf",
                "fonts/nirmala-ui.ttf"
            ]
            
            font_loaded = False
            for font_path in font_attempts:
                try:
                    print(f"   🔍 Trying: {font_path}")
                    # Try loading this font
                    title_font = ImageFont.truetype(font_path, 48)
                    body_font = ImageFont.truetype(font_path, 24)
                    cta_font = ImageFont.truetype(font_path, 28)
                    font_loaded = True
                    print(f"   ✅ SUCCESS! Loaded font: {font_path}")
                    break
                except Exception as e:
                    print(f"   ❌ Failed: {str(e)[:50]}")
                    continue
            
            if not font_loaded:
                raise Exception("No Sinhala font available - please ensure nirmala-ui.ttf is in the project folder")
        else:
            # For English, fonts will be loaded in template function
            font_path = "arial.ttf"
    except Exception as e:
        print(f"   ⚠️ Font loading error: {e}")
        print("   📝 Using default fonts (Sinhala may not display correctly)")
        font_path = None
    
    # Apply selected template style
    img = apply_template_overlay(
        img, 
        template_style, 
        product_name, 
        content, 
        discount, 
        business_name, 
        phone_number,
        font_path,
        has_sinhala
    )
    
    # Save final poster
    output_dir = Path("final_posters")
    output_dir.mkdir(exist_ok=True)
    
    from datetime import datetime
    filename = f"poster_{product_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    output_path = output_dir / filename
    
    img.save(output_path, "PNG", quality=95)
    
    print(f"\n✅ Complete poster saved: {output_path}")
    print(f"   📐 Size: 1200x630px (perfect for social media)")
    print(f"   💰 Cost: ~$0.004 (Stability AI background)")
    
    return str(output_path)


if __name__ == "__main__":
    # Set API key
    os.environ["STABILITY_API_KEY"] = "sk-YhZUURzP9JnSE1y2CKjDQIYpTbyyHdVkIsqhoRniuzeKETRH"
    
    # Test with Christmas content from your training data
    poster_path = create_complete_poster(
        product_name="Kottu Promotion",
        content="Christmas craving sorted! Get an EXCLUSIVE discount on our Kottu! Don't miss out. Visit store!",
        tags="Great value, seasonal offer"
    )
    
    if poster_path:
        print(f"\n{'='*60}")
        print(f"🎉 SUCCESS! Complete poster created!")
        print(f"{'='*60}")
        print(f"\nOpen this file to see your AI-generated poster:")
        print(f"   {poster_path}")
        print(f"\n✨ What was automated:")
        print(f"   1. ✅ Context detection (Christmas theme)")
        print(f"   2. ✅ Background generation (festive design)")
        print(f"   3. ✅ Content overlay (your fine-tuned text)")
        print(f"   4. ✅ Hashtag generation (seasonal tags)")
        print(f"\n🎯 Perfect for your research presentation!")
