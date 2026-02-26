import asyncio
import httpx
from affiliate import get_shopee_product_info
from scraper import fetch_product_metadata

async def test_problematic_shopee_url():
    url = 'https://s.shopee.com.br/7VBEgIyzUE'
    
    print(f"\n--- TESTANDO URL: {url} ---\n")
    
    # 1. Testar via get_shopee_product_info (APIs + Fallbacks)
    print(">>> Estratgia: Affiliate APIs & Fallbacks...")
    info = await get_shopee_product_info(url)
    if info:
        print(f"SUCCESS via Affiliate Logic!")
        print(f"   Titulo: {info.get('title')}")
        print(f"   Imagem: {info.get('image')}")
    else:
        print("FAILED via Affiliate Logic.")

    print("-" * 40)

    # 2. Testar via fetch_product_metadata (Scraper + Affiliate Fallback)
    print(">>> Estrategia: Scraper + Fallback...")
    metadata = await fetch_product_metadata(url)
    if metadata and metadata.get("title"):
        print(f"SUCCESS via SmartScraper!")
        print(f"   Titulo: {metadata.get('title')}")
        print(f"   Imagem: {metadata.get('image_url')}")
        print(f"   Local: {metadata.get('local_image_path')}")
    else:
        print("FAILED via SmartScraper.")

if __name__ == "__main__":
    asyncio.run(test_problematic_shopee_url())
