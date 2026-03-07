"""
FREE LOCAL Fine-Tuning Pipeline
Fine-tune models on your own marketing dataset using LoRA
Works on: GPU (faster) or CPU (slower but free)
"""
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from datasets import Dataset, load_dataset
import torch
import json
import os
from config import config

class FineTuner:
    """Fine-tune content generation models locally"""
    
    def __init__(self, model_type: str = "english"):
        """
        model_type: 'english' (GPT-2) or 'sinhala' (mT5)
        """
        self.model_type = model_type
        self.device = "cuda" if config.USE_GPU and torch.cuda.is_available() else "cpu"
        print(f"🖥️  Using device: {self.device}")
        
        # Select model based on type
        if model_type == "english":
            self.model_name = config.ENGLISH_MODEL
            self.is_seq2seq = False
        else:  # sinhala
            self.model_name = config.SINHALA_MODEL
            self.is_seq2seq = True
        
        print(f"📥 Loading base model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=config.MODEL_CACHE_DIR
        )
        
        # Add padding token if missing (for GPT-2)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        if self.is_seq2seq:
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                cache_dir=config.MODEL_CACHE_DIR
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=config.MODEL_CACHE_DIR
            )
        
        print("✅ Base model loaded!")
    
    def prepare_dataset(self, dataset_path: str):
        """
        Prepare dataset from JSON file
        Format: [{"prompt": "...", "completion": "..."}, ...]
        """
        print(f"📂 Loading dataset from {dataset_path}")
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to HuggingFace Dataset
        dataset = Dataset.from_list(data)
        
        # Tokenize
        def tokenize_function(examples):
            if self.is_seq2seq:
                # For Seq2Seq (mT5)
                model_inputs = self.tokenizer(
                    examples["prompt"],
                    max_length=128,
                    truncation=True,
                    padding="max_length"
                )
                
                labels = self.tokenizer(
                    examples["completion"],
                    max_length=128,
                    truncation=True,
                    padding="max_length"
                )
                
                model_inputs["labels"] = labels["input_ids"]
                return model_inputs
            else:
                # For Causal LM (GPT-2)
                text = [p + " " + c for p, c in zip(examples["prompt"], examples["completion"])]
                return self.tokenizer(
                    text,
                    max_length=256,
                    truncation=True,
                    padding="max_length"
                )
        
        tokenized = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        print(f"✅ Dataset prepared: {len(tokenized)} samples")
        return tokenized
    
    def setup_lora(self):
        """Setup LoRA (Low-Rank Adaptation) for efficient fine-tuning"""
        
        print("🔧 Setting up LoRA configuration...")
        
        # mT5/T5 uses "q", "v" for attention layers, GPT-2 uses "c_attn"
        if self.is_seq2seq:
            target_modules = ["q", "v"]  # For mT5/T5 models
        else:
            target_modules = ["c_attn"]  # For GPT-2 models
        
        lora_config = LoraConfig(
            r=16,  # Rank
            lora_alpha=32,
            target_modules=target_modules,
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.SEQ_2_SEQ_LM if self.is_seq2seq else TaskType.CAUSAL_LM
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        print("✅ LoRA setup complete!")
    
    def train(self, dataset_path: str, output_dir: str = None):
        """Train the model with LoRA"""
        
        if output_dir is None:
            output_dir = os.path.join(
                config.FINETUNE_OUTPUT_DIR,
                f"{self.model_type}_finetuned"
            )
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare dataset
        dataset = self.prepare_dataset(dataset_path)
        
        # Split into train/validation
        split = dataset.train_test_split(test_size=0.1)
        train_dataset = split["train"]
        eval_dataset = split["test"]
        
        # Setup LoRA
        self.setup_lora()
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=config.FINETUNE_EPOCHS,
            per_device_train_batch_size=config.FINETUNE_BATCH_SIZE,
            per_device_eval_batch_size=config.FINETUNE_BATCH_SIZE,
            learning_rate=config.FINETUNE_LEARNING_RATE,
            warmup_steps=100,
            logging_steps=10,
            eval_steps=50,
            save_steps=100,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            fp16=self.device == "cuda",  # Mixed precision for GPU
            report_to="none",
            save_total_limit=2
        )
        
        # Data collator
        if self.is_seq2seq:
            data_collator = DataCollatorForSeq2Seq(self.tokenizer, model=self.model)
        else:
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator
        )
        
        print("\n🚀 Starting training...")
        print(f"   Training samples: {len(train_dataset)}")
        print(f"   Validation samples: {len(eval_dataset)}")
        print(f"   Epochs: {config.FINETUNE_EPOCHS}")
        print(f"   Batch size: {config.FINETUNE_BATCH_SIZE}")
        
        # Train!
        trainer.train()
        
        # Save final model
        print(f"\n💾 Saving fine-tuned model to {output_dir}")
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        print("✅ Training complete!")
        return output_dir
    
    def load_finetuned(self, model_path: str):
        """Load a fine-tuned model"""
        print(f"📥 Loading fine-tuned model from {model_path}")
        
        # Load base model first
        if self.is_seq2seq:
            base_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                cache_dir=config.MODEL_CACHE_DIR
            )
        else:
            base_model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=config.MODEL_CACHE_DIR
            )
        
        # Load LoRA weights
        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model = self.model.to(self.device)
        
        print("✅ Fine-tuned model loaded!")

# Training script
if __name__ == "__main__":
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fine-tune models on marketing dataset")
    parser.add_argument("--model", type=str, default="english", choices=["english", "sinhala"],
                        help="Model to fine-tune (english=GPT-2, sinhala=mT5)")
    parser.add_argument("--dataset", type=str, default="training_data_english.json",
                        help="Path to dataset JSON file")
    parser.add_argument("--epochs", type=int, default=None,
                        help="Number of training epochs (overrides config)")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="Batch size (overrides config)")
    args = parser.parse_args()
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         FREE LOCAL MODEL FINE-TUNING                          ║
    ║  Fine-tune GPT-2 (English) or mT5 (Sinhala) on your data     ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Use command-line arguments
    print(f"\n1️⃣  Fine-tuning {args.model} model...")
    print(f"📊 Dataset: {args.dataset}")
    if args.epochs:
        print(f"📊 Epochs: {args.epochs}")
    if args.batch_size:
        print(f"📊 Batch size: {args.batch_size}")
    
    # Check if dataset exists
    dataset_path = args.dataset
    if not os.path.exists(dataset_path):
        print(f"⚠️  Dataset not found: {dataset_path}")
        print("📝 Create a dataset file with format:")
        print('''[
    {"prompt": "Product: Milk Powder. Description: High calcium", "completion": "Introducing our premium milk powder..."},
    {"prompt": "Product: Shoes. Description: Running shoes", "completion": "Step into comfort with our..."}
]''')
        
        # Create sample dataset
        sample_data = [
            {
                "prompt": "Write a professional marketing message for Premium Milk Powder. High calcium, vitamin enriched.",
                "completion": "Introducing Premium Milk Powder - your family's trusted choice for nutrition. Packed with high calcium and essential vitamins, it's specially formulated to support healthy growth and development."
            },
            {
                "prompt": "Write an exciting marketing message for Running Shoes. Lightweight, comfortable design.",
                "completion": "Step into the future of running! Our revolutionary lightweight running shoes combine cutting-edge technology with unmatched comfort. Every stride feels effortless!"
            }
        ]
        
        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sample dataset created: {dataset_path}")
    
    # Override config if command-line args provided
    if args.epochs:
        config.FINETUNE_EPOCHS = args.epochs
    if args.batch_size:
        config.FINETUNE_BATCH_SIZE = args.batch_size
    
    # Initialize fine-tuner
    tuner = FineTuner(model_type=args.model)
    
    # Train
    output = tuner.train(dataset_path)
    
    print(f"\n✅ Model saved to: {output}")
    print("📝 To use the fine-tuned model, update config.py with the path")
