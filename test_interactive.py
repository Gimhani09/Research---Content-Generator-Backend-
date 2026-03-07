"""
Interactive Test - Quickly Test Different Inputs
"""
import requests
import json

API_URL = "http://localhost:8000/generate_text"

def generate_content(product_name, description, tone="professional", language="english", season="", discount=""):
    """Generate content and display result"""
    data = {
        "product_name": product_name,
        "description": description,
        "tone": tone,
        "language": language,
        "season": season,
        "discount": discount
    }
    
    print(f"\n{'='*70}")
    print(f"🤖 Generating content...")
    print(f"{'='*70}")
    
    try:
        response = requests.post(API_URL, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ GENERATED CONTENT:\n")
            print(f"   {result['content']}\n")
            print(f"{'='*70}")
            print(f"Model: {result.get('model_used', 'unknown').upper()}")
            print(f"{'='*70}\n")
        else:
            print(f"\n❌ Error: {response.status_code} - {response.text}\n")
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to server!")
        print(f"Start the server first: python main.py\n")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")

# Quick test examples based on your training data
print("""
╔══════════════════════════════════════════════════════════════════╗
║              QUICK INTERACTIVE CONTENT TEST                      ║
║  Your model was trained on 15,005 marketing examples            ║
╚══════════════════════════════════════════════════════════════════╝
""")

print("\n📋 BEST INPUT PATTERNS FROM YOUR TRAINING DATA:\n")
print("Categories with most examples:")
print("  1. Fashion (956 examples)")
print("  2. General Sale (931 examples)")
print("  3. Beauty & Personal Care (924 examples)")
print("  4. Bank Offers (922 examples)")
print("  5. Food (915 examples)")
print("  6. Home Appliances (878 examples)")
print()
print("Best Description Keywords:")
print("  • New arrival / New arrivals")
print("  • Great value")
print("  • Limited time offer")
print("  • Best seller")
print("  • Top-rated choice")
print("  • Free delivery")
print("  • Special discount")
print()

# Test 1: Fashion (Top category)
print("TEST 1: Fashion - Top Category (956 training examples)")
generate_content(
    product_name="Summer Dress Collection",
    description="New arrival, trendy designs, limited stock",
    tone="exciting",
    language="english"
)

input("Press Enter to continue...")

# Test 2: Home Appliances
print("\nTEST 2: Home Appliances - Professional Tone")
generate_content(
    product_name="Smart Washing Machine",
    description="Energy efficient, large capacity, smart features",
    tone="professional",
    language="english"
)

input("Press Enter to continue...")

# Test 3: Food with Seasonal
print("\nTEST 3: Food - With Seasonal Context (Christmas)")
generate_content(
    product_name="Christmas Cake Special",
    description="Fresh baked, premium ingredients",
    tone="professional",
    language="english",
    season="Christmas",
    discount="25% OFF"
)

input("Press Enter to continue...")

# Test 4: Bank Offer
print("\nTEST 4: Bank Offer - With Discount")
generate_content(
    product_name="Credit Card Weekend Offer",
    description="Exclusive discounts, limited time",
    tone="professional",
    language="english",
    discount="20% OFF"
)

input("Press Enter to continue...")

# Test 5: Mixed Language
print("\nTEST 5: Mixed Language (English + Sinhala)")
generate_content(
    product_name="Kottu Special",
    description="Delicious, fresh ingredients, great value",
    tone="casual",
    language="both"
)

input("Press Enter to continue...")

# Test 6: Avurudu Special
print("\nTEST 6: Avurudu Special - Mixed Language")
generate_content(
    product_name="Avurudu Gift Hamper",
    description="Traditional sweets, premium quality",
    tone="casual",
    language="both",
    season="Avurudu",
    discount="15% OFF"
)

print("\n" + "="*70)
print("✅ Testing Complete!")
print("="*70)
print("\n💡 Try your own examples by modifying this script!")
print("   Edit: test_interactive.py\n")
