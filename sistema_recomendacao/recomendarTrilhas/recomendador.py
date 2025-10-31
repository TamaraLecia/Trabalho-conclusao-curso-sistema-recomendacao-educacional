import os
import numpy as np
import pandas as pd
import nltk

# utilizada na geração do gráficos

# from matplotlib.patches import Rectangle
# # utilizado para ajusta o texto no gráfico de dispersão
# from adjustText import adjust_text

from django.conf import settings
from recomendarTrilhas.models import Trilha, ProgressoCapitulo, Capitulo

# NLTK: garantir recursos
try:
    nltk.data.find('tokenizers/punkt')
except:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except:
    nltk.download('wordnet')

from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from itertools import tee

# Ferramentas de NLP
tokenizer = RegexpTokenizer(r'\w+')
stop_words = set(stopwords.words('portuguese')) | set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# Caminhos
MODEL_PATH = os.path.join(settings.BASE_DIR, 'recomendarTrilhas', 'data', 'modelo_doc2vec.model')
DATA_PATH = os.path.join(settings.BASE_DIR, 'recomendarTrilhas', 'data', 'cursos_programacao.csv')
CORPUS_PATH = os.path.join(settings.BASE_DIR, 'recomendarTrilhas', 'data', 'corpus_termos_tecnicos_programacao.csv')

# Carrega corpus base para treinar Doc2Vec
df_total = pd.read_csv(DATA_PATH, encoding='utf-8')

# Carrega termos técnicos (pesados no preprocess)
df_termos_tecnicos = pd.read_csv(CORPUS_PATH, encoding='utf-8')
termos_tecnicos = {str(t).lower().strip() for t in df_termos_tecnicos['termo'].dropna().unique()}

# Bigrams
def bigrams(tokens):
    a, b = tee(tokens)
    next(b, None)
    return [f"{x}_{y}" for x, y in zip(a, b)]

# Pré-processamento com termos prioritários
def preprocess(text, termos_prioritarios=None):
    tokens = tokenizer.tokenize(str(text).lower())
    termos_prioritarios_set = {tp.lower() for tp in (termos_prioritarios or [])}

    tokens_proc = []
    for t in tokens:
        # mantém termos prioritários sempre
        if t in termos_prioritarios_set:
            tokens_proc.append(t)
            continue

        # aumenta peso de termos técnicos
        if t in termos_tecnicos:
            tokens_proc.extend([t, t, t])
            continue

        # remove stopwords (exceto prioritários) e lematiza
        if t in stop_words:
            continue

        tokens_proc.append(lemmatizer.lemmatize(t))

    # adiciona bigrams
    tokens_proc += bigrams(tokens_proc)
    return tokens_proc

# Treinar modelo Doc2Vec
def treinarModelo():
    df = pd.read_csv(DATA_PATH, encoding='utf-8')
    df['tokens'] = df['Description'].apply(lambda txt: preprocess(txt))
    documents = [TaggedDocument(words=row['tokens'], tags=[row['Title']]) for _, row in df.iterrows()]

    model = Doc2Vec(vector_size=140, window=5, min_count=1, workers=4, epochs=60, dm=0)  # DBOW
    model.build_vocab(documents)
    model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)
    model.save(MODEL_PATH)
    print(f"✅ Modelo Doc2Vec treinado e salvo em: {MODEL_PATH}")

# Carrega ou treina
if not os.path.exists(MODEL_PATH):
    treinarModelo()
model = Doc2Vec.load(MODEL_PATH)

# # Normalização de níveis de conhecimento
# def normalizar_nivel(v):
#     # aceita "baixo/médio/alto" ou números 0-100
#     if isinstance(v, str):
#         s = v.strip().lower()
#         mapa = {"baixo": 0.1, "médio": 0.5, "medio": 0.5, "alto": 0.9}
#         if s in mapa:
#             return mapa[s]
#         # tenta converter porcentagem "70"
#         try:
#             return max(0.0, min(1.0, float(s) / 100.0))
#         except:
#             return 0.5
#     if isinstance(v, (int, float)):
#         # assume 0–100 ou 0–1
#         return v / 100.0 if v > 1 else max(0.0, min(1.0, v))
#     return 0.5

# Função de recomendação
def recomendar_trilha(conteudos_usuario, nivel_conhecimento=None, objetivo="", 
                      n_componentes_pca=20, limiar_similaridade=0.60):
    model = Doc2Vec.load(MODEL_PATH)

    descricao_input = (
        f"Quero estudar as tecnologias: {', '.join(conteudos_usuario)}. "
        f"Meu nível de conhecimento é: {', '.join([f'{c}:{n}' for c, n in (nivel_conhecimento or {}).items()])}. "
        f"Meu objetivo é: {objetivo}. "
        "Busco trilhas que combinem esses conteúdos e me ajudem a alcançar meu objetivo."
    )

    tokens_input = preprocess(descricao_input, termos_prioritarios=conteudos_usuario)
    vetor_usuario = model.infer_vector(tokens_input)

    trilhas_db = Trilha.objects.all()
    print("=== TRILHAS DISPONÍVEIS NO BANCO ===")
    for t in trilhas_db:
        print("-", t.id, t.nome)

    trilhas, vetores_trilhas, tokens_trilhas_cache = [], [], {}

    for trilha in trilhas_db:
        texto_trilha = f"{trilha.nome} {trilha.descricao or ''}"
        tokens_trilha = preprocess(texto_trilha, termos_prioritarios=conteudos_usuario)
        tokens_trilhas_cache[trilha] = set(tokens_trilha)
        vetores_trilhas.append(model.infer_vector(tokens_trilha))
        trilhas.append(trilha)

    if not vetores_trilhas:
        return []
    
    # === PCA + Similaridade ===
    todos_vetores = np.array(vetores_trilhas + [vetor_usuario])

    max_componentes = min(todos_vetores.shape[0], todos_vetores.shape[1])
    n_comp = max(2, min(n_componentes_pca, max_componentes))

    pca = PCA(n_components=n_comp)
    vetores_reduzidos = pca.fit_transform(todos_vetores)
    vet_trilhas_red = vetores_reduzidos[:-1]
    vet_usuario_red = vetores_reduzidos[-1]

    sims = cosine_similarity([vet_usuario_red], vet_trilhas_red)[0]
    resultados = list(zip(trilhas, sims))

    similares = [(t, s) for (t, s) in resultados if s >= limiar_similaridade]
    # if not similares:
    similares = sorted(resultados, key=lambda x: x[1], reverse=True)[:10]
    
    # === Regra de negócio: retorna só UMA trilha ===
    if nivel_conhecimento:
        def normalizar_nivel(v):
            mapa = {"baixo": 0.1, "médio": 0.5, "medio": 0.5, "alto": 0.9}
            if isinstance(v, str) and v.lower() in mapa:
                return mapa[v.lower()]
            try:
                print("entrou a aqui")
                return float(v) / 100.0
            except:
                print("Entrou no 0.5")
                return 0.5

        niveis_norm = {c.lower(): normalizar_nivel(v) for c, v in nivel_conhecimento.items()}
        print("niveis normalizados: ", niveis_norm.get)
        conteudo_menor = min(niveis_norm, key=niveis_norm.get)
        # palavra_chave = conteudo_menor.split()[-1].lower()
        palavra_chave = conteudo_menor.lower()

        print("\n=== DEBUG RERANKING ===")
        print("Conteúdo de menor conhecimento:", conteudo_menor)
        print("Palavra-chave usada para busca:", palavra_chave)

        com_menor = [
            (t, s) for (t, s) in similares
            if palavra_chave in (t.nome.lower() + " " + (t.descricao or "").lower())
        ]

        for t, s in similares:
            texto = (t.nome.lower() + " " + (t.descricao or "").lower())
            print(f"Comparando '{palavra_chave}' com: {texto}")

        if com_menor:
            # 🔑 pega só a trilha mais similar do menor conhecimento
            trilha_escolhida = max(com_menor, key=lambda x: x[1])[0]
            print("Trilha escolhida (menor conhecimento):", trilha_escolhida.nome)
            # return [trilha_escolhida]
        else:
            print("⚠️ Nenhuma trilha encontrada para o menor conhecimento, usando fallback.")

    # fallback: retorna só a trilha mais similar de todas
    trilha_escolhida = max(similares, key=lambda x: x[1])[0]
    print("Trilha escolhida (fallback):", trilha_escolhida.nome)
    # return [trilha_escolhida]

    # liberação de capítulos com base no nível de conhecimento do usuário
    capitulos_liberados = []
    if nivel_conhecimento:
        for conteudo, nivel in nivel_conhecimento.items():
            try:
                nivel_valor = float(nivel)
            except:
                continue

            if nivel_valor >= 80:
                # libera só os 3 primeiros capítulos do primeiro tópico
                primeiroTopico = trilha_escolhida.topicos.order_by("id").first()
                if primeiroTopico:
                    capitulos = primeiroTopico.capitulos.order_by("id")[:3]
                    capitulos_liberados.extend([c.id for c in capitulos])
            
            elif nivel_valor >= 50:
                # libera só o primeiro capítulo do primeiro tópico
                primeiro_topico = trilha_escolhida.topicos.order_by("id").first()
                if primeiro_topico:
                    cap = primeiro_topico.capitulos.order_by("id").first()
                    if cap:
                        capitulos_liberados.append(cap.id)
    return[{
        "trilha": trilha_escolhida,
        "capitulos_liberados": list(set(capitulos_liberados))
    }]


def recomendar_proxima_trilha(trilha_concluida, usuario=None, n_recomendacoes=3, limiar_similaridade= 0.50):
    model = Doc2Vec.load(MODEL_PATH)

    #Vetor da trilha concluida
    tokens_input = preprocess(f"{trilha_concluida.nome} {trilha_concluida.descricao or ''}")
    vetor_trilha = model.infer_vector(tokens_input)

    #Todas as trilhas, menos a concluída
    trilhas_db = Trilha.objects.exclude(id=trilha_concluida.id)

    if usuario:
        trilha_excluir = []

        for trilha in trilhas_db:
            capitulos = Capitulo.objects.filter(topico__trilha=trilha)
            total = capitulos.count()
            concluidos = ProgressoCapitulo.objects.filter(usuario=usuario, capitulo__in=capitulos, concluido=True).count()

            #trilhas não finalizadas
            if concluidos > 0 and  concluidos < total:
                trilha_excluir.append(trilha.id)
            
            # trilhas já concluidas
            if concluidos == total and total > 0:
                trilha_excluir.append(trilha.id)
        
        trilhas_db = trilhas_db.exclude(id__in=trilha_excluir)

    trilhas, vetores = [], []
    for trilha in trilhas_db:
        texto_trilha = f"{trilha.nome} {trilha.descricao or ''}"
        tokens_trilha = preprocess(texto_trilha)
        vetores.append(model.infer_vector(tokens_trilha))
        trilhas.append(trilha)
    
    if not vetores:
        return []
    
    # Similaridade
    sims = cosine_similarity([vetor_trilha], vetores)[0]
    resultados = list(zip(trilhas, sims))

    #ordena por similaridade
    similares = sorted(resultados, key=lambda x: x[1], reverse=True)

    #Filtrar pelo limiar e pega só os top N
    recomendadas = [triLHA for triLHA, similaridade in similares if similaridade >= limiar_similaridade][:n_recomendacoes]

    #Fallback: se não houver nenhuma trilha acima do limiar, pega as top N
    if not recomendadas:
        recomendadas = [triLHA for triLHA, similaridade in similares[:n_recomendacoes]]
    
    return recomendadas
