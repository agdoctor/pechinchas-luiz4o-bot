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
        self.log = open(filename, "a", encoding="utf-8")
        self.at_start_of_line = True

    def write(self, message):
        if not message: return
        from datetime import datetime, timedelta, timezone
        
        lines = message.splitlines(keepends=True)
        for line in lines:
            if self.at_start_of_line and line.strip():
                # Forçar UTC-3 (Brasil) indepedente de onde o bot rode
                now = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("[%d/%m %H:%M:%S] ")
                self.terminal.write(now)
                self.log.write(now)
                self.at_start_of_line = False
            
            self.terminal.write(line)
            self.log.write(line)
            
            if line.endswith('\n'):
                self.at_start_of_line = True
                
        self.log.flush()

    def flush(self):
        if hasattr(self.terminal, "flush"): self.terminal.flush()
        self.log.flush()

sys.stdout = LoggerWriter("bot.log")
sys.stderr = sys.stdout

async def run_task_with_retry(name, coro_func, delay=5):
    """Executa uma tarefa e a reinicia em caso de erro, sem derrubar as outras."""
    while True:
        try:
            print(f"🚀 Iniciando processo: {name}")
            await coro_func()
            print(f"ℹ️ Processo {name} finalizado voluntariamente.")
            break # Se a tarefa terminar normalmente, para o loop
        except asyncio.CancelledError:
            print(f"ℹ️ Processo {name} cancelado.")
            break
        except Exception as e:
            print(f"⚠️ Erro no processo {name}: {e}")
            print(f"🔄 Reiniciando {name} em {delay} segundos...")
            await asyncio.sleep(delay)

async def main():
    print("="*60)
    print("Bot Pechinchas do Luiz4o - Sistema de Monitoramento + Controle")
    print("="*60)
    
    # Criamos as tarefas de forma que uma não derrube a outra
    tasks = [
        asyncio.create_task(run_task_with_retry("Monitoramento", start_monitoring)),
        asyncio.create_task(run_task_with_retry("Bot Admin", start_admin_bot)),
        asyncio.create_task(run_task_with_retry("Dashboard Web", start_web_server))
    ]
    
    try:
        # Aguarda indefinidamente enquanto as tarefas rodam
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nDesligando sistema...")
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
