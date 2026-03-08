"""
HTML/CSS Poster Renderer with HarfBuzz Shaping
================================================
Renders marketing posters using HTML/CSS templates with Playwright (Chromium).

Why this approach:
  - Chromium uses HarfBuzz internally for text shaping
  - Perfect Sinhala rendering: rakaransaya, yansaya, virama, GSUB substitutions
  - No manual Unicode shaping code needed
  - Professional typography with CSS
  - Easy layout control

Research Contribution:
  "Integration of a Unicode-aware Sinhala text shaping pipeline using
   HarfBuzz-based rendering (via Chromium) within an AI-driven poster
   generation framework, ensuring correct handling of virama, ZWJ,
   rakaransaya, and OpenType glyph substitutions."

Architecture:
  AI Background (Stability AI / gradient)
      ↓
  HTML Template (Jinja2) with CSS Typography
      ↓
  Playwright/Chromium (HarfBuzz shaping engine)
      ↓
  Screenshot → High-Resolution PNG
"""
import os
import random
import base64
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("⚠️ Playwright not installed. Run: pip install playwright && playwright install chromium")

import concurrent.futures
from jinja2 import Template


class HtmlPosterRenderer:
    """
    Render marketing posters using HTML/CSS + Chromium/HarfBuzz.
    
    Supports:
    - Multiple poster sizes (Facebook, Instagram, Story, Twitter)
    - Multiple template styles (left_panel, minimal, bottom_banner, etc.)
    - Proper Sinhala Unicode rendering via HarfBuzz
    - AI-generated or gradient backgrounds
    - Business branding (name + phone)
    """
    
    # Poster size configurations
    SIZES = {
        "facebook":  {"width": 1200, "height": 630},
        "instagram": {"width": 1080, "height": 1080},
        "story":     {"width": 1080, "height": 1920},
        "twitter":   {"width": 1200, "height": 675},
    }
    
    # Template styles — professional marketing poster designs
    TEMPLATE_STYLES = [
        "bold_impact",
        "elegant_sale",
        "dramatic_gradient",
    ]
    
    def __init__(self, font_dir: str = None):
        """
        Initialize renderer.
        
        Args:
            font_dir: Directory containing font files (NotoSansSinhala, etc.)
        """
        self.font_dir = font_dir or self._find_font_dir()
        self.font_path = self._find_sinhala_font()
        self.gemunu_font_path = self._find_gemunu_font()
        self.abhaya_font_path = self._find_abhaya_font()
        # Use absolute path based on this file's location, not CWD
        self.output_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "final_posters"
        self.output_dir.mkdir(exist_ok=True)
        
        if not HAS_PLAYWRIGHT:
            print("⚠️ Playwright not available - HTML rendering disabled")
            print("   Install: pip install playwright && playwright install chromium")
        else:
            print("✅ HTML Poster Renderer initialized (Chromium/HarfBuzz)")
            print(f"   Body/Features Font: {self.font_path or 'Noto Sans Sinhala (CDN)'}")
            print(f"   Sub-heading Font: {self.gemunu_font_path or 'Gemunu Libre (CDN)'}")
            print(f"   Main Heading Font: {self.abhaya_font_path or 'Abhaya Libre (CDN)'}")
    
    def _find_font_dir(self) -> str:
        """Find fonts directory"""
        possible_dirs = [
            os.path.join(os.path.dirname(__file__), "fonts"),
            "fonts",
            os.path.join(os.path.dirname(__file__), "..", "content-generator-backend", "fonts"),
        ]
        for d in possible_dirs:
            if os.path.isdir(d):
                return os.path.abspath(d)
        
        # Create fonts dir
        fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
        os.makedirs(fonts_dir, exist_ok=True)
        return fonts_dir
    
    def _find_gemunu_font(self) -> Optional[str]:
        """Find the Gemunu Libre display font (with proper Sinhala GSUB/GPOS support)"""
        gemunu_names = [
            "GemunuLibre-Bold.ttf",
            "GemunuLibre-ExtraBold.ttf",
            "GemunuLibre-Regular.ttf",
            "GemunuLibre[wght].ttf",
        ]
        if self.font_dir:
            for name in gemunu_names:
                path = os.path.join(self.font_dir, name)
                if os.path.isfile(path):
                    return os.path.abspath(path)
        return None

    def _find_abhaya_font(self) -> Optional[str]:
        """Find the Abhaya Libre font (bold, impactful — for main headings)"""
        abhaya_names = [
            "AbhayaLibre-ExtraBold.ttf",
            "AbhayaLibre-Bold.ttf",
            "AbhayaLibre-SemiBold.ttf",
            "AbhayaLibre-Regular.ttf",
            "AbhayaLibre[wght].ttf",
        ]
        if self.font_dir:
            for name in abhaya_names:
                path = os.path.join(self.font_dir, name)
                if os.path.isfile(path):
                    return os.path.abspath(path)
        return None

    def _find_sinhala_font(self) -> Optional[str]:
        """Find a Sinhala-capable font file"""
        font_names = [
            "NotoSansSinhala-Variable.ttf",
            "NotoSansSinhala-Regular.ttf",
            "NotoSansSinhala-VariableFont_wdth,wght.ttf",
            "nirmala-ui.ttf",
            "nirmala.ttf",
            "Nirmala.ttf",
        ]
        
        # Search in font_dir
        if self.font_dir:
            for name in font_names:
                path = os.path.join(self.font_dir, name)
                if os.path.isfile(path):
                    return os.path.abspath(path)
        
        # Search in project root
        for name in font_names:
            if os.path.isfile(name):
                return os.path.abspath(name)
        
        # Search in Windows fonts
        win_fonts = "C:/Windows/Fonts"
        if os.path.isdir(win_fonts):
            for name in ["nirmala.ttf", "Nirmala.ttf"]:
                path = os.path.join(win_fonts, name)
                if os.path.isfile(path):
                    return path
        
        return None
    
    def _get_font_css(self) -> str:
        """Generate @font-face CSS for Sinhala font + Gemunu display font"""
        css_parts = []

        # Sinhala body font
        if self.font_path and os.path.isfile(self.font_path):
            try:
                with open(self.font_path, 'rb') as f:
                    font_data = base64.b64encode(f.read()).decode('utf-8')
                css_parts.append(f"""
                @font-face {{
                    font-family: 'SinhalaFont';
                    src: url(data:font/truetype;base64,{font_data}) format('truetype');
                    font-weight: 100 900;
                    font-style: normal;
                    font-display: block;
                }}
                """)
            except Exception as e:
                print(f"⚠️ Could not load local font: {e}")
                css_parts.append("""
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700;800&display=swap');
                @font-face { font-family: 'SinhalaFont'; src: local('Noto Sans Sinhala'); font-weight: 100 900; }
                """)
        else:
            css_parts.append("""
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;600;700;800&display=swap');
            @font-face {
                font-family: 'SinhalaFont';
                src: local('Noto Sans Sinhala'), local('NotoSansSinhala');
                font-weight: 100 900;
            }
            """)

        # Gemunu Libre display font for headings (has full Sinhala GSUB/GPOS support)
        if self.gemunu_font_path and os.path.isfile(self.gemunu_font_path):
            try:
                with open(self.gemunu_font_path, 'rb') as f:
                    gemunu_data = base64.b64encode(f.read()).decode('utf-8')
                css_parts.append(f"""
                @font-face {{
                    font-family: 'GemunuFont';
                    src: url(data:font/truetype;base64,{gemunu_data}) format('truetype');
                    font-weight: 100 900;
                    font-style: normal;
                    font-display: block;
                }}
                """)
            except Exception as e:
                print(f"⚠️ Could not load Gemunu Libre font: {e}")
                # Fallback to Google Fonts CDN
                css_parts.append("""
                @import url('https://fonts.googleapis.com/css2?family=Gemunu+Libre:wght@400;600;700;800&display=swap');
                @font-face { font-family: 'GemunuFont'; src: local('Gemunu Libre'); font-weight: 100 900; }
                """)
        else:
            # No local file - load from Google Fonts CDN
            css_parts.append("""
            @import url('https://fonts.googleapis.com/css2?family=Gemunu+Libre:wght@400;600;700;800&display=swap');
            @font-face {
                font-family: 'GemunuFont';
                src: local('Gemunu Libre');
                font-weight: 100 900;
            }
            """)

        # Abhaya Libre heading font (bold, impactful — for product name / main heading)
        if self.abhaya_font_path and os.path.isfile(self.abhaya_font_path):
            try:
                with open(self.abhaya_font_path, 'rb') as f:
                    abhaya_data = base64.b64encode(f.read()).decode('utf-8')
                css_parts.append(f"""
                @font-face {{
                    font-family: 'AbhayaFont';
                    src: url(data:font/truetype;base64,{abhaya_data}) format('truetype');
                    font-weight: 100 900;
                    font-style: normal;
                    font-display: block;
                }}
                """)
            except Exception as e:
                print(f"⚠️ Could not load Abhaya Libre font: {e}")
                css_parts.append("""
                @import url('https://fonts.googleapis.com/css2?family=Abhaya+Libre:wght@400;600;700;800&display=swap');
                @font-face { font-family: 'AbhayaFont'; src: local('Abhaya Libre'); font-weight: 100 900; }
                """)
        else:
            css_parts.append("""
            @import url('https://fonts.googleapis.com/css2?family=Abhaya+Libre:wght@400;600;700;800&display=swap');
            @font-face {
                font-family: 'AbhayaFont';
                src: local('Abhaya Libre');
                font-weight: 100 900;
            }
            """)

        return "\n".join(css_parts)
    
    def _get_smart_cta(
        self,
        product_name: str,
        content: str,
        discount: str,
        season: str,
        language: str = "en"
    ) -> str:
        """Generate a context-appropriate CTA based on product, discount, season and language."""
        product_lower = product_name.lower() if product_name else ""
        content_lower = content.lower() if content else ""
        combined = product_lower + " " + content_lower
        has_sinhala = self._has_sinhala(product_name + " " + content)
        
        # Sinhala CTAs
        sinhala_ctas = {
            "shop": "දැන්ම මිලදී ගන්න",
            "order": "දැන්ම ඇණවුම් කරන්න",
            "call": "දැන්ම අමතන්න",
            "visit": "අද පැමිණෙන්න",
            "get_deal": "දැන්ම ගන්න",
            "book": "දැන්ම වෙන් කරන්න",
            "try": "අත්විඳින්න",
            "learn": "තව දැනගන්න",
        }
        
        # English CTAs
        english_ctas = {
            "shop": "SHOP NOW",
            "order": "ORDER NOW",
            "call": "CALL NOW",
            "visit": "VISIT TODAY",
            "get_deal": "GRAB THE DEAL",
            "book": "BOOK NOW",
            "try": "TRY IT TODAY",
            "learn": "LEARN MORE",
        }
        
        ctas = sinhala_ctas if has_sinhala else english_ctas
        
        # Service-based businesses → CALL / VISIT
        service_keywords = ["service", "repair", "salon", "spa", "clinic", "hospital", "academy",
                           "restaurant", "hotel", "consulting", "සේවා", "අලුත්වැඩියා", "රෝහල"]
        if any(kw in combined for kw in service_keywords):
            return ctas["call"]
        
        # Booking-based → BOOK NOW
        booking_keywords = ["class", "course", "workshop", "event", "reservation", "appointment",
                           "පන්ති", "වැඩමුළු"]
        if any(kw in combined for kw in booking_keywords):
            return ctas["book"]
        
        # Food & dining → ORDER NOW
        food_keywords = ["food", "pizza", "burger", "rice", "biriyani", "menu", "eat",
                        "kottu", "hoppers", "roti", "cake", "bakery",
                        "කෑම", "බත්", "බර්ගර්", "පීසා", "කොත්තු"]
        if any(kw in combined for kw in food_keywords):
            return ctas["order"]
        
        # Heavy discounts → GRAB THE DEAL
        if discount and any(d in discount.upper() for d in ["50%", "60%", "70%", "80%", "BUY 1", "FREE"]):
            return ctas["get_deal"]
        
        # E-commerce / shopping products → SHOP NOW
        shop_keywords = ["laptop", "phone", "tv", "camera", "fashion", "clothing", "dress", "shoe",
                        "watch", "jewelry", "electronics", "furniture", "sofa", "bed", "table", "chair",
                        "fridge", "washing", "machine", "appliance",
                        "ලැප්ටොප්", "දුරකථන", "ඇඳුම්"]
        if any(kw in combined for kw in shop_keywords):
            return ctas["shop"]
        
        # Season sale → SHOP NOW  
        if season and any(s in season.lower() for s in ["sale", "friday", "christmas", "year", "avurudu"]):
            return ctas["shop"]
        
        # Default: SHOP NOW (more universally appropriate than ORDER NOW)
        return ctas["shop"]
    
    def render_poster(
        self,
        product_name: str,
        content: str,
        background_path: Optional[str] = None,
        template_style: Optional[str] = None,
        size: str = "facebook",
        discount: str = "",
        business_name: str = "",
        phone_number: str = "",
        season: str = "",
        cta_text: str = ""
    ) -> Optional[str]:
        """
        Render a marketing poster using HTML/CSS + Chromium/HarfBuzz.
        
        Args:
            product_name: Product name
            content: Marketing content text (may contain Sinhala Unicode)
            background_path: Path to background image (or None for gradient)
            template_style: Template style name (or None for random)
            size: Poster size key (facebook, instagram, story, twitter)
            discount: Discount text (e.g., "20% OFF")
            business_name: Business name for footer
            phone_number: Phone number for footer
            season: Season/festival name
            cta_text: Call-to-action button text
        
        Returns:
            Path to generated PNG poster, or None on failure
        """
        if not HAS_PLAYWRIGHT:
            print("❌ Playwright not available - cannot render HTML poster")
            return None
        
        # Extract [CTA] from structured content if present
        import re
        cta_match = re.search(r'\[CTA\]\s*\n?(.*?)(?=\[(?:HEADING|BODY|FEATURES)\]|\Z)', content, re.DOTALL | re.IGNORECASE)
        if cta_match and cta_match.group(1).strip():
            extracted_cta = cta_match.group(1).strip().split('\n')[0].strip()
            if extracted_cta:
                cta_text = extracted_cta
                # Remove [CTA] section from content so it's not rendered twice
                content = re.sub(r'\[CTA\]\s*\n?.*?(?=\[(?:HEADING|BODY|FEATURES)\]|\Z)', '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        
        # Auto-generate smart CTA if not provided
        if not cta_text:
            cta_text = self._get_smart_cta(product_name, content, discount, season)
            print(f"   🎯 Smart CTA: {cta_text}")
        
        # Get size dimensions
        dims = self.SIZES.get(size, self.SIZES["facebook"])
        width, height = dims["width"], dims["height"]
        
        # Select template style
        if template_style is None:
            template_style = random.choice(self.TEMPLATE_STYLES)
        
        print(f"\n🎨 HTML Poster Renderer (HarfBuzz)")
        print(f"   Template: {template_style}")
        print(f"   Size: {size} ({width}x{height})")
        print(f"   Sinhala detected: {self._has_sinhala(content)}")
        
        # Build background CSS
        bg_css = self._get_background_css(background_path, season, width, height)
        
        # Build HTML
        html = self._build_html(
            template_style=template_style,
            product_name=product_name,
            content=content,
            width=width,
            height=height,
            bg_css=bg_css,
            discount=discount,
            business_name=business_name,
            phone_number=phone_number,
            cta_text=cta_text,
            season=season
        )
        
        # Render with Playwright
        output_path = self._screenshot_html(html, width, height, product_name, size)
        
        return output_path
    
    def _has_sinhala(self, text: str) -> bool:
        """Check if text contains Sinhala characters"""
        return any(0x0D80 <= ord(c) <= 0x0DFF for c in text)
    
    def _get_background_css(
        self,
        background_path: Optional[str],
        season: str,
        width: int,
        height: int
    ) -> str:
        """Generate background CSS"""
        if background_path and os.path.isfile(background_path):
            # Encode background as base64
            try:
                with open(background_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = background_path.lower().split('.')[-1]
                mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else 'png'}"
                return f"background: url(data:{mime};base64,{img_data}) center/cover no-repeat;"
            except Exception:
                pass
        
        # Gradient fallback based on season
        gradients = {
            "christmas": "linear-gradient(135deg, #8B0000 0%, #2F4F2F 50%, #FFD700 100%)",
            "new year": "linear-gradient(135deg, #000080 0%, #191970 50%, #FFD700 100%)",
            "valentine": "linear-gradient(135deg, #FF1493 0%, #FF69B4 50%, #FFB6C1 100%)",
            "avurudu": "linear-gradient(135deg, #FF8C00 0%, #DAA520 50%, #FFD700 100%)",
            "summer": "linear-gradient(135deg, #00BFFF 0%, #87CEEB 50%, #F0E68C 100%)",
            "black friday": "linear-gradient(135deg, #000000 0%, #1a1a2e 50%, #FF4500 100%)",
            "back to school": "linear-gradient(135deg, #4169E1 0%, #6495ED 50%, #F0F8FF 100%)",
        }
        
        gradient = "linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%)"
        if season:
            for key, grad in gradients.items():
                if key in season.lower():
                    gradient = grad
                    break
        
        return f"background: {gradient};"
    
    def _build_html(
        self,
        template_style: str,
        product_name: str,
        content: str,
        width: int,
        height: int,
        bg_css: str,
        discount: str,
        business_name: str,
        phone_number: str,
        cta_text: str,
        season: str
    ) -> str:
        """Build complete HTML for the poster"""
        
        font_css = self._get_font_css()
        
        # Determine accent color based on season
        accent_colors = {
            "christmas": "#c0392b",
            "new year": "#f39c12",
            "valentine": "#e91e63",
            "avurudu": "#ff6f00",
            "summer": "#00bcd4",
            "black friday": "#ff5722",
            "default": "#ff6b35"
        }
        accent = accent_colors.get("default")
        if season:
            for key, color in accent_colors.items():
                if key in season.lower():
                    accent = color
                    break
        
        # Get template-specific HTML
        template_fn = {
            "bold_impact": self._template_bold_impact,
            "elegant_sale": self._template_elegant_sale,
            "dramatic_gradient": self._template_dramatic_gradient,
            # Legacy aliases
            "left_panel": self._template_bold_impact,
            "minimal": self._template_bold_impact,
            "bottom_banner": self._template_elegant_sale,
            "gradient_top": self._template_dramatic_gradient,
            "corner_accent": self._template_dramatic_gradient,
            "centered": self._template_bold_impact,
            "centered_gradient": self._template_elegant_sale,
            "centered_banner": self._template_dramatic_gradient,
        }
        
        template_builder = template_fn.get(template_style, self._template_bold_impact)
        
        inner_html = template_builder(
            product_name=product_name,
            content=content,
            discount=discount,
            business_name=business_name,
            phone_number=phone_number,
            cta_text=cta_text,
            accent=accent,
            width=width,
            height=height,
            season=season
        )
        
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{font_css}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

html, body {{
    width: {width}px;
    height: {height}px;
    overflow: hidden;
}}

body {{
    font-family: 'SinhalaFont', 'Noto Sans Sinhala', 'Nirmala UI', 'Arial', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-feature-settings: 'liga' 1, 'clig' 1, 'calt' 1;
    text-rendering: optimizeLegibility;
}}

.poster {{
    width: {width}px;
    height: {height}px;
    position: relative;
    {bg_css}
    overflow: hidden;
}}

/* === PRODUCT NAME: Big, bold, impactful — Abhaya Libre === */
.product-name {{
    font-family: 'AbhayaFont', 'Abhaya Libre', 'SinhalaFont', 'Noto Sans Sinhala', sans-serif;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 3px;
    line-height: 1.1;
    word-wrap: break-word;
    overflow-wrap: break-word;
}}

/* === HEADLINE / SUB-HEADING: Gemunu Libre — modern, clean === */
.headline-text {{
    font-family: 'GemunuFont', 'Gemunu Libre', 'SinhalaFont', 'Noto Sans Sinhala', sans-serif;
    font-weight: 800;
    line-height: 1.15;
    word-wrap: break-word;
    overflow-wrap: break-word;
}}

/* === CONTENT / BODY / FEATURES: Noto Sans Sinhala — clean, readable === */
.content-text {{
    font-family: 'SinhalaFont', 'Noto Sans Sinhala', 'Nirmala UI', sans-serif;
    line-height: 1.6;
    font-weight: 600;
    word-wrap: break-word;
    overflow-wrap: break-word;
}}

.content-line {{
    font-family: 'SinhalaFont', 'Noto Sans Sinhala', 'Nirmala UI', sans-serif;
    display: block;
    margin-bottom: 3px;
    font-weight: 600;
}}

/* === DISCOUNT: MASSIVE, the star of the poster === */
.discount-text {{
    font-family: 'AbhayaFont', 'Abhaya Libre', 'GemunuFont', 'SinhalaFont', sans-serif;
    font-weight: 900;
    line-height: 0.95;
    letter-spacing: -1px;
}}

/* === URGENCY / CTA LINE: Bold, colored — Gemunu Libre === */
.urgency-text {{
    font-family: 'GemunuFont', 'Gemunu Libre', 'SinhalaFont', 'Noto Sans Sinhala', sans-serif;
    font-weight: 800;
    line-height: 1.1;
}}

/* === FOOTER BAR === */
.footer-bar {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: {int(55 * width / 1200)}px;
    background: rgba(0, 0, 0, 0.92);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 {int(30 * width / 1200)}px;
}}

.footer-phone {{
    color: #ffffff;
    font-size: {int(18 * width / 1200)}px;
    font-weight: 600;
    letter-spacing: 1px;
}}

.footer-business {{
    color: #ffffff;
    font-family: 'AbhayaFont', 'Abhaya Libre', 'GemunuFont', 'SinhalaFont', sans-serif;
    font-size: {int(22 * width / 1200)}px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
}}
</style>
</head>
<body>
{inner_html}
</body>
</html>"""
    
    # ========================================
    # Template Builders — Professional Marketing Poster Styles
    # ========================================
    
    def _template_bold_impact(self, **kwargs) -> str:
        """Bold Impact: Like Daraz/BLOOM posters — huge headline, massive discount, gold text"""
        p = kwargs
        fs = self._get_font_scale(p['width'], p['height'])
        shadow = "3px 3px 12px rgba(0,0,0,0.95), 0 0 40px rgba(0,0,0,0.5)"
        gold = "#FFD700"
        
        season_badge = self._season_badge_html(p.get('season', ''), p['accent'], fs, dark_bg=True, centered=True)
        content_html = self._format_poster_content(p['content'], fs, p['accent'])
        discount_html = self._big_discount_html(p['discount'], p['accent'], fs)
        urgency_html = self._urgency_html(p.get('cta_text', ''), fs)
        
        return f"""
<div class="poster">
    <div style="
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.45);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: {int(25 * fs)}px {int(50 * fs)}px {int(70 * fs)}px;
    ">
        {season_badge}
        
        <div class="product-name" style="
            font-size: {int(56 * fs)}px;
            color: {gold};
            text-shadow: {shadow};
            margin-bottom: {int(8 * fs)}px;
            -webkit-text-stroke: 1px rgba(0,0,0,0.3);
            text-align: center;
            width: 100%;
        ">{self._escape_html(p['product_name'])}</div>
        
        {discount_html}
        
        <div style="margin: {int(8 * fs)}px 0; max-width: 90%; text-align: center;">
            {content_html}
        </div>
        
        {urgency_html}
    </div>
    
    {self._footer_html(p['phone_number'], p['business_name'])}
</div>"""
    
    def _template_elegant_sale(self, **kwargs) -> str:
        """Elegant Sale: Clean layout with colored accent sections, like Book Shop poster"""
        p = kwargs
        fs = self._get_font_scale(p['width'], p['height'])
        shadow = "2px 2px 8px rgba(0,0,0,0.9), 0 0 25px rgba(0,0,0,0.4)"
        
        season_badge = self._season_badge_html(p.get('season', ''), p['accent'], fs, dark_bg=True, centered=True)
        content_html = self._format_poster_content(p['content'], fs, p['accent'])
        discount_html = self._big_discount_html(p['discount'], p['accent'], fs)
        urgency_html = self._urgency_html(p.get('cta_text', ''), fs)
        
        return f"""
<div class="poster">
    <div style="
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(180deg, rgba(0,0,0,0.30) 0%, rgba(0,0,0,0.50) 50%, rgba(0,0,0,0.70) 100%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: {int(25 * fs)}px {int(50 * fs)}px {int(70 * fs)}px;
    ">
        {season_badge}
        
        <div class="product-name" style="
            font-size: {int(52 * fs)}px;
            color: #FFFFFF;
            text-shadow: {shadow};
            margin-bottom: {int(6 * fs)}px;
            text-align: center;
            width: 100%;
        ">{self._escape_html(p['product_name'])}</div>
        
        {discount_html}
        
        <div style="
            margin: {int(8 * fs)}px 0;
            max-width: 88%;
            background: rgba(0,0,0,0.35);
            border-radius: {int(8 * fs)}px;
            padding: {int(12 * fs)}px {int(20 * fs)}px;
            text-align: center;
        ">
            {content_html}
        </div>
        
        {urgency_html}
    </div>
    
    {self._footer_html(p['phone_number'], p['business_name'])}
</div>"""
    
    def _template_dramatic_gradient(self, **kwargs) -> str:
        """Dramatic Gradient: Strong radial vignette, HUGE discount, minimal text"""
        p = kwargs
        fs = self._get_font_scale(p['width'], p['height'])
        shadow = "3px 3px 15px rgba(0,0,0,0.95), 0 0 35px rgba(0,0,0,0.6)"
        gold = "#FFD700"
        
        season_badge = self._season_badge_html(p.get('season', ''), p['accent'], fs, dark_bg=True, centered=True)
        content_html = self._format_poster_content(p['content'], fs, p['accent'])
        discount_html = self._big_discount_html(p['discount'], p['accent'], fs)
        urgency_html = self._urgency_html(p.get('cta_text', ''), fs)
        
        return f"""
<div class="poster">
    <div style="
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at center, rgba(0,0,0,0.30) 0%, rgba(0,0,0,0.55) 55%, rgba(0,0,0,0.80) 100%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: {int(25 * fs)}px {int(50 * fs)}px {int(70 * fs)}px;
    ">
        {season_badge}
        
        <div class="product-name" style="
            font-size: {int(54 * fs)}px;
            color: {gold};
            text-shadow: {shadow};
            margin-bottom: {int(6 * fs)}px;
            -webkit-text-stroke: 1px rgba(0,0,0,0.25);
            text-align: center;
            width: 100%;
        ">{self._escape_html(p['product_name'])}</div>
        
        {discount_html}
        
        <div style="margin: {int(8 * fs)}px 0; max-width: 88%; text-align: center;">
            {content_html}
        </div>
        
        {urgency_html}
    </div>
    
    {self._footer_html(p['phone_number'], p['business_name'])}
</div>"""
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _get_font_scale(self, width: int, height: int) -> float:
        """Calculate font scale factor based on poster size"""
        base_width = 1200
        return width / base_width
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters while preserving Unicode"""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("\n", "<br>")
        )
    
    def _format_poster_content(
        self,
        content: str,
        font_scale: float,
        accent: str
    ) -> str:
        """Format content with professional poster hierarchy using section markers.
        Parses [HEADING], [BODY], [FEATURES], [CTA] sections from Gemini output.
        Falls back to legacy line-based formatting if markers not found."""
        if not content:
            return ""
        
        import re
        
        # Try to parse structured sections
        sections = self._parse_content_sections(content)
        
        if sections:
            return self._render_structured_content(sections, font_scale, accent)
        
        # Fallback: legacy line-based formatting
        return self._render_legacy_content(content, font_scale, accent)
    
    def _parse_content_sections(self, content: str) -> dict:
        """Parse [HEADING], [BODY], [FEATURES], [CTA] markers from content."""
        import re
        
        markers = ['HEADING', 'BODY', 'FEATURES', 'CTA']
        sections = {}
        
        # Check if at least HEADING marker exists
        if '[HEADING]' not in content.upper():
            return {}
        
        for marker in markers:
            pattern = rf'\[{marker}\]\s*\n?(.*?)(?=\[(?:HEADING|BODY|FEATURES|CTA)\]|\Z)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                if text:
                    sections[marker.lower()] = text
        
        return sections if 'heading' in sections else {}
    
    def _render_structured_content(self, sections: dict, font_scale: float, accent: str) -> str:
        """Render parsed sections with distinct font hierarchy.
        Note: CTA is rendered separately by _urgency_html, not here."""
        shadow = "2px 2px 10px rgba(0,0,0,0.9), 0 0 20px rgba(0,0,0,0.4)"
        html_parts = []
        
        # HEADING — large, bold, white — Gemunu Libre (Sub-heading style)
        if 'heading' in sections:
            size = int(36 * font_scale)
            html_parts.append(
                f'<div style="'
                f'font-family: \'GemunuFont\', \'Gemunu Libre\', \'SinhalaFont\', \'Noto Sans Sinhala\', sans-serif;'
                f'font-size: {size}px; '
                f'font-weight: 800; '
                f'color: #FFFFFF; '
                f'text-shadow: {shadow}; '
                f'margin-bottom: {int(8 * font_scale)}px; '
                f'line-height: 1.15; '
                f'text-align: center; width: 100%;'
                f'">{self._escape_html(sections["heading"])}</div>'
            )
        
        # BODY — medium, readable — Noto Sans Sinhala
        if 'body' in sections:
            size = int(20 * font_scale)
            html_parts.append(
                f'<div style="'
                f'font-family: \'SinhalaFont\', \'Noto Sans Sinhala\', \'Nirmala UI\', sans-serif;'
                f'font-size: {size}px; '
                f'font-weight: 500; '
                f'color: rgba(255,255,255,0.92); '
                f'text-shadow: {shadow}; '
                f'margin-bottom: {int(10 * font_scale)}px; '
                f'line-height: 1.4; '
                f'text-align: center; width: 100%;'
                f'">{self._escape_html(sections["body"])}</div>'
            )
        
        # FEATURES — with diamond bullet icons, medium-small
        if 'features' in sections:
            feature_lines = [l.strip() for l in sections['features'].split('\n') if l.strip()]
            size = int(18 * font_scale)
            features_html = []
            for line in feature_lines[:4]:  # Max 4 features
                import re
                cleaned = re.sub(r'^[>\-\*•✓✔◆◇●○]+\s*', '', line).strip()
                if cleaned:
                    features_html.append(
                        f'<div style="'
                        f'font-family: \'SinhalaFont\', \'Noto Sans Sinhala\', \'Nirmala UI\', sans-serif;'
                        f'font-size: {size}px; '
                        f'font-weight: 600; '
                        f'color: rgba(255,255,255,0.88); '
                        f'text-shadow: {shadow}; '
                        f'margin-bottom: {int(3 * font_scale)}px; '
                        f'line-height: 1.3;'
                        f'"><span style="color: {accent}; margin-right: {int(6 * font_scale)}px;">&#9670;</span>'
                        f'{self._escape_html(cleaned)}</div>'
                    )
            if features_html:
                html_parts.append(
                    f'<div style="margin-bottom: {int(8 * font_scale)}px; text-align: left; display: inline-block;">'
                    + '\n'.join(features_html) + '</div>'
                )
        
        return "\n".join(html_parts)
    
    def _render_legacy_content(self, content: str, font_scale: float, accent: str) -> str:
        """Legacy fallback: format flat content lines with basic hierarchy.
        Line 1 = headline (large, white), remaining = body (medium, lighter)."""
        import re
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        # Filter phone/contact lines and strip bullet prefixes
        phone_pattern = re.compile(r'(0\d{2}[\s-]?\d{7}|07\d[\s-]?\d{3}[\s-]?\d{4}|\d{3}[\s-]XXXXXXX|077|071|072|076|078|070)')
        contact_keywords = ['අමතන්න', 'call now', 'call us', 'contact', 'phone', 'දුරකථන']
        
        cleaned = []
        for line in lines:
            ll = line.lower()
            if phone_pattern.search(line) and len(line) < 25:
                continue
            if any(kw in ll for kw in contact_keywords) and len(line) < 30:
                continue
            stripped = re.sub(r'^[>\-\*•✓✔]+\s*', '', line).strip()
            if stripped:
                cleaned.append(stripped)
        
        if not cleaned:
            return ""
        
        shadow = "2px 2px 10px rgba(0,0,0,0.9), 0 0 20px rgba(0,0,0,0.4)"
        html_parts = []
        
        for i, line in enumerate(cleaned):
            escaped = self._escape_html(line)
            is_discount_line = any(kw in line.upper() for kw in ['OFF', 'RS.', 'LKR', 'රු.', 'වට්ටම', '%'])
            
            if i == 0:
                size = int(26 * font_scale)
                weight = 800
                color = "#FFFFFF"
            elif is_discount_line:
                size = int(24 * font_scale)
                weight = 800
                color = accent
            else:
                size = int(20 * font_scale)
                weight = 600
                color = "rgba(255,255,255,0.92)"
            
            html_parts.append(
                f'<div class="content-line" style="'
                f'font-size: {size}px; '
                f'font-weight: {weight}; '
                f'color: {color}; '
                f'text-shadow: {shadow};'
                f'margin-bottom: {int(4 * font_scale)}px;'
                f'">{escaped}</div>'
            )
        
        return "\n".join(html_parts)
    
    def _big_discount_html(
        self,
        discount: str,
        accent: str,
        font_scale: float
    ) -> str:
        """Generate MASSIVE discount text — the visual star of the poster.
        Like the reference posters: 80%, 50%, 25% are the biggest elements."""
        if not discount or not discount.strip():
            return ""
        
        discount_clean = discount.strip()
        shadow = "4px 4px 15px rgba(0,0,0,0.95), 0 0 40px rgba(0,0,0,0.5)"
        
        # Try to extract just the number+% for massive display
        import re
        pct_match = re.search(r'(\d+)\s*%', discount_clean)
        
        if pct_match:
            pct_num = pct_match.group(1)
            # Check for "Up to" prefix
            has_prefix = 'up to' in discount_clean.lower() or 'දක්වා' in discount_clean
            prefix_text = "Up to" if has_prefix else ""
            
            # Extract suffix like "OFF" or "වට්ටම්"
            suffix = "OFF"
            if 'වට්ටම' in discount_clean:
                suffix = "වට්ටම්"
            elif 'දක්වා' in discount_clean:
                suffix = "දක්වා වට්ටම්"
            
            return f"""
        <div style="text-align: center; margin: {int(6 * font_scale)}px 0;">
            {"<div style='font-size:" + str(int(18 * font_scale)) + "px; color: #FFFFFF; font-weight: 700; text-shadow:" + shadow + "; letter-spacing: 2px;'>" + self._escape_html(prefix_text) + "</div>" if prefix_text else ""}
            <div class="discount-text" style="
                font-size: {int(100 * font_scale)}px;
                color: {accent};
                text-shadow: {shadow};
                -webkit-text-stroke: 2px rgba(0,0,0,0.2);
            ">{pct_num}%</div>
            <div class="headline-text" style="
                font-size: {int(36 * font_scale)}px;
                color: #FFFFFF;
                text-shadow: {shadow};
                letter-spacing: 3px;
                margin-top: -{int(8 * font_scale)}px;
            ">{self._escape_html(suffix)}</div>
        </div>"""
        else:
            # Non-percentage discount (e.g., "Buy 1 Get 1 Free", "Rs.50,000 OFF")
            return f"""
        <div class="discount-text" style="
            font-size: {int(60 * font_scale)}px;
            color: {accent};
            text-shadow: {shadow};
            margin: {int(8 * font_scale)}px 0;
            -webkit-text-stroke: 1px rgba(0,0,0,0.2);
        ">{self._escape_html(discount_clean)}</div>"""
    
    def _urgency_html(self, cta_text: str, font_scale: float) -> str:
        """Generate urgency text (replaces CTA button) — bold, large, colored.
        Like reference posters: 'ඉක්මන් කරන්න' / 'GRAB THE DEAL' as prominent text."""
        if not cta_text or not cta_text.strip():
            return ""
        
        shadow = "3px 3px 12px rgba(0,0,0,0.9), 0 0 25px rgba(0,0,0,0.4)"
        
        return f"""
        <div class="urgency-text" style="
            font-size: {int(34 * font_scale)}px;
            color: #FFD700;
            text-shadow: {shadow};
            margin-top: {int(8 * font_scale)}px;
            letter-spacing: 2px;
            text-transform: uppercase;
            text-align: center;
            width: 100%;
        ">{self._escape_html(cta_text)}</div>"""
    
    def _season_badge_html(
        self,
        season: str,
        color: str,
        font_scale: float,
        dark_bg: bool = False,
        centered: bool = False
    ) -> str:
        """Generate a season/festival badge HTML element"""
        if not season or not season.strip():
            return ""
        
        # Season display names and icons (using Unicode symbols, not emojis)
        season_display = {
            "christmas": ("CHRISTMAS SALE", "★"),
            "new year": ("NEW YEAR SALE", "★"),
            "valentine": ("VALENTINE'S SALE", "♥"),
            "avurudu": ("AVURUDU SALE", "★"),
            "easter": ("EASTER SALE", "★"),
            "ramadan": ("RAMADAN SALE", "★"),
            "summer": ("SUMMER SALE", "★"),
            "black friday": ("BLACK FRIDAY", "●"),
            "cyber monday": ("CYBER MONDAY", "●"),
            "back to school": ("BACK TO SCHOOL", "★"),
        }
        
        display_name = season.upper() + " SALE"
        icon = "★"
        for key, (name, sym) in season_display.items():
            if key in season.lower():
                display_name = name
                icon = sym
                break
        
        bg_color = color
        text_color = "#fff"
        if not dark_bg:
            # On light background, use colored badge
            bg_color = color
            text_color = "#fff"
        else:
            # On dark background, use accent-colored badge
            bg_color = color
            text_color = "#fff"
        
        align = "text-align: center;" if centered else ""
        
        return f"""
        <div style="
            display: inline-block;
            background: {bg_color};
            color: {text_color};
            font-size: {12 * font_scale}px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: {6 * font_scale}px {16 * font_scale}px;
            border-radius: {4 * font_scale}px;
            margin-bottom: {12 * font_scale}px;
            {align}
        ">{icon} {self._escape_html(display_name)}</div>"""
    
    def _discount_html(
        self,
        discount: str,
        color: str,
        font_scale: float,
        shadow: str = "",
        centered: bool = False
    ) -> str:
        """Legacy method — redirects to _big_discount_html"""
        return self._big_discount_html(discount, color, font_scale)
    
    def _footer_html(self, phone_number: str, business_name: str) -> str:
        """Generate footer bar HTML with phone icon"""
        if not phone_number and not business_name:
            return ""
        
        # Phone icon SVG (inline, minimalistic)
        phone_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>'
        
        phone_html = f'<span class="footer-phone">{phone_icon}{self._escape_html(phone_number)}</span>' if phone_number else '<span></span>'
        business_html = f'<span class="footer-business">{self._escape_html(business_name)}</span>' if business_name else '<span></span>'
        
        return f"""
    <div class="footer-bar">
        {phone_html}
        {business_html}
    </div>"""
    
    def _screenshot_html(
        self,
        html: str,
        width: int,
        height: int,
        product_name: str,
        size: str
    ) -> Optional[str]:
        """
        Take screenshot of HTML using Playwright/Chromium.
        
        Uses a thread pool to avoid conflict with FastAPI's asyncio event loop
        (Playwright sync API cannot run inside an async context directly).
        
        This is where HarfBuzz shaping happens:
        Chromium's text rendering pipeline uses HarfBuzz to:
        1. Process OpenType GSUB tables
        2. Apply Sinhala-specific shaping rules
        3. Handle virama + ZWJ conjunct formation
        4. Reorder vowel signs
        5. Substitute ligature glyphs
        """
        try:
            # Write HTML to temp file
            temp_dir = tempfile.mkdtemp()
            html_path = os.path.join(temp_dir, "poster.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Generate output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = product_name.replace(' ', '_').replace('/', '_')[:30]
            filename = f"poster_{size}_{safe_name}_{timestamp}.png"
            output_path = str(self.output_dir / filename)
            
            # Run Playwright in a separate thread to avoid asyncio conflict
            def _run_playwright():
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',  # Required for containers (HF Spaces, Docker)
                            '--font-render-hinting=none',  # Better font rendering
                        ]
                    )
                    
                    page = browser.new_page(
                        viewport={"width": width, "height": height},
                        device_scale_factor=2  # 2x for high-resolution output
                    )
                    
                    # Navigate to HTML file
                    page.goto(f"file:///{html_path.replace(os.sep, '/')}")
                    
                    # Wait for fonts to load
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(500)  # Extra wait for font rendering
                    
                    # Screenshot
                    page.screenshot(
                        path=output_path,
                        full_page=False,
                        type="png"
                    )
                    
                    browser.close()
                return True
            
            # Execute in thread pool to avoid asyncio event loop conflict
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_playwright)
                future.result(timeout=30)  # 30 second timeout
            
            # Cleanup temp file
            try:
                os.remove(html_path)
                os.rmdir(temp_dir)
            except Exception:
                pass
            
            print(f"   ✅ HTML poster rendered: {output_path}")
            print(f"   📐 Resolution: {width * 2}x{height * 2}px (2x retina)")
            return output_path
        
        except Exception as e:
            print(f"   ❌ HTML rendering failed: {e}")
            import traceback
            traceback.print_exc()
            return None


# ============================================
# Singleton
# ============================================
_renderer = None


def get_html_renderer() -> Optional[HtmlPosterRenderer]:
    """Get or create HTML poster renderer"""
    global _renderer
    if _renderer is None:
        _renderer = HtmlPosterRenderer()
    return _renderer


# ============================================
# Test
# ============================================
if __name__ == "__main__":
    renderer = HtmlPosterRenderer()
    
    # Test with Sinhala content
    result = renderer.render_poster(
        product_name="Robot Vacuum",
        content="නත්තල් සමය විශේෂ දීමනාව! 🎄 Robot Vacuum එක දැන් 20% වට්ටමක්! ක්‍රිස්මස් gift එකට perfect! 🎁 Limited time only! දැන්ම ඇණවුම් කරන්න! 📞",
        size="facebook",
        discount="20% OFF",
        business_name="SINGER",
        phone_number="011 5 400 400",
        season="Christmas",
        template_style="left_panel"
    )
    
    if result:
        print(f"\n✅ Test poster generated: {result}")
    else:
        print("\n❌ Test failed")
