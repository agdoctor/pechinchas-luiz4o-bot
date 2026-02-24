import sqlite3
import os

DB_PATH = "bot_data.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco {DB_PATH} não encontrado.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- CANAIS MONITORADOS ---")
    c.execute("SELECT * FROM canais")
    for row in c.fetchall():
        print(row)
        
    print("\n--- KEYWORDS ATIVAS ---")
    c.execute("SELECT * FROM keywords")
    for row in c.fetchall():
        print(row)
        
    print("\n--- CONFIGURAÇÕES ---")
    c.execute("SELECT * FROM config")
    for row in c.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
