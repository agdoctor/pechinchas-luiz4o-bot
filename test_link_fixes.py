import asyncio
import re
from links import extract_urls, process_and_replace_links

async def test_fixes():
    print("--- Testando Extração de URLs (Pechinchas) ---")
    # Teste com asteriscos (problema reportado pelo usuário)
    text_with_stars = 'Olha esse link: https://amzn.to/4rzsqkT** legal!'
    urls = extract_urls(text_with_stars)
    print(f"URLs extraídas de texto com asteriscos: {urls}")
    assert "https://amzn.to/4rzsqkT" in urls
    assert "https://amzn.to/4rzsqkT**" not in urls

    text_with_html = '<a href="https://t.me/pechinchasdoluiz4o"><code>CUPOM</code></a>'
    urls = extract_urls(text_with_html)
    print(f"URLs extraídas de HTML: {urls}")
    assert "https://t.me/pechinchasdoluiz4o" in urls
    # Verifica se não pegou as aspas ou tags
    for u in urls:
        assert '"' not in u
        assert ">" not in u
        assert "<" not in u

    print("\n--- Testando Processamento e Placeholders (Pechinchas) ---")
    # Cenário: Link interno no meio do texto não deve quebrar o índice do próximo link de loja
    text = 'Cupom aqui: https://t.me/pechinchasdoluiz4o/123. Compre: https://amzn.to/loja.'
    extra = "https://example.com/promo"
    
    clean_text, p_map = await process_and_replace_links(text, extra)
    
    print(f"Texto Limpo: {clean_text}")
    print(f"Mapa de Placeholders: {p_map}")
    
    # [LINK_0] deve ser o 'extra'
    assert p_map.get("[LINK_0]") == "https://example.com/promo"
    
    # [LINK_1] deve ser o 'https://amzn.to/loja'
    # O link do canal oficial NÃO deve ter sido substituído por placeholder
    assert "https://t.me/pechinchasdoluiz4o/123" in clean_text
    assert "[LINK_1]" in clean_text
    assert p_map.get("[LINK_1]") is not None
    
    print("\n✅ Todos os testes de link do Pechinchas passaram!")

if __name__ == "__main__":
    asyncio.run(test_fixes())
