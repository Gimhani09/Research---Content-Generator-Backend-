"""
Sample test inputs for Serendib AI poster generator
Run: python test_samples.py
"""
import requests
import json
import os
import time

URL = "http://localhost:8000/api/generate-smart-poster"

# ============================================================
# SAMPLE INPUTS — edit ACTIVE_SAMPLE to switch between them
# ============================================================

SAMPLES = {

    # ── 1. Electronics – Black Friday – Sinhala ───────────────
    "smart_tv_black_friday": {
        "product_name": "Samsung Smart TV 55\"",
        "description": "4K Ultra HD, HDR, Smart Hub, 3 HDMI ports",
        "tone": "exciting",
        "language": "sinhala",
        "season": "Black Friday",
        "discount": "60%",
        "tags": ["4K", "Smart Hub", "HDR", "HDMI"],
        "size": "facebook",
        "business_name": "SINGER",
        "phone_number": "077-1942194"
    },

    # ── 2. Appliance – Avurudu – Bilingual ────────────────────
    "washing_machine_avurudu": {
        "product_name": "LG Washing Machine 7kg",
        "description": "Fully automatic, inverter motor, 10 wash programs",
        "tone": "friendly",
        "language": "both",
        "season": "Avurudu",
        "discount": "30%",
        "tags": ["Auto Clean", "Inverter Motor", "Energy Saving"],
        "size": "instagram",
        "business_name": "ABANS",
        "phone_number": "011-2300300"
    },

    # ── 3. Food – No season – English ─────────────────────────
    "kottu_promotion": {
        "product_name": "Spicy Chicken Kottu",
        "description": "Fresh ingredients, authentic Sri Lankan recipe, served hot",
        "tone": "casual",
        "language": "english",
        "season": "",
        "discount": "Buy 2 Get 1 Free",
        "tags": ["Fresh", "Authentic", "Hot & Spicy"],
        "size": "instagram",
        "business_name": "Cafe Serendib",
        "phone_number": "077-5500500"
    },

    # ── 4. Fashion – Valentine – Sinhala ──────────────────────
    "ladies_saree_valentine": {
        "product_name": "Silk Saree Collection",
        "description": "Handwoven pure silk sarees, traditional designs, vibrant colors",
        "tone": "luxurious",
        "language": "sinhala",
        "season": "Valentine",
        "discount": "25%",
        "tags": ["Handwoven", "Pure Silk", "Traditional"],
        "size": "story",
        "business_name": "Malee Fashion",
        "phone_number": "0774-123456"
    },

    # ── 5. Electronics – New Year – English ───────────────────
    "laptop_new_year": {
        "product_name": "ASUS VivoBook 15",
        "description": "Intel Core i5, 8GB RAM, 512GB SSD, Full HD display",
        "tone": "professional",
        "language": "english",
        "season": "New Year",
        "discount": "Rs. 20,000 OFF",
        "tags": ["Intel i5", "8GB RAM", "512GB SSD", "Full HD"],
        "size": "facebook",
        "business_name": "Tech Zone",
        "phone_number": "011-4500400"
    },

    # ── 6. Grocery – No season – Sinhala ──────────────────────
    "milk_powder_deal": {
        "product_name": "Anchor Milk Powder 400g",
        "description": "Full cream milk powder, calcium enriched, for the whole family",
        "tone": "friendly",
        "language": "sinhala",
        "season": "",
        "discount": "15%",
        "tags": ["Calcium", "Full Cream", "Family Pack"],
        "size": "facebook",
        "business_name": "Keells Super",
        "phone_number": "011-2112000"
    },

    # ── 7. Furniture – No season – Bilingual ──────────────────
    "sofa_set": {
        "product_name": "L-Shape Sofa Set",
        "description": "5-seater L-shape sofa, premium fabric, solid wood frame",
        "tone": "professional",
        "language": "both",
        "season": "",
        "discount": "20%",
        "tags": ["5-Seater", "Premium Fabric", "Solid Wood"],
        "size": "facebook",
        "business_name": "Home Decor LK",
        "phone_number": "077-8001800"
    },

    # ── 8. Smartphones – Back to School – English ─────────────
    "smartphone_back_to_school": {
        "product_name": "Redmi Note 14",
        "description": "108MP camera, 5000mAh battery, 6.67 inch display, 5G ready",
        "tone": "exciting",
        "language": "english",
        "season": "Back to School",
        "discount": "10,000 OFF",
        "tags": ["108MP", "5G", "5000mAh", "Fast Charge"],
        "size": "instagram",
        "business_name": "Dialog Axiata",
        "phone_number": "0777-678678"
    },

    # ── 9. Skincare – No season – Sinhala ─────────────────────
    "sunscreen_lotion": {
        "product_name": "Nivea Sun SPF50 Lotion",
        "description": "UVA/UVB protection, moisturizing, lightweight formula",
        "tone": "friendly",
        "language": "sinhala",
        "season": "Summer",
        "discount": "",
        "tags": ["SPF50", "UVA/UVB", "Moisturizing"],
        "size": "instagram",
        "business_name": "Pharmacy Plus",
        "phone_number": "011-3200200"
    },

    # ── 10. Service – No season – Bilingual ───────────────────
    "gym_membership": {
        "product_name": "Gold Gym Membership",
        "description": "Full gym access, personal trainer, swimming pool included",
        "tone": "urgent",
        "language": "both",
        "season": "New Year",
        "discount": "50%",
        "tags": ["Personal Trainer", "Swimming Pool", "Full Access"],
        "size": "story",
        "business_name": "FitLife Gym",
        "phone_number": "077-6060600"
    },
}

# ============================================================
# SELECT WHICH SAMPLE TO RUN
# ============================================================
ACTIVE_SAMPLE = "smart_tv_black_friday"   # ← change this to test different products

# ── To run ALL samples: set RUN_ALL = True ──────────────────
RUN_ALL = False

# ============================================================

def run_test(name: str, payload: dict):
    print("\n" + "="*65)
    print(f"  SAMPLE: {name}")
    print(f"  Product: {payload['product_name']}  |  Lang: {payload['language']}  |  Season: {payload.get('season') or 'None'}")
    print("="*65)
    
    try:
        r = requests.post(URL, json=payload, timeout=120)
        data = r.json()
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    content = data.get("content", "")
    lines = [l for l in content.split('\n') if l.strip()]
    
    print("\n  GENERATED POSTER TEXT:")
    print("  " + "-"*40)
    for i, line in enumerate(lines, 1):
        flag = " ⚠ LONG" if len(line) > 45 else ""
        print(f"  {i:2}. {line}{flag}")
    print("  " + "-"*40)
    print(f"\n  Lines: {len(lines)}  |  Total chars: {len(content)}")
    print(f"  Pipeline: {data.get('pipeline', '')}")
    print(f"  Poster:   {data.get('poster_path', 'N/A')}")
    
    # Check poster file exists
    poster_path = data.get("poster_path", "")
    if poster_path:
        # Convert to absolute path
        full_path = poster_path if os.path.isabs(poster_path) else os.path.join("d:\\content_generator", poster_path)
        exists = os.path.isfile(full_path)
        print(f"  File OK:  {'YES' if exists else 'NO - ' + full_path}")
    
    # Quality checks
    import re
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        "\u2600-\u26FF\u2700-\u27BF]"
    )
    emojis = emoji_pattern.findall(content)
    print(f"\n  Emoji check:   {'FAIL - found: ' + str(emojis) if emojis else 'PASS (no emojis)'}")
    
    season = payload.get("season", "").lower()
    if season and season in content.lower():
        print(f"  Season check:  PASS ({payload['season']} mentioned)")
    elif season:
        print(f"  Season check:  WARN ('{payload['season']}' not found in content)")
    
    discount = payload.get("discount", "")
    if discount and any(d in content for d in [discount, discount.replace("%", ""), "OFF", "off"]):
        print(f"  Discount check: PASS ({discount} referenced)")
    elif discount:
        print(f"  Discount check: WARN ({discount} not found in content)")
    
    print()
    return data


if __name__ == "__main__":
    if RUN_ALL:
        print(f"\nRunning ALL {len(SAMPLES)} samples...\n")
        for name, payload in SAMPLES.items():
            run_test(name, payload)
            time.sleep(3)  # avoid rate limits
        print("\nAll tests done.")
    else:
        payload = SAMPLES.get(ACTIVE_SAMPLE)
        if not payload:
            print(f"ERROR: Sample '{ACTIVE_SAMPLE}' not found. Available: {list(SAMPLES.keys())}")
        else:
            run_test(ACTIVE_SAMPLE, payload)
