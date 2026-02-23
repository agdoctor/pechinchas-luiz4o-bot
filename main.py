import asyncio
from monitor import start_monitoring
from admin import start_admin_bot
from web_dashboard import start_web_server

import sys

class LoggerWriter:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
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
