import asyncio
import httpx
import sys
import os

# Adiciona o diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def expand_url(short_url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            response = await client.get(short_url)
            return str(response.url)
    except Exception as e:
        print(f"Erro ao expandir URL {short_url}: {e}")
        return short_url

async def test():
    url = "https://mercadolivre.com/sec/1PJg3nq"
    expanded = await expand_url(url)
    print(f"Original: {url}")
    print(f"Expanded: {expanded}")

if __name__ == "__main__":
    asyncio.run(test())
