import httpx
import asyncio
from config import ML_AFFILIATE_COOKIE
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, unquote
from bs4 import BeautifulSoup
import re
import hashlib
from datetime import datetime

def clean_tracking_params(url: str) -> str:
    """
    Remove parâmetros de rastreamento conhecidos para evitar conflitos e links sujos.
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Lista de parâmetros para remover
        params_to_remove = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'smid', 'pf_rd_p', 'pf_rd_r', 'pd_rd_w', 'pd_rd_wg', 'pd_rd_r',
            'dchild', 'keywords', 'qid', 'sr', 'th', 'psc', 'sp_atk', 'is_from_signup',
            'matt_tool', 'matt_word', 'product_trigger_id', 'gad_source', 'gbraid', 'gclid'
        ]
        
        filtered_params = {k: v for k, v in params.items() if k not in params_to_remove}
        
        # Recompor a URL
        new_query = urlencode(filtered_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    except Exception as e:
        print(f"⚠️ Erro ao limpar parâmetros: {e}")
        return url

async def convert_ml_to_affiliate(original_url: str) -> str:
    """
    Converte um link do Mercado Livre em link de afiliado usando a Stripe API.
    Lida com links de vitrine (/social/) extraindo o produto destacado.
    """
    if not ML_AFFILIATE_COOKIE:
        print("⚠️ ML_AFFILIATE_COOKIE não configurado. Mantendo link original.")
        return original_url

    parsed = urlparse(original_url)
    target_product_url = original_url

    # Se a URL for uma vitrine social de um concorrente (ex: /social/nerdofertas), 
    # precisamos acessar a vitrine e raspar a URL do produto destacado.
    if '/social/' in parsed.path:
        print(f"🔍 Link Social (Vitrine) detectado: {original_url}")
        try:
            # Reutiliza httpx para baixar a vitrine
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
                res = await client.get(original_url)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # 1. Tentar encontrar link de Lista Curada (seeMoreLink com _Container_)
                match_list = re.search(r'"seeMoreLink":"([^"]+lista\.mercadolivre\.com\.br\\u002F_Container_[^"]+)"', res.text)
                if not match_list:
                    match_list = re.search(r'"seeMoreLink":"([^"]+)"', res.text)
                
                if match_list and 'lista.mercadolivre.com.br' in match_list.group(1):
                    raw_link = match_list.group(1)
                    # O JSON escapa as barras como \u002F ou \/
                    target_product_url = raw_link.replace('\\u002F', '/').replace('\\/', '/')
                    print(f"✅ Lista curada extraída da vitrine: {target_product_url}")
                else:
                    # 2. Se não for lista, tentar achar o produto em destaque usual
                    # O produto destacado no topo tem a classe poly-component__link--action-link
                    featured_link = soup.select_one("a.poly-component__link--action-link")
                    if not featured_link:
                        # Fallback via url
                        featured_link = soup.find("a", href=re.compile("card-featured"))
                        
                    if featured_link and featured_link.get("href"):
                        target_product_url = featured_link['href']
                        print(f"✅ Produto extraído da vitrine: {target_product_url}")
                    else:
                        print(f"❌ Não foi possível encontrar o produto destacado ou lista na vitrine.")
        except Exception as e:
            print(f"⚠️ Erro ao acessar vitrine social: {e}")

    # Limpar a URL do produto antes de enviar para a API
    clean_url = clean_tracking_params(target_product_url)

    # Se a API falhar, o fallback é passar a URL original inteira (ou limpa) no ref do nosso link social genérico
    fallback_social_url = f"https://www.mercadolivre.com.br/social/drmkt?forceInApp=true&matt_word=drmk&ref={clean_url}"

    try:
        print(f"🔗 Convertendo ML via API Stripe: {clean_url}")
        # A API Stripe exige um NOVO cliente httpx para não enviar _csrf cookies das requisições anteriores
        async with httpx.AsyncClient(timeout=10.0) as api_client:
            api_headers = {
                'Content-Type': 'application/json',
                'Cookie': ML_AFFILIATE_COOKIE,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://www.mercadolivre.com.br',
                'Referer': clean_url,
            }
            body = {
                'url': clean_url,
                'tag': 'drmkt'
            }
            
            response = await api_client.post(
                'https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links',
                headers=api_headers,
                json=body,
                follow_redirects=False
            )

            if response.status_code >= 300 and response.status_code < 400:
                print(f"❌ API do ML redirecionou (provavelmente cookie expirado): {response.headers.get('location')}")
                return fallback_social_url

            if response.status_code != 200:
                print(f"❌ Erro na API do ML ({response.status_code}): {response.text}")
                return fallback_social_url

            data = response.json()
            if isinstance(data, dict):
                short_url = data.get('url') or data.get('short_url')
                if short_url: return short_url
            elif isinstance(data, list) and len(data) > 0:
                short_url = data[0].get('short_url')
                if short_url: return short_url

            return fallback_social_url

    except Exception as e:
        print(f"⚠️ Erro ao gerar link de afiliado ML: {e}")
        return fallback_social_url

async def convert_aliexpress_to_affiliate(original_url: str) -> str:
    """
    Converte um link do AliExpress para link de afiliado usando a API oficial (Open Platform).
    """
    from config import ALI_APP_KEY, ALI_APP_SECRET, ALI_TRACKING_ID
    
    if not ALI_APP_KEY or not ALI_APP_SECRET or not ALI_TRACKING_ID:
        print("⚠️ Credenciais do AliExpress não configuradas. Mantendo link original.")
        return clean_tracking_params(original_url)

    clean_url = clean_tracking_params(original_url)
    
    # Parâmetros obrigatórios da API TopClient AliExpress
    params = {
        "method": "aliexpress.affiliate.link.generate",
        "app_key": ALI_APP_KEY,
        "sign_method": "md5",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "format": "json",
        "v": "2.0",
        "promotion_link_type": "0",
        "source_values": clean_url,
        "tracking_id": ALI_TRACKING_ID
    }
    
    # Algoritmo de Assinatura (MD5) da plataforma
    # 1. Ordenar parâmetros em ordem alfabética pela chave
    sorted_keys = sorted(params.keys())
    # 2. String = SECRET_KEY + key1 + value1 + key2 + value2 ... + SECRET_KEY
    sign_str = ALI_APP_SECRET
    for k in sorted_keys:
        sign_str += str(k) + str(params[k])
    sign_str += ALI_APP_SECRET
    
    # 3. MD5 hash em Maiúsculo
    sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()
    params["sign"] = sign

    try:
        print(f"🔗 Convertendo AliExpress via API Oficial: {clean_url}")
        async with httpx.AsyncClient(timeout=10.0) as api_client:
            response = await api_client.post(
                "https://api-sg.aliexpress.com/sync",
                data=params, # enviar como form-data
                headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
            )
            
            if response.status_code != 200:
                print(f"❌ Erro na API do AliExpress ({response.status_code}): {response.text}")
                return clean_url
                
            data = response.json()
            
            # Formato de resposta esperado: 
            # {"aliexpress_affiliate_link_generate_response": {
            #    "resp_result": { "result": { "promoted_links": { "promoted_link": [{"promotion_link": "..."}]}}}
            # }}
            
            try:
                base_resp = data.get("aliexpress_affiliate_link_generate_response", {})
                resp_result = base_resp.get("resp_result", {})
                
                # O resp_code pode vir como int ou str
                resp_code = str(resp_result.get("resp_code", ""))
                if resp_code != "200":
                    print(f"❌ API do AliExpress retornou erro na resposta interna: {resp_result}")
                    return clean_url
                    
                result = resp_result.get("result", {})
                promotion_links = result.get("promotion_links", {}).get("promotion_link", [])
                
                if promotion_links and len(promotion_links) > 0:
                    item_info = promotion_links[0]
                    short_url = item_info.get("promotion_link")
                    if short_url:
                        return short_url
                    else:
                        print(f"⚠️ Erro ao converter item no AliExpress: {item_info.get('message', 'Desconhecido')}")
                else:
                    print(f"⚠️ Módulo promotion_links vazio na resposta.")
                        
            except Exception as parse_err:
                print(f"⚠️ Erro ao analisar resposta do AliExpress: {parse_err}. Retorno bruto: {data}")
                return clean_url

    except Exception as e:
        print(f"⚠️ Erro ao gerar link de afiliado AliExpress: {e}")
        
    return clean_url

async def convert_to_affiliate(url: str) -> str:
    """
    Identifica a loja e aplica a lógica de conversão correspondente.
    """
    try:
        parsed = urlparse(url)
        if not parsed.hostname:
            return url
        domain = parsed.hostname.replace('www.', '').lower()
    except:
        return url

    # Mercado Livre
    if 'mercadolivre.com.br' in domain or 'mercadolibre.com' in domain:
        return await convert_ml_to_affiliate(url)
    
    # Amazon
    if 'amazon.com.br' in domain or 'amazon.com' in domain:
        # Importa a tag da config (fazemos o import local para evitar circular caso ocorra no futuro, ou import global)
        from config import AMAZON_TAG
        
        # Injetar tag de afiliado limpando sujeiras de outras tags
        params = parse_qs(parsed.query)
        
        # Remove tags antigas ou de outros afiliados
        if 'tag' in params:
            del params['tag']
            
        # Limpa parâmetros de rastreio de terceiros comuns na rede Amazon
        params_to_remove = ['linkCode', 'hvadid', 'hvpos', 'hvnetw', 'hvrand', 'hvpone', 'hvptwo', 'hvqmt', 'hvdev', 'hvdvcmdl', 'hvlocint', 'hvlocphy', 'hvtargid', 'psc', 'language', 'gad_source', 'mcid', 'ref']
        for p in params_to_remove:
            if p in params:
                del params[p]
                
        # Adiciona a nossa tag lida das configurações
        params['tag'] = [AMAZON_TAG] 
        
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    
    # AliExpress
    if 'aliexpress.com' in domain or 'aliexpress.us' in domain or 'aliexpress.ru' in domain or 's.click.aliexpress' in domain:
        return await convert_aliexpress_to_affiliate(url)
        
    # Futuramente: Shopee, Magalu...
    
    return clean_tracking_params(url)
