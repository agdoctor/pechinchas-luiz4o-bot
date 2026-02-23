import httpx
import base64
import os
import asyncio
from config import WHATSAPP_ENABLED, WHATSAPP_API_URL, WHATSAPP_API_KEY, WHATSAPP_INSTANCE, WHATSAPP_DESTINATION

async def send_whatsapp_msg(text: str, media_path: str | None = None):
    """
    Envia uma mensagem para o WhatsApp via Evolution API.
    Suporta texto simples e imagens (via base64).
    """
    if not WHATSAPP_ENABLED or not WHATSAPP_API_URL or not WHATSAPP_API_KEY or not WHATSAPP_DESTINATION:
        return None

    # Normaliza a URL da API (remove barra final se houver)
    api_url = WHATSAPP_API_URL.rstrip('/')
    
    # Prepara o cliente HTTP
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "apikey": WHATSAPP_API_KEY,
            "Content-Type": "application/json"
        }
        
        try:
            if media_path and os.path.exists(media_path):
                # Envio com Imagem
                endpoint = f"{api_url}/message/sendMedia/{WHATSAPP_INSTANCE}"
                
                with open(media_path, "rb") as f:
                    mime_type = "image/png" if media_path.endswith(".png") else "image/jpeg"
                    b64_data = base64.b64encode(f.read()).decode('utf-8')
                    
                payload = {
                    "number": WHATSAPP_DESTINATION,
                    "mediaMessage": {
                        "mediatype": "image",
                        "caption": text,
                        "media": b64_data,
                        "fileName": os.path.basename(media_path)
                    }
                }
            else:
                # Envio apenas de Texto
                endpoint = f"{api_url}/message/sendText/{WHATSAPP_INSTANCE}"
                payload = {
                    "number": WHATSAPP_DESTINATION,
                    "text": text,
                    "delay": 1200,
                    "linkPreview": True
                }
            
            print(f"📡 Enviando para WhatsApp ({endpoint})...")
            response = await client.post(endpoint, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                print("✅ Mensagem enviada com sucesso para o WhatsApp!")
                return True
            else:
                print(f"❌ Erro na Evolution API ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao conectar com Evolution API: {e}")
            return False

# Teste simples (Manual)
if __name__ == "__main__":
    # Para testar, execute: python whatsapp_publisher.py
    async def main():
        success = await send_whatsapp_msg("Teste de postagem via Bot Pechinchas!")
        print(f"Resultado teste: {success}")
    
    if WHATSAPP_ENABLED:
        asyncio.run(main())
