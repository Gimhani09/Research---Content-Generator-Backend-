"""
Test Stability AI poster generation with your fine-tuned content
"""
import os
import sys
from pathlib import Path
from smart_poster_generator import SmartPosterGenerator
from local_content_generator import LocalContentGenerator

# Set API key
os.environ["STABILITY_API_KEY"] = "sk-Q26uvsBntGg3SOJ3UJrar5Y4ZdQ2iVY7QRep1kKljq1g6zYE"

def test_stability_poster():
    """Generate a poster with Stability AI background + your AI content"""
    
    print("🚀 Testing Stability AI Poster Generation")
    print("=" * 60)
    
    # Initialize generators
    print("\n📝 Step 1: Generating content with your fine-tuned model...")
    content_gen = LocalContentGenerator()
    
    # Use a product from your training data
    test_product = "Sofa Set"
    test_tags = "Limited time offer, great value"
    test_tone = "exciting"
    
    # Generate content
    content = content_gen.generate_english(
        product_name=test_product,
        tags=test_tags,
        tone=test_tone
    )
    
    print(f"\n✅ Generated content:")
    print(f"   Product: {test_product}")
    print(f"   Content: {content}")
    
    # Generate contextual background
    print(f"\n🎨 Step 2: Generating contextual background with Stability AI...")
    poster_gen = SmartPosterGenerator(api_choice="stability")
    
    result = poster_gen.generate_poster(
        content=content,
        product_name=test_product
    )
    
    print(f"\n📊 Context detected:")
    print(f"   Season: {result['context']['season']}")
    print(f"   Category: {result['context']['category']}")
    print(f"   Mood: {result['context']['mood']}")
    
    print(f"\n🖼️ Background prompt:")
    print(f"   {result['prompt'][:200]}...")
    
    if "error" in result.get("result", {}):
        print(f"\n❌ Error: {result['result']['error']}")
        return False
    
    if result.get("result", {}).get("success"):
        img_path = result["result"]["image_path"]
        print(f"\n✅ Success! Background saved to:")
        print(f"   {img_path}")
        
        # Show next steps
        print(f"\n📋 Next Steps:")
        print(f"   1. Open {img_path} to view the generated background")
        print(f"   2. The background is contextual based on: {result['context']}")
        print(f"   3. Now we can overlay your content using poster_template.html")
        return True
    else:
        print(f"\n⚠️ Result: {result}")
        return False


def test_multiple_contexts():
    """Test different seasonal contexts"""
    print("\n\n🎯 Testing Multiple Context Detection")
    print("=" * 60)
    
    test_cases = [
        {
            "content": "Christmas craving sorted! Get an EXCLUSIVE discount on our Kottu!",
            "product": "Kottu Promotion",
            "expected_season": "christmas"
        },
        {
            "content": "Valentine special! Skin Care Set available now",
            "product": "Skin Care Set",
            "expected_season": "valentine"
        },
        {
            "content": "BackToSchool special! Kids Party Frocks available",
            "product": "Kids Party Frocks",
            "expected_season": "back_to_school"
        },
        {
            "content": "Summer special! Budget Smartphone at great prices",
            "product": "Budget Smartphone",
            "expected_season": "summer"
        }
    ]
    
    poster_gen = SmartPosterGenerator(api_choice="stability")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['product']}")
        context = poster_gen.detect_content_context(test['content'], test['product'])
        print(f"   Content: {test['content'][:50]}...")
        print(f"   Detected season: {context['season']} (expected: {test['expected_season']})")
        print(f"   Category: {context['category']}")
        print(f"   Mood: {context['mood']}")
        
        match = "✅" if context['season'] == test['expected_season'] else "❌"
        print(f"   {match} Season detection")


if __name__ == "__main__":
    print("🎨 Stability AI + Fine-tuned Model Poster Test\n")
    
    # First test context detection
    test_multiple_contexts()
    
    # Then generate actual poster
    print("\n" + "=" * 60)
    input("\nPress Enter to generate an actual poster with Stability AI...")
    
    success = test_stability_poster()
    
    if success:
        print("\n\n🎉 SUCCESS! Your system can now:")
        print("   ✅ Generate marketing content with fine-tuned GPT-2")
        print("   ✅ Detect seasonal/contextual themes automatically")
        print("   ✅ Generate matching backgrounds with Stability AI")
        print("   ✅ Ready to overlay text using your poster template")
        print("\n💡 Cost: ~$0.004 per poster background (very affordable!)")
    else:
        print("\n❌ Test failed. Check the error above.")
