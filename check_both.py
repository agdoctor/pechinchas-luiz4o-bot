import sqlite3
import os

def check_bot(path, name):
    db = os.path.join(path, "bot_data.db")
    if not os.path.exists(db):
        print(f"--- {name}: DB não encontrado ({db}) ---")
        return
    
    conn = sqlite3.connect(db)
    c = conn.cursor()
    print(f"--- CANAIS MONITORADOS ({name}) ---")
    try:
        c.execute("SELECT * FROM canais")
        for row in c.fetchall():
            print(row)
    except Exception as e:
        print(f"Erro ao ler canais: {e}")
    conn.close()

if __name__ == "__main__":
    check_bot(r"c:\Users\luizh\.gemini\antigravity\pechinchasdoluiz4o\pechinchas_bot", "Pechinchas")
    check_bot(r"c:\Users\luizh\.gemini\antigravity\literalmentepromo\literalmente_bot", "Literalmente")
