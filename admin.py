from typing import Optional
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, ReplyKeyboardRemove, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import config
from config import BOT_TOKEN
import database
from database import add_canal, get_canais, remove_canal, add_keyword, get_keywords, remove_keyword, get_config, set_config, is_admin, get_admins, add_admin, remove_admin, get_negative_keywords, add_negative_keyword, remove_negative_keyword
import os
import sys
import asyncio
import re

# O ADMIN_USER_ID agora é recuperado dinamicamente do banco de dados 
# quando o usuário envia /start ou /admin

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Estados simples para a conversa
user_states = {}
user_temp_data = {}

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    
    # Adiciona o botão do Painel Principal (Mini App) - PRIORIDADE
    webapp_url = get_config("webapp_url")
    console_token = get_config("console_token")
    
    if webapp_url and console_token:
        base_url = webapp_url.rstrip('/')
        full_url = f"{base_url}/?token={console_token}"
        builder.button(text="🖥️ ABRIR PAINEL DE CONTROLE", web_app=WebAppInfo(url=full_url))
        
    builder.button(text="🔗 Criar Oferta via Link", callback_data="menu_criar_link")
    builder.button(text="🎉 Ver Sorteios Ativos", callback_data="menu_sorteios")
    builder.button(text="🤖 Comandos Ativos", callback_data="mostrar_comandos")
    
    builder.adjust(1)
    return builder.as_markup()

@dp.callback_query(F.data == "mostrar_comandos")
async def mostrar_comandos_handler(callback: CallbackQuery):
    texto = (
        "🤖 **Comandos Ativos do Bot:**\n\n"
        "🔹 `/start` - Abre o painel principal interativo\n"
        "🔹 `/enviar` - Atalho para enviar uma oferta no canal\n"
        "🔹 `/log` - Recebe o arquivo `bot.log` com logs do terminal\n"
        "🔹 `/meuid` - Retorna o seu ID numérico do Telegram\n"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.message(Command("start", "admin"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    # Primeira vez? Registra como admin
    if not get_admins():
        add_admin(user_id, message.from_user.full_name or "Admin")
        await message.answer("👋 **Bem-vindo!** Você foi registrado como o primeiro admin.")
    else:
        # Verifica se 'somente admins' está ativo e se o usuário é admin
        if get_config("only_admins") == "1" and not is_admin(user_id):
            await message.answer("❌ **Acesso Negado.** Apenas administradores podem interagir com este bot.")
            return
        
        if not is_admin(user_id):
            await message.answer("👋 Bem-vindo ao Bot Pechinchas!")
            return

    # Gera URL para o Mini App
    url = f"{get_config('webapp_url')}?token={get_config('console_token')}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖥️ ABRIR PAINEL DE CONTROLE", web_app=WebAppInfo(url=url))]
    ])
    
    await message.answer(
        "🛠️ **Painel de Controle Admins**\n\n"
        "Toda a gestão do bot agora é feita pelo Mini App.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove()) # Limpa telado físico

@dp.message(Command("meuid"))
async def cmd_meuid(message: Message):
    await message.answer(f"Seu ID do Telegram é: <code>{message.from_user.id}</code>", parse_mode="HTML")

@dp.message(Command("config"))
async def cmd_config(message: Message):
    # Mantém apenas para emergências se o WebApp sumir
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Uso: `/config chave valor`", parse_mode="Markdown")
        return
    set_config(args[1], " ".join(args[2:]))
    await message.answer(f"✅ `{args[1]}` atualizado.")

from aiogram.types import FSInputFile

@dp.message(Command("log"))
async def cmd_log(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    log_path = "bot.log"
    if not os.path.exists(log_path):
        await message.answer("⚠️ Nenhum arquivo de log encontrado até o momento.")
        return
        
    try:
        log_file = FSInputFile(log_path)
        await message.answer_document(document=log_file, caption="📄 Arquivo de log atual do bot.")
    except Exception as e:
        await message.answer(f"❌ Erro ao enviar log: {e}")

@dp.message(Command("testali"))
async def cmd_test_ali(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("⚠️ Uso: `/testali [link do aliexpress]`", parse_mode="Markdown")
        return
        
    url = parts[1].strip()
    await message.answer("🔄 Testando conversão da API AliExpress...\nPor favor aguarde...")
    try:
        import affiliate
        result = await affiliate.convert_aliexpress_to_affiliate(url)
        # Tira parse_mode "Markdown" para evitar erro quando o URL contiver muitos `_` ou `*`
        await message.answer(
            f"✅ Resultado da Conversão:\n\n"
            f"{result}\n\n"
            f"Se o link começar com s.click.aliexpress.com/e/... a sua API funcionou! "
            f"Se tiver deep_link.htm, caiu no fallback de erro."
        )
    except Exception as e:
        await message.answer(f"❌ Erro no teste: {e}")

@dp.message(Command("enviar"))
async def cmd_enviar_shortcut(message: Message):
    await start_criar_oferta_msg(message)

@dp.message(Command("reiniciar"))
async def cmd_reiniciar(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔄 **Reiniciando o bot...**\nAguarde alguns instantes para que o sistema o inicie novamente.")
    await asyncio.sleep(1)
    
    try:
        from publisher import bot
        await bot.session.close()
    except: pass
    try:
        from monitor import client as userbot
        await userbot.disconnect()
    except: pass

    os.execv(sys.executable, ['python'] + sys.argv)

@dp.message(F.text == "🛠️ Abrir Painel Admin")
async def btn_admin(message: Message):
    await cmd_start(message)

@dp.message(F.text == "➕ Enviar Promoção")
async def btn_enviar(message: Message):
    await cmd_enviar_shortcut(message)

async def start_criar_oferta_msg(message: Message):
    user_states[message.from_user.id] = "esperando_link_criacao"
    user_temp_data[message.from_user.id] = {}
    await message.answer("🔗 **Criador de Ofertas**\n\nPor favor, envie o **LINK** do produto que deseja anunciar (Ex: Amazon, Mercado Livre):")

async def start_copiar_post_telegram(message: Message):
    link = message.text.strip()
    msg_status = await message.answer("🔍 Buscando postagem no Telegram...")
    try:
        import re
        match = re.search(r't\.me/(?:c/)?([^/]+)/(\d+)', link)
        if not match:
            await msg_status.edit_text("❌ Link do Telegram inválido. Use o formato t.me/canal/123")
            return
            
        channel_or_id = match.group(1)
        msg_id = int(match.group(2))
        
        if channel_or_id.isdigit():
            channel_or_id = int(f"-100{channel_or_id}")
            
        from monitor import client as telethon_client
        if not telethon_client.is_connected():
            await telethon_client.connect()
            
        telethon_msgs = await telethon_client.get_messages(channel_or_id, ids=[msg_id])
        if not telethon_msgs or not telethon_msgs[0]:
            await msg_status.edit_text("❌ Não foi possível encontrar a mensagem. Verifique se o bot de monitoramento tem acesso ao canal.")
            return
            
        tg_msg = telethon_msgs[0]
        texto_original = tg_msg.text or ""
        
        # Download da mídia se existir
        local_media_path = None
        if tg_msg.media:
            await msg_status.edit_text("📥 Baixando mídia...")
            from monitor import base_downloads_path
            local_media_path = await telethon_client.download_media(tg_msg, file=base_downloads_path)
            
            # Aplica marca d'água se for imagem
            if local_media_path and (local_media_path.endswith('.jpg') or local_media_path.endswith('.png') or local_media_path.endswith('.jpeg')):
                from watermark import apply_watermark
                local_media_path = apply_watermark(local_media_path)
        
        await msg_status.edit_text("✨ Reescrevendo postagem com IA...")
        
        # Processamento de links e reescrita
        from links import process_and_replace_links
        from rewriter import reescrever_promocao
        
        texto_com_nossos_links, _ = await process_and_replace_links(texto_original)
        texto_reescrito = await reescrever_promocao(texto_com_nossos_links)
        
        # Adiciona assinatura se houver
        assinatura = get_config("assinatura")
        if assinatura:
            texto_reescrito += f"\n\n{assinatura}"
            
        # Adiciona à lista de pendentes para aprovação
        from monitor import ofertas_pendentes_admin
        item_id = len(ofertas_pendentes_admin)
        ofertas_pendentes_admin.append({
            "texto": texto_reescrito,
            "media": local_media_path,
            "original_url": link
        })
        
        await msg_status.delete()
        
        # Mostra prévia para o admin
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Postar", callback_data=f"aprovar_{item_id}"),
                InlineKeyboardButton(text="✏️ Editar", callback_data=f"editar_{item_id}"),
                InlineKeyboardButton(text="❌ Descartar", callback_data=f"recusar_{item_id}")
            ]
        ])
        
        if local_media_path:
            await message.answer_photo(photo=FSInputFile(local_media_path), caption=texto_reescrito, reply_markup=markup, parse_mode="HTML")
        else:
            await message.answer(text=texto_reescrito, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
            
    except Exception as e:
        await msg_status.edit_text(f"❌ Erro ao copiar postagem: {e}")

# --- CRIAR OFERTA MANUAL ---
@dp.callback_query(F.data == "menu_criar_link")
async def start_criar_oferta(callback: CallbackQuery):
    await start_criar_oferta_msg(callback.message)
    await callback.answer()

# --- CANAIS ---
@dp.callback_query(F.data == "menu_canais")
async def menu_canais(callback: CallbackQuery):
    canais = get_canais()
    texto = "📺 **Canais Monitorados:**\n" + "\n".join([f"- {c}" for c in canais])
    texto += "\n\nPara remover, clique no canal abaixo. Para adicionar, digite o @ ou link do canal no chat agora."
    
    builder = InlineKeyboardBuilder()
    for c in canais:
        builder.button(text=f"❌ {c}", callback_data=f"delcanal_{c}")
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    builder.adjust(1)
    
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
    user_states[callback.from_user.id] = "esperando_canal"

@dp.callback_query(F.data.startswith("delcanal_"))
async def del_canal(callback: CallbackQuery):
    canal = callback.data.split("_", 1)[1]
    remove_canal(canal)
    await callback.answer(f"Canal {canal} removido!")
    await menu_canais(callback) # Atualiza a tela

# --- KEYWORDS ---
@dp.callback_query(F.data == "menu_keywords")
async def menu_keywords(callback: CallbackQuery):
    kws = get_keywords()
    
    texto_kws = "\n".join([f"- {k}" for k in kws[:100]])
    if len(kws) > 100:
        texto_kws += f"\n... (e mais {len(kws)-100} palavras. Use a busca!)"
        
    texto = "🔑 **Palavras-Chave:**\n*(Se a lista estiver vazia, ele encaminha TUDO)*\n\n" 
    texto += texto_kws
    texto += "\n\nPara buscar, remover ou adicionar, use os botões abaixo ou digite no chat."
    
    builder = InlineKeyboardBuilder()
    for k in kws[:90]:
        builder.button(text=f"❌ {k}", callback_data=f"delkw_{k}")
    builder.button(text="➕ Adicionar Keyword", callback_data="add_kw_btn")
    builder.button(text="🔍 Buscar Keyword", callback_data="buscar_kw")
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    
    sizes = [2] * ((len(kws[:90]) + 1) // 2) + [1, 1, 1]
    builder.adjust(*sizes)
    
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
    user_states[callback.from_user.id] = "esperando_kw"

@dp.callback_query(F.data == "buscar_kw")
async def btn_buscar_kw(callback: CallbackQuery):
    user_states[callback.from_user.id] = "esperando_busca_kw"
    await callback.message.edit_text("🔍 **Buscar Keyword**\n\nDigite a palavra (ou parte dela) que deseja procurar na sua lista:")
    await callback.answer()

@dp.callback_query(F.data == "add_kw_btn")
async def btn_add_kw(callback: CallbackQuery):
    user_states[callback.from_user.id] = "esperando_kw"
    # Salva o ID da mensagem do menu para podermos editá-la depois, se necessário
    user_temp_data[callback.from_user.id] = {"menu_msg_id": callback.message.message_id}
    await callback.message.edit_text("➕ **Adicionar Keyword**\n\nDigite a nova palavra-chave (ou várias separadas por vírgula) no chat:")
    await callback.answer()

@dp.callback_query(F.data.startswith("delkw_"))
async def del_kw(callback: CallbackQuery):
    kw = callback.data.split("_", 1)[1]
    remove_keyword(kw)
    await callback.answer(f"Keyword '{kw}' removida!")
    await menu_keywords(callback) 

# --- NEGATIVE KEYWORDS ---
@dp.callback_query(F.data == "menu_neg_keywords")
async def menu_neg_keywords(callback: CallbackQuery):
    kws = get_negative_keywords()
    
    texto_kws = "\n".join([f"- {k}" for k in kws[:100]])
    if len(kws) > 100:
        texto_kws += f"\n... (e mais {len(kws)-100} palavras. Use a busca!)"
        
    texto = "🚫 **Keywords Negativas:**\n*(O bot ignorará ofertas que contenham essas palavras)*\n\n" 
    texto += texto_kws
    texto += "\n\nPara buscar, remover ou adicionar, use os botões abaixo ou digite no chat."
    
    builder = InlineKeyboardBuilder()
    for k in kws[:90]:
        builder.button(text=f"❌ {k}", callback_data=f"delnkw_{k}")
    builder.button(text="➕ Adicionar Negativa", callback_data="add_nkw_btn")
    builder.button(text="🔍 Buscar", callback_data="buscar_nkw")
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    
    sizes = [2] * ((len(kws[:90]) + 1) // 2) + [1, 1, 1]
    builder.adjust(*sizes)
    
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
    user_states[callback.from_user.id] = "esperando_nkw"

@dp.callback_query(F.data == "buscar_nkw")
async def btn_buscar_nkw(callback: CallbackQuery):
    user_states[callback.from_user.id] = "esperando_busca_nkw"
    await callback.message.edit_text("🔍 **Buscar Keyword Negativa**\n\nDigite a palavra que deseja procurar na sua lista:")
    await callback.answer()

@dp.callback_query(F.data == "add_nkw_btn")
async def btn_add_nkw(callback: CallbackQuery):
    user_states[callback.from_user.id] = "esperando_nkw"
    user_temp_data[callback.from_user.id] = {"menu_msg_id": callback.message.message_id}
    await callback.message.edit_text("➕ **Adicionar Keyword Negativa**\n\nDigite a palavra-chave negativa (ou várias separadas por vírgula) no chat:")
    await callback.answer()

@dp.callback_query(F.data.startswith("delnkw_"))
async def del_nkw(callback: CallbackQuery):
    kw = callback.data.split("_", 1)[1]
    remove_negative_keyword(kw)
    await callback.answer(f"Keyword '{kw}' removida!")
    await menu_neg_keywords(callback) 

# --- GESTÃO DE ADMINS ---
@dp.callback_query(F.data == "menu_admins")
async def menu_admins(callback: CallbackQuery):
    admins = get_admins()
    texto = "👥 **Administradores do Bot:**\n\n"
    for user_id, username in admins:
        texto += f"- {username} (<code>{user_id}</code>)\n"
    
    texto += "\nPara remover, clique no botão abaixo. Para adicionar um novo, digite o **ID do Telegram** do novo admin aqui no chat."
    
    builder = InlineKeyboardBuilder()
    for user_id, username in admins:
        # Não permite o admin logado se remover (opcional, mas seguro)
        if user_id != callback.from_user.id:
            builder.button(text=f"❌ {username}", callback_data=f"deladmin_{user_id}")
    
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    builder.adjust(1)
    
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="HTML")
    user_states[callback.from_user.id] = "esperando_id_admin"

@dp.callback_query(F.data.startswith("deladmin_"))
async def handle_del_admin(callback: CallbackQuery):
    user_id_to_del = int(callback.data.split("_")[1])
    remove_admin(user_id_to_del)
    await callback.answer("Admin removido com sucesso!")
    await menu_admins(callback)

# --- SORTEIOS (GIVEAWAYS) ---
@dp.callback_query(F.data == "menu_sorteios")
async def menu_sorteios(callback: CallbackQuery):
    # Implementação base do menu de sorteios
    from database import get_active_giveaways
    active = get_active_giveaways()
    
    texto = "🎉 **Gestão de Sorteios**\n\n"
    if not active:
        texto += "Nenhum sorteio ativo no momento."
    else:
        texto += "Sorteios em aberto:\n"
        for sid, premio in active:
            texto += f"- ID: {sid} | Prêmio: {premio}\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Novo Sorteio", callback_data="novo_sorteio")
    for sid, premio in active:
        builder.button(text=f"🎲 Sortear: {premio}", callback_data=f"run_sorteio_{sid}")
    
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    builder.adjust(1)
    
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
    user_states[callback.from_user.id] = None

@dp.callback_query(F.data == "novo_sorteio")
async def handle_new_giveaway(callback: CallbackQuery):
    user_states[callback.from_user.id] = "novo_sorteio"
    await callback.message.edit_text("🎁 **Novo Sorteio**\n\nDigite o nome do prêmio que será sorteado:", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("run_sorteio_"))
async def handle_run_sorteio(callback: CallbackQuery):
    giveaway_id = int(callback.data.split("_")[-1])
    
    from database import get_admins, close_giveaway
    from monitor import draw_giveaway_winner
    from config import TARGET_CHANNEL
    
    await callback.message.edit_text("🎲 **Realizando sorteio...**\nIsso pode levar alguns segundos dependendo do tamanho do canal.")
    
    admins = get_admins()
    admin_ids = [a[0] for a in admins]
    
    winner = await draw_giveaway_winner(TARGET_CHANNEL, admin_ids)
    
    if not winner:
        await callback.message.answer("❌ Não foi possível realizar o sorteio. Verifique se o bot tem permissão para ver membros ou se há inscritos suficientes (não-admins).")
        return

    winner_name = f"{winner.first_name} {winner.last_name or ''}".strip()
    winner_handle = f"@{winner.username}" if winner.username else f"ID: {winner.id}"
    
    close_giveaway(giveaway_id, winner.id, winner_name)
    
    anuncio = (
        f"🎉 **TEMOS UM GANHADOR!** 🎉\n\n"
        f"O sorteio acaba de ser realizado e o vencedor(a) é:\n"
        f"👤 **{winner_name}** ({winner_handle})\n\n"
        f"Parabéns! Entre em contato com o suporte para resgatar seu prêmio. 🚀"
    )
    
    # Envia no canal oficial
    from publisher import publish_deal
    await publish_deal(anuncio)
    
    await callback.message.answer(f"✅ Sorteio realizado com sucesso!\nGanhador: {winner_name}\nAnúncio enviado no canal.")
    await menu_sorteios(callback)

# --- CONFIGURAÇÕES ---
@dp.callback_query(F.data == "menu_config")
async def menu_config(callback: CallbackQuery):
    pausado = "🔴 SIM" if get_config("pausado") == "1" else "🟢 NÃO"
    aprovacao = "🔴 SIM" if get_config("aprovacao_manual") == "1" else "🟢 NÃO"
    preco_min = get_config("preco_minimo") or "0"
    assinatura = get_config("assinatura") or "Nenhuma"

    texto = "⚙️ **Configurações Gerais**\n\n"
    texto += f"🛑 **Bot Pausado:** {pausado}\n"
    texto += f"⚖️ **Aprovação Manual:** {aprovacao}\n"
    texto += f"💲 **Preço Mínimo:** R$ {preco_min}\n"
    texto += f"📝 **Assinatura Atual:**\n`{assinatura}`"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Alternar Pausa", callback_data="toggle_pausa")
    builder.button(text="Alternar Aprovação", callback_data="toggle_aprovacao")
    builder.button(text="Alterar Preço Mínimo", callback_data="set_preco_min")
    builder.button(text="Alterar Assinatura", callback_data="set_assinatura")
    builder.button(text="🔄 Reiniciar Bot", callback_data="reboot_bot")
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    builder.adjust(1)
    
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
    user_states[callback.from_user.id] = None

@dp.callback_query(F.data == "toggle_pausa")
async def toggle_pausa(callback: CallbackQuery):
    atual = get_config("pausado")
    novo = "0" if atual == "1" else "1"
    set_config("pausado", novo)
    await menu_config(callback)

@dp.callback_query(F.data == "toggle_aprovacao")
async def toggle_aprovacao(callback: CallbackQuery):
    atual = get_config("aprovacao_manual")
    novo = "0" if atual == "1" else "1"
    set_config("aprovacao_manual", novo)
    await menu_config(callback)

@dp.callback_query(F.data == "set_preco")
async def ask_preco(callback: CallbackQuery):
    user_states[callback.from_user.id] = "esperando_preco"
    await callback.message.answer("Digite o valor do preço mínimo (Ex: 50 ou 15.90):")
    await callback.answer()

@dp.callback_query(F.data == "set_assinatura")
async def ask_assinatura(callback: CallbackQuery):
    user_states[callback.from_user.id] = "esperando_assinatura"
    await callback.message.answer("Digite o texto da assinatura que vai no final de cada postagem (suporta HTML/Links):\nEnvie 'LIMPAR' para remover a assinatura.")
    await callback.answer()

# --- VOLTAR ---
@dp.callback_query(F.data == "reboot_bot")
async def handle_reboot_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sem permissão.")
        return
    await callback.message.answer("🔄 **Comando de reinicialização recebido.**\nO sistema irá reiniciar o processo agora.")
    await asyncio.sleep(1)
    
    try:
        from publisher import bot
        await bot.session.close()
    except: pass
    try:
        from monitor import client as userbot
        await userbot.disconnect()
    except: pass
    
    os.execv(sys.executable, ['python'] + sys.argv)

@dp.callback_query(F.data == "voltar_main")
async def voltar_main(callback: CallbackQuery):
    user_states[callback.from_user.id] = None
    await callback.message.edit_text(
        "🛠️ **Painel de Controle - Pechinchas do Luiz4o**\n\nEscolha uma opção:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# --- TRATAR MENSAGENS DIGITADAS ---
@dp.message()
async def handle_text(message: Message):
    # if message.from_user.id != ADMIN_USER_ID: return
        
    estado = user_states.get(message.from_user.id)
    
    # Auto-detecção de links para facilitar
    if message.text:
        texto = message.text.lower()
        if any(dom in texto for dom in ["amazon.com.br", "amzlink.to", "amzn.to", "mercadolivre.com", "mlb.sh", "t.me"]):
            if "t.me" in texto:
                await start_copiar_post_telegram(message)
            else:
                await start_criar_oferta_msg(message)
            return

    if estado == "esperando_canal":
        canal = message.text.strip().replace("@", "")
        if add_canal(canal):
            await message.answer(f"✅ Canal `{canal}` adicionado à lista de monitoramento!")
        else:
            await message.answer("⚠️ Este canal já está sendo monitored.")
        user_states[message.from_user.id] = None
        # Idealmente, o userbot precisa ser reiniciado para ouvir novos canais na hora,
        # ou precisamos de uma lógica mais avançada no Telethon para "update_folder".
            
    elif estado == "esperando_edicao_texto":
        item_id = user_temp_data.get(message.from_user.id, {}).get("edit_item_id")
        from monitor import ofertas_pendentes_admin
        
        if item_id is not None and 0 <= item_id < len(ofertas_pendentes_admin):
            # Atualiza o texto da oferta pendente
            ofertas_pendentes_admin[item_id]["texto"] = message.text
            user_states[message.from_user.id] = None
            
            await message.answer("✅ Texto atualizado! Gerando nova prévia...")
            
            # Mostra a prévia novamente
            oferta = ofertas_pendentes_admin[item_id]
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Postar", callback_data=f"aprovar_{item_id}"),
                    InlineKeyboardButton(text="✏️ Editar", callback_data=f"editar_{item_id}"),
                    InlineKeyboardButton(text="❌ Descartar", callback_data=f"recusar_{item_id}")
                ]
            ])
            
            msg_amostra = f"**PRÉVIA ATUALIZADA:**\n\n{message.text}"
            
            from aiogram.types import FSInputFile
            if oferta["media"]:
                photo = FSInputFile(oferta["media"])
                await message.answer_photo(photo=photo, caption=msg_amostra, reply_markup=markup, parse_mode="HTML")
            else:
                await message.answer(text=msg_amostra, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await message.answer("❌ Erro ao localizar a oferta para edição.")
            user_states[message.from_user.id] = None

    elif estado == "esperando_kw":
        kws = [k.strip() for k in message.text.lower().split(",") if k.strip()]
        adicionadas = []
        ja_existem = []
        for kw in kws:
            if add_keyword(kw):
                adicionadas.append(kw)
            else:
                ja_existem.append(kw)
        
        msg_parts = []
        if adicionadas:
            msg_parts.append(f"✅ Keyword(s) adicionada(s): `{', '.join(adicionadas)}`\nO bot só filtrará mensagens que tenham essas palavras.")
        if ja_existem:
            msg_parts.append(f"⚠️ Já cadastrada(s): `{', '.join(ja_existem)}`")
            
        if not msg_parts:
            msg_parts.append("⚠️ Nenhuma keyword válida informada.")
            
        await message.answer("\n".join(msg_parts))
        
        # Apaga a mensagem digitada pelo usuário e reabre o menu
        try:
            await message.delete()
            menu_msg_id = user_temp_data.get(message.from_user.id, {}).get("menu_msg_id")
            if menu_msg_id:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=menu_msg_id)
        except:
            pass
            
        # Reabre o menu chamando a função recriando um falso callback
        from aiogram.types import CallbackQuery, User
        msg_carregando = await message.answer("Carregando...")
        fake_cb = CallbackQuery(
            id="0",
            from_user=message.from_user,
            chat_instance="0",
            message=msg_carregando
        )
        await menu_keywords(fake_cb)
        user_states[message.from_user.id] = None

    elif estado == "esperando_nkw":
        kws = [k.strip() for k in message.text.lower().split(",") if k.strip()]
        adicionadas = []
        ja_existem = []
        for kw in kws:
            if add_negative_keyword(kw):
                adicionadas.append(kw)
            else:
                ja_existem.append(kw)
        
        msg_parts = []
        if adicionadas:
            msg_parts.append(f"✅ Keyword(s) negativa(s) adicionada(s): `{', '.join(adicionadas)}`")
        if ja_existem:
            msg_parts.append(f"⚠️ Já cadastrada(s): `{', '.join(ja_existem)}`")
            
        if not msg_parts:
            msg_parts.append("⚠️ Nenhuma keyword válida informada.")
            
        await message.answer("\n".join(msg_parts))
        
        try:
            await message.delete()
            menu_msg_id = user_temp_data.get(message.from_user.id, {}).get("menu_msg_id")
            if menu_msg_id:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=menu_msg_id)
        except:
            pass
            
        from aiogram.types import CallbackQuery
        msg_carregando = await message.answer("Carregando...")
        fake_cb = CallbackQuery(id="0", from_user=message.from_user, chat_instance="0", message=msg_carregando)
        await menu_neg_keywords(fake_cb)
        user_states[message.from_user.id] = None

    elif estado == "esperando_busca_nkw":
        busca = message.text.strip().lower()
        kws = get_negative_keywords()
        resultados = [k for k in kws if busca in k.lower()]
        
        if resultados:
            texto = f"🔍 **Resultados para:** `{busca}`\n\n" + "\n".join([f"- {k}" for k in resultados[:100]])
            texto += "\n\nPara remover, clique abaixo. Para adicionar novas, digite no chat."
        else:
            texto = f"🔍 **Nenhum resultado para:** `{busca}`\n\nPara adicionar como nova keyword, basta digitar ela no chat."
            
        builder = InlineKeyboardBuilder()
        for k in resultados[:90]:
            builder.button(text=f"❌ {k}", callback_data=f"delnkw_{k}")
        builder.button(text="🔍 Nova Busca", callback_data="buscar_nkw")
        builder.button(text="🔙 Voltar p/ Negativas", callback_data="menu_neg_keywords")
        
        sizes = [2] * ((len(resultados[:90]) + 1) // 2) + [1, 1]
        builder.adjust(*sizes)
        
        await message.answer(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
        user_states[message.from_user.id] = "esperando_nkw"

    elif estado == "esperando_busca_kw":
        busca = message.text.strip().lower()
        kws = get_keywords()
        resultados = [k for k in kws if busca in k.lower()]
        
        if resultados:
            texto = f"🔍 **Resultados para:** `{busca}`\n\n" + "\n".join([f"- {k}" for k in resultados[:100]])
            texto += "\n\nPara remover, clique abaixo. Para adicionar novas, digite no chat."
        else:
            texto = f"🔍 **Nenhum resultado para:** `{busca}`\n\nPara adicionar como nova keyword, basta digitar ela no chat."
            
        builder = InlineKeyboardBuilder()
        for k in resultados[:90]:
            builder.button(text=f"❌ {k}", callback_data=f"delkw_{k}")
        builder.button(text="🔍 Nova Busca", callback_data="buscar_kw")
        builder.button(text="🔙 Voltar p/ Keywords", callback_data="menu_keywords")
        
        sizes = [2] * ((len(resultados[:90]) + 1) // 2) + [1, 1]
        builder.adjust(*sizes)
        
        await message.answer(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
        user_states[message.from_user.id] = "esperando_kw"

    elif estado == "esperando_id_admin":
        try:
            new_id = int(message.text.strip())
            if add_admin(new_id, "Novo Admin"):
                await message.answer(f"✅ Usuário <code>{new_id}</code> adicionado como Admin!", parse_mode="HTML")
            else:
                await message.answer("⚠️ Este usuário já é Admin.")
        except ValueError:
            await message.answer("❌ ID inválido. Por favor, envie apenas números.")
        user_states[message.from_user.id] = None

    elif estado == "novo_sorteio":
        from database import create_giveaway
        premio = message.text.strip()
        create_giveaway(premio)
        await message.answer(f"✅ Sorteio de **{premio}** criado! Use o menu /admin para realizar o sorteio quando desejar.", parse_mode="Markdown")
        user_states[message.from_user.id] = None

    elif estado == "esperando_preco":
        try:
            val = float(message.text.replace(',','.'))
            set_config("preco_minimo", str(val))
            await message.answer(f"✅ Preço mínimo configurado para R$ {val:.2f}")
        except:
            await message.answer("❌ Valor inválido. Tente novamente clicando no botão.")
        user_states[message.from_user.id] = None

    elif estado == "esperando_assinatura":
        if message.text.strip().upper() == "LIMPAR":
            set_config("assinatura", "")
            await message.answer("✅ Assinatura removida.")
        else:
            set_config("assinatura", message.text)
            await message.answer("✅ Nova assinatura configurada com sucesso!")
        user_states[message.from_user.id] = None

    elif estado == "esperando_link_criacao":
        await processar_link_criacao(message, message.text.strip())

    elif estado == "esperando_titulo_criacao":
        user_temp_data[message.from_user.id]["titulo"] = message.text.strip()
        user_states[message.from_user.id] = "esperando_preco_criacao"
        await message.answer(f"✅ Título definido.\n\nQual é o valor final da promoção? (Só números, ex: 150 ou 1500.50):")

    elif estado == "esperando_preco_criacao":
        preco = message.text.strip()
        user_temp_data[message.from_user.id]["preco"] = preco
        
        user_states[message.from_user.id] = "esperando_cupom_criacao"
        
        skip_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏩ Pular", callback_data="skip_coupon")]
        ])
        await message.answer("💸 E qual é o Cupom? (Digite o cupom ou clique em Pular):", reply_markup=skip_kb)

    elif estado == "esperando_cupom_criacao":
        cupom = message.text.strip()
        user_temp_data[message.from_user.id]["cupom"] = cupom
        
        obs_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏩ Pular Observação", callback_data="skip_obs")]
        ])
        user_states[message.from_user.id] = "esperando_obs_criacao"
        await message.answer("📝 **Observação Adicional** (Opcional):\nEx: 'Só hoje!', 'Primeira compra', 'Frete grátis prime', etc.\n\nOu clique em pular se não quiser adicionar nada.", reply_markup=obs_kb, parse_mode="Markdown")

    elif estado == "esperando_obs_criacao":
        obs = message.text.strip()
        user_temp_data[message.from_user.id]["observacao"] = obs
        
        choice_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🤖 Pela Inteligência Artificial", callback_data="text_mode_ai"),
                InlineKeyboardButton(text="✍️ Escrever Manualmente", callback_data="text_mode_manual")
            ]
        ])
        user_states[message.from_user.id] = "esperando_modo_texto"
        await message.answer("📝 Como deseja gerar o texto da promoção?", reply_markup=choice_kb)

    elif estado == "esperando_texto_manual":
        user_temp_data[message.from_user.id]["texto_manual"] = message.text
        user_states[message.from_user.id] = None
        
        await finalizar_criacao_manual(message, message.from_user.id)

    elif estado == "esperando_modo_texto":
        # Caso o usuário digite algo em vez de clicar no botão
        await message.answer("⚠️ Por favor, escolha uma das opções acima nos botões.")
        
async def finalizar_criacao_manual(event_message: Message, user_id: int, modo_ai: bool = False):
    data = user_temp_data.get(user_id)
    if not data:
        await event_message.answer("❌ Erro: Dados da oferta perdidos.")
        return

    msg = await event_message.answer("✨ Processando oferta e aplicando marca d'água...")
    
    from rewriter import gerar_promocao_por_link
    from links import process_and_replace_links
    from monitor import post_queue
    from watermark import apply_watermark
    
    try:
        if modo_ai:
            # Gerar Texto Base via Gemini
            texto_base = await gerar_promocao_por_link(
                data.get("titulo"), 
                data.get("link"), 
                data.get("preco"), 
                data.get("cupom"),
                data.get("observacao")
            )
        else:
            # Usar texto manual fornecido pelo usuário
            texto_base = data.get("texto_manual", "Oferta sem descrição.")

        # Garantir que o marcador de link existe no texto para manual creation
        if "[LINK_" not in texto_base:
            texto_base += "\n\n[LINK_0]"

        # Processar o link (Converter Amazon, expandir encurtados, etc)
        texto_com_placeholders, placeholder_map = await process_and_replace_links(texto_base, data.get('link'))
        
        # Formatar o texto final com links "Pegar promoção" substituindo os placeholders
        clean_text = texto_com_placeholders
        if placeholder_map:
            for placeholder, final_url in placeholder_map.items():
                if final_url is None:
                    clean_text = clean_text.replace(placeholder, "")
                else:
                    botao_html = f"🛒 <a href='{final_url}'>Pegar promoção</a>"
                    clean_text = clean_text.replace(placeholder, botao_html)
                    
        # Remove qualquer placeholder residual
        clean_text = re.sub(r'\[LINK_\d+\]', '', clean_text)

        # Assinatura
        assinatura = get_config("assinatura")
        if assinatura:
            clean_text += f"\n\n{assinatura}"
            
        # Watermark
        img_path = data.get("local_image_path")
        if img_path:
            img_path = apply_watermark(img_path)
            
        # Coloca na fila
        await post_queue.put((clean_text, img_path, None))
        
        await msg.delete()
        await event_message.answer("✅ **Oferta Criada com Sucesso!**\nEla já foi enviada para a fila de publicação.")
    except Exception as e:
        print(f"Erro fatal na criação manual: {e}")
        retry_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Tentar Novamente", callback_data=f"retry_scraping_{'ai' if modo_ai else 'manual'}")]
        ])
        await event_message.answer(
            f"❌ **Erro ao processar oferta:** {e}\n\n"
            "Isso pode ser um bloqueio temporário do servidor da loja ou falha na IA. Deseja tentar novamente?",
            reply_markup=retry_kb,
            parse_mode="Markdown"
        )

async def processar_link_criacao(message: Message, link: str):
    user_id = message.from_user.id
    user_temp_data[user_id] = {"link": link}
    
    msg = await message.answer("🔍 Extraindo informações da página...")
    
    try:
        from scraper import fetch_product_metadata
        metadata = await fetch_product_metadata(link)
        
        user_temp_data[user_id]["titulo"] = metadata.get("title")
        user_temp_data[user_id]["local_image_path"] = metadata.get("local_image_path")
        
        status = metadata.get("status_code", 200)
        titulo_achado = metadata.get('title')
        
        is_generic_title = False
        if titulo_achado:
            low_title = titulo_achado.lower().strip()
            if low_title in ["amazon.com.br", "mercado livre", "mercadolivre", "amazon"]:
                is_generic_title = True

        if status in [403, 503] or not titulo_achado or is_generic_title:
            user_states[user_id] = "esperando_titulo_criacao"
            warn_msg = "⚠️ **Bloqueio detectado ou falha na extração.**\nAmazon ou Mercado Livre bloqueou o acesso automático.\n\n"
            retry_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Tentar Novamente", callback_data="retry_scraping_initial")]
            ])
            await message.answer(f"{warn_msg}Por favor, **digite o nome do produto manualmente** para continuar:", reply_markup=retry_kb, parse_mode="Markdown")
        else:
            user_states[user_id] = "esperando_preco_criacao"
            await message.answer(f"✅ Identifiquei: **{titulo_achado}**\n\nQual é o valor final da promoção? (Só números, ex: 150 ou 1500.50):")
    finally:
        try:
            await msg.delete()
        except:
            pass

@dp.callback_query(F.data == "retry_scraping_initial")
async def handle_retry_initial(callback: CallbackQuery):
    user_id = callback.from_user.id
    link = user_temp_data.get(user_id, {}).get("link")
    if link:
        await callback.message.edit_text("🔄 Tentando extrair novamente...")
        user_states[user_id] = "esperando_link_criacao"
        await processar_link_criacao(callback.message, link)
    await callback.answer()

@dp.callback_query(F.data.startswith("retry_scraping_"))
async def handle_retry_scraping(callback: CallbackQuery):
    modo = callback.data.split("_")[-1]
    modo_ai = (modo == "ai")
    await callback.message.edit_text("🔄 Tentando novamente...")
    await finalizar_criacao_manual(callback.message, callback.from_user.id, modo_ai=modo_ai)
    await callback.answer()

# --- CALLBACK HANDLERS PARA FLUXO MANUAL ---
@dp.callback_query(F.data == "skip_coupon")
async def handle_skip_coupon(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_temp_data[user_id]["cupom"] = "-"
    
    obs_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ Pular Observação", callback_data="skip_obs")]
    ])
    user_states[user_id] = "esperando_obs_criacao"
    await callback.message.edit_text("📝 **Observação Adicional** (Opcional):\nDigite agora ou clique em pular.", reply_markup=obs_kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "skip_obs")
async def handle_skip_obs(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_temp_data[user_id]["observacao"] = ""
    
    choice_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Pela Inteligência Artificial", callback_data="text_mode_ai"),
            InlineKeyboardButton(text="✍️ Escrever Manualmente", callback_data="text_mode_manual")
        ]
    ])
    user_states[user_id] = "esperando_modo_texto"
    await callback.message.edit_text("📝 Como deseja gerar o texto da promoção?", reply_markup=choice_kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("text_mode_"))
async def handle_text_mode(callback: CallbackQuery):
    user_id = callback.from_user.id
    mode = callback.data.split("_")[-1]
    
    if mode == "ai":
        await callback.message.edit_text("✨ Gerando texto com IA...")
        await finalizar_criacao_manual(callback.message, user_id, modo_ai=True)
    else:
        user_states[user_id] = "esperando_texto_manual"
        await callback.message.edit_text("✍️ Digite agora o texto da promoção que você deseja (links serão adicionados automaticamente ao final):")
    
    await callback.answer()


# --- APROVAÇÃO MANUAL GESTÃO ---
@dp.callback_query(F.data.startswith("aprovar_") | F.data.startswith("recusar_") | F.data.startswith("editar_"))
async def tratar_aprovacao_manual(callback: CallbackQuery):
    from monitor import post_queue, ofertas_pendentes_admin
    
    parts = callback.data.split("_")
    acao = parts[0]
    item_id = int(parts[1])
    
    # Verifica se o id existe
    if item_id < 0 or item_id >= len(ofertas_pendentes_admin):
        await callback.answer("⚠️ Esta oferta já foi processada ou não existe mais.")
        return
        
    oferta = ofertas_pendentes_admin[item_id]
    if not oferta:
        await callback.answer("⚠️ Esta oferta já foi processada.")
        return

    if acao == "editar":
        user_id = callback.from_user.id
        user_states[user_id] = "esperando_edicao_texto"
        user_temp_data[user_id] = {"edit_item_id": item_id}
        
        await callback.message.answer("✍️ **Edição de Oferta**\n\nEnvie o novo texto completo para esta promoção (links HTML são permitidos):")
        await callback.answer()
        return
        
    if acao == "aprovar":
        await callback.answer("✅ Oferta aprovada! Adicionando à fila...")
        await post_queue.put((oferta["texto"], oferta["media"], None, oferta.get("source_url"))) # Adiciona o markup e a fonte
        await callback.message.edit_caption(caption=f"✅ **OFERTA APROVADA E NA FILA**\n\n{oferta['texto'][:800]}...", parse_mode="HTML", reply_markup=None)
    else:
        import os
        await callback.answer("❌ Oferta recusada!")
        await callback.message.edit_caption(caption=f"❌ **OFERTA RECUSADA**\n\n{oferta['texto'][:800]}...", parse_mode="HTML", reply_markup=None)
        if oferta["media"] and os.path.exists(oferta["media"]):
            try:
                os.remove(oferta["media"])
            except:
                pass
                
    # Marca como resolvido limpando a memoria
    ofertas_pendentes_admin[item_id] = None

from aiogram.types.error_event import ErrorEvent
import traceback

@dp.error()
async def global_error_handler(event: ErrorEvent):
    """Captura erros globais do Aiogram e notifica o admin"""
    print(f"⚠️ Erro Global Capturado: {event.exception}")
    try:
        admin_id_str = get_config("admin_id")
        if admin_id_str:
            error_msg = f"⚠️ **ALERTA DE SISTEMA: ERRO INTERNO** ⚠️\n\n**Tipo:** `{type(event.exception).__name__}`\n**Erro:** `{str(event.exception)[:500]}`\n\n*Detalhes no log do servidor.*"
            await bot.send_message(chat_id=int(admin_id_str), text=error_msg, parse_mode="Markdown")
    except Exception as notify_err:
        print(f"Não foi possível notificar o admin sobre o erro: {notify_err}")

async def start_admin_bot():
    print("🤖 Painel Admin do Bot iniciado (Aguardando /admin no Telegram)")
    
    # Configurar menu de comandos
    await bot.set_my_commands([
        BotCommand(command="start", description="Painel Admin"),
        BotCommand(command="enviar", description="Enviar Promoção via Link"),
    ])
    
    # Enviar notificação de reinício
    try:
        admin_id_str = get_config("admin_id")
        if admin_id_str:
            await bot.send_message(
                chat_id=int(admin_id_str), 
                text="🚀 **SISTEMA INICIADO / REINICIADO**\n\n✅ Bot ativo e monitorando grupos selecionados.",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Aviso: Não foi possível enviar notificação de startup: {e}")
        
    await dp.start_polling(bot)
