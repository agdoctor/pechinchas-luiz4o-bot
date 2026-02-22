import asyncio
import os
import re
import hashlib
from telethon import TelegramClient, events
from config import API_ID, API_HASH, TARGET_CHANNEL
from database import get_canais, get_keywords, get_config, check_duplicate, add_to_history

from rewriter import reescrever_promocao
from links import process_and_replace_links
from publisher import publish_deal, bot
from watermark import apply_watermark
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# O ADMIN_USER_ID agora é recuperado do banco de dados (chave 'admin_id')

# Variável global para armazenar as ofertas que aguardam aprovação manual
ofertas_pendentes_admin = []

# Certifique-se de que o diretório de downloads existe
if not os.path.exists("downloads"):
    os.makedirs("downloads")

client = TelegramClient('pechinchas_userbot', API_ID, API_HASH)

# Fila para gerenciar o delay e as postagens
post_queue = asyncio.Queue()

async def worker_queue():
    """Worker que fica rodando em background consumindo a fila e aplicando o delay"""
    while True:
        try:
            item = await post_queue.get()
            
            # Suporta tanto (texto, media) quanto (texto, media, markup)
            if len(item) == 3:
                texto_final, media_path, reply_markup = item
            else:
                texto_final, media_path = item
                reply_markup = None
            
            delay_str = get_config("delay_minutos") or "0"
            try:
                delay_mins = float(delay_str)
            except:
                delay_mins = 0
                
            if delay_mins > 0:
                print(f"⏳ Delay ativado. Aguardando {delay_mins} minutos antes de publicar...")
                await asyncio.sleep(delay_mins * 60)
            
            print("📤 Worker publicando oferta da fila...")
            await publish_deal(texto_final, media_path, reply_markup=reply_markup)
            
            # Limpar a mídia local depois de publicar de verdade
            if media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                    print("🗑️ Mídia local apagada.")
                except Exception as e:
                    print(f"Não foi possível apagar arquivo: {e}")
                    
            post_queue.task_done()
        except Exception as e:
            print(f"Erro no worker de fila: {e}")
            await asyncio.sleep(5)

async def start_monitoring():
    source_channels = get_canais()
    
    # Inicia o worker em background
    asyncio.create_task(worker_queue())
    
    print("⏳ Iniciando o Userbot. Se for a primeira vez, aguarde a solicitação do código no terminal.")
    await client.start()
    
    print(f"✅ Userbot conectado! Monitorando do Banco de Dados: {source_channels}")
    
    # Cache para não processar o mesmo álbum (várias fotos) duas vezes
    processed_grouped_ids = set()
    # Cache para não processar a mesma mensagem duas vezes (ex: edições rápidas ou múltiplos triggers do Telethon)
    processed_message_ids = set()
    
    @client.on(events.NewMessage())
    async def new_message_handler(event):
        try:
            # Verifica se o canal está na lista monitorada (vinda do banco de dados)
            source_channels = get_canais()
            
            # Identificadores possíveis: @username ou ID numérico (como string ou int)
            chat = await event.get_chat()
            chat_username = getattr(chat, 'username', None)
            chat_id = str(event.chat_id)
            
            is_monitored = False
            if chat_username and chat_username.lower() in [c.lower().replace('@', '') for c in source_channels]:
                is_monitored = True
            elif chat_id in source_channels or str(event.chat_id) in source_channels:
                is_monitored = True
                
            if not is_monitored:
                return

            # Verifica se o bot está pausado globalmente
            if get_config("pausado") == "1":
                return
                
            # Verifica mensagens já processadas pelo ID exato
            if event.message.id in processed_message_ids:
                print(f"⏭️ Mensagem já processada ignorada (ID: {event.message.id})")
                return
            processed_message_ids.add(event.message.id)
            if len(processed_message_ids) > 1000:
                processed_message_ids.clear()
                
            # Verifica se a mensagem faz parte de um álbum já processado
            if event.message.grouped_id:
                if event.message.grouped_id in processed_grouped_ids:
                    print(f"⏭️ Mensagem extra do mesmo álbum ignorada: {event.message.grouped_id}")
                    return
                processed_grouped_ids.add(event.message.grouped_id)
                # Mantém o set pequeno
                if len(processed_grouped_ids) > 500:
                    processed_grouped_ids.clear()
                
            print("\n" + "="*50)
            print("🚨 Nova mensagem identificada no canal fonte!")
            mensagem_texto = event.raw_text
            
            # Se a mensagem for só mídia ou mensagem vazia ignora
            if not mensagem_texto and not event.message.media:
                return
                
            # Verifica Preço Mínimo (Se houver $ / R$ no texto)
            preco_min = float(get_config("preco_minimo") or "0")
            if preco_min > 0:
                # Busca valores obrigatoriamente procedidos por R$
                valores_encontrados = re.findall(r'R\$\s?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', mensagem_texto)
                if valores_encontrados:
                    # Converte o primeiro valor achado pra float
                    str_valor = valores_encontrados[0].replace('.', '').replace(',', '.')
                    try:
                        valor_num = float(str_valor)
                        if valor_num < preco_min:
                            print(f"🛑 Ignorado por Filtro de Preço: R${valor_num:.2f} é menor que mínimo R${preco_min:.2f}")
                            return
                    except:
                        pass
                
            # --- DEDUPLICAÇÃO (Cooldown 60 min) ---
            # Extrai título (primeira linha ou primeiras palavras) e primeiro preço para criar um hash idêntico
            primeira_linha = mensagem_texto.split('\n')[0].strip()
            # Remove emojis e sujeira do título para o hash ficar mais estável
            titulo_limpo = re.sub(r'[^\w\s]', '', primeira_linha).strip().lower()[:50]
            
            # Pega o primeiro valor R$ achado (ou 0 se não houver)
            todos_precos = re.findall(r'R\$\s?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', mensagem_texto)
            valor_referencia = todos_precos[0].replace('.', '').replace(',', '.') if todos_precos else "0"
            
            # Cria o hash único (Titulo + Valor)
            hash_str = f"{titulo_limpo}_{valor_referencia}"
            hash_id = hashlib.md5(hash_str.encode()).hexdigest()
            
            if check_duplicate(hash_id):
                print(f"⏭️ Oferta duplicada detectada (Título/Valor recente). Ignorando: {primeira_linha} | R${valor_referencia}")
                return
            
            # Registra no histórico para as próximas checagens (cooldown de 60 min gerenciado no database.py)
            add_to_history(hash_id)

            # Verifica as keywords (se a lista não for vazia)
            keywords = get_keywords()
            if keywords:
                has_keyword = any(kw.lower() in mensagem_texto.lower() for kw in keywords)
                if not has_keyword:
                    # Nenhuma keyword encontrada, ignorar mensagem
                    return
            
            # --- NOTIFICAÇÃO ADMIN ---
            admin_id_str = get_config("admin_id")
            if admin_id_str:
                try:
                    msg_info = f"🔎 **Nova oferta detectada!**\nCanal: `{event.chat.title or event.chat_id}`\nProduzindo publicação agora..."
                    await bot.send_message(chat_id=int(admin_id_str), text=msg_info, parse_mode="Markdown")
                except:
                    pass
            
            media_path = None
            if event.message.media:
                print("⏬ Baixando mídia associada...")
                media_path = await event.message.download_media(file="downloads/")
                print(f"✅ Mídia baixada: {media_path}")
                
                # Applica a marca d'água (se o arquivo watermark.png existir na raiz)
                try:
                    media_path = apply_watermark(media_path)
                    print("🖌️ Marca d'água aplicada à imagem.")
                except Exception as e:
                    print(f"⚠️ Não foi possível aplicar marca d'água: {e}")
            
            # --- FASE 1: Extrair, Remover e Processar Links (Conversão e Expansão) ---
            print("🔗 Processando links e substituindo por placeholders...")
            texto_com_placeholders, placeholder_map = await process_and_replace_links(mensagem_texto)
            print(f"✅ {len(placeholder_map)} links processados.")
            
            # --- FASE 2: Reescrever Texto com Gemini ---
            print("🧠 Passando para o Gemini reescrever a copy...")
            texto_reescrito = await reescrever_promocao(texto_com_placeholders)
            
            # --- FASE 3: Remontar o Texto Final Substituindo Placeholders ---
            texto_final = texto_reescrito
            
            if placeholder_map:
                for placeholder, final_url in placeholder_map.items():
                    # Se o link original era da blacklist ou deu erro e for None, ignoramos a formatação ou deletamos o placeholder
                    if final_url is None:
                        texto_final = texto_final.replace(placeholder, "")
                    else:
                        botao_html = f"🛒 <a href='{final_url}'>Pegar promoção</a>"
                        texto_final = texto_final.replace(placeholder, botao_html)
                        
            # Remove qualquer placeholder residual que o Gemini possa ter inventado
            texto_final = re.sub(r'\[LINK_\d+\]', '', texto_final)
                    
            # --- FASE 3.5: Adicionar Assinatura Customizada ---
            assinatura = get_config("assinatura")
            if assinatura:
                texto_final += f"\n\n{assinatura}"
            
            print("✅ Texto final pronto!")
            
            # --- FASE 4: Direcionamento (Aprovação, Fila ou Direto) ---
            admin_id_str = get_config("admin_id")
            if not admin_id_str:
                print("⚠️ Admin ID não configurado no banco. O administrador precisa dar /start no bot.")
                # Se não tem admin mas o bot deveria postar, vamos colocar na fila apenas se NÃO for manual
                if get_config("aprovacao_manual") != "1":
                    await post_queue.put((texto_final, media_path, None))
                return

            admin_id = int(admin_id_str)
            msg_amostra = f"**NOVA OFERTA ENCONTRADA!**\n\n{texto_final}"

            if get_config("aprovacao_manual") == "1":
                # Lógica de aprovação manual
                print(f"⚖️ Modo Aprovação Manual ativado. Enviando para o Admin {admin_id}...")
                
                # Salva a oferta para aprovação futura
                ofertas_pendentes_admin.append({"texto": texto_final, "media": media_path})
                item_id = len(ofertas_pendentes_admin) - 1
                
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Postar", callback_data=f"aprovar_{item_id}"),
                        InlineKeyboardButton(text="✏️ Editar", callback_data=f"editar_{item_id}"),
                        InlineKeyboardButton(text="❌ Descartar", callback_data=f"recusar_{item_id}")
                    ]
                ])

                if media_path:
                    photo = FSInputFile(media_path)
                    try:
                        await bot.send_photo(chat_id=admin_id, photo=photo, caption=msg_amostra, reply_markup=markup, parse_mode="HTML")
                    except Exception as e:
                        # Se falhar o html
                        await bot.send_photo(chat_id=admin_id, photo=photo, caption=msg_amostra[:1024], reply_markup=markup)
                else:
                    await bot.send_message(chat_id=admin_id, text=msg_amostra, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)

            else:
                # Automático, joga na fila, o Worker dá o delay e posta
                print("📥 Enviando oferta para a fila de publicação...")
                await post_queue.put((texto_final, media_path, None))
            
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")
            admin_id_str = get_config("admin_id")
            if admin_id_str:
                try:
                    await bot.send_message(chat_id=int(admin_id_str), text=f"⚠️ **Erro no Monitor (Pechinchas):**\n`{str(e)[:500]}`", parse_mode="Markdown")
                except:
                    pass

    # Loop de reconexão persistente para evitar quedas por [Errno 104] (Connection reset by peer)
    while True:
        try:
            if not client.is_connected():
                await client.connect()
            await client.run_until_disconnected()
        except Exception as connection_error:
            print(f"⚠️ Aviso: Telethon desconectado. Reconectando em 10 segundos... Motivo: {connection_error}")
            await asyncio.sleep(10)
