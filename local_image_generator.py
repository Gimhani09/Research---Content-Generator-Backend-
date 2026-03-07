"""
FREE LOCAL Image Generation
Option 1: Stable Diffusion (AI-generated images)
Option 2: HTML2Image (Text-based posters)
"""
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import torch
from PIL import Image, ImageDraw, ImageFont
try:
    from html2image import Html2Image
    HAS_HTML2IMAGE = True
except (ImportError, SyntaxError):
    HAS_HTML2IMAGE = False
    print("⚠️ html2image not available (optional)")
from jinja2 import Environment, FileSystemLoader
import os
import uuid
from config import config

class LocalImageGenerator:
    def __init__(self):
        self.device = "cuda" if config.USE_GPU and torch.cuda.is_available() else "cpu"
        self.use_ai_images = config.USE_IMAGE_AI
        
        if self.use_ai_images:
            print("📥 Loading Stable Diffusion model (this may take a few minutes)...")
            self.sd_pipe = StableDiffusionPipeline.from_pretrained(
                config.IMAGE_MODEL,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                cache_dir=config.MODEL_CACHE_DIR
            )
            self.sd_pipe = self.sd_pipe.to(self.device)
            
            # Use faster scheduler
            self.sd_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.sd_pipe.scheduler.config
            )
            
            # Enable memory optimizations
            if self.device == "cuda":
                self.sd_pipe.enable_attention_slicing()
                
            print("✅ Stable Diffusion loaded!")
        else:
            print("📝 Using simple poster generation")
            self.hti = None
            if HAS_HTML2IMAGE:
                try:
                    self.hti = Html2Image()
                    self.hti.output_path = os.path.dirname(__file__)
                except Exception as e:
                    print(f"⚠️ Html2Image initialization failed: {e}")
    
    def generate_ai_image(self, prompt: str, negative_prompt: str = None) -> str:
        """Generate image using Stable Diffusion"""
        if not self.use_ai_images:
            raise ValueError("AI image generation is disabled. Set USE_IMAGE_AI=true in .env")
        
        if negative_prompt is None:
            negative_prompt = "low quality, blurry, distorted, ugly, bad anatomy"
        
        print(f"🎨 Generating AI image: {prompt[:50]}...")
        
        with torch.no_grad():
            image = self.sd_pipe(
                prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=config.IMAGE_STEPS,
                guidance_scale=7.5,
                height=768,
                width=768
            ).images[0]
        
        # Save image
        filename = f"ai_poster_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        image.save(filepath)
        
        print(f"✅ Image saved: {filename}")
        return filepath
    
    def generate_text_poster(self, content: str, product_name: str = "") -> str:
        """Generate HTML-based text poster"""
        
        # Split content for better layout
        lines = content.split(".")
        headline = lines[0].strip() if lines else content[:50]
        body = ". ".join([line.strip() for line in lines[1:3] if line.strip()])
        
        # HTML template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;700&family=Poppins:wght@400;700;900&display=swap');
                
                body {{
                    margin: 0;
                    padding: 0;
                    width: 1200px;
                    height: 630px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: 'Noto Sans Sinhala', 'Poppins', sans-serif;
                }}
                
                .container {{
                    width: 1100px;
                    height: 530px;
                    background: white;
                    border-radius: 20px;
                    padding: 50px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }}
                
                .headline {{
                    font-size: 48px;
                    font-weight: 900;
                    color: #2d3748;
                    margin-bottom: 30px;
                    line-height: 1.2;
                }}
                
                .body {{
                    font-size: 28px;
                    color: #4a5568;
                    line-height: 1.6;
                    margin-bottom: 40px;
                }}
                
                .cta {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px 50px;
                    border-radius: 50px;
                    font-size: 24px;
                    font-weight: 700;
                    text-decoration: none;
                    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
                }}
                
                .brand {{
                    position: absolute;
                    bottom: 40px;
                    right: 60px;
                    font-size: 20px;
                    color: #a0aec0;
                    font-weight: 700;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="headline">{headline}</div>
                <div class="body">{body if body else ''}</div>
                <a href="#" class="cta">Learn More →</a>
                <div class="brand">{product_name if product_name else 'Your Brand'}</div>
            </div>
        </body>
        </html>
        """
        
        # Generate image from HTML
        filename = f"poster_{uuid.uuid4().hex[:8]}.png"
        
        self.hti.screenshot(
            html_str=html_content,
            save_as=filename,
            size=(1200, 630)
        )
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        print(f"✅ Poster saved: {filename}")
        return filepath
    
    def generate_poster(self, content: str, product_name: str = "", use_ai: bool = None) -> str:
        """Generate poster (AI or text-based)"""
        
        if use_ai is None:
            use_ai = self.use_ai_images
        
        if use_ai and self.use_ai_images:
            # Create AI image prompt from content
            prompt = f"Professional marketing poster for {product_name}, modern design, clean layout, product photography, high quality, 4k"
            return self.generate_ai_image(prompt)
        else:
            return self.generate_text_poster(content, product_name)

# Singleton
_image_generator = None

def get_image_generator():
    global _image_generator
    if _image_generator is None:
        _image_generator = LocalImageGenerator()
    return _image_generator

# Test
if __name__ == "__main__":
    gen = LocalImageGenerator()
    
    test_content = "අපගේ නව කිරිපිටි නිෂ්පාදනය. ඉහළ කැල්සියම් සහිත, ළමුන් සඳහා විශේෂ. දැන්ම ඔබේ ළඟම සුපිරි වෙළඳසැලෙන් ලබා ගන්න."
    
    print("\n📸 Generating text-based poster...")
    poster_path = gen.generate_text_poster(test_content, "Premium Milk Powder")
    print(f"Saved to: {poster_path}")
