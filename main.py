from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
from typing import Optional, List

# Import our FREE LOCAL AI modules (kept for fine-tuned model pipeline)
# These require transformers/torch - only available when USE_FINETUNED is enabled
try:
    from local_content_generator import get_generator
    from enhanced_content_generator import get_enhanced_generator
    from local_image_generator import get_image_generator
    from gemini_polish import get_polisher
    from auto_image_generator import AutoImageGenerator
    from create_marketing_posters import MarketingPosterCreator
    HAS_LOCAL_MODELS = True
except Exception as e:
    print(f"⚠️ Local model modules not available: {e}")
    HAS_LOCAL_MODELS = False
    get_generator = None
    get_enhanced_generator = None
    get_image_generator = None
    get_polisher = None
    AutoImageGenerator = None
    MarketingPosterCreator = None

# These only need requests/json - no transformers required
try:
    from smart_poster_generator import SmartPosterGenerator
    from create_complete_poster import create_complete_poster
except Exception as e:
    print(f"⚠️ Poster utility modules not available: {e}")
    SmartPosterGenerator = None
    create_complete_poster = None

# NEW: Import Hybrid AI + HarfBuzz pipeline modules
try:
    from gemini_content_generator import get_gemini_generator
    from sinhala_shaping_engine import get_shaping_engine
    from html_poster_renderer import get_html_renderer
    HAS_GEMINI_PIPELINE = True
except Exception as e:
    print(f"⚠️ Gemini pipeline modules not available: {e}")
    HAS_GEMINI_PIPELINE = False
    get_gemini_generator = None
    get_shaping_engine = None
    get_html_renderer = None

from config import config

app = FastAPI(title="FREE LOCAL AI Content Generator")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models on startup (lazy loading)
content_generator = None
enhanced_generator = None
image_generator = None
gemini_polisher = None
auto_image_gen = None
poster_creator = None
stability_poster_gen = None

# NEW: Hybrid AI + HarfBuzz pipeline components
gemini_generator = None
sinhala_engine = None
html_renderer = None

# Configuration
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__)) or os.getcwd()

# Ensure required directories exist
os.makedirs(os.path.join(PROJECT_DIR, "final_posters"), exist_ok=True)
os.makedirs(os.path.join(PROJECT_DIR, "generated_backgrounds"), exist_ok=True)

# Serve generated posters as static files
# e.g. GET http://localhost:8000/final_posters/poster_facebook_xxx.png
app.mount(
    "/final_posters",
    StaticFiles(directory=os.path.join(PROJECT_DIR, "final_posters")),
    name="posters",
)

# Request models
class TextGenerationRequest(BaseModel):
    product_name: str
    description: str
    tone: str = "professional"
    language: str = "english"  # "english", "sinhala", or "both"
    season: str = ""  # Optional: Christmas, New Year, Valentine, Avurudu, etc.
    discount: str = ""  # Optional: 20%, up to 60% OFF, etc.

class PosterGenerationRequest(BaseModel):
    content: str
    product_name: str = ""

class SmartPosterRequest(BaseModel):
    product_name: str
    description: Optional[str] = ""  # Built description from tags
    tags: Optional[List[str]] = []  # List of tag strings from frontend
    tone: str = "professional"
    language: str = "english"
    season: Optional[str] = ""  # Optional season/festival
    discount: Optional[str] = ""  # Optional discount
    business_name: Optional[str] = ""  # Optional business name (right bottom)
    phone_number: Optional[str] = ""  # Optional phone number (left bottom)
    size: Optional[str] = "facebook"  # Poster size
    pipeline: Optional[str] = ""  # "gemini+harfbuzz" or "finetuned+pillow" (auto if empty)
    template_style: Optional[str] = None  # "bold_impact" | "elegant_sale" | "dramatic_gradient" | None (random)

class RenderPosterOnlyRequest(BaseModel):
    """Re-render an already-generated poster for a new size/style — skips Gemini API call."""
    product_name: str          # display product name (already extracted from [PRODUCT_SI])
    structured_content: str    # shaped content WITH [HEADING]/[BODY] markers intact
    background_path_raw: Optional[str] = None   # absolute OS path to background image
    size: str = "facebook"
    template_style: Optional[str] = None
    discount: Optional[str] = ""
    business_name: Optional[str] = ""
    phone_number: Optional[str] = ""
    season: Optional[str] = ""

@app.on_event("startup")
async def startup_event():
    """Load AI models on server startup"""
    global content_generator, image_generator
    print("🚀 Starting FREE LOCAL AI Content Generator...")
    print(f"📁 Models will be cached in: {config.MODEL_CACHE_DIR}")
    print("⏳ Loading models (first time may take a few minutes)...\n")
    
    # Load generators (lazy loading - only when first request comes)
    # This prevents slow startup
    print("✅ Server ready! Models will load on first request.")

@app.post("/generate_text")
async def generate_text(request: TextGenerationRequest):
    """
    Generate marketing content using research pipeline:
    Stage 1: Fine-tuned GPT-2 generates initial content
    Stage 2: Gemini polishes and enhances (if enabled)
    Stage 3: Hashtags generated (if Gemini enabled)
    """
    global content_generator, gemini_polisher
    
    try:
        # Load generator on first request
        if content_generator is None:
            print("📥 Loading content generation models...")
            content_generator = get_generator()
        
        # Load Gemini polisher if enabled
        if gemini_polisher is None and config.USE_GEMINI_POLISH:
            print("📥 Loading Gemini polisher...")
            gemini_polisher = get_polisher()
        
        # STAGE 1: Generate with GPT-2 (base or fine-tuned)
        print(f"🤖 Generating {request.language} content with GPT-2...")
        
        if request.language == "english":
            gpt2_content = content_generator.generate_english(
                request.product_name,
                request.description,
                request.tone
            )
            lang_for_polish = "english"
        
        elif request.language == "sinhala":
            gpt2_content = content_generator.generate_sinhala(
                request.product_name,
                request.description,
                request.tone
            )
            lang_for_polish = "sinhala"
        
        else:  # both
            result = content_generator.generate_bilingual(
                request.product_name,
                request.description,
                request.tone
            )
            gpt2_content = result["combined"]
            lang_for_polish = "mixed"
        
        # STAGE 2 & 3: Polish with Gemini (if enabled)
        if gemini_polisher and config.USE_GEMINI_POLISH:
            print("✨ Polishing content with Gemini...")
            
            polish_result = gemini_polisher.polish_with_hashtags(
                content=gpt2_content,
                language=lang_for_polish,
                tone=request.tone,
                product_name=request.product_name,
                num_hashtags=5,
                season=request.season,
                discount=request.discount,
                tags=request.description
            )
            
            final_content = polish_result["polished_content"]
            hashtags = polish_result["hashtags"]
            full_post = polish_result["full_post"]
            
            return JSONResponse({
                "success": True,
                "content": final_content,
                "full_post": full_post,
                "hashtags": hashtags,
                "gpt2_draft": gpt2_content,  # Raw fine-tuned output
                "gemini_polished": final_content,  # Enhanced version
                "language": request.language,
                "product_name": request.product_name,
                "description": request.description,
                "season": request.season,
                "discount": request.discount,
                "pipeline": "gpt2+gemini",
                "model_used": "fine-tuned" if content_generator.is_finetuned else "baseline"
            })
        else:
            # No Gemini polish - return GPT-2 output directly
            return JSONResponse({
                "success": True,
                "content": gpt2_content,
                "full_post": gpt2_content,
                "hashtags": [],
                "language": request.language,
                "product_name": request.product_name,
                "description": request.description,
                "pipeline": "gpt2_only",
                "model_used": "fine-tuned" if content_generator.is_finetuned else "baseline"
            })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_poster")
async def generate_poster(request: PosterGenerationRequest):
    """Generate poster using FREE LOCAL image generator"""
    global image_generator
    
    try:
        # Load image generator on first request
        if image_generator is None:
            print("📥 Loading image generation system...")
            image_generator = get_image_generator()
        
        # Generate poster
        poster_path = image_generator.generate_poster(
            content=request.content,
            product_name=request.product_name
        )
        
        # Return the image file
        if os.path.exists(poster_path):
            return FileResponse(
                poster_path,
                media_type="image/png",
                filename="poster.png"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate poster")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FALLBACK CONTENT GENERATOR (when Gemini API fails)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _generate_fallback_content(
    product_name: str,
    language: str,
    tone: str = "professional",
    season: str = "",
    discount: str = ""
) -> str:
    """
    Generate template-based content when Gemini API is unavailable.
    Uses pre-written Sinhala/English templates with dynamic substitution.
    """
    discount_text = f"\n{discount} OFF!" if discount else ""
    season_text = f"{season} " if season else ""
    
    # Season-specific Sinhala hooks
    season_sinhala = {
        "christmas": "නත්තලේ අසිරිය සමඟින්",
        "new year": "අලුත් අවුරුද්දේ සුභ පැතුම් සමඟ",
        "valentine": "ආදරයේ උත්සවය සමඟින්",
        "avurudu": "සිංහල හා දෙමළ අලුත් අවුරුදු සැමරුම සමඟ",
        "sinhala": "සිංහල හා දෙමළ අලුත් අවුරුදු සැමරුම සමඟ",
        "thai pongal": "තෛ පොංගල් සැමරුම සමඟ",
        "vesak": "වෙසක් පොහොය සුභ අවස්ථාවේ",
        "poson": "පොසොන් පොහොය සිහිවීමෙහිලා",
        "deepavali": "දීපාවලි ආලෝකෝත්සවය සමඟ",
        "easter": "පාස්කු සැමරුම සමඟින්",
        "black friday": "Black Friday මහා විකුණුම",
    }
    season_english = {
        "christmas": "Celebrate Christmas with",
        "new year": "Ring in the New Year with",
        "valentine": "This Valentine's, Gift",
        "avurudu": "Celebrate Sinhala & Tamil New Year with",
        "sinhala": "Celebrate Sinhala & Tamil New Year with",
        "thai pongal": "Celebrate Thai Pongal with",
        "vesak": "This Vesak, Discover",
        "poson": "This Poson, Explore",
        "deepavali": "Celebrate Deepavali with",
        "easter": "This Easter, Discover",
        "black friday": "Black Friday Mega Deals on",
    }
    
    season_hook_si = "සුවිශේෂී දීමනා"
    season_hook_en = "Exclusive Deals on"
    if season:
        for key, val in season_sinhala.items():
            if key in season.lower():
                season_hook_si = val
                season_hook_en = season_english.get(key, f"{season} Exclusive Deals on")
                break
    
    if language == "sinhala":
        templates = [
            f"[HEADING]\n{season_hook_si} නවීනතම {product_name} අත්දැකීමක්!\n"
            f"[BODY]\nසීමිත කාලයක් සඳහා පමණි. ඔබේ ජීවිතය වෙනස් කරන නවීන අත්දැකීම ලබාගන්න.\n"
            f"[FEATURES]\nඉහළ ගුණාත්මකභාවය, නවතම නිර්මාණ\nවටිනාකමට සරිලන මිල\nදිවයින පුරා බෙදාහැරීම ලබාගත හැක\n"
            f"[CTA]\nදැන්ම පිවිසෙන්න",

            f"[HEADING]\n{season_hook_si} {product_name} — ශ්‍රේෂ්ඨ දීමනාව!\n"
            f"[BODY]\nඋසස්ම ගුණාත්මකභාවය සහ නවීන නිර්මාණ ඔබේ ජීවිතයට ආලෝකය ගෙනෙයි.\n"
            f"[FEATURES]\nශ්‍රේෂ්ඨ ජනප්‍රිය නිෂ්පාදනය\nනොමිලේ දිවයින පුරා බෙදාහැරීම\nසීමිත තොගයක් — ඉක්මනින් ලබාගන්න\n"
            f"[CTA]\nඅද දිනයේම ඔබේ {product_name} තෝරාගන්න",
        ]
    elif language == "both":
        templates = [
            f"[HEADING]\n{season_hook_si} නවීනතම {product_name} අත්දැකීමක්!\n"
            f"[BODY]\nExclusive Deals for a Limited Time Only. ඉහළ ගුණාත්මකභාවය, නවතම නිර්මාණ.\n"
            f"[FEATURES]\nPremium Quality නවතම නිර්මාණ\nනොමිලේ දිවයින පුරා Delivery\nවටිනාකමට සරිලන මිල\n"
            f"[CTA]\nදැන්ම පිවිසෙන්න",

            f"[HEADING]\n{season_hook_en} {product_name}!\n"
            f"[BODY]\nසුවිශේෂී දීමනා සීමිත කාලයක් පමණි. Elevate Your Lifestyle Today.\n"
            f"[FEATURES]\nඋසස්ම ගුණාත්මකභාවය සහ නවීන නිර්මාණ\nIsland-wide Delivery Available\nBest Value for Your Money\n"
            f"[CTA]\nDon't Miss Out — Shop Now",
        ]
    else:  # english
        templates = [
            f"[HEADING]\n{season_hook_en} the Perfect {product_name}!\n"
            f"[BODY]\nExclusive deals for a limited time only. Premium quality at unbeatable prices.\n"
            f"[FEATURES]\nPremium Quality, Latest Designs\nUnbeatable Value for Your Money\nIsland-wide Delivery Available\n"
            f"[CTA]\nVisit Our Showroom Today",
            
            f"[HEADING]\nDiscover the Ultimate {product_name} Experience!\n"
            f"[BODY]\n{season_hook_en} {product_name} — trusted by thousands across Sri Lanka.\n"
            f"[FEATURES]\nElevate Your Lifestyle Today\nTrusted by Thousands Island-wide\nLimited Stock — Grab Yours Now\n"
            f"[CTA]\nShop Now Before Stock Runs Out",
        ]
    
    import random
    return random.choice(templates)


def _generate_local_hashtags(product_name: str, language: str, season: str = "") -> list:
    """
    Generate hashtags locally without API call.
    Saves Gemini quota for content generation.
    """
    hashtags = []
    
    # Product-based hashtag — sanitize to alphanumeric only
    if product_name:
        import re as _re
        clean_name = _re.sub(r'[^\w\u0D80-\u0DFF]', '', product_name.replace(" ", ""))
        if clean_name:
            hashtags.append(f"#{clean_name}")
    
    # Season hashtag — sanitize special chars (& etc.) that break hashtags on social platforms
    if season and season.strip():
        import re as _re
        clean_season = _re.sub(r'[^\w]', '', season.replace(" ", "").replace("&", "And"))
        if clean_season:
            hashtags.append(f"#{clean_season}")
    
    # Standard Sri Lankan marketing hashtags
    base_tags = ["#SriLanka", "#LK"]
    
    # Language-specific
    if language in ("sinhala", "both"):
        base_tags.extend(["#SriLankanDeals", "#ShopLK"])
    else:
        base_tags.extend(["#BestDeals", "#ShopNow"])
    
    hashtags.extend(base_tags)
    return hashtags[:5]


@app.post("/api/generate-smart-poster")
async def generate_smart_poster(request: SmartPosterRequest):
    """
    Generate content + contextual poster.
    
    Supports TWO pipelines (configurable):
    
    Pipeline 1 - Gemini + HarfBuzz (NEW - default):
      Gemini API → Sinhala Unicode Validation → HTML/CSS → Playwright/Chromium (HarfBuzz) → PNG
    
    Pipeline 2 - Fine-tuned + Pillow (ORIGINAL - preserved for future use):
      GPT-2/mT5 → Enhanced Generator → Gemini Polish → Pillow Rendering → PNG
    
    Pipeline selection:
      - Auto: Based on config (USE_GEMINI_GENERATION, USE_HTML_RENDERING)
      - Manual: Pass pipeline="gemini+harfbuzz" or pipeline="finetuned+pillow"
    """
    global content_generator, stability_poster_gen, enhanced_generator
    global gemini_generator, sinhala_engine, html_renderer, gemini_polisher
    
    try:
        # Auto-select pipeline based on language and availability
        # Sinhala/bilingual content benefits from HarfBuzz rendering
        # If no pipeline specified, auto-select the best one
        use_gemini = config.USE_GEMINI_GENERATION
        use_html = config.USE_HTML_RENDERING
        
        if request.pipeline:
            # Manual override (kept for backward compatibility / debug)
            if request.pipeline == "gemini+harfbuzz":
                use_gemini = True
                use_html = True
            elif request.pipeline == "finetuned+pillow":
                use_gemini = False
                use_html = False
        else:
            # Auto-select: prefer Gemini+HarfBuzz for Sinhala, use config defaults otherwise
            if request.language in ("sinhala", "both") and HAS_GEMINI_PIPELINE:
                use_gemini = True
                use_html = True
        
        # Convert tags list to comma-separated string
        tags_str = ", ".join(request.tags) if isinstance(request.tags, list) else str(request.tags)
        description = request.description if request.description else tags_str
        
        pipeline_name = ""
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 1: TEXT GENERATION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if use_gemini:
            # ═══ NEW PIPELINE: Gemini API ═══
            print(f"\n🔥 Using Gemini API pipeline for text generation")
            
            if gemini_generator is None:
                from gemini_content_generator import get_gemini_generator
                gemini_generator = get_gemini_generator()
            
            if gemini_generator is None:
                raise HTTPException(status_code=500, detail="Gemini generator not available. Check GEMINI_API_KEY.")
            
            print(f"📝 Generating {request.language} content via Gemini API...")
            
            try:
                if request.language == "english":
                    gpt2_content = gemini_generator.generate_english(
                        product_name=request.product_name,
                        description=description,
                        tone=request.tone,
                        season=request.season or "",
                        discount=request.discount or "",
                        tags=tags_str
                    )
                elif request.language == "sinhala":
                    gpt2_content = gemini_generator.generate_sinhala(
                        product_name=request.product_name,
                        description=description,
                        tone=request.tone,
                        season=request.season or "",
                        discount=request.discount or "",
                        tags=tags_str
                    )
                else:  # both / bilingual
                    gpt2_content = gemini_generator.generate_bilingual(
                        product_name=request.product_name,
                        description=description,
                        tone=request.tone,
                        season=request.season or "",
                        discount=request.discount or "",
                        tags=tags_str
                    )
                
                pipeline_name = "gemini_api"
                print(f"✅ Gemini content ({request.language}): {gpt2_content[:100]}...")
            
            except Exception as gemini_err:
                # Fallback: Generate template-based content when API fails (quota, network, etc.)
                print(f"⚠️ Gemini API failed ({gemini_err.__class__.__name__}), using template fallback...")
                gpt2_content = _generate_fallback_content(
                    product_name=request.product_name,
                    language=request.language,
                    tone=request.tone,
                    season=request.season or "",
                    discount=request.discount or ""
                )
                pipeline_name = "template_fallback"
                print(f"📋 Fallback content ({request.language}): {gpt2_content[:100]}...")
        
        else:
            # ═══ ORIGINAL PIPELINE: Fine-tuned models (preserved) ═══
            print(f"\n📦 Using fine-tuned model pipeline for text generation")
            
            if content_generator is None:
                print("📥 Loading content generator...")
                content_generator = get_generator()
            
            if enhanced_generator is None:
                enhanced_generator = get_enhanced_generator(content_generator)
            
            print(f"✨ Using Enhanced Content Generator...")
            
            if request.language == "english":
                gpt2_content = enhanced_generator.generate_english_enhanced(
                    product_name=request.product_name,
                    description=description,
                    tone=request.tone,
                    season=request.season or "",
                    discount=request.discount or "",
                    tags=tags_str
                )
            elif request.language == "sinhala":
                gpt2_content = enhanced_generator.generate_sinhala_enhanced(
                    product_name=request.product_name,
                    description=description,
                    tone=request.tone,
                    season=request.season or "",
                    discount=request.discount or "",
                    tags=tags_str
                )
            else:  # both
                english_content = enhanced_generator.generate_english_enhanced(
                    product_name=request.product_name,
                    description=description,
                    tone=request.tone,
                    season=request.season or "",
                    discount=request.discount or "",
                    tags=tags_str
                )
                sinhala_content = enhanced_generator.generate_sinhala_enhanced(
                    product_name=request.product_name,
                    description=description,
                    tone=request.tone,
                    season=request.season or "",
                    discount=request.discount or "",
                    tags=tags_str
                )
                gpt2_content = f"{english_content}\n\n{sinhala_content}"
            
            pipeline_name = "finetuned"
            print(f"✅ Enhanced content ({request.language}): {gpt2_content[:100]}...")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2: GEMINI POLISH (only for fine-tuned pipeline)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Skip polishing for Gemini pipeline — generation prompt already produces
        # polished poster-optimized text. This saves 2 API calls per poster.
        # Only polish fine-tuned model output (which benefits significantly from it).
        should_polish = config.USE_GEMINI_POLISH and not use_gemini  # Only for fine-tuned pipeline
        
        if should_polish:
            if gemini_polisher is None:
                gemini_polisher = get_polisher()
            
            if gemini_polisher:
                print(" Polishing with Gemini...")
                polish_result = gemini_polisher.polish_with_hashtags(
                    content=gpt2_content,
                    language=request.language if request.language != "both" else "mixed",
                    tone=request.tone,
                    product_name=request.product_name,
                    num_hashtags=5,
                    season=request.season or "",
                    discount=request.discount or "",
                    tags=tags_str
                )
                final_content = polish_result["polished_content"]
                hashtags = polish_result["hashtags"]
                pipeline_name += " + gemini_polish"
            else:
                final_content = gpt2_content
                hashtags = []
        else:
            final_content = gpt2_content
            # Generate hashtags locally without API call
            hashtags = _generate_local_hashtags(request.product_name, request.language, request.season or "")
            if use_gemini:
                print("⚡ Skipped polish (Gemini output already optimized) — saved 2 API calls")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2.5: STRIP EMOJIS (professional content)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        import re
        def strip_emojis(text):
            """Remove all emoji characters from text, preserving Sinhala ZWJ sequences"""
            # First, protect Sinhala ZWJ sequences by replacing with placeholder
            # Pattern: Sinhala consonant + virama + ZWJ + consonant
            sinhala_zwj_placeholder = "SINHALA_ZWJ_PLACEHOLDER"
            protected = re.sub(
                r'([\u0D9A-\u0DC6]\u0DCA)\u200D([\u0D9A-\u0DC6])',
                r'\1' + sinhala_zwj_placeholder + r'\2',
                text
            )
            
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags
                "\U00002702-\U000027B0"  # dingbats
                "\U000024C2-\U0001F251"  # enclosed characters
                "\U0001f926-\U0001f937"  # hand gestures
                "\U00010000-\U0010ffff"  # supplementary planes
                "\u200d"                 # zero-width joiner (for emoji sequences)
                "\u2640-\u2642"          # gender symbols
                "\u2600-\u26FF"          # misc symbols
                "\u2700-\u27BF"          # dingbats
                "\ufe0f"                 # variation selector
                "\u23f0-\u23fa"          # misc technical
                "\u23e9-\u23ef"          # playback symbols
                "\u231a-\u231b"          # watch/hourglass
                "]+",
                flags=re.UNICODE
            )
            result = emoji_pattern.sub('', protected)
            
            # Restore Sinhala ZWJ sequences
            result = result.replace(sinhala_zwj_placeholder, '\u200D')
            
            # Clean up extra spaces from emoji removal
            result = re.sub(r'  +', ' ', result)
            result = re.sub(r' \n', '\n', result)
            result = re.sub(r'\n ', '\n', result)
            return result.strip()
        
        final_content = strip_emojis(final_content)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2.6: EXTRACT [PRODUCT_SI] — Sinhala product name
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Gemini outputs [PRODUCT_SI] for Sinhala/bilingual content — the Sinhala
        # translation of the English product name. Extract it and use it as the
        # poster's displayed product name, then remove from content body.
        display_product_name = request.product_name  # default: original English
        product_si_match = re.search(
            r'\[PRODUCT_SI\]\s*\n?(.*?)(?=\[(?:HEADING|BODY|FEATURES|CTA)\]|\Z)',
            final_content, re.DOTALL | re.IGNORECASE
        )
        if product_si_match:
            extracted = product_si_match.group(1).strip().split('\n')[0].strip()
            if extracted:
                display_product_name = extracted
                print(f"   📝 Sinhala product name: {display_product_name}")
            # Strip [PRODUCT_SI] section from content
            final_content = re.sub(
                r'\[PRODUCT_SI\]\s*\n?.*?(?=\[(?:HEADING|BODY|FEATURES|CTA)\]|\Z)',
                '', final_content, flags=re.DOTALL | re.IGNORECASE
            ).strip()
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Always run shaping engine - it normalizes text for correct rendering
        if sinhala_engine is None:
            sinhala_engine = get_shaping_engine()
        
        shaped_content = sinhala_engine.process(final_content)
        
        # Get text analysis for response
        text_analysis = sinhala_engine.analyze_text(shaped_content)
        has_sinhala = text_analysis["sinhala_chars"] > 0
        
        if has_sinhala:
            print(f"🔤 Sinhala shaping applied:")
            print(f"   Consonants: {text_analysis['consonants']}, Viramas: {text_analysis['viramas']}")
            print(f"   ZWJ: {text_analysis['zwj_count']}, Rakaransaya: {text_analysis['rakaransaya_sequences']}")
            pipeline_name += " + sinhala_shaping"
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 4: POSTER RENDERING
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        poster_path = None
        background_path = None
        
        # Step 4a: Generate background (shared by both pipelines)
        os.environ["STABILITY_API_KEY"] = config.STABILITY_API_KEY
        
        try:
            if stability_poster_gen is None:
                stability_poster_gen = SmartPosterGenerator(api_choice="stability")
                stability_poster_gen.api_key = config.STABILITY_API_KEY
            
            # Include English description/tags so category detection works even when
            # product_name is in Sinhala script (English keywords won't match Sinhala text)
            english_context_hint = " ".join(filter(None, [
                request.description or "",
                ", ".join(request.tags) if isinstance(request.tags, list) else str(request.tags or ""),
            ]))
            context = stability_poster_gen.detect_content_context(
                shaped_content + " " + english_context_hint,
                request.product_name,
                user_season=request.season
            )
            
            # Try to generate AI background
            prompt = stability_poster_gen.generate_background_prompt(context, request.product_name)
            bg_result = stability_poster_gen.generate_with_stability(prompt)
            
            if bg_result.get("success"):
                background_path = bg_result.get("image_path")
                print(f"   ✅ AI background generated: {background_path}")
        except Exception as bg_error:
            print(f"   ⚠️ Background generation failed: {bg_error}")
            context = {"season": "general", "category": "general", "mood": "professional"}
        
        # Step 4b: Render poster
        if use_html:
            # ═══ NEW PIPELINE: HTML/CSS + Playwright/HarfBuzz ═══
            print(f"🌐 Rendering poster with HTML/CSS + Chromium/HarfBuzz...")
            
            if html_renderer is None:
                html_renderer = get_html_renderer()
            
            chosen_template_style = request.template_style or None
            poster_path = html_renderer.render_poster(
                product_name=display_product_name,
                content=shaped_content,
                background_path=background_path,
                template_style=chosen_template_style,
                size=request.size or "facebook",
                discount=request.discount or "",
                business_name=request.business_name or "",
                phone_number=request.phone_number or "",
                season=request.season or ""
            )
            
            pipeline_name += " + harfbuzz_html"
        
        if not poster_path:
            # ═══ FALLBACK / ORIGINAL: Pillow rendering ═══
            print(f"🖼️ Rendering poster with Pillow (fallback)...")
            
            try:
                poster_path = create_complete_poster(
                    product_name=display_product_name,
                    content=shaped_content,
                    tags=tags_str,
                    background_path=background_path,
                    season=request.season,
                    discount=request.discount,
                    business_name=request.business_name,
                    phone_number=request.phone_number
                )
                pipeline_name += " + pillow"
            except Exception as pillow_error:
                print(f"⚠️ Pillow rendering also failed: {pillow_error}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 5: RETURN RESPONSE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        response_data = {
            "success": True,
            "content": re.sub(r'\[(HEADING|BODY|FEATURES|CTA)\]\s*\n?', '', shaped_content).strip(),
            "structured_content": shaped_content,  # Keeps [HEADING]/[BODY] markers — used by render-only
            "hashtags": hashtags,
            "product_name": request.product_name,
            "display_product_name": display_product_name,  # Extracted Sinhala product name
            "language": request.language,
            "background_path_raw": background_path,  # Absolute OS path — used by render-only
            "template_style_used": request.template_style,  # None means random was chosen by renderer
            "pipeline": pipeline_name,
            "shaping_info": {
                "has_sinhala": has_sinhala,
                "zwj_count": text_analysis.get("zwj_count", 0),
                "rakaransaya_count": text_analysis.get("rakaransaya_sequences", 0),
                "yansaya_count": text_analysis.get("yansaya_sequences", 0),
                "nfc_normalized": True,  # Always normalised by sinhala_engine.process()
            },
        }
        
        if poster_path:
            # Return a relative URL path that matches the /final_posters static mount
            poster_filename = os.path.basename(poster_path)
            response_data["poster_path"] = f"final_posters/{poster_filename}"
            response_data["poster_url"] = f"/final_posters/{poster_filename}"
        else:
            response_data["poster_path"] = None
            response_data["poster_url"] = None
            response_data["error"] = "Poster rendering failed - content generated successfully"
        
        if context:
            response_data["context"] = context
        
        return JSONResponse(response_data)
        
    except Exception as e:
        print(f"❌ Error in generate_smart_poster: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = str(e) if str(e) else "Unknown error during poster generation"
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/api/render-poster-only")
async def render_poster_only(request: RenderPosterOnlyRequest):
    """
    Render a poster from already-generated content — skips Gemini API and background generation.
    Used by the frontend to create multiple poster sizes from a single Gemini call.
    Accepts structured_content (with [HEADING]/[BODY] markers) from a previous /api/generate-smart-poster response.
    """
    global html_renderer, sinhala_engine

    try:
        if html_renderer is None:
            html_renderer = get_html_renderer()

        if html_renderer is None:
            raise HTTPException(status_code=500, detail="HTML renderer not available")

        poster_path = html_renderer.render_poster(
            product_name=request.product_name,
            content=request.structured_content,
            background_path=request.background_path_raw,
            template_style=request.template_style or None,
            size=request.size or "facebook",
            discount=request.discount or "",
            business_name=request.business_name or "",
            phone_number=request.phone_number or "",
            season=request.season or "",
        )

        if poster_path:
            poster_filename = os.path.basename(poster_path)
            return JSONResponse({
                "success": True,
                "poster_path": f"final_posters/{poster_filename}",
                "poster_url": f"/final_posters/{poster_filename}",
                "size": request.size,
                "template_style": request.template_style,
            })
        else:
            raise HTTPException(status_code=500, detail="Poster rendering failed")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in render_poster_only: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e) or "Render failed")


@app.post("/api/generate-with-image")
async def generate_with_image(request: TextGenerationRequest):
    """
    Generate marketing content + matching AI image poster
    NEW: Complete workflow with automated image generation
    """
    global content_generator, gemini_polisher, auto_image_gen, poster_creator
    
    try:
        # Initialize generators if needed
        if auto_image_gen is None:
            auto_image_gen = AutoImageGenerator()
        if poster_creator is None:
            poster_creator = MarketingPosterCreator()
        
        # STEP 1: Generate text content (same as /api/generate)
        content_response = await generate_text(request)
        content_response = content_response.body.decode('utf-8')
        import json
        content_response = json.loads(content_response)
        
        # STEP 2: Generate background image based on content
        print(f" Generating AI image for: {request.product_name}")
        
        # Create entry for image generation
        entry = {
            'product_service': request.product_name,
            'content_type': 'Social Media Post',
            'target_audience': 'General Public',
            'tone': request.tone,
            'language': request.language,
            'content': content_response['polished_content']
        }
        
        # Generate background image
        bg_image_path = auto_image_gen.generate_from_content(entry, index=0)
        
        if not bg_image_path:
            raise HTTPException(status_code=500, detail="Image generation failed")
        
        # STEP 3: Add text overlay (your content) to image
        print("📝 Adding text overlay...")
        final_poster_path = poster_creator.process_content_entry(bg_image_path, entry, index=0)
        
        # Return content + image path
        return {
            **content_response,
            "image_path": final_poster_path.replace("\\", "/"),
            "image_url": f"/static/{final_poster_path.replace(chr(92), '/')}"
        }
        
    except Exception as e:
        print(f"❌ Error in generate_with_image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models_loaded": {
            "content_generator": content_generator is not None,
            "gemini_generator": gemini_generator is not None,
            "image_generator": image_generator is not None,
            "gemini_polisher": gemini_polisher is not None,
            "sinhala_engine": sinhala_engine is not None,
            "html_renderer": html_renderer is not None,
        },
        "config": {
            "english_model": config.ENGLISH_MODEL,
            "sinhala_model": config.SINHALA_MODEL,
            "use_finetuned": config.USE_FINETUNED,
            "use_gemini_generation": config.USE_GEMINI_GENERATION,
            "use_html_rendering": config.USE_HTML_RENDERING,
            "use_gemini_polish": config.USE_GEMINI_POLISH,
            "gemini_model": config.GEMINI_MODEL,
            "use_gpu": config.USE_GPU,
            "use_ai_images": config.USE_IMAGE_AI
        },
        "pipeline": {
            "active": "gemini+harfbuzz" if config.USE_GEMINI_GENERATION else "finetuned+pillow",
            "text_generation": "Gemini API" if config.USE_GEMINI_GENERATION else (
                "GPT-2 (fine-tuned)" if config.USE_FINETUNED else "GPT-2 (baseline)"
            ),
            "sinhala_shaping": "NFC + ZWJ + Virama validation",
            "poster_rendering": "HTML/CSS + Chromium/HarfBuzz" if config.USE_HTML_RENDERING else "Pillow",
            "polish": "Gemini polish" if config.USE_GEMINI_POLISH else "No polish",
            "backgrounds": "Stability AI" if config.USE_STABILITY_BACKGROUNDS else "Gradient fallback"
        }
    }

# Serve generated backgrounds as static files (final_posters already mounted above)
app.mount("/generated_backgrounds", StaticFiles(directory=os.path.join(PROJECT_DIR, "generated_backgrounds")), name="generated_backgrounds")

@app.get("/")
async def read_root():
    """Serve the frontend"""
    return FileResponse(os.path.join(PROJECT_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║     HYBRID AI + HarfBuzz CONTENT GENERATOR                   ║
    ║   🇬🇧 English + 🇱🇰 Sinhala Content Generation               ║
    ║    Poster Creation (HTML/CSS + HarfBuzz Shaping)           ║
    ║    Unicode-Aware Sinhala Rendering Pipeline                ║
    ╚══════════════════════════════════════════════════════════════╝
    
    📍 Server: http://localhost:{config.PORT}
    
    🔧 Active Pipeline:
       Text: {"Gemini API" if config.USE_GEMINI_GENERATION else "Fine-tuned GPT-2/mT5"}
       Shaping: Sinhala Unicode NFC + ZWJ + Virama
       Rendering: {"HTML/CSS + Chromium/HarfBuzz" if config.USE_HTML_RENDERING else "Pillow"}
       Polish: {"Gemini" if config.USE_GEMINI_POLISH else "Disabled"}
    
    📦 Fine-tuned models: PRESERVED (set USE_GEMINI_GENERATION=false to use)
    💾 Cache: {config.MODEL_CACHE_DIR}
    """)
    
    uvicorn.run(app, host=config.HOST, port=config.PORT)
