import re

text = "ममता बनर्जी और सरकार जनता अपना"
# Old regex
regex1 = r'[^\w\s#\u0900-\u097F\u200C\u200D]'
cleaned1 = re.sub(regex1, ' ', text)

# Even more explicit
regex2 = r'[^a-zA-Z0-9\s#\u0900-\u097F\u200C\u200D]'
cleaned2 = re.sub(regex2, ' ', text)

print(f"Original: [{text}]")
print(f"Cleaned 1: [{cleaned1}]")
print(f"Cleaned 2: [{cleaned2}]")

# Check hex of the matra at the end of 'अपना'
last_char = text[-1]
print(f"Last char of 'अपना': {last_char} (Hex: {hex(ord(last_char))})")
