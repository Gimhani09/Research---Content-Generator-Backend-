"""
Fine-tune mT5 for Sinhala/Code-Mixed Marketing Content Generation
Uses LoRA for efficient training on your local machine
"""
import os
import sys
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finetune import FineTuner
from config import config

def detect_and_configure_gpu():
    """Detect GPU and configure optimal batch size."""
    import torch
    has_gpu = torch.cuda.is_available()
    
    if has_gpu:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"\n🎮 GPU DETECTED: {gpu_name}")
        print(f"   VRAM: {gpu_memory:.1f} GB")
        
        # Auto-optimize batch size based on VRAM
        if gpu_memory >= 8:
            optimized_batch = 16
            print(f"   ⚡ Optimized batch size: {optimized_batch} (large VRAM)")
        elif gpu_memory >= 6:
            optimized_batch = 12
            print(f"   ⚡ Optimized batch size: {optimized_batch} (good VRAM)")
        elif gpu_memory >= 4:
            optimized_batch = 8
            print(f"   ⚡ Optimized batch size: {optimized_batch} (medium VRAM)")
        else:
            optimized_batch = 4
            print(f"   ⚡ Optimized batch size: {optimized_batch} (low VRAM)")
        
        config.FINETUNE_BATCH_SIZE = optimized_batch
        print("   ⏱️  Estimated time: 30-60 minutes")
    else:
        print("\n💻 CPU MODE")
        print("   No GPU detected - training will be slower")
        print("   ⏱️  Estimated time: 3-5 hours")
        config.FINETUNE_BATCH_SIZE = 2
    
    return has_gpu

def print_training_config():
    """Print training configuration."""
    print("\n📋 TRAINING CONFIGURATION:")
    print(f"   Model: mT5-base (580M params, multilingual)")
    print(f"   Method: LoRA (only ~0.5% parameters trained)")
    print(f"   Dataset: {config.DATASET_SINHALA_PATH}")
    print(f"   Output: {config.FINETUNED_SINHALA_MODEL_PATH}")
    print(f"   Epochs: {config.FINETUNE_EPOCHS}")
    print(f"   Batch Size: {config.FINETUNE_BATCH_SIZE}")
    print(f"   Learning Rate: {config.FINETUNE_LEARNING_RATE}")

def select_dataset():
    """Select dataset path with user interaction."""
    if os.path.exists(config.DATASET_SINHALA_PATH):
        return config.DATASET_SINHALA_PATH
    
    print(f"\n❌ Dataset not found: {config.DATASET_SINHALA_PATH}")
    print("\n💡 Available datasets:")
    if os.path.exists(config.DATASET_FULL_PATH):
        print(f"   ✅ {config.DATASET_FULL_PATH} (English + Sinhala combined)")
    if os.path.exists("training_data_sinhala_25k.json"):
        print("   ✅ training_data_sinhala_25k.json")
    
    print("\n📝 Would you like to:")
    print("   1. Use training_data_sinhala_25k.json (Sinhala + code-mixed only)")
    print("   2. Use training_data_full_25k.json and filter for Sinhala entries")
    print("   3. Exit and create your own dataset")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        return "training_data_sinhala_25k.json"
    elif choice == "2":
        print("\n⚠️ Note: Will use full dataset. You can filter by language in the dataset file.")
        return config.DATASET_FULL_PATH
    else:
        print("\n👋 Exiting. Create your dataset and run again.")
        return None

def print_dataset_info(dataset_path):
    """Print dataset statistics."""
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   📊 Total samples: {len(data):,}")
        print(f"   📊 Training samples: ~{int(len(data) * 0.9):,}")
        print(f"   📊 Validation samples: ~{int(len(data) * 0.1):,}")
    except (OSError, json.JSONDecodeError):
        pass

def confirm_training(has_gpu):
    """Get user confirmation to start training."""
    print("\n⚠️  IMPORTANT:")
    if has_gpu:
        print("   - GPU training will take 30-60 minutes")
        print("   - Your system may be slower during training")
    else:
        print("   - CPU training will take 3-5 hours")
        print("   - Consider using GPU for faster training")
    print("   - Make sure you have enough disk space (~2GB)")
    print("   - Don't close this window until training completes")
    
    confirm = input("\n🚀 Start fine-tuning now? (yes/no): ").strip().lower()
    return confirm in ['yes', 'y']

def convert_model_format(output_path):
    """Convert safetensors to .bin for compatibility."""
    print("\n📦 Converting model format for compatibility...")
    try:
        import torch
        from safetensors.torch import load_file
        
        safetensors_path = os.path.join(output_path, "adapter_model.safetensors")
        bin_path = os.path.join(output_path, "adapter_model.bin")
        
        if os.path.exists(safetensors_path) and not os.path.exists(bin_path):
            weights = load_file(safetensors_path)
            torch.save(weights, bin_path)
            print(f"✅ Converted to .bin format: {bin_path}")
    except (OSError, ImportError) as e:
        print(f"⚠️ Conversion skipped: {e}")

def main():
    """Main fine-tuning workflow."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║    SINHALA/CODE-MIXED CONTENT GENERATOR FINE-TUNING          ║
    ║      Fine-tune mT5 on Sinhala marketing content              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Detect GPU and configure
    has_gpu = detect_and_configure_gpu()
    
    # Step 2: Print configuration
    print_training_config()
    
    # Step 3: Select dataset
    dataset_path = select_dataset()
    if dataset_path is None:
        return
    
    print(f"\n✅ Using dataset: {dataset_path}")
    
    # Step 4: Show dataset info
    print_dataset_info(dataset_path)
    
    # Step 5: Get user confirmation
    if not confirm_training(has_gpu):
        print("\n👋 Cancelled. Run this script again when ready.")
        return
    
    # Step 6: Initialize fine-tuner
    print("\n" + "="*70)
    print("INITIALIZING FINE-TUNER")
    print("="*70)
    
    tuner = FineTuner(model_type="sinhala")
    
    # Step 7: Start training
    print("\n" + "="*70)
    print("STARTING TRAINING")
    print("="*70 + "\n")
    
    output_path = tuner.train(
        dataset_path=dataset_path,
        output_dir=config.FINETUNED_SINHALA_MODEL_PATH
    )
    
    # Step 8: Convert model format
    convert_model_format(output_path)
    
    # Step 9: Print completion message
    print("\n" + "="*70)
    print("✅ FINE-TUNING COMPLETE!")
    print("="*70)
    
    print(f"\n📁 Model saved to: {output_path}")
    print("\n📝 NEXT STEPS:")
    print("   1. The model is ready to use automatically")
    print("   2. Make sure USE_FINETUNED_SINHALA=true in your .env file (default)")
    print("   3. Run: python main.py")
    print("   4. Test Sinhala generation in your web interface")
    
    print("\n💡 TIP: Compare outputs:")
    print("   - Before: Translation-based (base mT5)")
    print("   - After: Direct generation from fine-tuned mT5")
    print("   - You should see more natural code-mixing and better marketing tone!")

if __name__ == "__main__":
    main()
