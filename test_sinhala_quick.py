"""Quick test of Sinhala code-mixed generation"""
from local_content_generator import get_generator

gen = get_generator()

print("\n🎯 Testing Enhanced Code-Mixed Templates:\n")
print("=" * 70)

products = [
    ("iPhone 15 Pro", "Premium smartphone with titanium design", "excited"),
    ("Samsung Galaxy S24", "AI camera with 200MP sensor", "professional"),
    ("Kottu Special", "Delicious kottu with special discount", "casual"),
]

for product, desc, tone in products:
    result = gen.generate_sinhala(product, desc, tone)
    print(f"\n📱 {product} ({tone}):")
    print(f"   {result}")
    print("-" * 70)

print("\n✅ All tests complete!")
