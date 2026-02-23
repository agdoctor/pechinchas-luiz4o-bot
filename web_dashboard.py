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
                overflow-x: auto; scrollbar-width: none; flex-shrink: 0; z-index: 100;
            }}
            .nav-item {{
                padding: 12px 15px; color: var(--text-dim); cursor: pointer; white-space: nowrap;
                font-size: 14px; border-bottom: 2px solid transparent; transition: 0.2s;
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
            #terminal {{ background: #000; padding: 10px; font-size: 11px; height: 300px; overflow-y: auto; white-space: pre-wrap; color: #0f0; border-radius: 4px; }}
            .toggle-switch {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; cursor: pointer; }}
            .toggle-switch input {{ width: auto; }}
        </style>
    </head>
    <body>
        <div id="navbar">
            <div class="nav-item active" onclick="showTab('dashboard', this)">🏠 Painel</div>
            <div class="nav-item" onclick="showTab('canais', this)">📺 Canais</div>
            <div class="nav-item" onclick="showTab('keywords', this)">🔑 Keywords</div>
            <div class="nav-item" onclick="showTab('admins', this)">👥 Admins</div>
            <div class="nav-item" onclick="showTab('sorteios', this)">🎉 Sorteios</div>
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
                        Apenas Admins interagem com o Bot
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
            <div id="tab-logs" class="tab-content">
                <div class="card"><div class="card-title">📜 Logs</div><div id="terminal"></div><button onclick="fetchLogs()" style="margin-top:10px">🔄 Atualizar</button></div>
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
                document.getElementById('btn-pausa').textContent = d.pausado==='1' ? 'Retomar Bot' : 'Pausar Bot';
                document.getElementById('check-only-admins').checked = d.only_admins==='1';
            }}
            async function restartBot() {{
                if(!confirm("Deseja reiniciar o bot? O painel ficará offline por alguns segundos.")) return;
                await api('restart', 'POST'); 
                Telegram.WebApp.close();
            }}
            async function toggleOnlyAdmins() {{
                const v = document.getElementById('check-only-admins').checked ? '1' : '0';
                await api('settings', 'POST', {{ chave: 'only_admins', valor: v }});
            }}
            async function togglePausa() {{
                const d = await api('status');
                await api('settings', 'POST', {{ chave: 'pausado', valor: d.pausado==='1'?'0':'1' }});
                loadStatus();
            }}
            async function loadCanais() {{
                const d = await api('canais');
                const l = document.getElementById('list-canais'); l.innerHTML = "";
                d.canais.forEach(c => {{ l.innerHTML += `<li>@${{c}} <button class="danger" onclick="delCanal('${{c}}')">x</button></li>`; }});
            }}
            async function addCanal() {{ const i=document.getElementById('new-canal'); await api('canais','POST',{{canal:i.value}}); i.value=""; loadCanais(); }}
            async function delCanal(c) {{ await api('canais','DELETE',{{canal:c}}); loadCanais(); }}
            async function loadKeywords() {{
                const k = await api('keywords'); const n = await api('neg_keywords');
                const lk = document.getElementById('list-keywords'); lk.innerHTML = "";
                k.keywords.forEach(x => {{ lk.innerHTML += `<li>${{x}} <button class="danger" onclick="delKw('kw','${{x}}')">x</button></li>`; }});
                const ln = document.getElementById('list-neg-keywords'); ln.innerHTML = "";
                n.keywords.forEach(x => {{ ln.innerHTML += `<li>${{x}} <button class="danger" onclick="delKw('nkw','${{x}}')">x</button></li>`; }});
            }}
            async function delKw(t,x) {{ await api(t==='kw'?'keywords':'neg_keywords','DELETE',{{keyword:x}}); loadKeywords(); }}
            async function addKeyword(t) {{ const i=document.getElementById(t==='kw'?'new-kw':'new-nkw'); await api(t==='kw'?'keywords':'neg_keywords','POST',{{keyword:i.value}}); i.value=""; loadKeywords(); }}
            async function loadAdmins() {{
                const d = await api('admins'); const l = document.getElementById('list-admins'); l.innerHTML = "";
                d.admins.forEach(a => {{ l.innerHTML += `<li>${{a[1]}} (${{a[0]}}) <button class="danger" onclick="delAdmin('${{a[0]}}')">x</button></li>`; }});
            }}
            async function addAdmin() {{ await api('admins','POST',{{user_id:document.getElementById('new-admin-id').value, username:document.getElementById('new-admin-name').value}}); loadAdmins(); }}
            async function delAdmin(id) {{ await api('admins','DELETE',{{user_id:id}}); loadAdmins(); }}
            async function loadSorteios() {{
                const d = await api('sorteios'); const l = document.getElementById('list-sorteios'); l.innerHTML = "";
                d.sorteios.forEach(s => {{ l.innerHTML += `<li>${{s[1]}} <button onclick="closeSorteio('${{s[0]}}')">Encerrar</button></li>`; }});
            }}
            async function addSorteio() {{ await api('sorteios','POST',{{premio:document.getElementById('new-premio').value}}); loadSorteios(); }}
            async function closeSorteio(id) {{ await api('sorteios','PATCH',{{id:id, winner_id:0, winner_name:'Ganhador'}}); loadSorteios(); }}
            async function loadSettings() {{
                const f = [{{k:'delay_minutos',l:'Delay'}},{{k:'preco_minimo',l:'Preço'}},{{k:'assinatura',l:'Assinatura'}},{{k:'webapp_url',l:'WebApp URL'}}];
                const c = document.getElementById('settings-form'); c.innerHTML = "";
                for(const x of f) {{
                    const v = await api('settings?key='+x.k);
                    const isA = x.k==='assinatura';
                    c.innerHTML += `<p>${{x.l}}:</p>${{isA ? `<textarea id="set-${{x.k}}">${{v.valor}}</textarea>` : `<input id="set-${{x.k}}" value="${{v.valor}}">`}}<button onclick="saveSet('${{x.k}}')" class="primary" style="margin-top:5px;width:100%">Salvar</button>`;
                }}
            }}
            async function saveSet(k) {{ await api('settings','POST',{{chave:k, valor:document.getElementById('set-'+k).value}}); Telegram.WebApp.showAlert("Salvo!"); }}
            async function fetchLogs() {{ const d=await api('logs'); document.getElementById('terminal').textContent=d.logs; }}
            if(window.Telegram && window.Telegram.WebApp) {{ Telegram.WebApp.ready(); Telegram.WebApp.expand(); }}
            setInterval(()=>{{ if(currentTab==='logs') fetchLogs(); if(currentTab==='dashboard') loadStatus(); }}, 5000);
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
    asyncio.create_task(asyncio.sleep(1)).add_done_callback(lambda _: os._exit(0))
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
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f"🌐 Dashboard rodando na porta {{port}}")
    while True: await asyncio.sleep(3600)
