import asyncio
import sys
import os

# Adiciona o diretrio atual ao path para importar publisher
sys.path.append(os.getcwd())

class MockException(Exception):
    pass

class MockBot:
    def __init__(self):
        self.attempts = 0

    async def send_photo(self, **kwargs):
        self.attempts += 1
        if self.attempts < 3:
            # Simula o erro 104
            raise Exception("HTTP Client says - ClientOSError: [Errno 104] Connection reset by peer")
        print(f"Sucesso na tentativa {self.attempts}!")
        return "mock_msg_id"

async def test_retry():
    import publisher
    mock_bot = MockBot()
    # Substitui temporariamente o bot global no publisher
    original_bot = publisher.bot
    publisher.bot = mock_bot
    
    # Mock BOT_TOKEN e TARGET_CHANNEL
    publisher.TARGET_CHANNEL = "@test"
    
    print("Iniciando teste de retry para Errno 104...")
    # Mock do FSInputFile para no dar erro de import
    publisher.FSInputFile = lambda x: x
    
    # Mock de os.path.exists
    original_exists = os.path.exists
    os.path.exists = lambda x: True
    
    try:
        # Chamamos send_with_retry diretamente com uma lambda que falha
        success = await publisher.send_with_retry(lambda: mock_bot.send_photo())
        print(f"Resultado final: {success}")
        if mock_bot.attempts == 3:
            print(" TESTE PASSOU: O bot tentou 3 vezes antes de ter sucesso.")
        else:
            print(f" TESTE FALHOU: O bot tentou {mock_bot.attempts} vezes.")
    except Exception as e:
        print(f"Erro inesperado no teste: {e}")
    finally:
        publisher.bot = original_bot
        os.path.exists = original_exists

if __name__ == "__main__":
    asyncio.run(test_retry())
