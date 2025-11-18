import os
import re
from typing import Dict, List
from openai import OpenAI
import asyncio

class ManualProcessor:
    def __init__(self, caminho_manuais: str, openai_api_key: str):
        print(f"🔧 Inicializando ManualProcessor...")
        print(f"📁 Caminho manuais: {caminho_manuais}")
        print(f"🔑 OpenAI key configurada: {bool(openai_api_key)}")
        
        self.caminho_manuais = caminho_manuais
        self.manuais = {}
        self.openai_api_key = openai_api_key
        
        # Configurar cliente OpenAI v1.x
        if self.openai_api_key:
            try:
                self.client = OpenAI(api_key=self.openai_api_key)
                print("✅ Cliente OpenAI v1.x inicializado com sucesso")
                
            except Exception as e:
                print(f"❌ Erro ao inicializar OpenAI: {e}")
                self.client = None
        else:
            print("❌ OpenAI API key não fornecida - usando apenas fallback")
            self.client = None
        
        self._carregar_manuais()
    
    def _carregar_manuais(self):
        """Carrega todos os manuais da pasta especificada"""
        print(f"📚 Carregando manuais de: {self.caminho_manuais}")
        
        if not os.path.exists(self.caminho_manuais):
            print(f"❌ Pasta de manuais não encontrada: {self.caminho_manuais}")
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
                    print(f"  ✅ {nome_manual}")
            except Exception as e:
                print(f"  ❌ Erro ao carregar {arquivo}: {e}")
        
        print(f"🎉 Total de {len(self.manuais)} manuais carregados com sucesso!")
    
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
        """Processa a pergunta usando OpenAI v1.x"""
        print("🚀 Processando com OpenAI v1.x...")
        
        # Preparar contexto dos manuais
        contexto_manuais = ""
        for nome, conteudo in manuais_relevantes.items():
            contexto_manuais += f"\n\n=== {nome} ===\n{conteudo[:2000]}..."
        
        # Prompt otimizado
        prompt = f"""Você é um especialista em máquinas agrícolas John Deere. 

PERGUNTA: {pergunta}

MANUAIS DISPONÍVEIS:
{contexto_manuais}

INSTRUÇÕES:
- Responda de forma CONCISA e DIRETA
- Use apenas informações dos manuais fornecidos
- Seja específico sobre o modelo mencionado
- Use emojis para destacar pontos importantes
- Máximo 200 palavras

RESPOSTA:"""

        try:
            # Usar nova sintaxe OpenAI v1.x
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em máquinas agrícolas John Deere."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            resposta = response.choices[0].message.content
            
            return {
                "resposta": resposta,
                "manuais_usados": list(manuais_relevantes.keys()),
                "modelo_usado": "gpt-4o-mini",
                "sucesso": True
            }
            
        except Exception as e:
            print(f"❌ Erro na OpenAI v1.x: {e}")
            raise e
    
    def _processar_offline(self, pergunta: str, manuais_relevantes: Dict[str, str]) -> dict:
        """Fallback: processamento offline simples"""
        print("🔄 Processando offline...")
        
        # Buscar informação específica nos manuais
        resposta_parts = []
        
        for nome_manual, conteudo in manuais_relevantes.items():
            # Buscar seções relevantes
            linhas = conteudo.split('\n')
            secoes_relevantes = []
            
            for i, linha in enumerate(linhas):
                if any(palavra.lower() in linha.lower() for palavra in pergunta.split()):
                    # Incluir contexto (linha anterior e próximas 2)
                    inicio = max(0, i-1)
                    fim = min(len(linhas), i+3)
                    secao = '\n'.join(linhas[inicio:fim])
                    secoes_relevantes.append(secao)
            
            if secoes_relevantes:
                resposta_parts.append(f"## {nome_manual}\n\n" + '\n\n'.join(secoes_relevantes[:2]))
        
        if not resposta_parts:
            resposta_final = "❌ Informação específica não encontrada nos manuais disponíveis."
        else:
            resposta_final = f"📋 **INFORMAÇÕES ENCONTRADAS:**\n\n" + '\n\n'.join(resposta_parts)
        
        return {
            "resposta": resposta_final,
            "manuais_usados": list(manuais_relevantes.keys()),
            "modelo_usado": "busca_offline",
            "sucesso": True
        }
    
    async def processar_pergunta(self, pergunta: str) -> dict:
        """Método principal para processar perguntas"""
        print(f"🤖 Processando pergunta: {pergunta[:50]}...")
        
        # Buscar manuais relevantes
        manuais_relevantes = self._buscar_manuais_relevantes(pergunta)
        print(f"📚 Manuais encontrados: {list(manuais_relevantes.keys())}")
        
        if not manuais_relevantes:
            return {
                "resposta": "❌ Nenhum manual relevante encontrado para sua pergunta.",
                "manuais_usados": [],
                "sucesso": False
            }
        
        # Tentar usar OpenAI primeiro
        if self.client:
            try:
                return await self._processar_com_openai(pergunta, manuais_relevantes)
                
            except Exception as e:
                print(f"❌ Erro na OpenAI: {e}")
                print("🔄 Fallback para busca offline...")
        
        # Fallback: busca offline
        return self._processar_offline(pergunta, manuais_relevantes)
