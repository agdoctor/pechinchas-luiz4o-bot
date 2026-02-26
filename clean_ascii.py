import re
import os

def clean_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove any character that is not ASCII
    clean_content = re.sub(r'[^\x00-\x7F]+', '', content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(clean_content)
    print(f"Successfully cleaned: {file_path}")

if __name__ == "__main__":
    files = [
        r'c:\Users\luizh\.gemini\antigravity\pechinchasdoluiz4o\pechinchas_bot\scraper.py',
        r'c:\Users\luizh\.gemini\antigravity\pechinchasdoluiz4o\pechinchas_bot\affiliate.py',
        r'c:\Users\luizh\.gemini\antigravity\pechinchasdoluiz4o\pechinchas_bot\test_shopee_strategies_v2.py'
    ]
    for f in files:
        clean_file(f)
