from typing import Optional
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import config
from config import BOT_TOKEN
import database
from database import add_canal, get_canais, remove_canal, add_keyword, get_keywords, remove_keyword, get_config, set_config, is_admin, get_admins, add_admin, remove_admin
import os
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
    builder.button(text="🔗 Criar Oferta via Link", callback_data="menu_criar_link")
    builder.button(text="📺 Gerenciar Canais", callback_data="menu_canais")
    builder.button(text="🔑 Gerenciar Keywords", callback_data="menu_keywords")
    builder.button(text="👥 Gerenciar Admins", callback_data="menu_admins")
    builder.button(text="🎉 Sorteios", callback_data="menu_sorteios")
    builder.button(text="⚙️ Configurações Gerais", callback_data="menu_config")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start", "admin"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    # Check if there are any admins. If none, the first one to use the bot becomes admin.
    admins = get_admins()
    if not admins:
        add_admin(user_id, message.from_user.full_name or "Admin Principal")
        await message.answer("👋 **Bem-vindo!** Como não havia nenhum administrador, você foi registrado como o primeiro admin do sistema.")
    else:
        if not is_admin(user_id):
            await message.answer("❌ **Acesso Negado.** Você não tem permissão para usar este bot.")
            return

    # Salva o ID do admin no banco de dados para o monitor saber para quem mandar alertas
    set_config("admin_id", str(user_id))
    
    await message.answer(
        "🛠️ **Painel de Controle - Pechinchas do Luiz4o**\n\n"
        "O que você deseja gerenciar?",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    # Remove explicitamente qualquer teclado físico (ReplyKeyboard) antigo
    await message.answer("Menu inline ativado.", reply_markup=ReplyKeyboardRemove())
    user_states[user_id] = None

@dp.message(Command("meuid"))
async def cmd_meuid(message: Message):
    await message.answer(f"Seu ID do Telegram é: <code>{message.from_user.id}</code>", parse_mode="HTML")

@dp.message(Command("enviar"))
async def cmd_enviar_shortcut(message: Message):
    await start_criar_oferta_msg(message)

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
    texto = "🔑 **Palavras-Chave:**\n*(Se a lista estiver vazia, ele encaminha TUDO)*\n\n" 
    texto += "\n".join([f"- {k}" for k in kws])
    texto += "\n\nPara remover, clique abaixo. Para adicionar, digite a(s) palavra(s) no chat (separe por vírgula se forem várias)."
    
    builder = InlineKeyboardBuilder()
    for k in kws:
        builder.button(text=f"❌ {k}", callback_data=f"delkw_{k}")
    builder.button(text="🔙 Voltar", callback_data="voltar_main")
    builder.adjust(2)
    
    await callback.message.edit_text(texto, reply_markup=builder.as_markup(), parse_mode="Markdown")
    user_states[callback.from_user.id] = "esperando_kw"

@dp.callback_query(F.data.startswith("delkw_"))
async def del_kw(callback: CallbackQuery):
    kw = callback.data.split("_", 1)[1]
    remove_keyword(kw)
    await callback.answer(f"Keyword '{kw}' removida!")
    await menu_keywords(callback) 

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
    builder.button(text="Alternar Aprovação Manual", callback_data="toggle_aprovacao")
    builder.button(text="Definir Preço Mínimo", callback_data="set_preco")
    builder.button(text="Definir Assinatura", callback_data="set_assinatura")
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
        for kw in kws:
            if add_keyword(kw):
                adicionadas.append(kw)
        
        if adicionadas:
            await message.answer(f"✅ Keyword(s) adicionada(s): `{', '.join(adicionadas)}`\nO bot só filtrará mensagens que tenham essas palavras.")
        else:
            await message.answer("⚠️ Nenhuma keyword nova foi adicionada (talvez já existam).")
        user_states[message.from_user.id] = None

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
        link = message.text.strip()
        user_temp_data[message.from_user.id] = {"link": link}
        
        msg = await message.answer("🔍 Extraindo informações da página...")
        
        from scraper import fetch_product_metadata
        metadata = await fetch_product_metadata(link)
        
        user_temp_data[message.from_user.id]["titulo"] = metadata.get("title")
        user_temp_data[message.from_user.id]["local_image_path"] = metadata.get("local_image_path")
        
        status = metadata.get("status_code", 200)
        titulo_achado = metadata.get('title')
        
        # Considera falha se o status for erro ou se o título for apenas o nome da loja
        is_generic_title = False
        if titulo_achado:
            low_title = titulo_achado.lower().strip()
            if low_title in ["amazon.com.br", "mercado livre", "mercadolivre", "amazon"]:
                is_generic_title = True

        if status in [403, 503] or not titulo_achado or is_generic_title:
            user_states[message.from_user.id] = "esperando_titulo_criacao"
            warn_msg = "⚠️ **Bloqueio detectado ou falha na extração.**\nAmazon ou Mercado Livre bloqueou o acesso automático.\n\n"
            retry_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Tentar Novamente", callback_data="retry_scraping_initial")]
            ])
            await message.answer(f"{warn_msg}Por favor, **digite o nome do produto manualmente** para continuar:", reply_markup=retry_kb, parse_mode="Markdown")
        else:
            user_states[message.from_user.id] = "esperando_preco_criacao"
            await message.answer(f"✅ Identifiquei: **{titulo_achado}**\n\nQual é o valor final da promoção? (Só números, ex: 150 ou 1500.50):")

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

@dp.callback_query(F.data == "retry_scraping_initial")
async def handle_retry_initial(callback: CallbackQuery):
    user_id = callback.from_user.id
    link = user_temp_data.get(user_id, {}).get("link")
    if link:
        await callback.message.edit_text("🔄 Tentando extrair novamente...")
        # Simula o recebimento do link de novo
        callback.message.text = link
        user_states[user_id] = "esperando_link_criacao"
        await handle_text(callback.message)
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
        await post_queue.put((oferta["texto"], oferta["media"], None)) # Adicionado None para markup
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

async def start_admin_bot():
    print("🤖 Painel Admin do Bot iniciado (Aguardando /admin no Telegram)")
    
    # Configurar menu de comandos
    await bot.set_my_commands([
        BotCommand(command="start", description="Painel Admin"),
        BotCommand(command="enviar", description="Enviar Promoção via Link"),
    ])
    
    await dp.start_polling(bot)
