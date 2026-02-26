import re
import asyncio
import httpx

async def expand_url(url: str) -> str:
    if any(d in url for d in ['s.shopee', 'shope.ee', 'shopee.page.link']):
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                r = await client.get(url)
                return str(r.url)
        except Exception as e:
            return url
    return url

def get_shopee_slug(url: str):
    try:
        path = url.split('?')[0].rstrip('/').split('/')[-1]
        slug = re.sub(r'-i\.\d+\.\d+$', '', path)
        candidate = slug.replace('-', ' ').strip()
        if len(candidate) > 8:
            return candidate
    except Exception:
        pass
    return None

async def test():
    urls = [
        "https://shopee.com.br/Apple-iPhone-16-128GB-Branco-i.1537155548.58251533763",
        "https://shope.ee/8A9iYVz1G2" # Exemplo de link curto que redireciona para um produto com slug
    ]
    
    for u in urls:
        expanded = await expand_url(u)
        slug = get_shopee_slug(expanded)
        print(f"Original: {u}")
        print(f"Expanded: {expanded[:80]}...")
        print(f"Slug Title: {slug}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test())
