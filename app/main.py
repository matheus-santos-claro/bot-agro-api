from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from .config import config

# Criar API
app = FastAPI(
    title="Bot Agrícola API",
    description="API para consulta de manuais de máquinas agrícolas",
    version="1.0.0"
)

# Variável global para o processador (será criado apenas quando necessário)
processor = None

def get_processor():
    """Cria o processador apenas quando alguém faz uma pergunta"""
    global processor
    if processor is None:
        print("🔄 Criando processador pela primeira vez...")
        from .manual_processor import ManualProcessor
        processor = ManualProcessor()
        print("✅ Processador criado!")
    return processor

# Modelos
class PerguntaRequest(BaseModel):
    pergunta: str

class RespostaResponse(BaseModel):
    resposta: str
    manuais_usados: list
    sucesso: bool

# =====================================================
# ENDPOINTS SIMPLES
# =====================================================

@app.get("/")
async def root():
    """Endpoint raiz - sempre funciona"""
    return {
        "message": "🚜 Bot Agrícola API - Funcionando!",
        "version": "1.0.0",
        "status": "ONLINE",
        "info": "Processador será inicializado na primeira pergunta"
    }

@app.get("/ping")
async def ping():
    """Teste de conectividade"""
    return {"status": "pong", "api": "funcionando"}

@app.get("/status")
async def get_status():
    """Status do sistema"""
    global processor
    
    if processor is None:
        return {
            "status": "AGUARDANDO_PRIMEIRA_PERGUNTA",
            "processador": "NAO_INICIALIZADO",
            "total_manuais": 0,
            "modo": "LAZY_INIT"
        }
    else:
        return processor.get_status()

@app.post("/perguntar", response_model=RespostaResponse)
async def fazer_pergunta(request: PerguntaRequest):
    """Endpoint principal - inicializa processador se necessário"""
    if not request.pergunta or len(request.pergunta.strip()) == 0:
        raise HTTPException(status_code=400, detail="Pergunta não pode estar vazia")
    
    try:
        # Só cria o processador quando alguém faz uma pergunta
        proc = get_processor()
        resultado = proc.responder_pergunta(request.pergunta)
        return RespostaResponse(**resultado)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/manuais")
async def listar_manuais():
    """Lista manuais - inicializa se necessário"""
    try:
        proc = get_processor()
        status = proc.get_status()
        return {
            "total": status["total_manuais"],
            "amostra": status.get("manuais_indexados", [])[:10]
        }
    except Exception as e:
        return {"erro": str(e)}

@app.get("/inicializar")
async def inicializar_manualmente():
    """Endpoint para inicializar o processador manualmente"""
    try:
        proc = get_processor()
        status = proc.get_status()
        return {
            "message": "✅ Processador inicializado com sucesso!",
            "total_manuais": status["total_manuais"],
            "status": status["status"]
        }
    except Exception as e:
        return {"erro": f"Falha na inicialização: {str(e)}"}

# =====================================================
# SERVIDOR
# =====================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando servidor SEM inicialização automática...")
    print("💡 O processador será criado apenas na primeira pergunta")
    print(f"🌐 Servidor rodará em: http://localhost:{config.PORT}")
    
    # CONFIGURAÇÃO PARA RENDER
    uvicorn.run(
        "app.main:app",
        host=config.HOST,      # 0.0.0.0 (essencial)
        port=config.PORT,      # Porta do Render
        reload=False,          # False em produção
        log_level="info"
    )
