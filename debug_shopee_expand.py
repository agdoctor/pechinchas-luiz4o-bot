import httpx
import asyncio
import re

async def debug_expand():
    url = "https://s.shopee.com.br/7VBEgIyzUE"
    print(f"Original: {url}")
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        r = await client.get(url)
        expanded = str(r.url)
        print(f"Expanded: {expanded}")
        
        path_segments = expanded.split('?')[0].rstrip('/').split('/')
        print(f"Segments: {path_segments}")
        last_part = path_segments[-1]
        print(f"Last part: {last_part}")
        
        slug = re.sub(r'-i\.\d+\.\d+$', '', last_part)
        print(f"Derived Slug: {slug}")

if __name__ == "__main__":
    asyncio.run(debug_expand())
