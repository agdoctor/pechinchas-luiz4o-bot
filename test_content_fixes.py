import asyncio
import os
import sys

# Mocking necessary environment variables
os.environ["TELEGRAM_STRING_SESSION"] = "fake_session"

# Adiciona o diretório atual ao path
sys.path.append(os.getcwd())

from links import extract_urls, process_and_replace_links
from scraper import fetch_product_metadata, download_image

async def test_button_extraction():
    print("--- Testando Extracao de Links de Botoes ---")
    text = "Confira essa oferta incrivel! (mao apontando)"
    original_button_links = ["https://amzn.to/3vXpZaV"]
    
    # Simula o que o monitor.py faz agora
    texto_para_processar = text
    if original_button_links:
        links_str = "\n".join(original_button_links)
        texto_para_processar += f"\n{links_str}"
        
    print(f"Texto para processar:\n{texto_para_processar}")
    
    clean_text, placeholder_map = await process_and_replace_links(texto_para_processar)
    
    print(f"Texto com placeholders: {clean_text}")
    print(f"Placeholder Map: {placeholder_map}")
    
    if "[LINK_0]" in placeholder_map:
        print("✅ Sucesso: Link do botão foi capturado e processado.")
    else:
        print("❌ Falha: Link do botão não foi encontrado.")

async def test_clean_image_fetching():
    print("\n--- Testando Busca de Imagem Limpa ---")
    # Usando um link real da Amazon para testar o scraper (se houver rede)
    test_link = "https://www.amazon.com.br/dp/B0C7SJR5P6"
    
    print(f"Buscando metadata para: {test_link}")
    metadata = await fetch_product_metadata(test_link)
    
    if metadata.get("local_image_path"):
        print(f"✅ Sucesso: Imagem limpa baixada em {metadata['local_image_path']}")
        # Limpeza
        if os.path.exists(metadata['local_image_path']):
            os.remove(metadata['local_image_path'])
    else:
        print("⚠️ Aviso: Não foi possível baixar imagem limpa (pode ser bloqueio de rede/WAF).")

if __name__ == "__main__":
    asyncio.run(test_button_extraction())
    # asyncio.run(test_clean_image_fetching()) # Comentado para evitar dependência de rede externa no teste rápido
