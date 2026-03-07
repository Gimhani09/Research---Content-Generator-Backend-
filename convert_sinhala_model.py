"""Convert trained Sinhala model to LoRA adapter format"""
import torch
import os
import shutil

checkpoint_dir = "finetuned_models/sinhala_finetuned/checkpoint-6700"
output_dir = "finetuned_models/sinhala_finetuned"

print(f"📂 Loading model from {checkpoint_dir}")
model_path = os.path.join(checkpoint_dir, "pytorch_model.bin")

# Load the full model
state_dict = torch.load(model_path, map_location="cpu")

print(f"✅ Loaded {len(state_dict)} weights")

# Copy to adapter_model.bin (the full model IS the adapter in LoRA training)
output_path = os.path.join(output_dir, "adapter_model.bin")
torch.save(state_dict, output_path)

file_size = os.path.getsize(output_path) / 1024 / 1024
print(f"✅ Created adapter_model.bin ({file_size:.1f} MB)")

# Copy tokenizer files if they exist
tokenizer_files = ["special_tokens_map.json", "tokenizer_config.json", "tokenizer.json", 
                   "spiece.model", "vocab.json", "merges.txt"]

# Get tokenizer from base model cache
base_model_cache = "models/models--google--mt5-base/snapshots"
if os.path.exists(base_model_cache):
    # Find the snapshot directory
    snapshots = os.listdir(base_model_cache)
    if snapshots:
        snapshot_dir = os.path.join(base_model_cache, snapshots[0])
        print(f"\n📋 Copying tokenizer from {snapshot_dir}")
        for file in tokenizer_files:
            src = os.path.join(snapshot_dir, file)
            dst = os.path.join(output_dir, file)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f"  ✅ Copied {file}")

print("\n🎉 Sinhala fine-tuned model ready!")
print(f"📁 Location: {output_dir}")
print("\n📋 Model files:")
for file in os.listdir(output_dir):
    if os.path.isfile(os.path.join(output_dir, file)):
        size = os.path.getsize(os.path.join(output_dir, file)) / 1024 / 1024
        print(f"  • {file} ({size:.1f} MB)")
