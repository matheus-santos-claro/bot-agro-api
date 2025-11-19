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
                    # Limitar tamanho como no local
                    if len(conteudo) > 15000:
                        conteudo = conteudo[:15000] + "\n[...conteúdo truncado...]"
                    self.manuais[nome_manual] = conteudo
            except Exception as e:
                print(f"❌ Erro ao carregar {arquivo}: {e}")
        
        print(f"🎉 {len(self.manuais)} manuais carregados!")
    
    def _buscar_manuais_relevantes(self, pergunta: str) -> Dict[str, str]:
        """Busca manuais relevantes - versão melhorada baseada no local"""
        print(f"🔍 Buscando por palavras-chave: '{pergunta}'")
        
        pergunta_lower = pergunta.lower()
        palavras_pergunta = re.findall(r'\b\w+\b', pergunta_lower)
        palavras_pergunta = [p for p in palavras_pergunta if len(p) > 2]
        
        scores = []
        
        for nome_manual, conteudo in self.manuais.items():
            nome_lower = nome_manual.lower()
            conteudo_lower = conteudo.lower()
            
            score = 0
            
            # Busca no nome do arquivo (peso maior)
            for palavra in palavras_pergunta:
                if palavra in nome_lower:
                    score += 10
                
                # Busca no conteúdo (peso menor)
                if palavra in conteudo_lower:
                    score += 1
            
            if score > 0:
                scores.append((nome_manual, conteudo, score))
        
        # Ordenar por relevância
        scores.sort(key=lambda x: x[2], reverse=True)
        
        # Fallback se não encontrou nada
        if not scores:
            print("⚠️ Busca principal falhou, tentando fallback...")
            for nome_manual, conteudo in self.manuais.items():
                nome_lower = nome_manual.lower()
                for palavra in palavras_pergunta:
                    if any(palavra in pk for pk in nome_lower.split('_')):
                        scores.append((nome_manual, conteudo, 1))
                        break
        
        # Pegar top 3
        resultado = {}
        for nome_manual, conteudo, score in scores[:3]:
            resultado[nome_manual] = conteudo
        
        print(f"✅ Encontrados {len(resultado)} manuais relevantes")
        return resultado
    
    async def _processar_com_openai(self, pergunta: str, manuais_relevantes: Dict[str, str]) -> dict:
        """Processa a pergunta usando OpenAI v0.28 - CORRIGIDO"""
        print("🚀 Processando com IA...")
        
        # Preparar contexto (mais contexto como no local)
        contexto = ""
        for nome, conteudo in manuais_relevantes.items():
            contexto += f"\n\n### {nome} ###\n{conteudo[:4000]}"  # Mais contexto
        
        # Prompt melhorado baseado no local
        prompt = f"""Você é um especialista em máquinas agrícolas.

Use as informações dos manuais abaixo para responder à pergunta de forma técnica e precisa.

MANUAIS CONSULTADOS:
{contexto}

PERGUNTA: {pergunta}

Instruções:
- Responda baseado apenas nas informações fornecidas
- Cite o manual usado como fonte
- Seja técnico mas claro
- Se não houver informação suficiente, diga isso
- Mantenha tom profissional e cordial
"""

        try:
            # CORREÇÃO: Usar modelo compatível com v0.28
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # ← Modelo compatível com v0.28
                messages=[
                    {"role": "system", "content": "Você é um especialista em máquinas agrícolas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )
            
            resposta = response.choices[0].message.content.strip()
            
            return {
                "resposta": resposta,
                "manuais_usados": list(manuais_relevantes.keys()),
                "modelo_usado": "gpt-3.5-turbo",
                "sucesso": True
            }
            
        except Exception as e:
            print(f"❌ Erro OpenAI v0.28: {e}")
            raise e
    
    def _processar_offline(self, pergunta: str, manuais_relevantes: Dict[str, str]) -> dict:
        """Fallback offline melhorado - baseado na versão local"""
        print("🔄 Processando offline...")
        
        # Analisar tipo de pergunta
        pergunta_lower = pergunta.lower()
        
        if any(palavra in pergunta_lower for palavra in ['manutenção', 'manter', 'cuidar', 'preventiva']):
            tipo_pergunta = "MANUTENÇÃO"
        elif any(palavra in pergunta_lower for palavra in ['problema', 'defeito', 'erro', 'falha']):
            tipo_pergunta = "PROBLEMA"
        elif any(palavra in pergunta_lower for palavra in ['como', 'usar', 'operar', 'funciona']):
            tipo_pergunta = "OPERAÇÃO"
        elif any(palavra in pergunta_lower for palavra in ['especificação', 'dados', 'características', 'potência', 'capacidade']):
            tipo_pergunta = "ESPECIFICAÇÕES"
        else:
            tipo_pergunta = "GERAL"
        
        resposta = f"📋 **RESPOSTA TÉCNICA - {tipo_pergunta}**\n\n"
        resposta += f"**Pergunta:** {pergunta}\n\n"
        
        # Processar cada manual
        for i, (nome_manual, conteudo) in enumerate(manuais_relevantes.items(), 1):
            resposta += f"## {i}. {nome_manual}\n\n"
            
            linhas = conteudo.split('\n')
            info_relevante = []
            
            for linha in linhas:
                linha = linha.strip()
                if not linha or linha.startswith('#'):
                    continue
                
                linha_lower = linha.lower()
                
                # Filtrar por tipo de pergunta
                if tipo_pergunta == "ESPECIFICAÇÕES" and any(palavra in linha_lower for palavra in ['potência', 'peso', 'dimensões', 'capacidade', 'motor', 'cv', 'hp', 'litros']):
                    info_relevante.append(f"📊 {linha}")
                elif tipo_pergunta == "MANUTENÇÃO" and any(palavra in linha_lower for palavra in ['manutenção', 'troca', 'filtro', 'óleo']):
                    info_relevante.append(f"🔧 {linha}")
                elif any(palavra in pergunta_lower for palavra in linha_lower.split() if len(palavra) > 3):
                    info_relevante.append(f"📌 {linha}")
            
            # Se não encontrou nada específico, pegar informações gerais
            if not info_relevante:
                for linha in linhas[:5]:
                    linha = linha.strip()
                    if linha and not linha.startswith('#') and len(linha) > 20:
                        info_relevante.append(f"📝 {linha}")
            
            # Adicionar até 3 informações por manual
            for info in info_relevante[:3]:
                resposta += f"{info}\n"
            
            resposta += "\n"
        
        # Adicionar fonte
        resposta += f"\n💡 **Manuais consultados:** {', '.join(manuais_relevantes.keys())}\n"
        resposta += "⚙️ **Modo:** Resposta técnica estruturada\n"
        
        return {
            "resposta": resposta,
            "manuais_usados": list(manuais_relevantes.keys()),
            "modelo_usado": "busca_offline_inteligente",
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
                "resposta": f"❌ Não encontrei manuais relevantes para '{pergunta}'. Tente usar palavras-chave como: marca, modelo, ou tipo de problema.",
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
        
        # Fallback offline inteligente
        return self._processar_offline(pergunta, manuais_relevantes)
    
    def get_status(self):
        """Retorna status do processador"""
        return {
            "status": "INICIALIZADO",
            "total_manuais": len(self.manuais),
            "openai_disponivel": self.openai_disponivel,
            "manuais_indexados": list(self.manuais.keys())
        }




