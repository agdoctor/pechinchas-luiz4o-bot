import asyncio
import sys
import os

# Adiciona o diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import links
import affiliate

async def test_full_process():
    text = "Confira essa oferta: https://mercadolivre.com/sec/1PJg3nq"
    print(f"Texto original: {text}")
    
    clean_text, placeholder_map = await links.process_and_replace_links(text)
    
    print(f"Texto com placeholders: {clean_text}")
    print(f"Placeholder Map: {placeholder_map}")
    
    final_text = clean_text
    for placeholder, final_url in placeholder_map.items():
        if final_url:
            final_text = final_text.replace(placeholder, final_url)
        else:
            final_text = final_text.replace(placeholder, "[LINK REMOVIDO]")
            
    print(f"Texto final: {final_text}")

if __name__ == "__main__":
    asyncio.run(test_full_process())
