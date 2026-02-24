from aiohttp import web
from database import (
    get_config, set_config, get_canais, add_canal, remove_canal,
    get_keywords, add_keyword, remove_keyword,
    get_negative_keywords, add_negative_keyword, remove_negative_keyword,
    get_admins, add_admin, remove_admin, get_active_giveaways, create_giveaway, close_giveaway
)
import secrets
import os
import sys
import json
import asyncio

async def handle_index(request):
    token = request.query.get('token')
    valid_token = get_config("console_token")
    if not valid_token or token != valid_token:
        return web.Response(text="<h1>403 Forbidden</h1>", status=403, content_type='text/html')

    headers = {
        'Content-Security-Policy': "frame-ancestors https://web.telegram.org https://pwa.telegram.org https://desktop.telegram.org https://*.telegram.org;",
        'X-Frame-Options': 'ALLOWALL'
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pechinchas - Admin</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            :root {{
                --bg-main: #0d1117; --bg-sec: #161b22; --bg-card: #21262d;
                --border: #30363d; --text: #e6edf3; --text-dim: #8b949e;
                --accent: #58a6ff; --success: #238636; --error: #da3633;
            }}
            body {{
                background: var(--bg-main); color: var(--text);
                font-family: sans-serif; margin: 0; padding: 0;
                display: flex; flex-direction: column; height: 100vh; overflow: hidden;
            }}
            #navbar {{
                display: flex; background: var(--bg-sec); border-bottom: 1px solid var(--border);
                overflow-x: auto; flex-shrink: 0; z-index: 100;
            }}
            #navbar::-webkit-scrollbar {{ height: 8px; }}
            #navbar::-webkit-scrollbar-thumb {{ background: var(--accent); border-radius: 10px; }}
            /* Global Scrollbar */
            ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
            ::-webkit-scrollbar-track {{ background: var(--bg-main); }}
            ::-webkit-scrollbar-thumb {{ background: var(--accent); border-radius: 10px; border: 2px solid var(--bg-main); }}
            ::-webkit-scrollbar-thumb:hover {{ background: #79b6ff; }}
            .nav-item {{
                padding: 12px 15px; color: var(--text-dim); cursor: pointer; white-space: nowrap;
                font-size: 14px; border-bottom: 2px solid transparent; transition: 0.2s;
                flex-shrink: 0;
            }}
            .nav-item.active {{ color: var(--text); border-bottom-color: var(--accent); }}
            main {{ flex-grow: 1; overflow-y: auto; padding: 15px; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .card {{ background: var(--bg-sec); border: 1px solid var(--border); border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
            .card-title {{ font-size: 16px; font-weight: bold; margin-bottom: 12px; color: var(--accent); display: flex; align-items: center; gap: 8px; }}
            .input-group {{ display: flex; gap: 8px; margin-bottom: 10px; }}
            input, textarea {{ width: 100%; background: var(--bg-main); border: 1px solid var(--border); color: var(--text); padding: 8px; border-radius: 6px; outline: none; font-family: inherit; }}
            button {{ background: var(--bg-card); border: 1px solid var(--border); color: var(--text); padding: 8px 15px; border-radius: 6px; cursor: pointer; }}
            button.primary {{ background: var(--success); }}
            button.danger {{ background: var(--error); }}
            ul {{ list-style: none; padding: 0; }}
            li {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); }}
            #terminal {{ background: #000; padding: 10px; font-size: 11px; height: 300px; transition: height 0.3s; overflow-y: auto; white-space: pre-wrap; color: #0f0; border-radius: 4px; border: 1px solid var(--border); }}
            #terminal.expanded {{ height: 70vh; font-size: 12px; }}
            .log-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .toggle-switch {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; cursor: pointer; }}
            .toggle-switch input {{ width: auto; }}
        </style>
    </head>
    <body>
        <div id="navbar">
            <div class="nav-item active" onclick="showTab('dashboard', this)">🏠 Painel</div>
            <div class="nav-item" onclick="showTab('enviar', this)">🚀 Enviar</div>
            <div class="nav-item" onclick="showTab('canais', this)">📺 Canais</div>
            <div class="nav-item" onclick="showTab('keywords', this)">🔑 Keywords</div>
            <div class="nav-item" onclick="showTab('admins', this)">👥 Admins</div>
            <div class="nav-item" onclick="showTab('sorteios', this)">🎉 Sorteios</div>
            <div class="nav-item" onclick="showTab('moldura', this)">🖼️ Moldura</div>
            <div class="nav-item" onclick="showTab('settings', this)">⚙️ Config</div>
            <div class="nav-item" onclick="showTab('logs', this)">📜 Logs</div>
        </div>
        <main>
            <div id="tab-dashboard" class="tab-content active">
                <div class="card">
                    <div class="card-title">🤖 Controle do Bot</div>
                    <div id="status-container">Carregando...</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                        <button onclick="togglePausa()" id="btn-pausa">Pausar Bot</button>
                        <button onclick="restartBot()" class="danger">🔄 REINICIAR BOT</button>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">🔐 Segurança</div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="check-only-admins" onchange="toggleOnlyAdmins()">
                        Bloquear Bot para não-admins
                    </label>
                    <label class="toggle-switch">
                        <input type="checkbox" id="check-aprovacao" onchange="toggleAprovacao()">
                        Aprovação Manual de ofertas
                    </label>
                </div>
            </div>
            <div id="tab-canais" class="tab-content">
                <div class="card">
                    <div class="card-title">📺 Canais Monitorados</div>
                    <div class="input-group">
                        <input type="text" id="new-canal" placeholder="promocoesdodia">
                        <button class="primary" onclick="addCanal()">Add</button>
                    </div>
                    <ul id="list-canais"></ul>
                </div>
            </div>
            <div id="tab-keywords" class="tab-content">
                <div class="card"><div class="card-title">🔑 Positivas</div><div class="input-group"><input type="text" id="new-kw"><button onclick="addKeyword('kw')">Add</button></div><ul id="list-keywords"></ul></div>
                <div class="card"><div class="card-title">🚫 Negativas</div><div class="input-group"><input type="text" id="new-nkw"><button onclick="addKeyword('nkw')">Add</button></div><ul id="list-neg-keywords"></ul></div>
            </div>
            <div id="tab-admins" class="tab-content">
                <div class="card">
                    <div class="card-title">👥 Admins</div>
                    <div class="input-group">
                        <input type="number" id="new-admin-id" placeholder="ID">
                        <input type="text" id="new-admin-name" placeholder="Nome">
                        <button onclick="addAdmin()">Add</button>
                    </div>
                    <ul id="list-admins"></ul>
                </div>
            </div>
            <div id="tab-sorteios" class="tab-content">
                <div class="card">
                    <div class="card-title">🎉 Sorteios Ativos</div>
                    <div class="input-group"><input type="text" id="new-premio"><button onclick="addSorteio()">Criar</button></div>
                    <ul id="list-sorteios"></ul>
                </div>
            </div>
            <div id="tab-settings" class="tab-content">
                <div class="card"><div class="card-title">⚙️ Geral</div><div id="settings-form"></div></div>
            </div>
            <div id="tab-moldura" class="tab-content">
                <div class="card">
                    <div class="card-title">🖼️ Gerenciar Moldura</div>
                    <p style="font-size:13px; color:var(--text-dim)">Esta é a imagem que será sobreposta às fotos dos produtos. <b>A imagem deve ter fundo transparente para funcionar corretamente.</b></p>
                    <div id="wm-preview-container" style="text-align: center; margin: 15px 0; background: #fff; padding: 10px; border-radius: 8px;">
                        <img id="wm-current-img" src="/api/watermark?token={token}" style="max-width: 100%; max-height: 200px; border: 1px solid var(--border);">
                    </div>
                    <div class="input-group" style="flex-direction: column;">
                        <input type="file" id="wm-file" accept="image/png" style="padding: 10px;">
                        <button class="primary" onclick="uploadWatermark()" style="width: 100%">📤 Subir Nova Moldura (PNG)</button>
                    </div>
                    <small style="color:var(--text-dim)">Recomendado: PNG transparente 1000x1000.</small>
                </div>
            </div>
            <div id="tab-logs" class="tab-content">
                <div class="card">
                    <div class="log-header">
                        <div class="card-title" style="margin:0">📜 Logs</div>
                        <small id="log-time" style="color:var(--text-dim)"></small>
                    </div>
                    <div id="terminal"></div>
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <button onclick="fetchLogs()" style="flex-grow: 1">🔄 Atualizar</button>
                        <button onclick="toggleExpandLog()" id="btn-expand">↕️ Expandir</button>
                    </div>
                </div>
            </div>
        </main>
        <script>
            const token = "{token}";
            let currentTab = 'dashboard';
            function showTab(t, el) {{
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                document.getElementById('tab-'+t).classList.add('active');
                if(el) el.classList.add('active');
                currentTab = t;
                if(t==='canais') loadCanais(); if(t==='keywords') loadKeywords();
                if(t==='admins') loadAdmins(); if(t==='sorteios') loadSorteios();
                if(t==='settings') loadSettings(); if(t==='dashboard') loadStatus();
                if(t==='logs') fetchLogs(); if(t==='moldura') loadWatermark();
            }}
            function loadWatermark() {{
                const img = document.getElementById('wm-current-img');
                img.src = '/api/watermark?token=' + token + '&t=' + Date.now();
            }}
            async function uploadWatermark() {{
                const fileInput = document.getElementById('wm-file');
                if(!fileInput.files[0]) return Telegram.WebApp.showAlert("Selecione um arquivo primeiro!");
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {{
                    const r = await fetch(`/api/watermark?token=${{token}}`, {{
                        method: 'POST',
                        body: formData
                    }});
                    const res = await r.json();
                    if(res.success) {{
                        Telegram.WebApp.showAlert("Moldura atualizada com sucesso!");
                        loadWatermark();
                    }} else {{
                        Telegram.WebApp.showAlert("Erro: " + res.error);
                    }}
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao subir arquivo.");
                }}
            }}
            async function api(p, m='GET', b=null) {{
                const s = p.includes('?') ? '&' : '?';
                const r = await fetch(`/api/${{p}}${{s}}token=${{token}}`, {{ method: m, body: b ? JSON.stringify(b) : null, headers: {{'Content-Type':'application/json'}} }});
                return await r.json();
            }}
            async function loadStatus() {{
                const d = await api('status');
                document.getElementById('status-container').innerHTML = `
                    <p>Monitorando: <b>${{d.canais_count}} canais</b></p>
                    <p>Keywords: <b>${{d.kw_count}}</b> (+) / <b>${{d.nkw_count}}</b> (-)</p>
                    <p>Bot: <b>${{d.pausado==='1' ? '⏸️ PAUSADO' : '▶️ ATIVO'}}</b></p>
                `;
                document.getElementById('btn-pausa').textContent = d.pausado==='1' ? '▶️ RETOMAR BOT' : '⏸️ PAUSAR BOT';
                document.getElementById('check-only-admins').checked = d.only_admins==='1';
                document.getElementById('check-aprovacao').checked = d.aprovacao==='1';
            }}
            async function restartBot() {{
                Telegram.WebApp.showConfirm("Deseja reiniciar o bot? O painel ficará offline por alguns segundos.", async (ok) => {{
                    if(ok) {{
                        await api('restart', 'POST'); 
                        Telegram.WebApp.showAlert("Solicitação enviada! O bot irá reiniciar em instantes.");
                        setTimeout(() => Telegram.WebApp.close(), 2000);
                    }}
                }});
            }}
            async function toggleOnlyAdmins() {{
                const v = document.getElementById('check-only-admins').checked ? '1' : '0';
                await api('settings', 'POST', {{ chave: 'only_admins', valor: v }});
            }}
            async function toggleAprovacao() {{
                const v = document.getElementById('check-aprovacao').checked ? '1' : '0';
                await api('settings', 'POST', {{ chave: 'aprovacao_manual', valor: v }});
            }}
            async function togglePausa() {{
                const d = await api('status');
                const v = d.pausado==='1' ? '0' : '1';
                await api('settings', 'POST', {{ chave: 'pausado', valor: v }});
                loadStatus();
            }}

            // Fluxo Enviar Promoção
            let scrapeData = {{}};
            function backToStep(s) {{
                document.querySelectorAll('#tab-enviar .card').forEach(c => c.style.display = 'none');
                document.getElementById('step-'+s).style.display = 'block';
            }}
            async function startScrape() {{
                const url = document.getElementById('promo-url').value;
                if(!url) return Telegram.WebApp.showAlert("Cole um link!");
                
                Telegram.WebApp.MainButton.setText("🔍 Buscando dados...").show();
                try {{
                    const d = await api('scrape', 'POST', {{ url: url }});
                    if(d.error) throw new Error(d.error);
                    
                    scrapeData = d;
                    document.getElementById('preview-title').value = d.title || "";
                    document.getElementById('preview-price').value = d.price || "";
                    document.getElementById('preview-img').src = d.image || "";
                    
                    backToStep(2);
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao buscar dados: " + e.message);
                }} finally {{
                    Telegram.WebApp.MainButton.hide();
                }}
            }}
            async function generateText() {{
                Telegram.WebApp.MainButton.setText("✨ Gerando texto...").show();
                try {{
                    const d = await api('generate_text', 'POST', {{
                        url: document.getElementById('promo-url').value,
                        title: document.getElementById('preview-title').value,
                        price: document.getElementById('preview-price').value,
                        coupon: document.getElementById('preview-coupon').value,
                        observation: document.getElementById('preview-obs').value
                    }});
                    document.getElementById('final-text').value = d.text;
                    backToStep(3);
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao gerar texto: " + e.message);
                }} finally {{
                    Telegram.WebApp.MainButton.hide();
                }}
            }}
            async function postOffer() {{
                const btn = document.getElementById('btn-post');
                btn.disabled = true;
                btn.textContent = "⌛ Postando...";
                try {{
                    const d = await api('post_offer', 'POST', {{
                        url: document.getElementById('promo-url').value,
                        text: document.getElementById('final-text').value,
                        image_path: scrapeData.image_path // O scraper deve salvar a imagem e retornar o path
                    }});
                    if(d.success) {{
                        Telegram.WebApp.showAlert("🚀 Promoção postada com sucesso!");
                        document.getElementById('promo-url').value = "";
                        backToStep(1);
                        showTab('dashboard'); // Volta pro painel
                    }} else {{
                        throw new Error(d.error);
                    }}
                }} catch(e) {{
                    Telegram.WebApp.showAlert("Erro ao postar: " + e.message);
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = "POSTAR AGORA 🚀";
                }}
            }}
            async function loadCanais() {{
                const d = await api('canais');
                const l = document.getElementById('list-canais');
                let h = "";
                d.canais.forEach(c => {{ h += `<li>${{c}} <button class="danger" onclick="delCanal('${{c}}')">x</button></li>`; }});
                l.innerHTML = h || "<li>Nenhum canal monitorado.</li>";
            }}
            async function addCanal() {{ const i=document.getElementById('new-canal'); await api('canais','POST',{{canal:i.value}}); i.value=""; loadCanais(); }}
            async function delCanal(c) {{ await api('canais','DELETE',{{canal:c}}); loadCanais(); }}
            async function loadKeywords() {{
                const k = await api('keywords'); const n = await api('neg_keywords');
                const lk = document.getElementById('list-keywords');
                const ln = document.getElementById('list-neg-keywords');
                let hk = "", hn = "";
                k.keywords.forEach(x => {{ hk += `<li>${{x}} <button class="danger" onclick="delKw('kw','${{x}}')">x</button></li>`; }});
                n.keywords.forEach(x => {{ hn += `<li>${{x}} <button class="danger" onclick="delKw('nkw','${{x}}')">x</button></li>`; }});
                lk.innerHTML = hk || "<li>Nenhuma keyword (+)</li>";
                ln.innerHTML = hn || "<li>Nenhuma keyword (-)</li>";
            }}
            async function delKw(t,x) {{ await api(t==='kw'?'keywords':'neg_keywords','DELETE',{{keyword:x}}); loadKeywords(); }}
            async function addKeyword(t) {{ const i=document.getElementById(t==='kw'?'new-kw':'new-nkw'); await api(t==='kw'?'keywords':'neg_keywords','POST',{{keyword:i.value}}); i.value=""; loadKeywords(); }}
            async function loadAdmins() {{
                const d = await api('admins'); const l = document.getElementById('list-admins');
                let h = "";
                d.admins.forEach(a => {{ h += `<li>${{a[1]}} (${{a[0]}}) <button class="danger" onclick="delAdmin('${{a[0]}}')">x</button></li>`; }});
                l.innerHTML = h || "<li>Apenas você.</li>";
            }}
            async function addAdmin() {{ await api('admins','POST',{{user_id:document.getElementById('new-admin-id').value, username:document.getElementById('new-admin-name').value}}); loadAdmins(); }}
            async function delAdmin(id) {{ await api('admins','DELETE',{{user_id:id}}); loadAdmins(); }}
            async function loadSorteios() {{
                const d = await api('sorteios'); const l = document.getElementById('list-sorteios');
                let h = "";
                d.sorteios.forEach(s => {{ h += `<li>${{s[1]}} <button onclick="closeSorteio('${{s[0]}}')">Encerrar</button></li>`; }});
                l.innerHTML = h || "<li>Nenhum sorteio ativo.</li>";
            }}
            async function addSorteio() {{ await api('sorteios','POST',{{premio:document.getElementById('new-premio').value}}); loadSorteios(); }}
            async function closeSorteio(id) {{ await api('sorteios','PATCH',{{id:id, winner_id:0, winner_name:'Ganhador'}}); loadSorteios(); }}
            async function loadSettings() {{
                const f = [{{k:'delay_minutos',l:'Delay'}},{{k:'preco_minimo',l:'Preço'}},{{k:'assinatura',l:'Assinatura'}},{{k:'webapp_url',l:'WebApp URL'}}];
                const c = document.getElementById('settings-form');
                c.innerHTML = "Carregando...";
                let html = "";
                for(const x of f) {{
                    const v = await api('settings?key='+x.k);
                    const isA = x.k==='assinatura';
                    html += `
                        <p style="margin-bottom:5px; font-weight:bold; font-size:13px;">${{x.l}}:</p>
                        ${{isA ? `
                                 <div id="editor-toolbar" style="margin-bottom:5px; display:flex; gap:5px">
                                    <button type="button" onclick="tag('b')" style="padding:2px 8px; font-size:12px"><b>B</b></button>
                                    <button type="button" onclick="tag('i')" style="padding:2px 8px; font-size:12px"><i>I</i></button>
                                    <button type="button" onclick="tag('u')" style="padding:2px 8px; font-size:12px"><u>U</u></button>
                                    <button type="button" onclick="tag('a')" style="padding:2px 8px; font-size:12px">Link</button>
                                    <button type="button" onclick="tag('code')" style="padding:2px 8px; font-size:12px">&lt;&gt;</button>
                                 </div>
                                 <textarea id="set-${{x.k}}" oninput="updatePreview(this.value)" style="height:120px; font-family:monospace; font-size:12px;">${{v.valor}}</textarea>
                                 <div id="html-preview" style="background:#000; padding:10px; border-radius:4px; margin:5px 0; font-size:12px; border:1px dashed var(--border)">
                                    <small style="color:var(--text-dim);display:block;margin-bottom:5px">Preview Visual (Telegram HTML):</small>
                                    <div id="preview-content" style="white-space: pre-wrap;">${{v.valor}}</div>
                                 </div>` 
                               : `<input id="set-${{x.k}}" value="${{v.valor}}">`
                        }}
                        <button onclick="saveSet('${{x.k}}')" class="primary" style="margin-top:5px;width:100%">Salvar</button>
                        <hr style="border:0; border-top:1px solid var(--border); margin:15px 0;">
                    `;
                }}
                c.innerHTML = html;
            }}
            function updatePreview(val) {{
                const p = document.getElementById('preview-content');
                if(p) p.innerHTML = val;
            }}
            function tag(t) {{
                const i = document.getElementById('set-assinatura');
                const s = i.selectionStart, e = i.selectionEnd;
                const txt = i.value;
                const sel = txt.substring(s, e);
                let rep = "";
                if(t==='a') rep = `<a href="URL_AQUI">${{sel || "texto"}}</a>`;
                else rep = `<${{t}}>${{sel}}</${{t}}>`;
                i.value = txt.substring(0, s) + rep + txt.substring(e);
                updatePreview(i.value);
                i.focus();
            }}
            async function saveSet(k) {{ 
                const val = document.getElementById('set-'+k).value;
                await api('settings','POST',{{chave:k, valor:val}}); 
                Telegram.WebApp.showAlert("Configuração '"+k+"' salva com sucesso!"); 
            }}
            async function fetchLogs() {{ 
                const term = document.getElementById('terminal');
                const timeStr = document.getElementById('log-time');
                if(!term.textContent) term.textContent = "Carregando logs...";
                const d = await api('logs'); 
                if(d.logs) {{
                    term.textContent = d.logs; 
                    term.scrollTop = term.scrollHeight;
                    const now = new Date();
                    timeStr.textContent = "Sincronizado: " + now.toLocaleDateString('pt-BR') + " " + now.toLocaleTimeString('pt-BR');
                }} else if(d.error) {{
                    term.textContent = "Erro: " + d.error;
                }}
            }}
            function toggleExpandLog() {{
                const t = document.getElementById('terminal');
                const b = document.getElementById('btn-expand');
                t.classList.toggle('expanded');
                b.textContent = t.classList.contains('expanded') ? '↕️ Reduzir' : '↕️ Expandir';
            }}
            if(window.Telegram && window.Telegram.WebApp) {{ Telegram.WebApp.ready(); Telegram.WebApp.expand(); }}
            setInterval(()=>{{ if(currentTab==='logs') fetchLogs(); if(currentTab==='dashboard') loadStatus(); }}, 2000);
            loadStatus();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html', headers=headers)

async def check_token(request):
    token = request.query.get('token')
    valid_token = get_config("console_token")
    return valid_token and token == valid_token

async def handle_status_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    return web.json_response({
        "canais_count": len(get_canais()),
        "kw_count": len(get_keywords()),
        "nkw_count": len(get_negative_keywords()),
        "pausado": get_config("pausado"),
        "aprovacao": get_config("aprovacao_manual"),
        "only_admins": get_config("only_admins") or "0"
    })

async def handle_restart_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    print("🔄 Reinicialização do Bot solicitada via Dashboard...")
    sys.stdout.flush()
    # Força a saída do processo após 2 segundos para dar tempo do dashboard receber o OK
    def terminate():
        print("💀 Encerrando processo para reinício automático...")
        os._exit(1) # Saída com erro costuma forçar o restart em plataformas como SquareCloud
    asyncio.get_event_loop().call_later(2.0, terminate)
    return web.json_response({"success": True, "message": "Bot reiniciando..."})

async def handle_canais_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    if request.method == 'GET': return web.json_response({"canais": get_canais()})
    elif request.method == 'POST':
        data = await request.json(); add_canal(data.get('canal'))
        return web.json_response({"success": True})
    elif request.method == 'DELETE':
        data = await request.json(); remove_canal(data.get('canal'))
        return web.json_response({"success": True})

async def handle_keywords_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    is_neg = 'neg' in request.path
    if request.method == 'GET': return web.json_response({"keywords": get_negative_keywords() if is_neg else get_keywords()})
    elif request.method == 'POST':
        data = await request.json(); kw = data.get('keyword')
        if kw: add_negative_keyword(kw) if is_neg else add_keyword(kw)
        return web.json_response({"success": True})
    elif request.method == 'DELETE':
        data = await request.json(); kw = data.get('keyword')
        if kw: remove_negative_keyword(kw) if is_neg else remove_keyword(kw)
        return web.json_response({"success": True})

async def handle_admins_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    if request.method == 'GET': return web.json_response({"admins": get_admins()})
    elif request.method == 'POST':
        data = await request.json(); add_admin(int(data['user_id']), data.get('username', ''))
        return web.json_response({"success": True})
    elif request.method == 'DELETE':
        data = await request.json(); remove_admin(int(data['user_id']))
        return web.json_response({"success": True})

async def handle_sorteios_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    if request.method == 'GET': return web.json_response({"sorteios": get_active_giveaways()})
    elif request.method == 'POST':
        data = await request.json(); create_giveaway(data['premio'])
        return web.json_response({"success": True})
    elif request.method == 'PATCH':
        data = await request.json(); close_giveaway(int(data['id']), int(data['winner_id']), data['winner_name'])
        return web.json_response({"success": True})

async def handle_settings_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    if request.method == 'GET': return web.json_response({"valor": get_config(request.query.get('key'))})
    elif request.method == 'POST':
        data = await request.json(); set_config(data['chave'], str(data['valor']))
        return web.json_response({"success": True})

async def handle_logs_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    if not os.path.exists("bot.log"): return web.json_response({"logs": "Sem logs"})
    with open("bot.log", "r", encoding="utf-8") as f:
        return web.json_response({"logs": "".join(f.readlines()[-150:])})

async def handle_watermark_get(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    if not os.path.exists("watermark.png"):
        return web.Response(status=404, text="Arquivo não encontrado")
    return web.FileResponse("watermark.png")

async def handle_watermark_post(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    data = await request.post()
    file = data.get('file')
    if not file: return web.json_response({"error": "No file uploaded"}, status=400)
    
    content = file.file.read()
    with open("watermark.png", "wb") as f:
        f.write(content)
        
    print(f"🖼️ Nova moldura recebida via Mini App: {len(content)} bytes")
    return web.json_response({"success": True, "size": len(content)})

async def handle_scrape(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    try:
        data = await request.json()
        url = data.get("url")
        if not url: return web.json_response({"error": "URL missing"}, status=400)
        from scraper import fetch_product_metadata
        metadata = await fetch_product_metadata(url)
        return web.json_response(metadata)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_generate_text(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    try:
        data = await request.json()
        from rewriter import gerar_promocao_por_link
        texto = await gerar_promocao_por_link(
            data.get("title"),
            data.get("url"),
            data.get("price"),
            data.get("coupon"),
            data.get("observation")
        )
        return web.json_response({"text": texto})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_post_offer(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    try:
        data = await request.json()
        from monitor import post_queue
        from watermark import apply_watermark
        from links import process_and_replace_links
        import re

        text_base = data.get("text")
        img_path = data.get("image_path")
        orig_url = data.get("url")

        if not text_base: return web.json_response({"error": "Text missing"}, status=400)

        # Processar links se necessário (garantir botões)
        if "[LINK_" not in text_base and "Pegar promoção" not in text_base:
             text_base += "\n\n[LINK_0]"

        clean_text, placeholder_map = await process_and_replace_links(text_base, orig_url)
        
        # Formata botões
        if placeholder_map:
            for placeholder, final_url in placeholder_map.items():
                if final_url:
                    text_base = text_base.replace(placeholder, f"🛒 <a href='{final_url}'>Pegar promoção</a>")
                else:
                    text_base = text_base.replace(placeholder, "")
        
        text_base = re.sub(r'\[LINK_\d+\]', '', text_base)

        # Assinatura
        assinatura = get_config("assinatura")
        if assinatura: text_base += f"\n\n{assinatura}"

        # Watermark
        if img_path and os.path.exists(img_path):
            img_path = apply_watermark(img_path)

        # Postar
        await post_queue.put((text_base, img_path, None))
        return web.json_response({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

async def start_web_server():
    if not get_config("console_token"): set_config("console_token", secrets.token_urlsafe(16))
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/status', handle_status_api)
    app.router.add_post('/api/restart', handle_restart_api)
    app.router.add_route('*', '/api/canais', handle_canais_api)
    app.router.add_route('*', '/api/keywords', handle_keywords_api)
    app.router.add_route('*', '/api/neg_keywords', handle_keywords_api)
    app.router.add_route('*', '/api/admins', handle_admins_api)
    app.router.add_route('*', '/api/sorteios', handle_sorteios_api)
    app.router.add_route('*', '/api/settings', handle_settings_api)
    app.router.add_get('/api/logs', handle_logs_api)
    app.router.add_get('/api/watermark', handle_watermark_get)
    app.router.add_post('/api/watermark', handle_watermark_post)
    app.router.add_post('/api/scrape', handle_scrape)
    app.router.add_post('/api/generate_text', handle_generate_text)
    app.router.add_post('/api/post_offer', handle_post_offer)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f"🌐 Dashboard rodando na porta {port}")
    while True: await asyncio.sleep(3600)
