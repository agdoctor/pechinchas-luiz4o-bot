import asyncio
from monitor import start_monitoring
from admin import start_admin_bot

async def main():
    print("="*60)
    print("🤖 Bot Pechinchas do Luiz4o - Sistema de Monitoramento + Controle")
    print("="*60)
    
    while True:
        try:
            # Roda os dois processos (Userbot Telethon + Admin Aiogram) juntos assincronamente
            await asyncio.gather(
                start_monitoring(),
                start_admin_bot()
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
