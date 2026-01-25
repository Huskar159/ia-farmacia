"""
Core de Inteligência Artificial - Motor RAG (Retrieval Augmented Generation).
Responsável por buscar insumos relevantes e gerar recomendações.
VERSÃO CORRIGIDA - Validação rigorosa de nomes químicos
"""

import os
import json
from typing import Dict, List
from dotenv import load_dotenv

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


class AssistenteFarmaceutico:
    """Motor de IA para recomendação de fórmulas magistrais."""
    
    def __init__(self, vectorstore_path: str):
        self.vectorstore_path = vectorstore_path
        
        # Carregar vectorstore
        # Forçar CPU para funcionar no Streamlit Cloud (sem GPU)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        self.vectorstore = Chroma(
            persist_directory=vectorstore_path,
            embedding_function=self.embeddings
        )
        
        # Configurar LLM
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        
        if self.provider == "groq":
            # Usar Groq com Llama 3.3 70B
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                temperature=0.1,
                groq_api_key=os.getenv("GROQ_API_KEY"),
            )
        elif self.provider == "gemini":
            self.llm = ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                temperature=0.1,
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                convert_system_message_to_human=True
            )
        else:
            print(f"⚠️ Provider '{self.provider}' não suportado. Usando Groq como fallback.")
            self.provider = "groq"
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                temperature=0.1,
                groq_api_key=os.getenv("GROQ_API_KEY"),
            )
        
        print(f"✅ Assistente inicializado com {self.provider.upper()}")
    
    def expandir_query_inteligente(self, sintomas: str) -> str:
        """
        Usa o LLM para analisar os sintomas e sugerir classes terapêuticas.
        Isso elimina a necessidade de mapeamento manual de termos.
        O LLM deve entender variações de linguagem, erros ortográficos e gírias.
        """
        prompt = f"""Você é um especialista em farmacologia brasileira. Sua tarefa é analisar sintomas 
descritos por pacientes (mesmo com erros ortográficos, gírias ou linguagem informal) e sugerir:

1. Classes terapêuticas apropriadas (ex: analgésico, antipirético, antianginoso, mucolítico)
2. Nomes de PRINCÍPIOS ATIVOS que existem na Farmacopeia Brasileira

IMPORTANTE: Você deve entender o que o paciente quer dizer, mesmo que escreva errado.
Exemplos:
- "dor d cabesa" = dor de cabeça = analgésico
- "pontada no lado esquerdo do peito" = dor no peito/angina = antianginoso
- "to com o bucho zoado" = dor de estômago = antiácido

MEDICAMENTOS DISPONÍVEIS NA FARMACOPEIA BRASILEIRA (use ESTES nomes):
- Dor/Febre: PARACETAMOL, DIPIRONA, ÁCIDO ACETILSALICÍLICO, IBUPROFENO, NAPROXENO
- Coração/Peito: CLORIDRATO DE PROPRANOLOL, CLORIDRATO DE DILTIAZEM, CAPTOPRIL, ATENOLOL
- Tosse/Catarro: ACETILCISTEÍNA, AMINOFILINA, TEOFILINA
- Estômago: BICARBONATO DE SÓDIO, HIDRÓXIDO DE ALUMÍNIO, CARBONATO DE CÁLCIO
- Alergia: LORATADINA, MALEATO DE DEXCLORFENIRAMINA, ACETATO DE HIDROCORTISONA
- Infecção: AMOXICILINA, AZITROMICINA, AMPICILINA
- Diabetes: CLORIDRATO DE METFORMINA, GLIBENCLAMIDA
- Hipertensão: CAPTOPRIL, ATENOLOL, HIDROCLOROTIAZIDA
- Ansiedade: DIAZEPAM, CLONAZEPAM
- Fungos: FLUCONAZOL, NISTATINA, GRISEOFULVINA
- Intestino: SULFATO DE MAGNÉSIO, BROMOPRIDA

SINTOMAS DO PACIENTE: {sintomas}

Responda APENAS com termos separados por espaço (classes + nomes de medicamentos).
Não inclua explicações, apenas os termos.

Sua resposta:"""

        try:
            resposta = self.llm.invoke([HumanMessage(content=prompt)])
            termos_llm = resposta.content.strip()
            
            # Limpar resposta - remover caracteres especiais
            termos_llm = termos_llm.replace('\n', ' ').replace(',', ' ').replace('.', ' ')
            termos_llm = ' '.join(termos_llm.split())  # Normalizar espaços
            
            print(f"🤖 LLM sugeriu: {termos_llm[:80]}...")
            return termos_llm
        except Exception as e:
            print(f"⚠️ Erro na expansão inteligente: {e}")
            return ""
    def expandir_query(self, sintomas: str) -> str:
        """Expande a query adicionando classes terapêuticas relacionadas."""
        sintomas_para_classes = {
            # === TOSSE E SISTEMA RESPIRATÓRIO ===
            'tosse': 'mucolítico expectorante ACETILCISTEÍNA',
            'catarro': 'mucolítico expectorante ACETILCISTEÍNA',
            'secreção': 'mucolítico expectorante ACETILCISTEÍNA',
            'tosse seca': 'antitussígeno',
            'tosse produtiva': 'mucolítico expectorante ACETILCISTEÍNA',
            'tossindo': 'mucolítico expectorante',
            'pigarro': 'mucolítico expectorante',
            'peito carregado': 'mucolítico expectorante',
            'pulmão': 'broncodilatador',
            'respirar': 'broncodilatador',
            'respiração': 'broncodilatador',
            'falta de ar': 'broncodilatador antiasmático AMINOFILINA SALBUTAMOL',
            'dificuldade para respirar': 'broncodilatador antiasmático',
            'chiado': 'broncodilatador antiasmático',
            'asma': 'broncodilatador antiasmático AMINOFILINA SALBUTAMOL',
            'bronquite': 'broncodilatador',
            'nariz entupido': 'descongestionante',
            'nariz': 'descongestionante anti-histamínico',
            'coriza': 'anti-histamínico descongestionante',
            'espirro': 'anti-histamínico',
            'espirrando': 'anti-histamínico',
            'sinusite': 'descongestionante antibiótico',
            'rinite': 'anti-histamínico descongestionante',
            
            # === DOR E FEBRE ===
            'dor de cabeça': 'analgésico antipirético PARACETAMOL DIPIRONA',
            'cabeça': 'analgésico antipirético PARACETAMOL',
            'cefaleia': 'analgésico antipirético',
            'enxaqueca': 'analgésico',
            'febre': 'antipirético analgésico PARACETAMOL DIPIRONA',
            'febril': 'antipirético',
            'temperatura': 'antipirético',
            'corpo quente': 'antipirético',
            'calafrio': 'antipirético analgésico',
            'dor': 'analgésico anti-inflamatório',
            'doendo': 'analgésico anti-inflamatório',
            'doído': 'analgésico',
            'dói': 'analgésico anti-inflamatório',
            'latejando': 'analgésico',
            'dor no corpo': 'analgésico anti-inflamatório',
            'dor muscular': 'analgésico relaxante muscular anti-inflamatório',
            'músculo': 'relaxante muscular anti-inflamatório',
            'contratura': 'relaxante muscular',
            'tensão muscular': 'relaxante muscular',
            'costas': 'analgésico relaxante muscular anti-inflamatório',
            'lombar': 'analgésico anti-inflamatório',
            'coluna': 'analgésico anti-inflamatório',
            
            # === SISTEMA DIGESTIVO ===
            'estômago': 'antiácido antissecretor',
            'estomago': 'antiácido antissecretor',
            'barriga': 'antiespasmódico antiácido',
            'abdome': 'antiespasmódico',
            'abdominal': 'antiespasmódico',
            'azia': 'antiácido BICARBONATO DE SÓDIO CARBONATO DE CÁLCIO',
            'queimação': 'antiácido BICARBONATO DE SÓDIO CARBONATO DE CÁLCIO',
            'refluxo': 'antiácido BICARBONATO DE SÓDIO',
            'gastrite': 'antiácido BICARBONATO DE SÓDIO',
            'úlcera': 'antiácido antissecretor',
            'indigestão': 'antiácido BICARBONATO DE SÓDIO',
            'má digestão': 'antiácido BICARBONATO DE SÓDIO',
            'empachado': 'antiácido BICARBONATO DE SÓDIO',
            'náusea': 'antiemético',
            'nausea': 'antiemético',
            'enjoo': 'antiemético',
            'enjoado': 'antiemético',
            'vômito': 'antiemético',
            'vomito': 'antiemético',
            'vomitando': 'antiemético',
            'diarreia': 'antiespasmódico BROMOPRIDA',
            'diarréia': 'antiespasmódico BROMOPRIDA',
            'intestino': 'antiespasmódico laxante SULFATO DE MAGNÉSIO',
            'intestino preso': 'laxante SULFATO DE MAGNÉSIO SULFATO DE SÓDIO',
            'constipação': 'laxante SULFATO DE MAGNÉSIO',
            'prisão de ventre': 'laxante SULFATO DE MAGNÉSIO SULFATO DE SÓDIO',
            'gases': 'antiespasmódico',
            'cólica': 'antiespasmódico analgésico',
            'colica': 'antiespasmódico analgésico',
            
            # === INFECÇÕES ===
            'infecção': 'antibiótico antibacteriano',
            'infeccao': 'antibiótico antibacteriano',
            'infectado': 'antibiótico',
            'bactéria': 'antibiótico antibacteriano',
            'bacteria': 'antibiótico',
            'pus': 'antibiótico',
            'garganta': 'antibiótico anti-inflamatório analgésico',
            'amigdalite': 'antibiótico anti-inflamatório',
            'faringite': 'antibiótico anti-inflamatório',
            'urinária': 'antibiótico',
            'urina': 'antibiótico',
            'ardência': 'antibiótico',
            
            # === PELE E ALERGIAS ===
            'alergia': 'anti-histamínico antialérgico',
            'alérgico': 'anti-histamínico',
            'alergico': 'anti-histamínico',
            'coceira': 'anti-histamínico antipruriginoso',
            'coçando': 'anti-histamínico',
            'urticária': 'anti-histamínico',
            'vermelhidão': 'anti-histamínico anti-inflamatório',
            'dermatite': 'corticosteroide anti-inflamatório',
            'eczema': 'corticosteroide',
            'pele': 'corticosteroide anti-inflamatório',
            'fungo': 'antifúngico FLUCONAZOL NISTATINA GRISEOFULVINA',
            'micose': 'antifúngico FLUCONAZOL NISTATINA CICLOPIROX',
            'frieira': 'antifúngico NISTATINA CICLOPIROX FLUCONAZOL',
            'herpes': 'antiviral ACICLOVIR',
            'ferida': 'antisséptico cicatrizante',
            
            # === SISTEMA CARDIOVASCULAR ===
            'pressão alta': 'anti-hipertensivo CAPTOPRIL ATENOLOL',
            'pressão': 'anti-hipertensivo',
            'hipertensão': 'anti-hipertensivo diurético',
            'hipertensao': 'anti-hipertensivo',
            'coração': 'anti-hipertensivo antiarrítmico antianginoso CLORIDRATO DE PROPRANOLOL CLORIDRATO DE DILTIAZEM',
            'coracao': 'anti-hipertensivo antianginoso CLORIDRATO DE PROPRANOLOL',
            'palpitação': 'antiarrítmico',
            'taquicardia': 'antiarrítmico',
            
            # Dor no peito - variações
            'dor no peito': 'antianginoso CLORIDRATO DE PROPRANOLOL CLORIDRATO DE DILTIAZEM',
            'pontada no peito': 'antianginoso CLORIDRATO DE PROPRANOLOL CLORIDRATO DE DILTIAZEM',
            'pontada': 'antianginoso analgésico CLORIDRATO DE PROPRANOLOL',
            'lado esquerdo': 'antianginoso CLORIDRATO DE PROPRANOLOL CLORIDRATO DE DILTIAZEM',
            'aperto no peito': 'antianginoso CLORIDRATO DE PROPRANOLOL CLORIDRATO DE DILTIAZEM',
            'angina': 'antianginoso CLORIDRATO DE PROPRANOLOL CLORIDRATO DE DILTIAZEM',
            'peito apertado': 'antianginoso CLORIDRATO DE PROPRANOLOL',
            'peito doendo': 'antianginoso CLORIDRATO DE PROPRANOLOL CLORIDRATO DE DILTIAZEM',
            'inchaço': 'diurético',
            'inchaco': 'diurético',
            'inchado': 'diurético',
            'retenção': 'diurético',
            
            # === SISTEMA NERVOSO ===
            'ansiedade': 'ansiolítico benzodiazepínico DIAZEPAM',
            'ansioso': 'ansiolítico',
            'nervoso': 'ansiolítico',
            'nervosismo': 'ansiolítico',
            'agitado': 'ansiolítico',
            'inquieto': 'ansiolítico',
            'insônia': 'sedativo hipnótico benzodiazepínico',
            'insonia': 'sedativo hipnótico benzodiazepínico',
            'dormir': 'sedativo hipnótico',
            'sono': 'sedativo hipnótico',
            'não consigo dormir': 'sedativo hipnótico',
            'acordando': 'sedativo',
            'depressão': 'antidepressivo',
            'depressao': 'antidepressivo',
            'triste': 'antidepressivo',
            'desânimo': 'antidepressivo',
            'convulsão': 'anticonvulsivante',
            
            # === DIABETES E METABOLISMO ===
            'diabetes': 'hipoglicemiante antidiabético METFORMINA GLIBENCLAMIDA',
            'diabético': 'hipoglicemiante',
            'glicose': 'hipoglicemiante',
            'açúcar': 'hipoglicemiante',
            'colesterol': 'hipolipemiante antilipêmico',
            'triglicérides': 'hipolipemiante',
            
            # === VÍRUS E GRIPE ===
            'virus': 'antiviral',
            'vírus': 'antiviral',
            'gripe': 'antiviral antipirético analgésico',
            'gripado': 'antipirético analgésico',
            'resfriado': 'antipirético analgésico descongestionante',
            'covid': 'antiviral antipirético',
            
            # === INFLAMAÇÃO ===
            'inflamação': 'anti-inflamatório corticosteroide',
            'inflamacao': 'anti-inflamatório',
            'inflamado': 'anti-inflamatório',
            'artrite': 'anti-inflamatório analgésico',
            'reumatismo': 'anti-inflamatório analgésico',
            'artrose': 'anti-inflamatório analgésico',
            
            # === OLHOS ===
            'olho': 'colírio anti-inflamatório',
            'olhos': 'colírio anti-inflamatório',
            'conjuntivite': 'antibiótico anti-inflamatório',
            'visão': 'antiglaucomatoso',
            
            # === OUVIDO ===
            'ouvido': 'antibiótico analgésico',
            'otite': 'antibiótico',
            
            # === VERMES ===
            'verme': 'anti-helmíntico',
            'parasita': 'antiparasitário',
            'lombriga': 'anti-helmíntico',
            
            # === TERMOS INFORMAIS / GÍRIAS BRASILEIRAS ===
            # Dor e mal-estar
            'tô mal': 'analgésico antipirético',
            'to mal': 'analgésico antipirético',
            'mal estar': 'analgésico antipirético',
            'passando mal': 'antiemético analgésico',
            'me sentindo mal': 'analgésico',
            'zoado': 'analgésico antipirético',
            'acabado': 'analgésico antipirético',
            'destruído': 'analgésico',
            'morrendo': 'analgésico antipirético',
            'ruim': 'analgésico',
            'péssimo': 'analgésico antipirético',
            'horrível': 'analgésico',
            
            # Cabeça
            'cabecinha': 'analgésico PARACETAMOL',
            'dor de cachola': 'analgésico PARACETAMOL',
            'cabeça explodindo': 'analgésico PARACETAMOL DIPIRONA',
            'martelando': 'analgésico',
            
            # Estômago/Barriga
            'bucho': 'antiácido antiespasmódico',
            'buchinho': 'antiácido',
            'estomago embrulhado': 'antiemético antiácido',
            'barriga revirada': 'antiemético',
            'barriga doendo': 'antiespasmódico analgésico',
            'tripas': 'antiespasmódico',
            'pança': 'antiácido',
            'caganeira': 'antidiarreico',
            'soltura': 'antidiarreico',
            'travado': 'laxante',
            'entupido': 'laxante',
            
            # Febre/Gripe
            'pegando fogo': 'antipirético',
            'ardendo': 'antipirético',
            'morrendo de febre': 'antipirético PARACETAMOL',
            'queimando': 'antipirético',
            'pegou gripe': 'antipirético analgésico',
            'gripão': 'antipirético analgésico descongestionante',
            'resfriado brabo': 'antipirético analgésico',
            
            # Tosse/Respiração
            'catarro verde': 'mucolítico ACETILCISTEÍNA antibiótico',
            'meleca': 'descongestionante',
            'cuspindo catarro': 'mucolítico expectorante',
            'escarro': 'mucolítico expectorante',
            'garganta trancada': 'anti-inflamatório analgésico',
            'garganta arranhando': 'anti-inflamatório',
            'nariz escorrendo': 'anti-histamínico descongestionante',
            'fungando': 'descongestionante',
            
            # Dor muscular/Corpo
            'travei': 'relaxante muscular',
            'travado': 'relaxante muscular',
            'duro': 'relaxante muscular',
            'moído': 'analgésico anti-inflamatório',
            'corpo todo doendo': 'analgésico anti-inflamatório',
            'não consigo me mexer': 'relaxante muscular analgésico',
            'mau jeito': 'relaxante muscular analgésico',
            
            # Sono/Ansiedade
            'pilhado': 'ansiolítico',
            'elétrico': 'ansiolítico',
            'ligado': 'ansiolítico sedativo',
            'não paro quieto': 'ansiolítico',
            'aperreado': 'ansiolítico',
            'estressado': 'ansiolítico',
            'tenso': 'ansiolítico relaxante muscular',
            'não durmo': 'sedativo hipnótico',
            'insone': 'sedativo hipnótico',
            'virando a noite': 'sedativo hipnótico',
            
            # Pele
            'ardendo a pele': 'anti-inflamatório corticosteroide',
            'vermelho': 'anti-histamínico',
            'pipocando': 'anti-histamínico',
            'bolinhas': 'anti-histamínico antialérgico',
            'manchas': 'anti-histamínico',
            'ferida braba': 'antibiótico antisséptico',
            'infeccionou': 'antibiótico',
            
            # Digestivo informal
            'ânsia': 'antiemético',
            'ancia': 'antiemético',
            'queimando por dentro': 'antiácido',
            'estômago pegando fogo': 'antiácido antissecretor',
            'arrotando': 'antiácido',
            'soluço': 'antiespasmódico',
            
            # Outros informais
            'zureta': 'ansiolítico',
            'pirado': 'ansiolítico antipsicótico',
            'tremendo': 'ansiolítico',
            'coisa ruim': 'analgésico',
            'problema': 'analgésico',
            'me ajuda': 'analgésico',
            'preciso de remédio': 'analgésico',
            
            # === TERMOS FALTANTES (correção teste matador) ===
            # Azia com variações - usando nomes específicos do banco
            'terrível': 'antiácido BICARBONATO DE SÓDIO CARBONATO DE CÁLCIO',
            'depois de comer': 'antiácido BICARBONATO DE SÓDIO CARBONATO DE CÁLCIO',
            'comi': 'antiácido BICARBONATO DE SÓDIO',
            'comida': 'antiácido BICARBONATO DE SÓDIO',
            'alimentação': 'antiácido BICARBONATO DE SÓDIO',
            
            # Glicose/Diabetes variações - usando nomes específicos
            'descontrolada': 'hipoglicemiante CLORIDRATO DE METFORMINA GLIBENCLAMIDA',
            'descontrolado': 'hipoglicemiante CLORIDRATO DE METFORMINA GLIBENCLAMIDA',
            'alto': 'hipoglicemiante CLORIDRATO DE METFORMINA anti-hipertensivo',
            'alta': 'hipoglicemiante CLORIDRATO DE METFORMINA anti-hipertensivo',
            'subiu': 'hipoglicemiante CLORIDRATO DE METFORMINA anti-hipertensivo',
            'açúcar no sangue': 'hipoglicemiante CLORIDRATO DE METFORMINA',
            
            # Diarreia variações - NÃO HÁ ANTIDIARREICO no banco, usar antiespasmódico
            'banheiro': 'antiespasmódico BROMOPRIDA',
            'fezes': 'antiespasmódico laxante',
            'líquido': 'antiespasmódico',
            'solta': 'antiespasmódico BROMOPRIDA',
            'solto': 'antiespasmódico',
            
            # Intestino/Constipação variações - usando SULFATO DE MAGNÉSIO
            'preso': 'laxante SULFATO DE MAGNÉSIO',
            'dias': 'analgésico',
            'há dias': 'analgésico',
            'evacuar': 'laxante SULFATO DE MAGNÉSIO',
            'não consigo evacuar': 'laxante SULFATO DE MAGNÉSIO',
            
            # Asma/Respiração variações - usando nomes específicos
            'chiado no peito': 'broncodilatador AMINOFILINA TEOFILINA SULFATO DE EFEDRINA',
            'peito': 'broncodilatador AMINOFILINA analgésico',
            'pulmões': 'broncodilatador AMINOFILINA TEOFILINA',
            'respiratório': 'broncodilatador AMINOFILINA',
            'cansaço': 'broncodilatador analgésico',
            'cansado': 'analgésico',
            'ofegante': 'broncodilatador AMINOFILINA TEOFILINA',
            
            # Frieira/Pé variações - usando nomes específicos de antifúngicos
            'pé': 'antifúngico FLUCONAZOL NISTATINA GRISEOFULVINA',
            'pés': 'antifúngico FLUCONAZOL NISTATINA',
            'dedos': 'antifúngico FLUCONAZOL NISTATINA CICLOPIROX',
            'entre os dedos': 'antifúngico FLUCONAZOL NISTATINA',
            'unha': 'antifúngico GRISEOFULVINA FLUCONAZOL',
            'unhas': 'antifúngico GRISEOFULVINA FLUCONAZOL',
        }
        
        query_expandida = sintomas
        sintomas_lower = sintomas.lower()
        
        for termo, expansao in sintomas_para_classes.items():
            if termo in sintomas_lower:
                query_expandida += f" {expansao}"
        
        print(f"🔍 Query expandida: {query_expandida[:100]}...")
        return query_expandida
    
    def buscar_insumos_relevantes(self, sintomas: str, top_k: int = 5) -> List[Dict]:
        """Busca semântica no vectorstore pelos insumos mais relevantes."""
        
        # PASSO 1: Expansão INTELIGENTE via LLM
        print(f"\n🔎 Buscando insumos para: {sintomas}")
        termos_llm = self.expandir_query_inteligente(sintomas)
        
        # PASSO 2: Expansão via mapeamento manual (fallback/complemento)
        termos_manual = self.expandir_query(sintomas)
        
        # Combinar ambas as expansões
        query_final = f"{sintomas} {termos_llm} {termos_manual}"
        print(f"🔍 Query combinada: {query_final[:120]}...")
        
        busca_ampliada = top_k * 4  # Aumentar para ter mais candidatos
        
        resultados = self.vectorstore.similarity_search_with_score(
            query_final,
            k=busca_ampliada
        )
        
        insumos_encontrados = []
        nomes_adicionados = set()
        
        termos_irrelevantes = [
            "sumário", "índice", "presidentes", "colaboradores",
            "prefácio", "apresentação", "agradecimentos",
            "classe terapêutica"  # NOVO: Filtrar esse termo também
        ]
        
        for doc, score in resultados:
            nome_insumo = doc.metadata.get("nome", "").lower()
            
            # Filtrar páginas irrelevantes
            if any(termo in nome_insumo for termo in termos_irrelevantes):
                continue
            
            # Filtrar nomes muito curtos
            if len(nome_insumo) < 5:
                continue
            
            # Evitar duplicatas
            if nome_insumo in nomes_adicionados:
                continue
            
            nomes_adicionados.add(nome_insumo)
            
            insumos_encontrados.append({
                "conteudo": doc.page_content,
                "metadata": doc.metadata,
                "relevancia_score": round(1 - score, 2)
            })
            
            if len(insumos_encontrados) >= top_k:
                break
        
        return insumos_encontrados
    
    def criar_prompt_recomendacao(self, sintomas: str, contexto_insumos: List[Dict]) -> str:
        """Cria o prompt rigoroso para o LLM."""
        # Montar contexto com NOME QUÍMICO em destaque
        contexto_formatado = "\n\n".join([
            f"""===== INSUMO {i+1} =====
🔬 NOME QUÍMICO OBRIGATÓRIO: {insumo['metadata'].get('nome', 'NÃO ESPECIFICADO').upper()}

CONTEÚDO DA MONOGRAFIA:
{insumo['conteudo']}

(Relevância: {insumo['relevancia_score']})
{'='*50}"""
            for i, insumo in enumerate(contexto_insumos)
        ])
        
        prompt = f"""Você é um Assistente Farmacêutico Magistral especializado em formulações baseadas na Farmacopeia Brasileira.

**CONTEXTO DOS INSUMOS DISPONÍVEIS:**
{contexto_formatado}

**SINTOMAS RELATADOS PELO PACIENTE:**
{sintomas}

**SUA TAREFA:**
Baseado EXCLUSIVAMENTE nos insumos fornecidos acima, recomende uma formulação magistral apropriada.

**⚠️ REGRAS ABSOLUTAS - NÃO VIOLAR EM HIPÓTESE ALGUMA:**

1. **NOME DO INSUMO - REGRA CRÍTICA #1:**
   - O campo "nome" DEVE ser COPIADO EXATAMENTE de "🔬 NOME QUÍMICO OBRIGATÓRIO:"
   - NUNCA use termos como: "CLASSE TERAPÊUTICA", "Analgésico", "Antipirético"
   - NUNCA use descrições genéricas de categoria farmacológica
   
   ✅ EXEMPLOS CORRETOS:
   - "nome": "PARACETAMOL"
   - "nome": "DIPIRONA MONOIDRATADA"
   - "nome": "IBUPROFENO"
   - "nome": "ÁCIDO ACETILSALICÍLICO"
   
   ❌ EXEMPLOS PROIBIDOS:
   - "nome": "CLASSE TERAPÊUTICA"
   - "nome": "Analgésico, antipirético"
   - "nome": "Anticonvulsivante, hipnótico, sedativo"
   - "nome": "Anti-inflamatório não esteroidal"

2. **VALIDAÇÃO OBRIGATÓRIA:**
   - Antes de gerar a resposta JSON, VERIFIQUE se você está usando o nome químico EXATO
   - Se você não conseguir identificar o nome químico, retorne erro ao invés de usar "CLASSE TERAPÊUTICA"

3. **ADEQUAÇÃO CLÍNICA - IMPORTANTE:**
   - SEMPRE tente encontrar um medicamento adequado na lista fornecida
   - Medicamentos para sintomas RELACIONADOS são aceitáveis (ex: dor no peito → antianginoso, anti-inflamatório, analgésico)
   - SOMENTE retorne erro se NENHUM dos 20 insumos for minimamente adequado
   - Exemplo: "pontada no peito" pode ser tratada com PROPRANOLOL, DILTIAZEM ou ÁCIDO ACETILSALICÍLICO
   - Se houver dúvida, PREFIRA recomendar um medicamento com alertas de segurança
   - APENAS se realmente não houver opção adequada, retorne:
   {{
     "erro": "Medicamento não disponível na Farmacopeia",
     "tipo_erro": "LIMITACAO_FARMACOPEIA",
     "explicacao": "Não foi possível encontrar medicamentos adequados para esses sintomas específicos.",
     "sintomas_informados": "{sintomas}"
   }}

4. Use SOMENTE os insumos do contexto acima

5. Dosagens conservadoras baseadas na Farmacopeia

**FORMATO DE RESPOSTA (JSON):**
```json
{{
  "formula": {{
    "nome_sugerido": "Nome comercial sugestivo",
    "insumos": [
      {{
        "nome": "COPIE_EXATAMENTE_O_NOME_QUIMICO_ACIMA",
        "dose": "500mg",
        "justificativa": "Explicação da escolha"
      }}
    ],
    "forma_farmaceutica": "cápsula|solução|creme",
    "quantidade_total": "30 cápsulas"
  }},
  "posologia": "Instruções de uso",
  "justificativa_tecnica": "Explicação baseada na Farmacopeia",
  "alertas_seguranca": [
    "Contraindicações",
    "Interações importantes"
  ],
  "referencias": [
    "Farmacopeia Brasileira 6ª Ed."
  ]
}}
```

**VERIFICAÇÃO FINAL ANTES DE RESPONDER:**
- ✓ Verifiquei que o campo "nome" contém o nome químico EXATO?
- ✓ Não estou usando "CLASSE TERAPÊUTICA" ou termos genéricos?
- ✓ Copiei o texto EXATAMENTE de "🔬 NOME QUÍMICO OBRIGATÓRIO:"?

Responda APENAS com o JSON, sem texto adicional."""

        return prompt
    
    def validar_nome_quimico(self, nome: str) -> bool:
        """
        Valida se o nome é um nome químico válido (não é descrição genérica).
        """
        nome_upper = nome.upper()
        
        # Lista de termos proibidos
        termos_proibidos = [
            "CLASSE TERAPÊUTICA",
            "ANALGÉSICO",
            "ANTIPIRÉTICO",
            "ANTICONVULSIVANTE",
            "SEDATIVO",
            "HIPNÓTICO",
            "ANTI-INFLAMATÓRIO",
            "ANTIBIÓTICO",
            "ANTIEMÉTICO",
            "CATEGORIA",
            "TERAPÊUTICA",
            "MEDICAMENTO"
        ]
        
        # Se contém qualquer termo proibido, é inválido
        for termo in termos_proibidos:
            if termo in nome_upper:
                return False
        
        # Se tem vírgula, provavelmente é descrição
        if "," in nome:
            return False
        
        # Nome muito curto provavelmente é inválido
        if len(nome) < 5:
            return False
        
        return True
    
    def gerar_recomendacao(self, sintomas: str) -> Dict:
        """Pipeline completo: busca + geração de recomendação."""
        print(f"🔎 Buscando insumos para: {sintomas}")
        
        # 1. Buscar insumos relevantes
        top_k = int(os.getenv("TOP_K_RESULTS", 5))
        insumos = self.buscar_insumos_relevantes(sintomas, top_k=top_k)
        
        if not insumos:
            return {
                "erro": "Não foi possível encontrar medicamentos adequados",
                "tipo_erro": "LIMITACAO_FARMACOPEIA",
                "explicacao": """A Farmacopeia Brasileira 6ª Edição é um documento oficial que contém 
monografias de medicamentos específicos. Nem todos os medicamentos ou classes terapêuticas 
estão disponíveis neste documento.

Para os sintomas informados, não foram encontrados medicamentos adequados na base de dados 
extraída da Farmacopeia Brasileira.""",
                "sugestoes": [
                    "Tente descrever os sintomas de forma diferente",
                    "Consulte um profissional de saúde para orientação adequada",
                    "Verifique se existe outro medicamento similar disponível"
                ],
                "sintomas_informados": sintomas
            }
        
        print(f"✅ {len(insumos)} insumos encontrados")
        print("\n📋 Nomes disponíveis para o LLM:")
        for i, ins in enumerate(insumos, 1):
            print(f"  {i}. {ins['metadata'].get('nome', 'N/A')}")
        
        # 2. Criar prompt
        prompt = self.criar_prompt_recomendacao(sintomas, insumos)
        
        # 3. Chamar LLM
        print(f"\n🤖 Gerando recomendação com {self.provider.upper()}...")
        
        try:
            messages = [
                SystemMessage(content="Você é um assistente farmacêutico preciso. SEMPRE use nomes químicos EXATOS, NUNCA classes terapêuticas genéricas."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            resposta_texto = response.content
            
            # Limpar markdown se presente
            if "```json" in resposta_texto:
                resposta_texto = resposta_texto.split("```json")[1].split("```")[0]
            elif "```" in resposta_texto:
                resposta_texto = resposta_texto.split("```")[1].split("```")[0]
            
            resultado = json.loads(resposta_texto.strip())
            
            # Verificar se LLM retornou erro (medicamento não adequado)
            if "erro" in resultado:
                # LLM indicou que não há medicamento adequado - propagar com tipo correto
                if "tipo_erro" not in resultado:
                    resultado["tipo_erro"] = "LIMITACAO_FARMACOPEIA"
                if "explicacao" not in resultado:
                    resultado["explicacao"] = """A Farmacopeia Brasileira 6ª Edição não contém medicamentos 
específicos para tratar esses sintomas. Isso não significa que não existe tratamento - apenas que 
o medicamento adequado não está catalogado neste documento oficial."""
                resultado["sintomas_informados"] = sintomas
                resultado["sugestoes"] = [
                    "Tente descrever os sintomas de forma diferente",
                    "Consulte um profissional de saúde para orientação adequada",
                    "Verifique se existe outro medicamento similar disponível"
                ]
                print("⚠️ LLM indicou: medicamento não disponível na Farmacopeia")
                return resultado
            
            # VALIDAÇÃO CRÍTICA: Verificar nomes químicos
            if "formula" in resultado and "insumos" in resultado["formula"]:
                insumos_validados = []
                erros_validacao = []
                
                for insumo in resultado["formula"]["insumos"]:
                    nome = insumo.get("nome", "")
                    
                    # Verificar se é nome químico válido
                    if not self.validar_nome_quimico(nome):
                        print(f"❌ NOME INVÁLIDO DETECTADO: {nome}")
                        erros_validacao.append(f"Nome inválido: {nome}")
                        
                        # Tentar corrigir usando os metadados
                        nome_corrigido = None
                        for i in insumos:
                            nome_candidato = i["metadata"].get("nome", "")
                            if self.validar_nome_quimico(nome_candidato):
                                nome_corrigido = nome_candidato
                                break
                        
                        if nome_corrigido:
                            print(f"✅ CORRIGIDO PARA: {nome_corrigido}")
                            insumo["nome"] = nome_corrigido
                            insumo["justificativa"] += f" [Nome corrigido automaticamente: {nome_corrigido}]"
                        else:
                            # Se não conseguir corrigir, retornar erro
                            return {
                                "erro": f"Sistema gerou nome inválido '{nome}' e não foi possível corrigir",
                                "sugestao": "Tente reformular os sintomas ou re-indexar a base de dados",
                                "detalhes_validacao": erros_validacao
                            }
                    
                    insumos_validados.append(insumo)
                
                resultado["formula"]["insumos"] = insumos_validados
                
                if erros_validacao:
                    resultado["avisos_sistema"] = erros_validacao
            
            # Adicionar metadados
            resultado["metadados"] = {
                "modelo": self.provider,
                "insumos_consultados": len(insumos),
                "sintomas_originais": sintomas
            }
            
            # === VALIDAÇÃO DE SEGURANÇA (Medicamentos Controlados) ===
            if "formula" in resultado:
                validacao = self.validar_seguranca(resultado["formula"], sintomas)
                
                if validacao["requer_atencao_especial"]:
                    resultado["alertas_criticos"] = validacao["alertas_criticos"]
                    resultado["medicamentos_controlados"] = validacao["medicamentos_controlados"]
                    print("🚨 ATENÇÃO: Medicamento controlado detectado!")
                    for med in validacao["medicamentos_controlados"]:
                        print(f"   - {med['nome']} (Tarja {med['tarja']})")
                
                # Adicionar alertas de validação aos alertas de segurança existentes
                if validacao["alertas_validacao"]:
                    alertas_existentes = resultado.get("alertas_seguranca", [])
                    resultado["alertas_seguranca"] = alertas_existentes + validacao["alertas_validacao"]
            
            print("✅ Recomendação gerada com sucesso!")
            return resultado
            
        except json.JSONDecodeError as e:
            return {
                "erro": "Falha ao parsear resposta do modelo",
                "detalhes": str(e),
                "resposta_bruta": response.content if 'response' in locals() else None
            }
        
        except Exception as e:
            return {
                "erro": "Erro ao gerar recomendação",
                "detalhes": str(e)
            }
    
    # Lista de medicamentos controlados (Tarja Preta/Vermelha)
    # Estes requerem prescrição especial e atenção redobrada
    MEDICAMENTOS_CONTROLADOS = {
        # === TARJA PRETA (B1 - Psicotrópicos) ===
        "DIAZEPAM": {"tarja": "PRETA", "classe": "Benzodiazepínico", "risco": "Dependência, sedação excessiva"},
        "CLONAZEPAM": {"tarja": "PRETA", "classe": "Benzodiazepínico", "risco": "Dependência, sedação excessiva"},
        "ALPRAZOLAM": {"tarja": "PRETA", "classe": "Benzodiazepínico", "risco": "Dependência, sedação excessiva"},
        "LORAZEPAM": {"tarja": "PRETA", "classe": "Benzodiazepínico", "risco": "Dependência, sedação excessiva"},
        "BROMAZEPAM": {"tarja": "PRETA", "classe": "Benzodiazepínico", "risco": "Dependência, sedação excessiva"},
        "MIDAZOLAM": {"tarja": "PRETA", "classe": "Benzodiazepínico", "risco": "Depressão respiratória"},
        "FENOBARBITAL": {"tarja": "PRETA", "classe": "Barbitúrico", "risco": "Dependência, depressão SNC"},
        "ZOLPIDEM": {"tarja": "PRETA", "classe": "Hipnótico", "risco": "Dependência, comportamento alterado"},
        
        # === TARJA PRETA (Antidepressivos Tricíclicos) ===
        "AMITRIPTILINA": {"tarja": "VERMELHA", "classe": "Antidepressivo Tricíclico", "risco": "Arritmia, overdose letal"},
        "CLORIDRATO DE AMITRIPTILINA": {"tarja": "VERMELHA", "classe": "Antidepressivo Tricíclico", "risco": "Arritmia, overdose letal"},
        "NORTRIPTILINA": {"tarja": "VERMELHA", "classe": "Antidepressivo Tricíclico", "risco": "Arritmia, overdose letal"},
        "IMIPRAMINA": {"tarja": "VERMELHA", "classe": "Antidepressivo Tricíclico", "risco": "Arritmia, overdose letal"},
        "CLOMIPRAMINA": {"tarja": "VERMELHA", "classe": "Antidepressivo Tricíclico", "risco": "Arritmia, overdose letal"},
        
        # === TARJA VERMELHA (Outros Psicotrópicos) ===
        "FLUOXETINA": {"tarja": "VERMELHA", "classe": "Antidepressivo ISRS", "risco": "Síndrome serotoninérgica"},
        "SERTRALINA": {"tarja": "VERMELHA", "classe": "Antidepressivo ISRS", "risco": "Síndrome serotoninérgica"},
        "PAROXETINA": {"tarja": "VERMELHA", "classe": "Antidepressivo ISRS", "risco": "Síndrome de descontinuação"},
        "CITALOPRAM": {"tarja": "VERMELHA", "classe": "Antidepressivo ISRS", "risco": "Prolongamento QT"},
        "ESCITALOPRAM": {"tarja": "VERMELHA", "classe": "Antidepressivo ISRS", "risco": "Prolongamento QT"},
        "VENLAFAXINA": {"tarja": "VERMELHA", "classe": "Antidepressivo IRSN", "risco": "Hipertensão, descontinuação"},
        "DULOXETINA": {"tarja": "VERMELHA", "classe": "Antidepressivo IRSN", "risco": "Hepatotoxicidade"},
        "BUPROPIONA": {"tarja": "VERMELHA", "classe": "Antidepressivo", "risco": "Convulsões em doses altas"},
        
        # === TARJA VERMELHA (Antipsicóticos) ===
        "HALOPERIDOL": {"tarja": "VERMELHA", "classe": "Antipsicótico", "risco": "Síndrome extrapiramidal"},
        "CLORPROMAZINA": {"tarja": "VERMELHA", "classe": "Antipsicótico", "risco": "Sedação, hipotensão"},
        "RISPERIDONA": {"tarja": "VERMELHA", "classe": "Antipsicótico", "risco": "Ganho de peso, diabetes"},
        "QUETIAPINA": {"tarja": "VERMELHA", "classe": "Antipsicótico", "risco": "Sedação, síndrome metabólica"},
        "OLANZAPINA": {"tarja": "VERMELHA", "classe": "Antipsicótico", "risco": "Ganho de peso, diabetes"},
        
        # === TARJA AMARELA (A1 - Entorpecentes/Opioides) ===
        "MORFINA": {"tarja": "AMARELA", "classe": "Opioide", "risco": "Dependência, depressão respiratória"},
        "CODEÍNA": {"tarja": "AMARELA", "classe": "Opioide", "risco": "Dependência, constipação"},
        "TRAMADOL": {"tarja": "VERMELHA", "classe": "Opioide", "risco": "Dependência, convulsões"},
        "METADONA": {"tarja": "AMARELA", "classe": "Opioide", "risco": "Depressão respiratória prolongada"},
        "OXICODONA": {"tarja": "AMARELA", "classe": "Opioide", "risco": "Alta dependência"},
        "FENTANILA": {"tarja": "AMARELA", "classe": "Opioide", "risco": "Depressão respiratória grave"},
        
        # === TARJA VERMELHA (Anticonvulsivantes) ===
        "CARBAMAZEPINA": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Síndrome Stevens-Johnson, agranulocitose"},
        "FENITOÍNA": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Hiperplasia gengival, ataxia"},
        "VALPROATO": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Hepatotoxicidade, teratogenia"},
        "ÁCIDO VALPRÓICO": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Hepatotoxicidade, teratogenia"},
        "LAMOTRIGINA": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Síndrome Stevens-Johnson"},
        "TOPIRAMATO": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Glaucoma, acidose metabólica"},
        "GABAPENTINA": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Sedação, dependência"},
        "PREGABALINA": {"tarja": "VERMELHA", "classe": "Anticonvulsivante", "risco": "Dependência, sedação"},
    }
    
    # Sintomas vagos que NÃO justificam medicamentos controlados
    SINTOMAS_VAGOS = [
        "fraqueza", "cansaço", "cansado", "fraco", "fadigado", "fadiga",
        "mal estar", "indisposição", "indisposto", "sem energia", "desânimo",
        "sono ruim", "dormindo mal", "não durmo bem", "acordo cansado",
        "estresse", "estressado", "nervoso", "ansioso", "preocupado",
        "triste", "desanimado", "sem vontade", "desmotivado"
    ]
    
    def verificar_medicamento_controlado(self, nome_medicamento: str) -> Dict:
        """Verifica se um medicamento é controlado e retorna informações."""
        nome_upper = nome_medicamento.upper().strip()
        
        # Busca exata
        if nome_upper in self.MEDICAMENTOS_CONTROLADOS:
            return {
                "controlado": True,
                **self.MEDICAMENTOS_CONTROLADOS[nome_upper]
            }
        
        # Busca parcial (ex: "CLORIDRATO DE DIAZEPAM" contém "DIAZEPAM")
        for med, info in self.MEDICAMENTOS_CONTROLADOS.items():
            if med in nome_upper or nome_upper in med:
                return {
                    "controlado": True,
                    **info
                }
        
        return {"controlado": False}
    
    def sintoma_eh_vago(self, sintomas: str) -> bool:
        """Verifica se os sintomas são muito vagos para justificar medicamentos controlados."""
        sintomas_lower = sintomas.lower()
        
        # Conta quantos termos vagos aparecem
        termos_vagos_encontrados = sum(1 for termo in self.SINTOMAS_VAGOS if termo in sintomas_lower)
        
        # Se a maioria dos termos são vagos, é um sintoma vago
        palavras_sintoma = len(sintomas_lower.split())
        
        # Se tem mais de 50% de termos vagos ou o sintoma é muito curto
        return termos_vagos_encontrados > 0 and palavras_sintoma < 10
    
    def validar_seguranca(self, formula: Dict, sintomas_originais: str = "") -> Dict:
        """Valida aspectos de segurança da fórmula gerada."""
        alertas = []
        alertas_criticos = []  # Alertas de medicamentos controlados
        medicamentos_controlados_detectados = []
        
        # === VALIDAÇÃO DE MEDICAMENTOS CONTROLADOS ===
        for insumo in formula.get("insumos", []):
            nome = insumo.get("nome", "")
            info_controlado = self.verificar_medicamento_controlado(nome)
            
            if info_controlado["controlado"]:
                medicamentos_controlados_detectados.append({
                    "nome": nome,
                    **info_controlado
                })
                
                alerta_critico = (
                    f"🚨 MEDICAMENTO CONTROLADO: {nome}\n"
                    f"   • Tarja: {info_controlado['tarja']}\n"
                    f"   • Classe: {info_controlado['classe']}\n"
                    f"   • Risco: {info_controlado['risco']}\n"
                    f"   • REQUER: Receita especial + Avaliação médica prévia"
                )
                alertas_criticos.append(alerta_critico)
        
        # Verificar se sintomas vagos + medicamento controlado = ALERTA MÁXIMO
        if medicamentos_controlados_detectados and sintomas_originais:
            if self.sintoma_eh_vago(sintomas_originais):
                alertas_criticos.insert(0, 
                    "⛔ ATENÇÃO CRÍTICA: Medicamento controlado sugerido para sintomas VAGOS!\n"
                    "   A IA pode ter feito uma conexão inadequada.\n"
                    "   RECOMENDAÇÃO: Antes de prescrever, investigue:\n"
                    "   - Exames laboratoriais (hemograma, glicemia, TSH)\n"
                    "   - Histórico do paciente\n"
                    "   - Possíveis causas orgânicas\n"
                    "   Este tipo de sintoma geralmente NÃO requer psicotrópicos."
                )
        
        # === VALIDAÇÕES EXISTENTES ===
        num_insumos = len(formula.get("insumos", []))
        if num_insumos > 5:
            alertas.append("⚠️ Fórmula com muitos insumos (>5). Revisar interações.")
        
        texto_completo = json.dumps(formula, ensure_ascii=False).lower()
        if "contraindicação" not in texto_completo and "contraindicado" not in texto_completo:
            alertas.append("ℹ️ Verifique contraindicações individuais de cada insumo.")
        
        for insumo in formula.get("insumos", []):
            dose = insumo.get("dose", "")
            if not any(unidade in dose.upper() for unidade in ["MG", "G", "ML", "UI"]):
                alertas.append(f"⚠️ Unidade de medida não clara para: {insumo.get('nome')}")
        
        return {
            "aprovado": len(alertas_criticos) == 0 and len(alertas) == 0,
            "alertas_validacao": alertas,
            "alertas_criticos": alertas_criticos,
            "medicamentos_controlados": medicamentos_controlados_detectados,
            "requer_atencao_especial": len(alertas_criticos) > 0
        }


def main():
    """Teste standalone do sistema."""
    vectorstore_path = os.getenv("VECTORSTORE_PATH", "data/vectorstore")
    
    assistente = AssistenteFarmaceutico(vectorstore_path)
    
    # Teste
    resultado = assistente.gerar_recomendacao("febre alta")
    
    print("\n" + "="*60)
    print("RESULTADO DA RECOMENDAÇÃO:")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    print("="*60)


if __name__ == "__main__":
    main()