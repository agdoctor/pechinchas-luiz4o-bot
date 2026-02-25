import asyncio
from monitor import start_monitoring
from admin import start_admin_bot
from web_dashboard import start_web_server

import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class LoggerWriter:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log_filename = filename
        self.at_start_of_line = True
        # Abre o log apenas quando necessário para evitar travas de escrita se o disco estiver lento
        self._check_file()

    def _check_file(self):
        try:
            with open(self.log_filename, "a", encoding="utf-8") as f:
                pass
        except: pass

    def write(self, message):
        if not message: return
        from datetime import datetime, timedelta, timezone
        
        try:
            timestamp = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("[%d/%m %H:%M:%S] ")
            
            output = ""
            lines = message.splitlines(keepends=True)
            for line in lines:
                if self.at_start_of_line and line.strip():
                    output += timestamp
                    self.at_start_of_line = False
                output += line
                if line.endswith('\n'):
                    self.at_start_of_line = True

            self.terminal.write(output)
            # Escrita no arquivo de forma mais eficiente
            with open(self.log_filename, "a", encoding="utf-8") as f:
                f.write(output)
        except:
            self.terminal.write(message)

    def flush(self):
        if hasattr(self.terminal, "flush"): self.terminal.flush()

sys.stdout = LoggerWriter("bot.log")
sys.stderr = sys.stdout

async def run_task_with_retry(name, coro_func, delay=5):
    """Executa uma tarefa e a reinicia em caso de erro, sem derrubar as outras."""
    while True:
        try:
            print(f"🚀 Iniciando processo: {name}")
            await coro_func()
            print(f"ℹ️ Processo {name} finalizado voluntariamente.")
            break 
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"⚠️ Erro no processo {name}: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(delay)

async def main():
    print("="*60)
    print("Bot Pechinchas do Luiz4o - Sistema de Monitoramento + Controle")
    print("="*60)
    
    # 1. Garante que o banco de dados está pronto
    from database import init_db
    init_db()

    # 2. Inicia o Dashboard Web PRIMEIRO para garantir que a porta 8080 seja vinculada antes do bot
    # Isso evita os erros 408/502 caso o bot demore pra iniciar ou trave no login.
    dashboard_task = asyncio.create_task(run_task_with_retry("Dashboard Web", start_web_server))
    
    # Pequeno delay para o Dashboard bindar a porta
    await asyncio.sleep(2)

    # 3. Inicia as demais tarefas em background
    tasks = [
        dashboard_task,
        asyncio.create_task(run_task_with_retry("Monitoramento", start_monitoring)),
        asyncio.create_task(run_task_with_retry("Bot Admin", start_admin_bot))
    ]
    
    try:
         await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nDesligando sistema...")
    finally:
        for t in tasks:
            if not t.done(): t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
