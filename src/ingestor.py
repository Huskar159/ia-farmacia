"""
Módulo responsável por extrair e indexar insumos da Farmacopeia Brasileira.
Cria um banco vetorial local para busca semântica.
VERSÃO 2.0 - Extração correta de monografias do Volume 2
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm

load_dotenv()


class FarmacopeiaIngestor:
    """Extrai e indexa monografias da Farmacopeia Brasileira."""
    
    def __init__(self, pdf_paths: List[str], vectorstore_path: str):
        self.pdf_paths = pdf_paths if isinstance(pdf_paths, list) else [pdf_paths]
        self.vectorstore_path = vectorstore_path
        
        # Embeddings locais
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Configuracoes de chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", 1000)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 200)),
            length_function=len,
        )
        
        # Padrao para identificar codigo de monografia (IF###-## ou EF###-##)
        self.codigo_pattern = re.compile(r'(IF|EF)\d{3}-\d{2}')
    
    def is_volume_monografias(self, pdf_path: str) -> bool:
        """Verifica se o PDF e o volume de monografias (Volume 2)."""
        with pdfplumber.open(pdf_path) as pdf:
            # Verificar primeiras paginas
            for i in range(min(5, len(pdf.pages))):
                text = pdf.pages[i].extract_text()
                if text and "Monografias" in text:
                    return True
                if text and "Insumos Farmacêuticos" in text:
                    return True
        return False
    
    def extrair_monografias_volume2(self, pdf_path: str) -> List[Dict]:
        """Extrai monografias do Volume 2 da Farmacopeia."""
        monografias = []
        monografia_atual = None
        
        print(f"Lendo PDF: {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for i in tqdm(range(total_pages), desc=f"Extraindo {os.path.basename(pdf_path)}"):
                text = pdf.pages[i].extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                if len(lines) < 2:
                    continue
                
                primeira_linha = lines[0].strip()
                segunda_linha = lines[1].strip() if len(lines) > 1 else ""
                
                # Verificar se e inicio de nova monografia
                # Padrao: "Farmacopeia Brasileira, 6a edicao IF###-##" ou "EF###-##"
                codigo_match = self.codigo_pattern.search(primeira_linha)
                
                if codigo_match:
                    codigo = codigo_match.group(0)
                    
                    # Verificar se a segunda linha e um nome de medicamento (maiusculas)
                    if self._is_nome_medicamento(segunda_linha):
                        # Salvar monografia anterior se existir
                        if monografia_atual and monografia_atual.get('nome'):
                            monografias.append(monografia_atual)
                        
                        # Iniciar nova monografia
                        monografia_atual = {
                            'codigo': codigo,
                            'nome': segunda_linha,
                            'conteudo': text,
                            'classe_terapeutica': '',
                            'tipo': 'Insumo Farmaceutico' if codigo.startswith('IF') else 'Especialidade Farmaceutica',
                            'fonte': os.path.basename(pdf_path)
                        }
                    elif monografia_atual:
                        # Continuar acumulando conteudo da monografia atual
                        monografia_atual['conteudo'] += '\n\n' + text
                else:
                    if monografia_atual:
                        monografia_atual['conteudo'] += '\n\n' + text
                
                # Extrair classe terapeutica se presente
                if monografia_atual:
                    classe = self._extrair_classe_terapeutica(text)
                    if classe and not monografia_atual['classe_terapeutica']:
                        monografia_atual['classe_terapeutica'] = classe
            
            # Adicionar ultima monografia
            if monografia_atual and monografia_atual.get('nome'):
                monografias.append(monografia_atual)
        
        return monografias
    
    def _is_nome_medicamento(self, texto: str) -> bool:
        """Verifica se o texto e um nome de medicamento valido."""
        if not texto or len(texto) < 3:
            return False
        
        # Deve ser maiusculas (nomes de medicamentos sao em maiusculas)
        if not re.match(r'^[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s\-\,0-9]+$', texto):
            return False
        
        # Nao deve ser cabecalho ou secao
        termos_invalidos = [
            'FARMACOPEIA', 'BRASILEIRA', 'DESCRICAO', 'IDENTIFICACAO',
            'ENSAIOS', 'DOSEAMENTO', 'EMBALAGEM', 'ROTULAGEM', 'CLASSE',
            'PROCEDIMENTO', 'SOLUCAO', 'TESTES', 'CARACTERISTICAS',
            'ARMAZENAMENTO', 'SEGURANCA', 'BIOLOGICA', 'PUREZA',
            'CONTAGEM', 'PESQUISA', 'MICRO-ORGANISMOS', 'OBSERVAR',
            'LEGISLACAO', 'VIGENTE', 'RECIPIENTES', 'CATEGORIA'
        ]
        texto_upper = texto.upper()
        
        # Verificar se o texto inteiro é um termo inválido
        for termo in termos_invalidos:
            if texto_upper.strip() == termo:
                return False
        
        # Verificar se começa com termos inválidos conhecidos
        if texto_upper.startswith('EMBALAGEM') or texto_upper.startswith('ARMAZENAMENTO'):
            return False
        if texto_upper.startswith('CLASSE TERAPÊUTICA') or texto_upper.startswith('CLASSE TERAPEUTICA'):
            return False
        if texto_upper.startswith('ROTULAGEM') or texto_upper.startswith('DOSEAMENTO'):
            return False
        if texto_upper.startswith('TESTES DE') or texto_upper.startswith('ENSAIOS DE'):
            return False
        
        # Deve ter pelo menos uma palavra de 4+ caracteres
        palavras = texto.split()
        if not any(len(p) >= 4 for p in palavras):
            return False
        
        return True
    
    def _extrair_classe_terapeutica(self, texto: str) -> Optional[str]:
        """Extrai a classe terapeutica do texto."""
        if 'CLASSE TERAPÊUTICA' not in texto:
            return None
        
        lines = texto.split('\n')
        for i, line in enumerate(lines):
            if 'CLASSE TERAPÊUTICA' in line:
                # Pegar proximas linhas ate encontrar outra secao
                classe_parts = []
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not any(sec in next_line for sec in ['EMBALAGEM', 'ARMAZENAMENTO', 'ROTULAGEM', 'Farmacopeia']):
                        classe_parts.append(next_line)
                    else:
                        break
                
                if classe_parts:
                    return ' '.join(classe_parts)
        
        return None
    
    def process_all_pdfs(self) -> List[Dict]:
        """Processa cada PDF individualmente."""
        todas_monografias = []
        
        for pdf_path in self.pdf_paths:
            nome_arquivo = os.path.basename(pdf_path)
            print(f"\n{'='*60}")
            print(f"Processando: {nome_arquivo}")
            print(f"{'='*60}")
            
            # Verificar se e volume de monografias
            if self.is_volume_monografias(pdf_path):
                print("Identificado como Volume de Monografias")
                monografias = self.extrair_monografias_volume2(pdf_path)
            else:
                print("Volume de metodos gerais - ignorando para extracao de monografias")
                continue
            
            print(f"{len(monografias)} monografias identificadas")
            
            if monografias:
                print(f"\nExemplos de nomes extraidos:")
                for m in monografias[:10]:
                    classe = m.get('classe_terapeutica', '')[:50]
                    print(f"  - {m['nome']}")
                    if classe:
                        print(f"    Classe: {classe}...")
            
            todas_monografias.extend(monografias)
        
        return todas_monografias
    
    def enriquecer_metadados(self, monografias: List[Dict]) -> List[Dict]:
        """Adiciona metadados extras baseados na classe terapeutica."""
        # Mapeamento de classes para sintomas/indicacoes (EXPANDIDO)
        classe_para_indicacoes = {
            # Analgésicos
            'analgésico': ['dor', 'dor de cabeca', 'cefaleia', 'enxaqueca', 'dor muscular'],
            'antipirético': ['febre', 'temperatura alta'],
            'opioide': ['dor intensa', 'dor cronica'],
            'agonista': ['dor', 'dor intensa'],
            
            # Anti-inflamatórios
            'anti-inflamatório': ['inflamacao', 'inchaco', 'artrite', 'dor muscular', 'reumatismo'],
            'antirreumático': ['reumatismo', 'artrite', 'dor articular'],
            'corticosteroide': ['inflamacao', 'alergia', 'dermatite', 'eczema'],
            
            # Antibióticos/Antimicrobianos
            'antibacteriano': ['infeccao', 'bacteria', 'infeccao bacteriana'],
            'antibiótico': ['infeccao', 'bacteria', 'infeccao bacteriana'],
            'antimicrobiano': ['infeccao', 'bacteria'],
            'tuberculostático': ['tuberculose'],
            
            # Antifúngicos
            'antifúngico': ['fungo', 'micose', 'candidiase', 'frieira'],
            
            # Antivirais
            'antiviral': ['virus', 'herpes', 'gripe', 'infeccao viral'],
            'antirretroviral': ['hiv', 'aids'],
            
            # Anti-helmínticos/Antiparasitários
            'anti-helmíntico': ['verme', 'parasita', 'lombriga', 'oxiurose'],
            'antiparasitário': ['verme', 'parasita', 'sarna'],
            'escabicida': ['sarna', 'escabiose'],
            
            # Respiratório
            'broncodilatador': ['asma', 'bronquite', 'falta de ar', 'dispneia', 'chiado no peito'],
            'antiasmático': ['asma', 'bronquite', 'falta de ar', 'dispneia'],
            'adrenérgico': ['asma', 'bronquite', 'congestao nasal'],
            'mucolítico': ['tosse', 'catarro', 'secrecao', 'expectoracao'],
            'expectorante': ['tosse', 'catarro', 'secrecao'],
            'descongestionante': ['congestao nasal', 'nariz entupido', 'sinusite'],
            
            # Cardiovascular
            'anti-hipertensivo': ['pressao alta', 'hipertensao'],
            'antiarrítmico': ['arritmia', 'palpitacao', 'taquicardia'],
            'antianginoso': ['angina', 'dor no peito'],
            'vasodilatador': ['pressao alta', 'hipertensao', 'circulacao'],
            'diurético': ['inchaco', 'retencao de liquido', 'hipertensao', 'edema'],
            'cardiotônico': ['insuficiencia cardiaca'],
            
            # Sistema Nervoso
            'ansiolítico': ['ansiedade', 'insonia', 'nervosismo'],
            'benzodiazepínico': ['ansiedade', 'insonia', 'nervosismo', 'convulsao'],
            'sedativo': ['insonia', 'ansiedade', 'agitacao'],
            'hipnótico': ['insonia', 'dificuldade para dormir'],
            'anticonvulsivante': ['convulsao', 'epilepsia'],
            'antidepressivo': ['depressao', 'ansiedade', 'tristeza'],
            'antipsicótico': ['psicose', 'esquizofrenia'],
            'neuroléptico': ['psicose', 'agitacao'],
            'antiparkinsoniano': ['parkinson', 'tremor'],
            'relaxante muscular': ['contratura', 'espasmo muscular', 'tensao muscular'],
            
            # Gastrointestinal
            'antiácido': ['azia', 'gastrite', 'refluxo', 'queimacao'],
            'antissecretor': ['ulcera', 'gastrite', 'refluxo'],
            'antiemético': ['nausea', 'vomito', 'enjoo'],
            'laxante': ['constipacao', 'intestino preso', 'prisao de ventre'],
            'antiespasmódico': ['colica', 'espasmo abdominal', 'dor abdominal'],
            'colagogo': ['digestao', 'bile'],
            
            # Diabetes
            'hipoglicemiante': ['diabetes', 'glicose alta', 'acucar no sangue'],
            'antidiabético': ['diabetes', 'glicose alta'],
            
            # Alergias
            'anti-histamínico': ['alergia', 'coriza', 'espirro', 'urticaria', 'coceira'],
            'antialérgico': ['alergia', 'rinite', 'urticaria'],
            'antipruriginoso': ['coceira', 'prurido'],
            
            # Vitaminas e Suplementos
            'vitamina': ['deficiencia vitaminica', 'suplementacao', 'fraqueza'],
            'suplemento': ['deficiencia', 'fraqueza'],
            'hematopoiético': ['anemia'],
            'antianêmico': ['anemia', 'fraqueza'],
            
            # Dermatológico
            'protetor': ['pele ressecada', 'protecao da pele'],
            'ceratolítico': ['calosidade', 'verruga'],
            'queratolítico': ['caspa', 'psoríase'],
            'despigmentante': ['manchas na pele'],
            'adstringente': ['poros dilatados', 'oleosidade'],
            'antisséptico': ['desinfeccao', 'feridas', 'infeccao de pele'],
            
            # Outros medicamentos
            'anestésico': ['anestesia', 'dor local'],
            'anticoagulante': ['trombose', 'coagulo'],
            'hormônio': ['reposicao hormonal'],
            'contraceptivo': ['anticoncepcional', 'prevencao de gravidez'],
            'imunossupressor': ['transplante', 'doenca autoimune'],
            
            # Classes faltantes - Cobertura 100%
            'acidificante': ['acidez urinaria'],
            'adjuvante': ['dialise', 'excipiente'],
            'adoçante': ['adocante', 'edulcorante'],
            'antigotoso': ['gota', 'acido urico'],
            'antitireoidiano': ['hipertireoidismo', 'tireoide'],
            'diagnóstico': ['exame', 'diagnostico'],
            'dopaminérgico': ['parkinson'],
            'alcalinizante': ['acidez', 'alcalinizar'],
            'aminoácido': ['aminoacido', 'proteina'],
            'anti-hemorrágico': ['sangramento', 'hemorragia'],
            'antiandrogênico': ['alopecia', 'queda de cabelo'],
            'antichagásico': ['chagas', 'doenca de chagas'],
            'anticolinérgico': ['espasmo', 'secrecao'],
            'antiglaucomatoso': ['glaucoma', 'pressao ocular'],
            'antilipêmico': ['colesterol', 'triglicerides'],
            'hipolipemiante': ['colesterol alto', 'triglicerides alto'],
            'antimalárico': ['malaria'],
            'antineoplásico': ['cancer', 'tumor'],
            'quimioterápico': ['cancer', 'quimioterapia'],
            'antitranspirante': ['suor', 'transpiracao'],
            'catártico': ['constipacao', 'purgante'],
            'colinérgico': ['bexiga', 'retencao urinaria'],
            'estimulante': ['fadiga', 'cansaco', 'sonolencia'],
            'estrogênio': ['menopausa', 'reposicao hormonal feminina'],
            'progestágeno': ['ciclo menstrual', 'hormonio feminino'],
            'progestagênio': ['ciclo menstrual', 'hormonio feminino'],
            'hansenostático': ['hanseniase', 'lepra'],
            'inibidor': ['inibidor enzimatico'],
            'lipotrópico': ['figado', 'gordura hepatica'],
            'profilático': ['prevencao', 'carie'],
            'repositor': ['reposicao eletrolitica', 'desidratacao'],
            'simpatomimético': ['hipotensao', 'choque'],
            'vasoconstritor': ['sangramento nasal', 'hemorragia'],
            'vitamínico': ['deficiencia vitaminica', 'suplementacao'],
        }
        
        for mono in tqdm(monografias, desc="Processando"):
            classe = mono.get('classe_terapeutica', '').lower()
            indicacoes = []
            
            for classe_key, sintomas in classe_para_indicacoes.items():
                if classe_key in classe:
                    indicacoes.extend(sintomas)
            
            mono['indicacoes'] = list(set(indicacoes))
            
            # Categorias baseadas no tipo
            categorias = []
            if mono.get('tipo') == 'Especialidade Farmaceutica':
                nome_lower = mono['nome'].lower()
                if 'comprimido' in nome_lower:
                    categorias.append('comprimido')
                elif 'capsula' in nome_lower:
                    categorias.append('capsula')
                elif 'solucao' in nome_lower:
                    categorias.append('solucao')
                elif 'suspensao' in nome_lower:
                    categorias.append('suspensao')
                elif 'creme' in nome_lower:
                    categorias.append('uso topico')
            
            mono['categorias'] = categorias
        
        return monografias
    
    def criar_chunks(self, monografias: List[Dict]) -> List[Dict]:
        """Divide monografias em chunks para indexacao."""
        all_chunks = []
        
        for mono in monografias:
            texto = f"""
MEDICAMENTO: {mono['nome']}
CODIGO: {mono['codigo']}
TIPO: {mono['tipo']}
CLASSE TERAPEUTICA: {mono.get('classe_terapeutica', 'Nao especificada')}
INDICACOES: {', '.join(mono.get('indicacoes', []))}

{mono['conteudo']}
"""
            chunks = self.text_splitter.split_text(texto)
            
            for chunk in chunks:
                all_chunks.append({
                    'content': chunk,
                    'metadata': {
                        'nome': mono['nome'],
                        'codigo': mono['codigo'],
                        'tipo': mono['tipo'],
                        'classe_terapeutica': mono.get('classe_terapeutica', ''),
                        'indicacoes': mono.get('indicacoes', []),
                        'categorias': mono.get('categorias', []),
                        'fonte': mono['fonte']
                    }
                })
        
        return all_chunks
    
    def criar_vectorstore(self, chunks: List[Dict]):
        """Cria o banco vetorial com os chunks."""
        print("\nCriando banco vetorial...")
        
        texts = [c['content'] for c in chunks]
        metadatas = [c['metadata'] for c in chunks]
        
        # Converter listas para strings nos metadados (Chroma nao suporta listas)
        for m in metadatas:
            m['indicacoes'] = ', '.join(m.get('indicacoes', []))
            m['categorias'] = ', '.join(m.get('categorias', []))
        
        vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            persist_directory=self.vectorstore_path
        )
        
        print(f"Vectorstore criado com {len(texts)} chunks")
        print(f"Salvo em: {self.vectorstore_path}")
        
        return vectorstore
    
    def run(self):
        """Executa o pipeline completo de ingestao."""
        # 1. Extrair monografias
        monografias = self.process_all_pdfs()
        
        if not monografias:
            print("Nenhuma monografia encontrada!")
            return None
        
        # 2. Enriquecer com metadados
        print("\nEnriquecendo metadados...")
        monografias = self.enriquecer_metadados(monografias)
        
        # 3. Salvar backup JSON
        backup_path = "data/monografias_backup.json"
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(monografias, f, ensure_ascii=False, indent=2)
        print(f"\nBackup salvo: {backup_path}")
        
        # 4. Criar chunks
        chunks = self.criar_chunks(monografias)
        
        # 5. Criar vectorstore
        vectorstore = self.criar_vectorstore(chunks)
        
        print(f"\n{'='*60}")
        print("INGESTAO CONCLUIDA COM SUCESSO!")
        print(f"Total de monografias: {len(monografias)}")
        print(f"Total de chunks: {len(chunks)}")
        print(f"{'='*60}")
        
        return vectorstore


def main():
    pdf_paths_str = os.getenv("PDF_PATHS") or os.getenv("PDF_PATH", "")
    
    if not pdf_paths_str:
        raise ValueError("Configure PDF_PATHS no arquivo .env")
    
    pdf_paths = [path.strip() for path in pdf_paths_str.split(",")]
    vectorstore_path = os.getenv("VECTORSTORE_PATH", "data/vectorstore")
    
    print(f"PDFs configurados: {len(pdf_paths)}")
    for path in pdf_paths:
        print(f"  - {path}")
    
    Path(vectorstore_path).parent.mkdir(parents=True, exist_ok=True)
    
    ingestor = FarmacopeiaIngestor(pdf_paths, vectorstore_path)
    ingestor.run()


if __name__ == "__main__":
    main()