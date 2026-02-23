from aiohttp import web
from database import get_config, set_config
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
        'Content-Type': 'text/html',
        'Content-Security-Policy': "frame-ancestors https://web.telegram.org https://pwa.telegram.org https://desktop.telegram.org https://*.telegram.org;",
        'X-Frame-Options': 'ALLOWALL'
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bot Console - Pechinchas</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            /* (estilos omitidos para brevidade, herdar o resto) */
            body {{
                background-color: #0d1117;
                color: #e6edf3;
                font-family: 'Cascadia Code', 'Courier New', Courier, monospace;
                margin: 0;
                padding: 10px;
                display: flex;
                flex-direction: column;
                height: 100vh;
                box-sizing: border-box;
            }}
            #header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #30363d;
                padding-bottom: 8px;
                margin-bottom: 10px;
            }}
            #terminal {{
                flex-grow: 1;
                overflow-y: auto;
                background-color: #010409;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #30363d;
                line-height: 1.4;
                font-size: 13px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            .log-line {{ margin-bottom: 2px; }}
            .error {{ color: #ff7b72; }}
            .success {{ color: #3fb950; }}
            .warning {{ color: #d29945; }}
            .info {{ color: #58a6ff; }}
            .highlight {{ color: #ffa657; }}
            
            #controls {{
                margin-top: 10px;
                display: flex;
                gap: 10px;
            }}
            button {{
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
            }}
            button:hover {{ background-color: #30363d; }}
            button.active {{ background-color: #238636; color: white; border-color: #2ea043; }}
            
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #010409; }}
            ::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div id="header">
            <span style="font-weight: bold; color: #58a6ff;">🚀 Pechinchas Console</span>
            <span id="status" style="font-size: 11px;">Conectando...</span>
        </div>
        <div id="terminal">Iniciando console...</div>
        <div id="controls">
            <button id="refreshBtn">🔄 Atualizar</button>
            <button id="autoUpdateBtn" class="active">📡 Auto-Update: ON</button>
            <button id="clearBtn">🧹 Limpar Tela</button>
        </div>

        <script>
            const terminal = document.getElementById('terminal');
            const status = document.getElementById('status');
            const refreshBtn = document.getElementById('refreshBtn');
            const autoUpdateBtn = document.getElementById('autoUpdateBtn');
            const clearBtn = document.getElementById('clearBtn');
            
            let autoUpdate = true;
            let lastContent = "";

            function formatLine(line) {{
                if (!line.trim()) return "";
                let className = "";
                if (line.includes("❌") || line.includes("Erro") || line.includes("fail")) className = "error";
                if (line.includes("✅") || line.includes("Sucesso") || line.includes("publicada")) className = "success";
                if (line.includes("⚠️") || line.includes("Aviso") || line.includes("Warning")) className = "warning";
                if (line.includes("🚨") || line.includes("Nova mensagem")) className = "highlight";
                if (line.includes("🔍") || line.includes("Processando")) className = "info";
                
                return `<div class="log-line ${{className}}">${{line}}</div>`;
            }}

            async function fetchLogs() {{
                try {{
                    // Passa o token também na chamada da API
                    const response = await fetch('/api/logs?token={token}');
                    const data = await response.json();
                    
                    if (data.logs !== lastContent) {{
                        lastContent = data.logs;
                        const lines = data.logs.split('\\n');
                        terminal.innerHTML = lines.map(formatLine).join('');
                        terminal.scrollTop = terminal.scrollHeight;
                        status.textContent = "Atualizado: " + new Date().toLocaleTimeString();
                        status.style.color = "#3fb950";
                    }}
                }} catch (err) {{
                    status.textContent = "Erro na conexão";
                    status.style.color = "#ff7b72";
                }}
            }}

            refreshBtn.onclick = fetchLogs;
            clearBtn.onclick = () => {{ terminal.innerHTML = ""; lastContent = ""; }};
            autoUpdateBtn.onclick = () => {{
                autoUpdate = !autoUpdate;
                autoUpdateBtn.classList.toggle('active');
                autoUpdateBtn.textContent = "📡 Auto-Update: " + (autoUpdate ? "ON" : "OFF");
            }};

            setInterval(() => {{
                if (autoUpdate) fetchLogs();
            }}, 3000);

            fetchLogs();
            
            if (window.Telegram && window.Telegram.WebApp) {{
                Telegram.WebApp.ready();
                Telegram.WebApp.expand();
            }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html', headers=headers)

async def handle_logs_api(request):
    # Verifica Token de Segurança
    token = request.query.get('token')
    valid_token = get_config("console_token")
    if not valid_token or token != valid_token:
        return web.json_response({"error": "Unauthorized"}, status=403)

    log_path = "bot.log"
    if not os.path.exists(log_path):
        return web.json_response({"logs": "Arquivo de log ainda não criado."})
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # Pega as últimas 150 linhas
            lines = f.readlines()
            last_lines = lines[-150:]
            return web.json_response({"logs": "".join(last_lines)})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def start_web_server():
    # Gera um token se não existir
    if not get_config("console_token"):
        new_token = secrets.token_urlsafe(16)
        set_config("console_token", new_token)
        print(f"🔑 Novo Token de Segurança gerado para o Console.")

    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/logs', handle_logs_api)
    
    # Pega porta do ambiente (padrão 8080 para SquareCloud)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    print(f"🌐 Servidor Web do Console iniciado na porta {port}")
    try:
        await site.start()
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:
            print(f"⚠️ A porta {port} já está em uso. O Console Web não pôde ser iniciado agora.")
            print(f"💡 Dica: Verifique se outra instância do bot está rodando.")
            # Não Mata o bot, apenas encerra esta task
            return
        else:
            raise e
    
    # Mantém rodando
    while True:
        await asyncio.sleep(3600)
