"""
Quick test of Stability AI background generation
"""
import os
from smart_poster_generator import SmartPosterGenerator

# Set API key
os.environ["STABILITY_API_KEY"] = "sk-YhZUURzP9JnSE1y2CKjDQIYpTbyyHdVkIsqhoRniuzeKETRH"

def quick_test():
    """Test Stability AI with sample content from your training data"""
    
    print("🎨 Quick Stability AI Test")
    print("=" * 60)
    
    # Sample from your actual training data
    test_cases = [
        {
            "product": "Sofa Set",
            "content": "Get Sofa Set with Limited time offer, great value. limited time offer. DM now!",
            "description": "Furniture item (should detect 'home' category)"
        },
        {
            "product": "Kottu Promotion",
            "content": "Christmas craving sorted! Get an EXCLUSIVE discount on our Kottu! Don't miss out. Visit store!",
            "description": "Christmas food (should detect 'christmas' season + 'food' category)"
        },
        {
            "product": "Robot Vacuum",
            "content": "New Year, Clean Home! Robot Vacuums at GREAT prices! Limited time only. Book now!",
            "description": "Tech product with New Year theme"
        }
    ]
    
    # Initialize generator
    poster_gen = SmartPosterGenerator(api_choice="stability")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['product']}")
        print(f"Expected: {test['description']}")
        print(f"\nContent: {test['content']}")
        
        # Detect context
        context = poster_gen.detect_content_context(test['content'], test['product'])
        print(f"\n✅ Detected Context:")
        print(f"   Season: {context['season']}")
        print(f"   Category: {context['category']}")
        print(f"   Mood: {context['mood']}")
        
        # Generate prompt
        prompt = poster_gen.generate_background_prompt(context, test['product'])
        print(f"\n📝 Background Prompt (first 150 chars):")
        print(f"   {prompt[:150]}...")
        
        # Ask if user wants to generate
        if i == 1:  # Only generate first one as test
            print(f"\n🎨 Generating background with Stability AI...")
            result = poster_gen.generate_poster(test['content'], test['product'])
            
            if "error" in result.get("result", {}):
                print(f"\n❌ Error: {result['result']}")
            elif result.get("result", {}).get("success"):
                print(f"\n✅ SUCCESS!")
                print(f"   Image saved: {result['result']['image_path']}")
                print(f"\n💡 Cost: ~$0.004 per image (very affordable!)")
                return result['result']['image_path']
            else:
                print(f"\n⚠️ Unexpected result: {result}")
    
    return None


if __name__ == "__main__":
    img_path = quick_test()
    
    if img_path:
        print(f"\n\n{'='*60}")
        print(f"🎉 STABILITY AI TEST SUCCESSFUL!")
        print(f"{'='*60}")
        print(f"\n✅ Generated contextual background: {img_path}")
        print(f"\n📋 What this means for your research:")
        print(f"   1. Your system can auto-detect themes (Christmas, Valentine, etc.)")
        print(f"   2. Stability AI generates matching backgrounds (~$0.004 each)")
        print(f"   3. Perfect for your presentation - show AI content + AI visuals")
        print(f"\n🚀 Next step: Overlay your fine-tuned content on this background")
