"""
Configuration for FREE LOCAL AI models
No API keys needed - everything runs on your machine
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Model Cache Directory
    MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./models")
    USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"
    
    # Content Generation Models (FREE)
    ENGLISH_MODEL = os.getenv("ENGLISH_MODEL", "gpt2-medium")  # 355M params, good quality
    SINHALA_MODEL = os.getenv("SINHALA_MODEL", "google/mt5-base")  # 580M params, multilingual
    
    # Fine-tuned Model Paths (for research)
    FINETUNED_MODEL_PATH = os.getenv("FINETUNED_MODEL_PATH", "./finetuned_models/english_finetuned")
    FINETUNED_SINHALA_MODEL_PATH = os.getenv("FINETUNED_SINHALA_MODEL_PATH", "./finetuned_models/sinhala_finetuned")
    USE_FINETUNED = os.getenv("USE_FINETUNED", "true").lower() == "true"
    USE_FINETUNED_SINHALA = os.getenv("USE_FINETUNED_SINHALA", "true").lower() == "true"
    
    # Gemini API Configuration (for content polishing AND direct generation)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Set via .env or HF Spaces Secrets
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")  # Gemini 3.1 Flash-Lite — fast & efficient
    USE_GEMINI_POLISH = os.getenv("USE_GEMINI_POLISH", "true").lower() == "true"  # Now enabled with API
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NEW: Hybrid AI + HarfBuzz Pipeline Configuration
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Use Gemini API for direct content generation (instead of fine-tuned models)
    # Set to "false" when fine-tuned models are ready to use them instead
    USE_GEMINI_GENERATION = os.getenv("USE_GEMINI_GENERATION", "true").lower() == "true"
    
    # Use HTML/CSS + Playwright/Chromium for poster rendering (HarfBuzz shaping)
    # Set to "false" to fall back to Pillow-based rendering
    USE_HTML_RENDERING = os.getenv("USE_HTML_RENDERING", "true").lower() == "true"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Stability AI Configuration (for contextual poster backgrounds)
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")  # Set via .env or HF Spaces Secrets
    STABILITY_MODEL = os.getenv("STABILITY_MODEL", "stable-diffusion-xl-1024-v1-0")
    USE_STABILITY_BACKGROUNDS = os.getenv("USE_STABILITY_BACKGROUNDS", "true").lower() == "true"
    
    # Memory Optimization
    USE_4BIT = os.getenv("USE_4BIT_QUANTIZATION", "true").lower() == "true"
    
    # Image Generation (FREE)
    IMAGE_MODEL = os.getenv("IMAGE_MODEL", "stabilityai/stable-diffusion-2-1")
    USE_IMAGE_AI = os.getenv("USE_IMAGE_AI", "false").lower() == "true"
    IMAGE_STEPS = int(os.getenv("IMAGE_STEPS", "20"))
    
    # Fine-tuning (Research Component)
    FINETUNE_OUTPUT_DIR = os.getenv("FINETUNE_OUTPUT_DIR", "./finetuned_models")
    FINETUNE_BATCH_SIZE = int(os.getenv("FINETUNE_BATCH_SIZE", "8"))  # Optimized for GPU
    FINETUNE_LEARNING_RATE = float(os.getenv("FINETUNE_LEARNING_RATE", "3e-5"))  # Slightly higher for mT5
    FINETUNE_EPOCHS = int(os.getenv("FINETUNE_EPOCHS", "5"))  # More epochs for better quality
    FINETUNE_MAX_LENGTH = int(os.getenv("FINETUNE_MAX_LENGTH", "256"))
    
    # Dataset Paths
    DATASET_PATH = os.getenv("DATASET_PATH", "./dataset/marketing_content.json")
    DATASET_ENGLISH_PATH = os.getenv("DATASET_ENGLISH_PATH", "./training_data_english_25k.json")
    DATASET_SINHALA_PATH = os.getenv("DATASET_SINHALA_PATH", "./training_data_sinhala_25k.json")
    DATASET_FULL_PATH = os.getenv("DATASET_FULL_PATH", "./training_data_full_25k.json")
    DATASET_TRAIN_SPLIT = float(os.getenv("DATASET_TRAIN_SPLIT", "0.8"))
    
    # Evaluation
    EVALUATION_OUTPUT_DIR = os.getenv("EVALUATION_OUTPUT_DIR", "./evaluation_results")
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

config = Config()
