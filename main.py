import asyncio
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone

# Forçar UTF-8 para evitar erros de encode em logs de nuvem
if sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

def get_now_br():
    return (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("[%d/%m %H:%M:%S]")

def log_print(msg):
    now = get_now_br()
    text = f"{now} {msg}"
    print(text)
    try:
        with open("bot.log", "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except: pass

async def run_task_with_retry(name, coro_func, delay=10):
    """Executa uma tarefa e a reinicia em caso de erro fatal."""
    while True:
        try:
            log_print(f"🚀 Iniciando: {name}")
            await coro_func()
            log_print(f"ℹ️ {name} finalizado.")
            break 
        except asyncio.CancelledError:
            break
        except Exception as e:
            log_print(f"❌ Erro em {name}: {e}")
            traceback.print_exc()
            log_print(f"🔄 Reiniciando {name} em {delay}s...")
            await asyncio.sleep(delay)

async def main():
    log_print("="*50)
    log_print("INICIANDO SISTEMA PECHINCHAS")
    log_print("="*50)
    
    # 1. Banco de dados rápido
    try:
        from database import init_db
        init_db()
    except Exception as e:
        log_print(f"⚠️ Erro no Banco de Dados: {e}")

    # 2. Imports das funções (dentro do main para evitar travas no topo)
    from web_dashboard import start_web_server
    from monitor import start_monitoring
    from admin import start_admin_bot

    # 3. Dashboard é PRIORIDADE ZERO. Sem ele a Square Cloud dá 408/502.
    # Criamos em background e não aguardamos ele para iniciar os outros.
    asyncio.create_task(run_task_with_retry("Dashboard Web", start_web_server, delay=5))
    
    # Pequeno respiro para bindar a porta
    await asyncio.sleep(1)

    # 4. Outros robôs
    tasks = [
        asyncio.create_task(run_task_with_retry("Monitoramento (Userbot)", start_monitoring, delay=15)),
        asyncio.create_task(run_task_with_retry("Bot Admin (Telegram)", start_admin_bot, delay=10))
    ]
    
    # Mantém o main vivo
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        log_print("Desligando...")
    except Exception as e:
        log_print(f"Erro critico no loop main: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
