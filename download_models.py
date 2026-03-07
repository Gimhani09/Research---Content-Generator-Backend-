"""
Download Models Script
Properly downloads all required models with resume capability
"""
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
import torch

def download_models():
    """Download all required models"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         MODEL DOWNLOAD SCRIPT                                ║
    ║  Downloads all required models with auto-resume              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Create cache directory
    cache_dir = "./models"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Check GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🖥️  Device: {device}")
    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"   GPU: {gpu_name}")
        print(f"   VRAM: {vram:.1f} GB")
    
    models_to_download = [
        ("English Model", "gpt2-medium", "causal"),
        ("Sinhala Model", "google/mt5-base", "seq2seq"),
    ]
    
    for name, model_id, model_type in models_to_download:
        print(f"\n📥 Downloading {name}: {model_id}")
        print(f"   (Files will be cached in: {cache_dir})")
        
        try:
            # Download tokenizer
            print("   ⏳ Downloading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=cache_dir,
                resume_download=True
            )
            print("   ✅ Tokenizer downloaded")
            
            # Download model
            print("   ⏳ Downloading model (this is the large file ~500MB-2GB)...")
            if model_type == "seq2seq":
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_id,
                    cache_dir=cache_dir,
                    resume_download=True,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32
                )
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    cache_dir=cache_dir,
                    resume_download=True,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    load_in_4bit=True if device == "cuda" else False
                )
            print(f"   ✅ {name} downloaded successfully!")
            
            # Clean up memory
            del model
            del tokenizer
            if device == "cuda":
                torch.cuda.empty_cache()
                
        except Exception as e:
            print(f"   ❌ Error downloading {name}: {e}")
            print("   💡 Don't worry! Just run this script again - downloads will resume!")
            return False
    
    print("""
    
    ╔══════════════════════════════════════════════════════════════╗
    ║              ✅ ALL MODELS DOWNLOADED!                       ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🎉 Success! All models are ready to use.
    
    📁 Models cached in: ./models
    💾 Total size: ~2-3 GB
    
    🚀 Next steps:
       1. Run: python main.py
       2. Open: http://localhost:8000
       3. Start generating content!
    
    💡 These models are now cached locally.
       Future runs will be instant (no download needed).
    """)
    return True

if __name__ == "__main__":
    success = download_models()
    if not success:
        print("\n⚠️  Some downloads failed. Just run this script again!")
        print("   Downloads will automatically resume from where they stopped.")
