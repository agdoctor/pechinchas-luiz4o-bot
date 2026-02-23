import asyncio
from monitor import start_monitoring
from admin import start_admin_bot
from web_dashboard import start_web_server

import sys

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
    print("🤖 Bot Pechinchas do Luiz4o - Sistema de Monitoramento + Controle")
    print("="*60)
    
    while True:
        try:
            # Roda os três processos (Monitor + Admin + Web Console) juntos
            await asyncio.gather(
                start_monitoring(),
                start_admin_bot(),
                start_web_server()
            )
            # Se gather terminar (o que não deve ocorrer normalmente), quebra o loop
            break
        except KeyboardInterrupt:
            print("\nDesligando sistema...")
            break
        except Exception as e:
            print(f"\nErro fatal: {e}")
            print("⏳ Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
