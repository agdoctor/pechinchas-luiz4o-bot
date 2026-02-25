import asyncio
from affiliate import convert_shopee_to_affiliate
import os
from dotenv import load_dotenv

async def test_conversion():
    load_dotenv()
    
    # URL de teste da Shopee
    test_url = "https://shopee.com.br/product/308949826/22194164344"
    
    print(f"Iniciando teste de conversao Shopee API...")
    print(f"URL Original: {test_url}")
    
    try:
        short_url = await convert_shopee_to_affiliate(test_url)
        print(f"\nResultado Final: {short_url}")
        
        if "shope.ee" in short_url or "shopee.com.br" in short_url:
            if "universal-link" in short_url:
                print("Atencao: O link parece ser o fallback (Universal Link). Verifique os logs acima por erros da API.")
            else:
                print("Sucesso! O link foi convertido via API Oficial.")
        else:
            print("Erro: O link retornado nao parece ser um link da Shopee valido.")
            
    except Exception as e:
        print(f"Falha critica no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_conversion())
