from aiohttp import web
from database import (
    get_config, set_config, get_canais, add_canal, remove_canal,
    get_keywords, add_keyword, remove_keyword,
    get_negative_keywords, add_negative_keyword, remove_negative_keyword
)
import secrets
import os
import json
import asyncio

async def handle_index(request):
    # Verifica Token de Segurança
    token = request.query.get('token')
    valid_token = get_config("console_token")
    
    if not valid_token or token != valid_token:
        return web.Response(text="<h1>403 Forbidden</h1><p>Acesso negado. Token inválido.</p>", status=403, content_type='text/html')

    # Headers para permitir o Mini App abrir no Telegram Web sem bloqueios
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
        <title>Pechinchas - Admin Dashboard</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            :root {{
                --bg-main: #0d1117;
                --bg-sec: #161b22;
                --bg-card: #21262d;
                --border: #30363d;
                --text: #e6edf3;
                --text-dim: #8b949e;
                --accent: #58a6ff;
                --success: #238636;
                --error: #da3633;
                --warning: #d29945;
            }}

            body {{
                background-color: var(--bg-main);
                color: var(--text);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                height: 100vh;
                overflow: hidden;
            }}

            #navbar {{
                display: flex;
                background: var(--bg-sec);
                border-bottom: 1px solid var(--border);
                padding: 0 10px;
                overflow-x: auto;
                scrollbar-width: none;
            }}
            #navbar::-webkit-scrollbar {{ display: none; }}
            
            .nav-item {{
                padding: 12px 15px;
                color: var(--text-dim);
                cursor: pointer;
                white-space: nowrap;
                font-size: 14px;
                font-weight: 500;
                border-bottom: 2px solid transparent;
                transition: 0.2s;
            }}
            .nav-item.active {{
                color: var(--text);
                border-bottom-color: var(--accent);
            }}

            main {{
                flex-grow: 1;
                overflow-y: auto;
                padding: 15px;
            }}

            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}

            /* Cards & Groups */
            .card {{
                background: var(--bg-sec);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }}
            .card-title {{
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 12px;
                color: var(--accent);
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            /* Inputs & Forms */
            .input-group {{
                display: flex;
                gap: 8px;
                margin-bottom: 10px;
            }}
            input {{
                flex-grow: 1;
                background: var(--bg-main);
                border: 1px solid var(--border);
                color: var(--text);
                padding: 8px 12px;
                border-radius: 6px;
                outline: none;
            }}
            input:focus {{ border-color: var(--accent); }}
            
            button {{
                background: var(--bg-card);
                border: 1px solid var(--border);
                color: var(--text);
                padding: 8px 15px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                transition: 0.2s;
            }}
            button:hover {{ background: var(--border); }}
            button.primary {{ background: var(--success); border-color: rgba(255,255,255,0.1); }}
            button.danger {{ color: var(--error); }}

            /* Lists */
            ul {{ list-style: none; padding: 0; margin: 0; }}
            li {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid var(--border);
            }}
            li:last-child {{ border-bottom: none; }}

            /* Terminal View */
            #terminal {{
                background: #010409;
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 10px;
                font-family: 'Cascadia Code', monospace;
                font-size: 12px;
                height: 400px;
                overflow-y: auto;
                white-space: pre-wrap;
            }}
            .log-line {{ margin-bottom: 2px; }}

            /* Status Pills */
            .badge {{
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
                background: var(--border);
            }}
            .badge.success {{ background: #23863644; color: #3fb950; }}
            .badge.error {{ background: #da363344; color: #ff7b72; }}
        </style>
    </head>
    <body>
        <div id="navbar">
            <div class="nav-item active" onclick="showTab('dashboard')">🏠 Painel</div>
            <div class="nav-item" onclick="showTab('canais')">📺 Canais</div>
            <div class="nav-item" onclick="showTab('keywords')">🔑 Keywords</div>
            <div class="nav-item" onclick="showTab('settings')">⚙️ Config</div>
            <div class="nav-item" onclick="showTab('logs')">📜 Logs</div>
        </div>

        <main>
            <!-- TAB DASHBOARD -->
            <div id="tab-dashboard" class="tab-content active">
                <div class="card">
                    <div class="card-title">🤖 Status do Sistema</div>
                    <div id="status-container">Carregando...</div>
                </div>
                <div class="card">
                    <div class="card-title">🚀 Atalhos Rápidos</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <button onclick="togglePausa()" id="btn-pausa">Pausar Bot</button>
                        <button onclick="toggleAprovacao()" id="btn-aprovacao">Aprovação Manual</button>
                    </div>
                </div>
            </div>

            <!-- TAB CANAIS -->
            <div id="tab-canais" class="tab-content">
                <div class="card">
                    <div class="card-title">📺 Canais Monitorados</div>
                    <div class="input-group">
                        <input type="text" id="new-canal" placeholder="Ex: promocoesdodia">
                        <button class="primary" onclick="addCanal()">Adicionar</button>
                    </div>
                    <ul id="list-canais"></ul>
                </div>
            </div>

            <!-- TAB KEYWORDS -->
            <div id="tab-keywords" class="tab-content">
                <div class="card">
                    <div class="card-title">🔑 Keywords (Positivas)</div>
                    <p style="font-size: 12px; color: var(--text-dim);">O bot só posta se encontrar alguma dessas:</p>
                    <div class="input-group">
                        <input type="text" id="new-kw" placeholder="Ex: iphone, ps5">
                        <button class="primary" onclick="addKeyword('kw')">Add</button>
                    </div>
                    <ul id="list-keywords"></ul>
                </div>
                <div class="card">
                    <div class="card-title">🚫 Keywords Negativas</div>
                    <p style="font-size: 12px; color: var(--text-dim);">O bot ignora se encontrar alguma dessas:</p>
                    <div class="input-group">
                        <input type="text" id="new-nkw" placeholder="Ex: seminovo, usado">
                        <button class="primary" onclick="addKeyword('nkw')">Add</button>
                    </div>
                    <ul id="list-neg-keywords"></ul>
                </div>
            </div>

            <!-- TAB CONFIG -->
            <div id="tab-settings" class="tab-content">
                <div class="card">
                    <div class="card-title">⚙️ Configurações Gerais</div>
                    <div id="settings-form">Carregando...</div>
                </div>
            </div>

            <!-- TAB LOGS -->
            <div id="tab-logs" class="tab-content">
                <div class="card">
                    <div class="card-title">📜 Console de Logs em Tempo Real</div>
                    <div id="terminal"></div>
                    <div style="margin-top: 10px; display: flex; gap: 10px;">
                        <button onclick="fetchLogs()">🔄 Atualizar</button>
                        <button onclick="clearTerminal()">🧹 Limpar</button>
                    </div>
                </div>
            </div>
        </main>

        <script>
            const token = "{token}";
            let currentTab = 'dashboard';

            function showTab(tabId) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                
                document.getElementById('tab-' + tabId).classList.add('active');
                event.target.classList.add('active');
                currentTab = tabId;
                
                if (tabId === 'canais') loadCanais();
                if (tabId === 'keywords') loadKeywords();
                if (tabId === 'settings') loadSettings();
                if (tabId === 'dashboard') loadStatus();
            }}

            async function api(path, method = 'GET', body = null) {{
                try {{
                    const options = {{
                        method,
                        headers: {{ 'Content-Type': 'application/json' }}
                    }};
                    if (body) options.body = JSON.stringify(body);
                    
                    const separator = path.includes('?') ? '&' : '?';
                    const res = await fetch(`/api/${{path}}${{separator}}token=${{token}}`, options);
                    const data = await res.json();
                    
                    if (!res.ok) return {{ error: data.error || "Erro no servidor" }};
                    return data;
                }} catch (e) {{
                    console.error("Erro API:", e);
                    return {{ error: "Erro de conexão" }};
                }}
            }}

            /* DASHBOARD / STATUS */
            async function loadStatus() {{
                const data = await api('status');
                const container = document.getElementById('status-container');
                if (data.error) {{
                    container.innerHTML = `<span class="badge error">Erro ao carregar dados</span>`;
                    return;
                }}
                
                container.innerHTML = `
                    <div style="margin-bottom: 8px;">Monitorando: <b>${{data.canais_count}} canais</b></div>
                    <div style="margin-bottom: 8px;">Keywords: <b>${{data.kw_count}}</b> (+), <b>${{data.nkw_count}}</b> (-)</div>
                    <div>Status Bot: <span class="badge ${{data.pausado === '1' ? 'error' : 'success'}}">${{data.pausado === '1' ? '⏸️ PAUSADO' : '▶️ ATIVO'}}</span></div>
                `;
                
                const btnPausa = document.getElementById('btn-pausa');
                btnPausa.textContent = data.pausado === '1' ? 'Retomar Bot' : 'Pausar Bot';
                btnPausa.className = data.pausado === '1' ? 'primary' : '';

                const btnAprov = document.getElementById('btn-aprovacao');
                btnAprov.textContent = data.aprovacao === '1' ? 'Desativar Aprovação Manual' : 'Ativar Aprovação Manual';
                btnAprov.className = data.aprovacao === '1' ? 'primary' : '';
            }}

            async function togglePausa() {{
                const data = await api('status');
                const novoVal = data.pausado === '1' ? '0' : '1';
                await api('settings', 'POST', {{ chave: 'pausado', valor: novoVal }});
                loadStatus();
            }}

            async function toggleAprovacao() {{
                const data = await api('status');
                const novoVal = data.aprovacao === '1' ? '0' : '1';
                await api('settings', 'POST', {{ chave: 'aprovacao_manual', valor: novoVal }});
                loadStatus();
            }}

            /* CANAIS */
            async function loadCanais() {{
                const data = await api('canais');
                const list = document.getElementById('list-canais');
                list.innerHTML = "";
                data.canais.forEach(c => {{
                    const li = document.createElement('li');
                    li.innerHTML = `<span>@${{c}}</span> <button class="danger" onclick="delCanal('${{c}}')">Remover</button>`;
                    list.appendChild(li);
                }});
            }}

            async function addCanal() {{
                const input = document.getElementById('new-canal');
                const val = input.value.trim().replace('@', '');
                if (!val) return;
                await api('canais', 'POST', {{ canal: val }});
                input.value = "";
                loadCanais();
            }}

            async function delCanal(c) {{
                if (!confirm("Remover "+c+"?")) return;
                await api('canais', 'DELETE', {{ canal: c }});
                loadCanais();
            }}

            /* KEYWORDS */
            async function loadKeywords() {{
                const kwData = await api('keywords');
                const nkwData = await api('neg_keywords');
                
                const listKw = document.getElementById('list-keywords');
                listKw.innerHTML = "";
                kwData.keywords.forEach(k => {{
                    const li = document.createElement('li');
                    li.innerHTML = `<span>${{k}}</span> <button class="danger" onclick="delKeyword('kw', '${{k}}')">x</button>`;
                    listKw.appendChild(li);
                }});

                const listNkw = document.getElementById('list-neg-keywords');
                listNkw.innerHTML = "";
                nkwData.keywords.forEach(k => {{
                    const li = document.createElement('li');
                    li.innerHTML = `<span>${{k}}</span> <button class="danger" onclick="delKeyword('nkw', '${{k}}')">x</button>`;
                    listNkw.appendChild(li);
                }});
            }}

            async function addKeyword(type) {{
                const input = document.getElementById(type === 'kw' ? 'new-kw' : 'new-nkw');
                const val = input.value.trim();
                if (!val) return;
                await api(type === 'kw' ? 'keywords' : 'neg_keywords', 'POST', {{ keyword: val }});
                input.value = "";
                loadKeywords();
            }}

            async function delKeyword(type, k) {{
                await api(type === 'kw' ? 'keywords' : 'neg_keywords', 'DELETE', {{ keyword: k }});
                loadKeywords();
            }}

            /* SETTINGS */
            async function loadSettings() {{
                // Simplificado para campos comuns
                const fields = [
                    {{ key: 'delay_minutos', label: 'Delay (minutos)', type: 'number' }},
                    {{ key: 'preco_minimo', label: 'Preço Mínimo (R$)', type: 'number' }},
                    {{ key: 'assinatura', label: 'Assinatura', type: 'text' }},
                    {{ key: 'webapp_url', label: 'Mini App URL', type: 'text' }}
                ];
                
                const container = document.getElementById('settings-form');
                container.innerHTML = "";
                
                for (const f of fields) {{
                    const val = await api('settings?key=' + f.key);
                    const div = document.createElement('div');
                    div.className = "card";
                    div.style.padding = "10px";
                    div.innerHTML = `
                        <label style="display:block; font-size:12px; margin-bottom:5px;">${{f.label}}:</label>
                        <div class="input-group">
                            <input type="${{f.type}}" id="set-${{f.key}}" value="${{val.valor}}">
                            <button onclick="saveSetting('${{f.key}}')">Salvar</button>
                        </div>
                    `;
                    container.appendChild(div);
                }}
            }}

            async function saveSetting(key) {{
                const val = document.getElementById('set-' + key).value;
                await api('settings', 'POST', {{ chave: key, valor: val }});
                Telegram.WebApp.showScanQrPopup({{ text: "Configuração salva!" }}); // Pequeno truque para feedback
                setTimeout(() => Telegram.WebApp.closeScanQrPopup(), 1000);
            }}

            /* LOGS */
            let lastLogContent = "";
            async function fetchLogs() {{
                const data = await api('logs');
                const term = document.getElementById('terminal');
                if (data.logs !== lastLogContent) {{
                    lastLogContent = data.logs;
                    term.textContent = data.logs;
                    term.scrollTop = term.scrollHeight;
                }}
            }}
            function clearTerminal() {{ document.getElementById('terminal').textContent = ""; lastLogContent = ""; }}

            // Init
            if (window.Telegram && window.Telegram.WebApp) {{
                Telegram.WebApp.ready();
                Telegram.WebApp.expand();
            }}
            setInterval(() => {{
                if (currentTab === 'logs') fetchLogs();
                if (currentTab === 'dashboard') loadStatus();
            }}, 5000);
            
            loadStatus();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html', headers=headers)

# --- API HANDLERS ---

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
    })

async def handle_canais_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    
    if request.method == 'GET':
        return web.json_response({"canais": get_canais()})
    
    elif request.method == 'POST':
        data = await request.json()
        canal = data.get('canal')
        if canal: add_canal(canal)
        return web.json_response({"success": True})
    
    elif request.method == 'DELETE':
        data = await request.json()
        canal = data.get('canal')
        if canal: remove_canal(canal)
        return web.json_response({"success": True})

async def handle_keywords_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    is_neg = 'neg' in request.path
    
    if request.method == 'GET':
        kws = get_negative_keywords() if is_neg else get_keywords()
        return web.json_response({"keywords": kws})
    
    elif request.method == 'POST':
        data = await request.json()
        kw = data.get('keyword')
        if kw:
            if is_neg: add_negative_keyword(kw)
            else: add_keyword(kw)
        return web.json_response({"success": True})
    
    elif request.method == 'DELETE':
        data = await request.json()
        kw = data.get('keyword')
        if kw:
            if is_neg: remove_negative_keyword(kw)
            else: remove_keyword(kw)
        return web.json_response({"success": True})

async def handle_settings_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    
    if request.method == 'GET':
        key = request.query.get('key')
        return web.json_response({"valor": get_config(key)})
    
    elif request.method == 'POST':
        data = await request.json()
        chave = data.get('chave')
        valor = data.get('valor')
        if chave is not None: set_config(chave, str(valor))
        return web.json_response({"success": True})

async def handle_logs_api(request):
    if not await check_token(request): return web.json_response({"error": "Unauthorized"}, status=403)
    
    log_path = "bot.log"
    if not os.path.exists(log_path): return web.json_response({"logs": "Sem logs"})
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return web.json_response({"logs": "".join(lines[-150:])})
    except:
        return web.json_response({"error": "Erro ao ler logs"}, status=500)

async def start_web_server():
    if not get_config("console_token"):
        set_config("console_token", secrets.token_urlsafe(16))

    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/status', handle_status_api)
    app.router.add_route('*', '/api/canais', handle_canais_api)
    app.router.add_route('*', '/api/keywords', handle_keywords_api)
    app.router.add_route('*', '/api/neg_keywords', handle_keywords_api)
    app.router.add_route('*', '/api/settings', handle_settings_api)
    app.router.add_get('/api/logs', handle_logs_api)
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    print(f"🌐 Servidor Web do Dashboard Admin iniciado na porta {{port}}")
    try:
        await site.start()
    except Exception as e:
        print(f"⚠️ Erro ao iniciar servidor web: {{e}}")
        return
    
    while True:
        await asyncio.sleep(3600)
