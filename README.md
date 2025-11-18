# 🚜 Bot Agrícola API

API inteligente para consulta de manuais de máquinas agrícolas usando IA.

## 🌟 Características

- ✅ **156 manuais** de máquinas agrícolas indexados
- ✅ **Busca inteligente** por palavras-chave
- ✅ **IA híbrida** com múltiplos modelos (GPT-4o-mini, GPT-3.5-turbo)
- ✅ **Fallback offline** inteligente
- ✅ **Cache otimizado** para performance
- ✅ **Deploy-ready** para Render

## 🚀 Deploy no Render

### Configuração Automática:
1. **Build Command:** `pip install -r requirements.txt`
2. **Start Command:** `python -m app.main`
3. **Environment Variable:** `OPENAI_API_KEY=sua_chave_aqui`

### Configuração Manual:
- **Runtime:** Python 3.9+
- **Port:** Automático (variável PORT)
- **Health Check:** `/ping`

## 📊 Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Página inicial |
| `/ping` | GET | Health check |
| `/status` | GET | Status do sistema |
| `/inicializar` | GET | Inicializar processador |
| `/perguntar` | POST | Fazer pergunta |
| `/manuais` | GET | Listar manuais |
| `/docs` | GET | Documentação interativa |

##    Exemplo de Uso

```bash
curl -X POST "https://sua-app.onrender.com/perguntar" \
     -H "Content-Type: application/json" \
     -d '{"pergunta": "Como fazer manutenção do motor John Deere?"}'