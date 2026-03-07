"""
Quick Test Script for Content Generation
Tests the fine-tuned model with optimal inputs from training data
"""
import requests
import json
from typing import Dict

API_URL = "http://localhost:8000/generate_text"

def test_generation(test_name: str, data: Dict):
    """Test content generation and display results"""
    print(f"\n{'='*70}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*70}")
    print(f"📝 Input:")
    print(f"   Product: {data['product_name']}")
    print(f"   Description: {data['description']}")
    print(f"   Tone: {data['tone']}")
    print(f"   Language: {data['language']}")
    if data.get('season'):
        print(f"   Season: {data['season']}")
    if data.get('discount'):
        print(f"   Discount: {data['discount']}")
    
    try:
        response = requests.post(API_URL, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ GENERATED CONTENT:")
            print(f"   {result['content']}")
            print(f"\n📊 Details:")
            print(f"   Model Used: {result.get('model_used', 'unknown')}")
            print(f"   Pipeline: {result.get('pipeline', 'unknown')}")
            
            if result.get('hashtags'):
                print(f"   Hashtags: {', '.join(result['hashtags'])}")
            
            return True
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to server!")
        print(f"   Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def main():
    """Run all test cases"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║          CONTENT GENERATION TEST SUITE                           ║
    ║  Testing Fine-tuned GPT-2 with Optimal Training Data Patterns    ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Test cases based on actual training data patterns
    test_cases = [
        {
            "name": "Home Appliances - Professional (Top Category)",
            "data": {
                "product_name": "Smart Washing Machine",
                "description": "Energy efficient, large capacity, smart features",
                "tone": "professional",
                "language": "english"
            }
        },
        {
            "name": "Fashion - Exciting (Second Top Category)",
            "data": {
                "product_name": "Summer Dress Collection",
                "description": "New arrival, trendy designs, limited stock",
                "tone": "exciting",
                "language": "english"
            }
        },
        {
            "name": "Food - Professional with Seasonal",
            "data": {
                "product_name": "Christmas Cake Special",
                "description": "Fresh baked, premium ingredients, special discount",
                "tone": "professional",
                "language": "english",
                "season": "Christmas",
                "discount": "25% OFF"
            }
        },
        {
            "name": "Bank Offer - Professional with Discount",
            "data": {
                "product_name": "Weekend Credit Card Offer",
                "description": "Exclusive discounts, limited time, all major brands",
                "tone": "professional",
                "language": "english",
                "discount": "20% OFF"
            }
        },
        {
            "name": "Beauty - Exciting with Features",
            "data": {
                "product_name": "Skin Care Set",
                "description": "Great value, fast delivery available, top-rated choice",
                "tone": "exciting",
                "language": "english"
            }
        },
        {
            "name": "Mobile Phone - Professional",
            "data": {
                "product_name": "Flagship Smartphone Pro",
                "description": "5G enabled, triple camera, fast charging, best seller",
                "tone": "professional",
                "language": "english"
            }
        },
        {
            "name": "Furniture - Professional",
            "data": {
                "product_name": "Living Room Sofa Set",
                "description": "New arrival, premium quality, free delivery",
                "tone": "professional",
                "language": "english"
            }
        },
        {
            "name": "Food - Mixed Language (English + Sinhala)",
            "data": {
                "product_name": "Kottu Special",
                "description": "Delicious, fresh ingredients, great value",
                "tone": "casual",
                "language": "both"
            }
        },
        {
            "name": "Avurudu Special - Mixed Language",
            "data": {
                "product_name": "Avurudu Gift Hamper",
                "description": "Traditional sweets, premium quality, special offer",
                "tone": "casual",
                "language": "both",
                "season": "Avurudu",
                "discount": "15% OFF"
            }
        },
        {
            "name": "Electronics - Exciting Flash Sale",
            "data": {
                "product_name": "Smart TV Flash Sale",
                "description": "Limited time offer, huge discounts, latest models",
                "tone": "exciting",
                "language": "english",
                "discount": "Up to 40% OFF"
            }
        }
    ]
    
    # Run all tests
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        if test_generation(test["name"], test["data"]):
            passed += 1
        else:
            failed += 1
        
        # Pause between tests
        if i < len(test_cases):
            import time
            time.sleep(1)
    
    # Summary
    print(f"\n\n{'='*70}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"{'='*70}\n")
    
    if passed == len(test_cases):
        print("🎉 All tests passed! Your fine-tuned model is working perfectly!")
    elif passed > 0:
        print("⚠️  Some tests passed. Check if the server is running properly.")
    else:
        print("❌ All tests failed. Make sure to start the server first:")
        print("   python main.py")

if __name__ == "__main__":
    main()
