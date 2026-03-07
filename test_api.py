"""Quick test script for content generation quality"""
import requests
import json

url = "http://localhost:8000/api/generate-smart-poster"

payload = {
    "product_name": "Smart TV",
    "description": "",
    "tone": "professional",
    "language": "sinhala",
    "season": "Black Friday",
    "discount": "60%",
    "tags": [],
    "size": "facebook",
    "business_name": "SINGER",
    "phone_number": "0711942194"
}

print("Sending request...")
r = requests.post(url, json=payload, timeout=120)
data = r.json()

print("\n=== GPT2/GEMINI DRAFT ===")
print(data.get("gpt2_draft", ""))

print("\n=== POLISHED CONTENT ===")  
print(data.get("gemini_polished", "N/A"))

print("\n=== FINAL CONTENT (after shaping + emoji strip) ===")
print(data.get("content", ""))

# Check for emojis
import re
emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]")
content = data.get("content", "")
emojis_found = emoji_pattern.findall(content)
if emojis_found:
    print(f"\n⚠️ WARNING: Emojis still found: {emojis_found}")
else:
    print(f"\n✅ No emojis in content - clean professional text")

# Check for Black Friday (not Christmas)
if "black friday" in content.lower() or "Black Friday" in content:
    print("✅ Correct season: Black Friday mentioned")
elif "christmas" in content.lower() or "නත්තල්" in content:
    print("⚠️ WARNING: Wrong season - Christmas mentioned instead of Black Friday!")

print(f"\n=== STATS ===")
print(f"Content length: {len(content)} chars")
print(f"Lines: {len([l for l in content.split(chr(10)) if l.strip()])}")
print(f"Pipeline: {data.get('pipeline', '')}")
print(f"Hashtags: {data.get('hashtags', [])}")
print(f"Poster path: {data.get('poster_path', 'N/A')}")
print(f"Season in response: {data.get('season', '')}")
print(f"Discount in response: {data.get('discount', '')}")

# Check line lengths (poster-optimized should be short)
lines = [l for l in content.split('\n') if l.strip()]
long_lines = [l for l in lines if len(l) > 50]
if long_lines:
    print(f"\n⚠️ {len(long_lines)} lines over 50 chars (poster text should be short):")
    for l in long_lines:
        print(f"   [{len(l)} chars] {l}")
else:
    print(f"\n✅ All {len(lines)} lines are poster-length (under 50 chars)")

# Save full response
with open("test_output_full.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("\nFull response saved to test_output_full.json")
