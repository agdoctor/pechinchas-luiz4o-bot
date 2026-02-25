import asyncio
import os
import sys

# Mocking necessary environment variables
os.environ["TELEGRAM_STRING_SESSION"] = "fake_session"

# Adiciona o diretório atual ao path
sys.path.append(os.getcwd())

from links import process_and_replace_links

async def test_filtering_logic():
    print("--- Testando Logica de Filtragem de Conteudo ---")
    
    # Caso 1: Apenas YouTube (Deve ser ignorado)
    text_yt = "Assista minha analise completa do monitor TCL! link: https://www.youtube.com/watch?v=rxRfnV1FkJo"
    _, placeholder_map_yt = await process_and_replace_links(text_yt)
    
    valid_buy_links_yt = {
        p: url for p, url in placeholder_map_yt.items() 
        if url and not any(content in url.lower() for content in ["youtube.com", "youtu.be", "t.me", "chat.whatsapp.com"])
    }
    
    if not valid_buy_links_yt:
        print("OK: Post de YouTube sem links de compra foi CORRETAMENTE ignorado.")
    else:
        print(f"ERRO: Post de YouTube foi identificado com links invalidos: {valid_buy_links_yt}")

    # Caso 2: YouTube + Link de Compra (Deve ser aceito)
    text_promo = "Monitor TCL em oferta! Compre aqui: https://www.amazon.com.br/dp/B0C7SJR5P6 . Veja o video: https://youtu.be/abc"
    _, placeholder_map_promo = await process_and_replace_links(text_promo)
    
    valid_buy_links_promo = {
        p: url for p, url in placeholder_map_promo.items() 
        if url and not any(content in url.lower() for content in ["youtube.com", "youtu.be", "t.me", "chat.whatsapp.com"])
    }
    
    if valid_buy_links_promo:
        print(f"OK: Post com link de compra real foi CORRETAMENTE aceito. Links: {valid_buy_links_promo}")
    else:
        print("ERRO: Post com link de compra real foi ignorado.")

    # Caso 3: Palavras de filtro de conteudo (Deve ser ignorado se nao houver compra)
    text_review = "Testei o novo monitor da Samsung e o resultado me surpreendeu! Inscreva-se no meu canal."
    palavras_filtro_conteudo = ["análise completa", "testei o", "vídeo novo", "inscreva-se", "meu canal"]
    
    has_content_kw = any(p in text_review.lower() for p in palavras_filtro_conteudo)
    if has_content_kw:
        print("OK: Palavras de filtro de conteudo detectadas.")
    else:
        print("ERRO: Palavras de filtro de conteudo NAO detectadas.")

if __name__ == "__main__":
    asyncio.run(test_filtering_logic())
