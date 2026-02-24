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

async def main():
    print("="*60)
    print("Bot Pechinchas do Luiz4o - Sistema de Monitoramento + Controle")
    print("="*60)
    
    while True:
        tasks = []
        try:
            # Create a new event loop scope or tasks for this iteration
            t1 = asyncio.create_task(start_monitoring())
            t2 = asyncio.create_task(start_admin_bot())
            t3 = asyncio.create_task(start_web_server())
            tasks = [t1, t2, t3]
            
            # Roda os três processos juntos
            await asyncio.gather(*tasks)
            # Se gather terminar (o que não deve ocorrer normalmente), quebra o loop
            break
        except KeyboardInterrupt:
            print("\nDesligando sistema...")
            for t in tasks: t.cancel()
            break
        except Exception as e:
            print(f"\nErro fatal: {e}")
            print("⏳ Cancelando processos em segundo plano...")
            for t in tasks: t.cancel()
            print("⏳ Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
