import asyncio
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone

# 1. Sistema de Logs Global (Redireciona tudo para o bot.log)
class LoggerWriter:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.filename = filename
        self.at_start = True

    def write(self, message):
        if not message or message == '\n': 
            try:
                self.terminal.write(message)
            except UnicodeEncodeError:
                self.terminal.write(message.encode(self.terminal.encoding, errors='backslashreplace').decode(self.terminal.encoding))
            return
            
        now = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("[%d/%m %H:%M:%S] ")
        formatted = ""
        lines = message.splitlines(keepends=True)
        for line in lines:
            if self.at_start and line.strip():
                formatted += now
                self.at_start = False
            formatted += line
            if line.endswith('\n'):
                self.at_start = True
        
        try:
            self.terminal.write(formatted)
        except UnicodeEncodeError:
            # Fallback para terminais que não suportam certos caracteres (ex: Windows CMD sem UTF-8)
            self.terminal.write(formatted.encode(self.terminal.encoding, errors='backslashreplace').decode(self.terminal.encoding))
            
        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(formatted)
        except: pass

    def flush(self):
        self.terminal.flush()

if sys.stdout.encoding.lower() != 'utf-8':
    try: 
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except: pass

sys.stdout = LoggerWriter("bot.log")
sys.stderr = sys.stdout

async def run_task_with_retry(name, coro_func, delay=10):
    """Executa uma tarefa e a reinicia em caso de erro fatal."""
    while True:
        try:
            print(f"🚀 Iniciando: {name}")
            await coro_func()
            print(f"ℹ️ {name} finalizado voluntariamente.")
            break 
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ Erro em {name}: {e}")
            traceback.print_exc()
            print(f"🔄 Reiniciando {name} em {delay}s...")
            await asyncio.sleep(delay)

async def main():
    print("="*50)
    print("INICIANDO SISTEMA PECHINCHAS")
    print("="*50)
    
    # Banco de dados
    from database import init_db
    init_db()

    # Imports locais para evitar circular dependency
    from web_dashboard import start_web_server
    from monitor import start_monitoring
    from admin import start_admin_bot

    # Criamos as tarefas
    # Dashboard é o MAIS IMPORTANTE para a Square Cloud (Porta 8080)
    dashboard_task = asyncio.create_task(run_task_with_retry("Dashboard Web", start_web_server, delay=5))
    
    # Aguarda o dashboard subir antes de tentar conectar bots (evita 408 por bloqueio de rede inicial)
    await asyncio.sleep(2)

    monitor_task = asyncio.create_task(run_task_with_retry("Monitoramento", start_monitoring, delay=20))
    admin_task = asyncio.create_task(run_task_with_retry("Bot Admin", start_admin_bot, delay=10))
    
    tasks = [dashboard_task, monitor_task, admin_task]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nDesligando...")
    finally:
        for t in tasks:
            if not t.done(): t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
