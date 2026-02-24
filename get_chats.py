import requests
import json
import os
from dotenv import load_dotenv

# Tenta carregar do .env primeiro
load_dotenv()

ID_INSTANCE = os.getenv("GREEN_API_INSTANCE_ID")
API_TOKEN = os.getenv("GREEN_API_TOKEN")
HOST = os.getenv("GREEN_API_HOST")

# Se não estiver no .env, tenta buscar no banco de dados do bot
if not ID_INSTANCE or not API_TOKEN:
    try:
        import sqlite3
        db_file = "bot_data.db"
        if os.path.exists(db_file):
            print(f"📂 Banco de dados '{db_file}' encontrado. Lendo chaves...")
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            
            # Debug: Listar o que tem no banco
            c.execute("SELECT chave, valor FROM config")
            rows = c.fetchall()
            found_keys = [r[0] for r in rows]
            
            for key, val in rows:
                if key == 'green_api_instance_id': ID_INSTANCE = val
                if key == 'green_api_token': API_TOKEN = val
                if key == 'green_api_host': HOST = val
            
            conn.close()
            
            if not ID_INSTANCE or not API_TOKEN:
                print(f"⚠️ Chaves da Green-API não encontradas no banco '{db_file}'.")
                print(f"🔍 Chaves disponíveis no seu Dashboard: {', '.join(found_keys)}")
        else:
            print(f"❌ Arquivo '{db_file}' não encontrado na pasta atual ({os.getcwd()}).")
    except Exception as e:
        print(f"⚠️ Aviso ao ler banco de dados: {e}")

if not HOST: HOST = "api.green-api.com"

def get_group_info(jid):
    """Consulta detalhes extras do grupo para ver se é de anúncios."""
    url = f"https://{HOST}/waInstance{ID_INSTANCE}/getGroupData/{API_TOKEN}"
    payload = {"groupId": jid}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('isCommunityAnnounce'): return "📣 AVISOS (COMUNIDADE)"
            if data.get('isCommunity'): return "🏢 COMUNIDADE (RAIZ)"
        return "Grupo Comum"
    except:
        return "---"

def list_chats():
    global ID_INSTANCE, API_TOKEN, HOST
    
    if not ID_INSTANCE or not API_TOKEN:
        print("\n🔑 Credenciais não encontradas automaticamente.")
        ID_INSTANCE = input("Digite o seu ID INSTÂNCIA da Green-API: ").strip()
        API_TOKEN = input("Digite o seu TOKEN da Green-API: ").strip()
        host_input = input(f"Digite o seu HOST (aperte Enter para usar {HOST}): ").strip()
        if host_input: HOST = host_input
        
        # Salva localmente para não pedir de novo
        if ID_INSTANCE and API_TOKEN:
            try:
                import sqlite3
                conn = sqlite3.connect("bot_data.db")
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", ('green_api_instance_id', ID_INSTANCE))
                c.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", ('green_api_token', API_TOKEN))
                c.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", ('green_api_host', HOST))
                conn.commit()
                conn.close()
                print("💾 Credenciais salvas no banco de dados local para a próxima vez!")
            except Exception as e:
                print(f"⚠️ Erro ao salvar localmente: {e}")

    if not ID_INSTANCE or not API_TOKEN:
        print("❌ Erro: ID e Token são obrigatórios.")
        return

    print(f"📡 Buscando chats no host {HOST}...")
    url = f"https://{HOST}/waInstance{ID_INSTANCE}/getChats/{API_TOKEN}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            chats = response.json()
            print(f"\n✅ Encontrados {len(chats)} chats!\n")
            
            # Filtra apenas os que tem "Pechinchas" no nome para ser rápido
            print(f"{'NOME':<30} | {'ID':<40} | {'TIPO DETALHADO'}")
            print("-" * 105)
            
            for chat in chats:
                name = chat.get('name', 'Sem Nome')
                jid = chat.get('id', 'Sem ID')
                
                if "@g.us" in jid:
                    # Se o nome contiver Pechinchas, fazemos o "Deep Scan"
                    if "PECHINCHAS" in name.upper() or "LUIZ4O" in name.upper():
                        tipo = get_group_info(jid)
                        print(f"🔍 {name:<28} | {jid:<40} | {tipo}")
                    else:
                        print(f"{name:<30} | {jid:<40} | ---")
            
            print("\n💡 Dica: O bot deve postar no ID marcado como '📣 AVISOS (COMUNIDADE)'.")
        else:
            print(f"❌ Erro Green-API ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    list_chats()
