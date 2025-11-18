import os

class Config:
    def __init__(self):
        # Chave OpenAI - SEMPRE usar variável de ambiente
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        if not self.OPENAI_API_KEY:
            print("OPENAI_API_KEY não configurada!")
            print("Configure a variável de ambiente no Render")
        
        # Caminho para os manuais
        self.CAMINHO_MANUAIS = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "manuais", "agro", "md"
        )
        
        # Configurações da API
        self.HOST = "0.0.0.0"
        self.PORT = int(os.getenv("PORT", 8000))
        self.DEBUG = False

# Instância global da configuração
config = Config()


