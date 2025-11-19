import os
import re
from typing import Dict, List
import openai
import asyncio

class ManualProcessor:
    def __init__(self, caminho_manuais: str, openai_api_key: str):
        print(f"🔧 Inicializando ManualProcessor...")
        print(f"🔑 OpenAI key configurada: {bool(openai_api_key)}")
        
        self.caminho_manuais = caminho_manuais
        self.manuais = {}
        self.openai_api_key = openai_api_key
        
        # Configurar OpenAI v0.28
        if self.openai_api_key:
            try:
                openai.api_key = self.openai_api_key
                print("✅ Cliente OpenAI v0.28 inicializado")
                self.openai_disponivel = True
                
            except Exception as e:
                print(f"❌ Erro OpenAI: {e}")
                self.openai_disponivel = False
        else:
            print("❌ OpenAI key não fornecida")
            self.openai_disponivel = False
        
        self._carregar_manuais()
    
    def _carregar_manuais(self):
        """Carrega todos os manuais da pasta especificada"""
        print(f"📚 Carregando manuais de: {self.caminho_manuais}")
        
        if not os.path.exists(self.caminho_manuais):
            print(f"❌ Pasta não encontrada: {self.caminho_manuais}")
            return
        
        arquivos_md = [f for f in os.listdir(self.caminho_manuais) if f.endswith('.md')]
        print(f"📋 Encontrados {len(arquivos_md)} arquivos .md")
        
        for arquivo in arquivos_md:
            nome_manual = arquivo.replace('.md', '')
            caminho_arquivo = os.path.join(self.caminho_manuais, arquivo)
            
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    self.manuais[nome_manual] = conteudo
            except Exception as e:
                print(f"❌ Erro ao carregar {arquivo}: {e}")
        
        print(f"🎉 {len(self.manuais)} manuais carregados!")
    
    def _buscar_manuais_relevantes(self, pergunta: str) -> Dict[str, str]:
        """Busca manuais relevantes baseado na pergunta"""
        pergunta_lower = pergunta.lower()
        manuais_relevantes = {}
        
        # Palavras-chave para busca
        palavras_chave = re.findall(r'\b\w+\b', pergunta_lower)
        
        for nome_manual, conteudo in self.manuais.items():
            nome_lower = nome_manual.lower()
            conteudo_lower = conteudo.lower()
            
            # Calcular relevância
            score = 0
            
            # Busca no nome do arquivo
            for palavra in palavras_chave:
                if palavra in nome_lower:
                    score += 10
                if palavra in conteudo_lower:
                    score += 1
            
            # Se encontrou alguma relevância, incluir
            if score > 0:
                manuais_relevantes[nome_manual] = conteudo
        
        # Ordenar por relevância e pegar os top 3
        manuais_ordenados = dict(sorted(manuais_relevantes.items(), 
                                      key=lambda x: sum(palavra in x[1].lower() 
                                                       for palavra in palavras_chave), 
                                      reverse=True)[:3])
        
        return manuais_ordenados
    
    async def _processar_com_openai(self, pergunta: str, manuais_relevantes: Dict[str, str]) -> dict:
    """Processa a pergunta usando OpenAI v0.28 com GPT-4o-mini"""
    print("🚀 Processando com IA...")
    
    # Preparar contexto dos manuais (usar mais contexto como no original)
    contexto = ""
    for nome, conteudo in manuais_relevantes.items():
        contexto += f"\n\n=== MANUAL: {nome} ===\n{conteudo[:2000]}"  # Mais contexto
    
    # Prompt original adaptado
    prompt = f"""
Você é um especialista técnico em máquinas agrícolas.
Use apenas o conteúdo dos manuais abaixo para responder à pergunta do usuário.

Instruções:
- Se a pergunta envolver marcas diferentes, peça educadamente para o usuário perguntar uma por vez.
- Se a pergunta não tiver relação com máquinas agrícolas, RESPONDA usando seu conhecimento geral,
  mas explique gentilmente que seu foco é máquinas agrícolas.
- Se a pergunta mencionar várias máquinas da MESMA marca, responda com todas as informações relevantes.
- Mantenha um tom profissional e cordial.
- Cite sempre o nome do manual (APENAS 1 MANUAL) e a seção/subseção usada como base.

---
📘 CONTEXTO:
{contexto}
---
🧭 PERGUNTA:
{pergunta}

RESPOSTA TÉCNICA:"""

    try:
        # Usar ChatCompletion com OpenAI v0.28 (simula chat com completion)
        response = openai.Completion.create(
            model="gpt-4o-mini",  # Usar GPT-4o-mini
            prompt=prompt,
            max_tokens=500,       # Mais tokens para respostas completas
            temperature=0.2,      # Mesma temperatura do original
            stop=None
        )
        
        resposta = response.choices[0].text.strip()
        
        return {
            "resposta": resposta,
            "manuais_usados": list(manuais_relevantes.keys()),
            "modelo_usado": "gpt-4o-mini",
            "sucesso": True
        }
        
    except Exception as e:
        print(f"❌ Erro OpenAI v0.28: {e}")
        raise e
    
    def _processar_offline(self, pergunta: str, manuais_relevantes: Dict[str, str]) -> dict:
        """Fallback: processamento offline"""
        print("🔄 Processando offline...")
        
        # Buscar informação específica
        resposta_parts = []
        
        for nome_manual, conteudo in manuais_relevantes.items():
            linhas = conteudo.split('\n')
            secoes_relevantes = []
            
            for i, linha in enumerate(linhas):
                if any(palavra.lower() in linha.lower() for palavra in pergunta.split()):
                    inicio = max(0, i-1)
                    fim = min(len(linhas), i+2)
                    secao = '\n'.join(linhas[inicio:fim])
                    secoes_relevantes.append(secao)
            
            if secoes_relevantes:
                resposta_parts.append(f"## {nome_manual}\n{secoes_relevantes[0]}")
        
        if not resposta_parts:
            resposta_final = "❌ Informação específica não encontrada nos manuais."
        else:
            resposta_final = f"📋 **INFORMAÇÕES ENCONTRADAS:**\n\n" + '\n\n'.join(resposta_parts[:2])
        
        return {
            "resposta": resposta_final,
            "manuais_usados": list(manuais_relevantes.keys()),
            "modelo_usado": "busca_offline",
            "sucesso": True
        }
    
    async def processar_pergunta(self, pergunta: str) -> dict:
        """Método principal para processar perguntas"""
        print(f"🤖 Processando: {pergunta[:50]}...")
        
        # Buscar manuais relevantes
        manuais_relevantes = self._buscar_manuais_relevantes(pergunta)
        print(f"📚 Manuais encontrados: {list(manuais_relevantes.keys())}")
        
        if not manuais_relevantes:
            return {
                "resposta": "❌ Nenhum manual relevante encontrado.",
                "manuais_usados": [],
                "sucesso": False
            }
        
        # Tentar OpenAI primeiro
        if self.openai_disponivel:
            try:
                return await self._processar_com_openai(pergunta, manuais_relevantes)
                
            except Exception as e:
                print(f"❌ Erro OpenAI: {e}")
                print("🔄 Fallback para offline...")
        
        # Fallback offline
        return self._processar_offline(pergunta, manuais_relevantes)
    
    def get_status(self):
        """Retorna status do processador"""
        return {
            "status": "INICIALIZADO",
            "total_manuais": len(self.manuais),
            "openai_disponivel": self.openai_disponivel,
            "manuais_indexados": list(self.manuais.keys())
        }



