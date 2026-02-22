import httpx
from bs4 import BeautifulSoup
import os

async def fetch_product_metadata(url: str) -> dict:
    """
    Acessa a URL e tenta extrair o título do produto e a imagem principal (og:image).
    Retorna um dicionário com 'title', 'image_url' e 'local_image_path'.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1"
    }
    
    metadata = {
        "title": None,
        "image_url": None,
        "local_image_path": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tenta pegar og:title, se não tiver, pega a tag <title>
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                metadata["title"] = og_title["content"]
            else:
                title_tag = soup.find("title")
                if title_tag:
                    metadata["title"] = title_tag.text.strip()
                    
            # Tenta pegar og:image
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                metadata["image_url"] = og_image["content"]
            
            # --- Fallbacks Específicos Amazon ---
            if not metadata.get("image_url"):
                # 1. Tenta o seletor principal da imagem da Amazon
                img_tag = soup.find("img", id="landingImage") or soup.find("img", id="main-image") or soup.find("img", {"data-old-hires": True})
                
                if img_tag:
                    # Amazon as vezes usa 'data-old-hires' ou 'data-a-dynamic-image' ou src
                    img_src = img_tag.get("data-old-hires") or img_tag.get("src")
                    
                    if not img_src and img_tag.get("data-a-dynamic-image"):
                        try:
                            import json
                            # data-a-dynamic-image é um JSON tipo {"url": [w,h], ...}
                            dyn_img = json.loads(img_tag.get("data-a-dynamic-image"))
                            img_src = list(dyn_img.keys())[0] if dyn_img else None
                        except Exception as e:
                            print(f"Erro ao parsear dynamic image: {e}")
                    
                    metadata["image_url"] = img_src
                
                # 2. Se ainda não achou, tenta qualquer imagem que pareça ser a principal (geralmente grande)
                if not metadata.get("image_url"):
                    for img in soup.find_all("img"):
                        # Ignora captcha e ícones pequenos
                        img_src = img.get("src", "")
                        if "captcha" in img_src.lower() or "icon" in img_src.lower(): continue
                        
                        width = img.get("width", "0")
                        if width.isdigit() and int(width) > 300:
                            metadata["image_url"] = img_src
                            break

            # Baixa a imagem se encontrou
            if metadata.get("image_url"):
                img_url = metadata["image_url"]
                # Garante que a URL é absoluta
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                
                print(f"尝试下载图片: {img_url}")
                try:
                    img_response = await client.get(img_url, headers=headers, timeout=10.0)
                    if img_response.status_code == 200:
                        if not os.path.exists("downloads"):
                            os.makedirs("downloads")
                        
                        import random
                        file_name = f"downloads/scraped_{random.randint(1000, 9999)}.jpg"
                        with open(file_name, "wb") as f:
                            f.write(img_response.content)
                        metadata["local_image_path"] = file_name
                        print(f"✅ Imagem salva em: {file_name}")
                    else:
                        print(f"❌ Falha ao baixar imagem: Status {img_response.status_code}")
                except Exception as e:
                    print(f"❌ Erro ao baixar imagem: {e}")
                        
    except Exception as e:
        print(f"Erro no Scraper para a URL {url}: {e}")
        
    return metadata
