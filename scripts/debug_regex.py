import re

file_path = "/Users/sam/.gemini/antigravity/brain/27afd509-2740-4cb1-b1f2-66549afbf2f8/communications_handbook.md"
with open(file_path, 'r') as f:
    text = f.read()

tokens = ["Lagos", "Naira", "USDS", "Alaba", "Pidgin", "Igbo", "Yoruba", "Hausa"]

print(f"File content length: {len(text)}")
print(f"First 100 chars: {text[:100]}")

for token in tokens:
    pattern = r'\b' + re.escape(token) + r'\b'
    match = re.search(pattern, text, re.IGNORECASE)
    print(f"Token '{token}': Match={bool(match)}")
    if match:
        print(f"   Found at: {match.span()} -> '{text[match.start():match.end()]}'")
