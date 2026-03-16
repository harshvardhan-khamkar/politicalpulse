import sys
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, r'c:\Users\admin\Desktop\final anti\backend')

from app.database import SessionLocal
from app.models.social_media import TwitterPost

db = SessionLocal()
post = db.query(TwitterPost).filter(TwitterPost.language == 'hi').first()
text = post.content[:80]

print("Original text:", text)
print()

# Try various recovery chains
encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'cp437', 'iso-8859-1']

for enc1 in encodings_to_try:
    for enc2 in ['utf-8']:
        try:
            recovered = text.encode(enc1, errors='surrogateescape').decode(enc2, errors='strict')
            if any('\u0900' <= c <= '\u097F' for c in recovered):
                print(f"SUCCESS: encode({enc1}) -> decode({enc2}): {recovered[:60]}")
        except Exception:
            pass

# Also try double recovery
for enc1 in encodings_to_try:
    for enc2 in encodings_to_try:
        for enc3 in ['utf-8']:
            try:
                step1 = text.encode(enc1, errors='surrogateescape')
                step2 = step1.decode(enc2, errors='surrogateescape')
                step3 = step2.encode(enc2, errors='surrogateescape')
                step4 = step3.decode(enc3, errors='strict')
                if any('\u0900' <= c <= '\u097F' for c in step4):
                    print(f"DOUBLE: {enc1} -> {enc2} -> {enc3}: {step4[:60]}")
            except Exception:
                pass

# Check if any Devanagari characters exist at all
has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
print(f"\nHas Devanagari in original text: {has_devanagari}")
print(f"Character samples: {[hex(ord(c)) for c in text[:20]]}")

db.close()
