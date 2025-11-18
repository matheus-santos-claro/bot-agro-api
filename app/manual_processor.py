import os
import re
from typing import List, Dict, Any

class ManualProcessor:
    def __init__(self):
        """Inicializa INSTANTANEAMENTE sem OpenAI"""
        print("🚀 Inicializando Bot Agrícola (modo offline)...")
        
        # Importar config apenas quando necessário
        from .config import config
        self.config = config
        
        self.base_manuais = []
        self.cache_conteudo = {}
        
        # Carregar apenas lista de arquivos (instantâneo)
        self._indexar_arquivos()
        print("✅ Sistema pronto INSTANTANEAMENTE!")
    
    def _indexar_arquivos(self):
        """Indexa arquivos sem carregar conteúdo"""
        print(f"📂 Indexando arquivos de: {self.config.CAMINHO_MANUAIS}")
        
        if not os.path.exists(self.config.CAMINHO_MANUAIS):
            print("⚠️ Pasta não encontrada!")
            return
        
        arquivos = [f for f in os.listdir(self.config.CAMINHO_MANUAIS) if f.endswith(".md")]
        
        for arquivo in arquivos:
            titulo = arquivo.replace(".md", "")
            caminho = os.path.join(self.config.CAMINHO_MANUAIS, arquivo)
            
            self.base_manuais.append({
                "arquivo": caminho,
                "titulo": titulo,
                "palavras_chave": self._extrair_palavras_chave(titulo)
            })
        
        print(f"📋 {len(self.base_manuais)} arquivos indexados!")
    
    def _extrair_palavras_chave(self, titulo: str) -> List[str]:
        """Extrai palavras-chave do título"""
        palavras = re.findall(r'\b\w+\b', titulo.lower())
        return [p for p in palavras if len(p) > 2]
    
    def _carregar_conteudo(self, caminho: str) -> str:
        """Carrega conteúdo de um arquivo"""
        if caminho in self.cache_conteudo:
            return self.cache_conteudo[caminho]
        
        try:
            with open(caminho, encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()
            
            if len(conteudo) > 15000:
                conteudo = conteudo[:15000] + "\n[...conteúdo truncado...]"
            
            self.cache_conteudo[caminho] = conteudo
            return conteudo
            
        except Exception as e:
            print(f"❌ Erro ao carregar {os.path.basename(caminho)}: {e}")
            return ""
    
    def _buscar_por_palavras_chave(self, pergunta: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """Busca manuais usando apenas palavras-chave"""
        if not self.base_manuais:
            return []
        
        print(f"🔍 Buscando por palavras-chave: '{pergunta}'")
        
        palavras_pergunta = re.findall(r'\b\w+\b', pergunta.lower())
        palavras_pergunta = [p for p in palavras_pergunta if len(p) > 2]
        
        scores = []
        for manual in self.base_manuais:
            score = 0
            titulo_lower = manual["titulo"].lower()
            
            for palavra in palavras_pergunta:
                if palavra in titulo_lower:
                    score += 10
                
                for palavra_chave in manual["palavras_chave"]:
                    if palavra in palavra_chave or palavra_chave in palavra:
                        score += 5
            
            if score > 0:
                scores.append((manual, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if not scores:
            for manual in self.base_manuais:
                titulo_lower = manual["titulo"].lower()
                for palavra in palavras_pergunta:
                    if any(palavra in pk for pk in manual["palavras_chave"]):
                        scores.append((manual, 1))
                        break
        
        resultado = [x[0] for x in scores[:top_n]]
        print(f"  ✅ Encontrados {len(resultado)} manuais relevantes")
        
        return resultado
    
    def _gerar_resposta_com_openai(self, pergunta: str, contexto: str) -> str:
        """Tenta usar OpenAI com múltiplas estratégias"""
        
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
"""

        # ESTRATÉGIA 1: Tentar OpenAI v1.x
        try:
            from openai import OpenAI
            print("🔄 Tentando OpenAI v1.x...")
            
            client = OpenAI(api_key=self.config.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em máquinas agrícolas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )
            
            print("✅ OpenAI v1.x funcionou!")
            return response.choices[0].message.content.strip()
            
        except Exception as e1:
            print(f"❌ OpenAI v1.x falhou: {str(e1)}")
            
            # ESTRATÉGIA 2: Tentar OpenAI v0.x
            try:
                import openai
                print("🔄 Tentando OpenAI v0.x...")
                
                openai.api_key = self.config.OPENAI_API_KEY
                
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você é um especialista em máquinas agrícolas."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=600
                )
                
                print("✅ OpenAI v0.x funcionou!")
                return response.choices[0].message.content.strip()
                
            except Exception as e2:
                print(f"❌ OpenAI v0.x também falhou: {str(e2)}")
                
                # ESTRATÉGIA 3: Usar modelo mais simples
                try:
                    print("🔄 Tentando modelo gpt-3.5-turbo...")
                    
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Você é um especialista em máquinas agrícolas."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                        max_tokens=600
                    )
                    
                    print("✅ GPT-3.5-turbo funcionou!")
                    return response.choices[0].message.content.strip()
                    
                except Exception as e3:
                    print(f"❌ Todas as estratégias falharam. Último erro: {str(e3)}")
                    raise Exception(f"OpenAI completamente inacessível: {str(e3)}")
    
    def _gerar_resposta_offline_inteligente(self, pergunta: str, contexto: str, manuais_usados: List[str]) -> str:
        """Gera resposta estruturada e inteligente SEM IA"""
        
        # Analisar a pergunta para entender o que o usuário quer
        pergunta_lower = pergunta.lower()
        
        # Identificar tipo de pergunta
        if any(palavra in pergunta_lower for palavra in ['manutenção', 'manter', 'cuidar', 'preventiva']):
            tipo_pergunta = "MANUTENÇÃO"
        elif any(palavra in pergunta_lower for palavra in ['problema', 'defeito', 'erro', 'falha', 'não funciona']):
            tipo_pergunta = "PROBLEMA"
        elif any(palavra in pergunta_lower for palavra in ['como', 'usar', 'operar', 'funciona']):
            tipo_pergunta = "OPERAÇÃO"
        elif any(palavra in pergunta_lower for palavra in ['especificação', 'dados', 'características']):
            tipo_pergunta = "ESPECIFICAÇÕES"
        else:
            tipo_pergunta = "GERAL"
        
        # Processar contexto para extrair informações relevantes
        secoes = contexto.split("###")
        
        resposta = f"📋 **RESPOSTA TÉCNICA - {tipo_pergunta}**\n\n"
        resposta += f"**Pergunta:** {pergunta}\n\n"
        
        # Processar cada manual
        for i, secao in enumerate(secoes[1:], 1):
            if secao.strip():
                linhas = secao.strip().split('\n')
                titulo_manual = linhas[0].strip()
                
                resposta += f"## {i}. {titulo_manual}\n\n"
                
                # Extrair informações baseadas no tipo de pergunta
                info_relevante = []
                
                for linha in linhas[1:]:
                    linha = linha.strip()
                    if not linha or linha.startswith('#'):
                        continue
                    
                    linha_lower = linha.lower()
                    
                    # Filtrar por tipo de pergunta
                    if tipo_pergunta == "MANUTENÇÃO" and any(palavra in linha_lower for palavra in ['manutenção', 'troca', 'filtro', 'óleo', 'lubrificação', 'limpeza']):
                        info_relevante.append(f"🔧 {linha}")
                    elif tipo_pergunta == "PROBLEMA" and any(palavra in linha_lower for palavra in ['problema', 'erro', 'falha', 'defeito', 'solução']):
                        info_relevante.append(f"⚠️ {linha}")
                    elif tipo_pergunta == "OPERAÇÃO" and any(palavra in linha_lower for palavra in ['operação', 'usar', 'funciona', 'comando', 'controle']):
                        info_relevante.append(f"⚙️ {linha}")
                    elif tipo_pergunta == "ESPECIFICAÇÕES" and any(palavra in linha_lower for palavra in ['potência', 'peso', 'dimensões', 'capacidade', 'motor']):
                        info_relevante.append(f"📊 {linha}")
                    elif any(palavra in pergunta_lower for palavra in linha_lower.split() if len(palavra) > 3):
                        info_relevante.append(f"📌 {linha}")
                
                # Se não encontrou nada específico, pegar informações gerais
                if not info_relevante:
                    for linha in linhas[1:4]:
                        linha = linha.strip()
                        if linha and not linha.startswith('#') and len(linha) > 20:
                            info_relevante.append(f"📝 {linha}")
                
                # Adicionar até 4 informações por manual
                for info in info_relevante[:4]:
                    resposta += f"{info}\n"
                
                resposta += "\n"
        
        # Adicionar recomendações baseadas no tipo
        resposta += "\n## 💡 Recomendações:\n\n"
        
        if tipo_pergunta == "MANUTENÇÃO":
            resposta += "- Siga sempre o cronograma de manutenção preventiva\n"
            resposta += "- Use apenas peças e fluidos originais\n"
            resposta += "- Mantenha registro das manutenções realizadas\n"
        elif tipo_pergunta == "PROBLEMA":
            resposta += "- Identifique primeiro a causa raiz do problema\n"
            resposta += "- Consulte um técnico autorizado se necessário\n"
            resposta += "- Não force operações se houver resistência\n"
        elif tipo_pergunta == "OPERAÇÃO":
            resposta += "- Leia completamente o manual antes de operar\n"
            resposta += "- Respeite os limites de capacidade da máquina\n"
            resposta += "- Use equipamentos de proteção individual\n"
        
        resposta += f"\n💡 **Manuais consultados:** {', '.join(manuais_usados)}\n"
        resposta += "⚙️ **Modo:** Resposta técnica estruturada\n"
        resposta += "📞 **Para suporte especializado:** Consulte a assistência técnica autorizada"
        
        return resposta
    
    def responder_pergunta(self, pergunta: str) -> Dict[str, Any]:
        """Responde pergunta tentando IA primeiro, fallback inteligente depois"""
        try:
            if not self.base_manuais:
                return {
                    "resposta": "❌ Nenhum manual foi indexado.",
                    "manuais_usados": [],
                    "sucesso": False
                }
            
            # Buscar manuais relevantes
            manuais_relevantes = self._buscar_por_palavras_chave(pergunta, top_n=3)
            
            if not manuais_relevantes:
                return {
                    "resposta": f"❌ Não encontrei manuais relevantes para '{pergunta}'. Tente usar palavras-chave como: marca, modelo, ou tipo de problema.",
                    "manuais_usados": [],
                    "sucesso": False
                }
            
            # Carregar conteúdo
            print("📖 Carregando conteúdo dos manuais...")
            contexto = ""
            manuais_usados = []
            
            for manual in manuais_relevantes:
                print(f"  📄 {manual['titulo']}")
                conteudo = self._carregar_conteudo(manual["arquivo"])
                
                if conteudo:
                    contexto += f"\n\n### {manual['titulo']} ###\n{conteudo[:4000]}"
                    manuais_usados.append(manual['titulo'])
            
            if not contexto:
                return {
                    "resposta": "❌ Erro ao carregar conteúdo dos manuais.",
                    "manuais_usados": [],
                    "sucesso": False
                }
            
            # Tentar IA primeiro
            try:
                print("🧠 Tentando gerar resposta com IA...")
                resposta_texto = self._gerar_resposta_com_openai(pergunta, contexto)
                print("✅ Resposta gerada com IA!")
                
            except Exception as e:
                print(f"❌ IA falhou: {str(e)}")
                print("🔄 Gerando resposta offline inteligente...")
                resposta_texto = self._gerar_resposta_offline_inteligente(pergunta, contexto, manuais_usados)
                print("✅ Resposta offline gerada!")
            
            return {
                "resposta": resposta_texto,
                "manuais_usados": manuais_usados,
                "sucesso": True
            }
            
        except Exception as e:
            return {
                "resposta": f"❌ Erro interno: {str(e)}",
                "manuais_usados": [],
                "sucesso": False
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Status do sistema"""
        return {
            "total_manuais": len(self.base_manuais),
            "manuais_indexados": [m["titulo"] for m in self.base_manuais[:10]],
            "cache_size": len(self.cache_conteudo),
            "caminho_manuais": self.config.CAMINHO_MANUAIS,
            "status": "OK" if self.base_manuais else "SEM_MANUAIS",
            "modo": "HYBRID_SMART"
        }
