import asyncio
import httpx
from bs4 import BeautifulSoup
import re
import random
import os

async def run_diagnostic():
    url = input("Cole a URL da Shopee (aquela com /product/): ").strip()
    print("-" * 50)
    print("INICIANDO DIAGNÓSTICO DE HEADERS E BLOQUEIO")
    print("-" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    print("1. Testando requisição padrão (Sem Proxy)...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 403:
                print(">>> RESULTADO: Bloqueio 403 Detectado. IP do servidor está na lista negra.")
            elif resp.status_code == 200:
                print(">>> RESULTADO: Sucesso parcial. Verificando conteúdo...")
                if "captcha" in resp.text.lower():
                    print(">>> AVISO: Captcha detectado no HTML.")
    except Exception as e:
        print(f"Erro: {e}")

    print("\n2. ORIENTAÇÕES PARA F12 (CHROME):")
    print("A. No Chrome, abra a Dashboard da Shopee e o console (F12).")
    print("B. Vá na aba NETWORK e marque 'Preserve Log'.")
    print("C. Converta o link no dashboard.")
    print("D. Procure por uma requisição POST que comece com 'graphql' ou 'api/v4'.")
    print("E. No painel da direita, clique em 'Headers' e me mande o que aparece em:")
    print("   - x-sap-sec (se houver)")
    print("   - af-ac-enc-dat (se houver)")
    print("   - x-shopee-client-id (se houver)")
    print("-" * 50)
    print("Isso vai me permitir clonar o comportamento exato que funciona no seu navegador.")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
