import sqlite3
import os

DB_PATH = "bot_data.db"

def add_promotop():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco {DB_PATH} não encontrado.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Verifica se já existe
        c.execute("SELECT * FROM canais WHERE nome_ou_link = 'promotop'")
        if c.fetchone():
            print("✅ canal 'promotop' já está na lista.")
        else:
            c.execute("INSERT INTO canais (nome_ou_link) VALUES ('promotop')")
            conn.commit()
            print("🚀 canal 'promotop' adicionado com sucesso!")
    except Exception as e:
        print(f"Erro: {e}")
        
    conn.close()

if __name__ == "__main__":
    add_promotop()
