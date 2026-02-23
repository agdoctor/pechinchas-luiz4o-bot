import asyncio
from urllib.parse import urlparse
import sys
import os

# Adiciona o diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_domain():
    urls = [
        "https://mercadolivre.com/sec/1PJg3nq",
        "https://www.mercadolivre.com.br/social/test"
    ]
    
    for url in urls:
        parsed = urlparse(url)
        domain = parsed.hostname.replace('www.', '').lower()
        print(f"URL: {url}")
        print(f"Domain: {domain}")
        match_br = 'mercadolivre.com.br' in domain
        match_es = 'mercadolibre.com' in domain
        print(f"Matches .br: {match_br}")
        print(f"Matches .es: {match_es}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_domain())
