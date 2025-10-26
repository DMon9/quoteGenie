import json

# Simulate Gemini response with markdown fences
response = '''```json
{
  "materials": [
    {"name": "Floor Tile", "quantity": "60", "unit": "sq ft"},
    {"name": "Wall Tile", "quantity": "200", "unit": "sq ft"}
  ],
  "labor_hours": 24,
  "challenges": ["Waterproofing critical", "Proper ventilation needed"],
  "approach": "Remove old fixtures, install cement board, waterproof, tile, grout"
}
```'''

print("Original response:")
print(repr(response[:150]))
print()

# Test cleaning
cleaned = response.strip()
if "```json" in cleaned or "```" in cleaned:
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

print("Cleaned:")
print(repr(cleaned[:150]))
print()

# Test parsing
try:
    data = json.loads(cleaned)
    print("✅ Parsed successfully!")
    print(f"Materials: {len(data.get('materials', []))}")
    for m in data.get('materials', []):
        print(f"  - {m['name']}: {m['quantity']} {m['unit']}")
    print(f"Challenges: {data.get('challenges')}")
except Exception as e:
    print(f"❌ Parsing failed: {e}")
