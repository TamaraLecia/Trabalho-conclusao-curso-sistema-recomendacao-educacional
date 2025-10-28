import os
import numpy as np
import pandas as pd
import nltk

# utilizada na geração do gráficos
import matplotlib.pyplot as plt
import seaborn as sns
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
    trilhas, vetores_trilhas, tokens_trilhas_cache = [], [], {}

    for trilha in trilhas_db:
        texto_trilha = f"{trilha.nome} {trilha.descricao or ''}"
        tokens_trilha = preprocess(texto_trilha, termos_prioritarios=conteudos_usuario)
        tokens_trilhas_cache[trilha] = set(tokens_trilha)
        vetores_trilhas.append(model.infer_vector(tokens_trilha))
        trilhas.append(trilha)

    if not vetores_trilhas:
        return []
    
    # visualizar_matriz_coloridaNormalizada(vetores_trilhas, vetor_usuario)
    # nomes_trilhas = [trilha.nome for trilha in trilhas]
    # visualizar_matriz_colorida(vetores_trilhas, [vetor_usuario], nomes_trilhas)
    # visualizar_matriz_original(vetores_trilhas, vetor_usuario)

    # === PCA + Similaridade ===
    todos_vetores = np.array(vetores_trilhas + [vetor_usuario])
    # max_componentes = min(todos_vetores.shape[0], todos_vetores.shape[1])
    # if max_componentes < 2:
    #     print("⚠️ Não há componentes suficientes para visualização 2D com PCA.")
    #     visualizar_matriz_pca_semPersonalizar(todos_vetores)  # ou apenas pule
    # else:
    #     n_comp = min(n_componentes_pca, max_componentes)
    #     pca = PCA(n_components=n_comp)
    #     vetores_reduzidos = pca.fit_transform(todos_vetores)

    #     vet_trilhas_red = vetores_reduzidos[:-1]
    #     vet_usuario_red = vetores_reduzidos[-1]

    #     nomes_trilhas = [trilha.nome for trilha in trilhas]
    #     if vetores_reduzidos.shape[1] >= 2:
    #         visualizar_matriz_pca(vetores_reduzidos, nomes_trilhas)
    #     else:
    #         print("⚠️ Vetores PCA têm menos de 2 dimensões. Pulando visualização 2D.")



    max_componentes = min(todos_vetores.shape[0], todos_vetores.shape[1])
    n_comp = max(2, min(n_componentes_pca, max_componentes))

    pca = PCA(n_components=n_comp)
    vetores_reduzidos = pca.fit_transform(todos_vetores)
    vet_trilhas_red = vetores_reduzidos[:-1]
    vet_usuario_red = vetores_reduzidos[-1]

    # nomes_trilhas = [trilha.nome for trilha in trilhas]
    # visualizar_matriz_pca(vetores_reduzidos, nomes_trilhas)

    # nomesTrilhas = [trilha.nome for trilha in trilhas]
    # nomesTrilhas = nomesTrilhas + ["Usuário"]
    # visualizar_matriz_pca_semPersonalizar(vetores_reduzidos , nomesTrilhas)

    sims = cosine_similarity([vet_usuario_red], vet_trilhas_red)[0]
    resultados = list(zip(trilhas, sims))

    similares = [(t, s) for (t, s) in resultados if s >= limiar_similaridade]
    if not similares:
        similares = sorted(resultados, key=lambda x: x[1], reverse=True)[:10]
    
    # nomesTrilhas_similares = [tri for (tri, sim) in similares]
    # valoresTrilhas_similares = [sim for (trin, sim) in similares]

    # visualizar_matriz_similaridade(nomesTrilhas_similares, valoresTrilhas_similares)
    # visualizar_similaridade_barras(nomesTrilhas_similares, valoresTrilhas_similares)

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
        palavra_chave = conteudo_menor.split()[-1].lower()

        print("\n=== DEBUG RERANKING ===")
        print("Conteúdo de menor conhecimento:", conteudo_menor)
        print("Palavra-chave usada para busca:", palavra_chave)

        com_menor = [
            (t, s) for (t, s) in similares 
            if palavra_chave in (t.nome.lower() + " " + (t.descricao or "").lower())
        ]

        if com_menor:
            # 🔑 pega só a trilha mais similar do menor conhecimento
            trilha_escolhida = max(com_menor, key=lambda x: x[1])[0]
            print("Trilha escolhida (menor conhecimento):", trilha_escolhida.nome)
            return [trilha_escolhida]
        else:
            print("⚠️ Nenhuma trilha encontrada para o menor conhecimento, usando fallback.")

    # fallback: retorna só a trilha mais similar de todas
    trilha_escolhida = max(similares, key=lambda x: x[1])[0]
    print("Trilha escolhida (fallback):", trilha_escolhida.nome)
    return [trilha_escolhida]


# def visualizar_matriz_coloridaNormalizada(vetores_trilha, vetores_usuario, caminho_arquivo="recomendarTrilhas/static/matriz_normalizada_colorida.png"):
#     todos_vetores = np.array(vetores_trilha + vetores_usuario)

#     # Normalizando os valores para um melhor contraste visual
#     matriz_normalizada = (todos_vetores - np.min(todos_vetores)) / (np.max(todos_vetores) - np.min(todos_vetores))

#     # Cria figura
#     fig, ax = plt.subplots(figsize=(14,6))

#     # Cores: azul para os vetores das trilhas e vermelho para o vetores do usuário
#     cores = ['Blues'] * len(vetores_trilha) + ['Reds']

#     for i, linha in enumerate(matriz_normalizada):
#         cmap = plt.get_cmap(cores[i])
#         ax.imshow([linha], aspect='auto', cmap=cmap,
#                     extent=[0, linha.shape[0], i, i+1],
#                     interpolation='nearest')
        
#     ax.set_yticks(np.arange(len(todos_vetores)) + 0.05)
#     ax.get_yticklabels([f"Trilha {i+1}" for i in range(len(vetores_trilha))]) + ["Usuário"]

#     # Exibe a matriz como imagem
#     # ax.imshow(matriz_normalizada, aspect='auto', cmap='Blues')

#     # # Destaca o vetor do usuário com uma linha
#     # idx_usuario = len(vetores_trilha)
#     # faixa = Rectangle((0, idx_usuario), matriz_normalizada.shape[1], 1, linewidth=0, edgecolor=None, facecolor='red', alpha=0.3)
#     # ax.add_patch(faixa)
#     # ax.axhline(idx_usuario - 0.5, color='red', linewidth=2, label='Usuário')

#     ax.set_title("Matriz Original - Trilhas (azul) e Usuário (linha vermelha)", fontsize=14)
#     ax.set_xlabel("Dimensões do vetor", fontsize=12)
#     ax.set_ylabel("Vetores (trilhas + usuário)", fontsize=12)
#     plt.tight_layout()

#     plt.savefig(caminho_arquivo)
#     plt.close()

# def visualizar_matriz_colorida(vetores_trilhas, vetores_usuario, nomes_trilha=None, caminho_arquivo="recomendarTrilhas/static/matriz_colorida_sem_normaliza.png"):
#     todos_vetores = np.array(vetores_trilhas + vetores_usuario)

#     # Define os rótulos do eixo Y
#     if nomes_trilha is None:
#         nomes_trilha = [f"Trilha {i+1}" for i in range(len(vetores_trilhas))]
#     nomes_eixo_y = nomes_trilha + [f"Usuário {i+1}" for i in range(len(vetores_usuario))]
    
#     # cria a figura
#     fig, ax = plt.subplots(figsize=(14, 6))

#     # Exibe cada linha com a cor diferente
#     indices = list(range(len(todos_vetores)))[::-1] #inverte os índices
#     for j, i in enumerate(indices):
#         linha = todos_vetores[i]       
#         cmap = 'Blues' if i < len(vetores_trilhas) else 'Reds'
#         ax.imshow([linha], aspect='auto', cmap=cmap, extent=[0, linha.shape[0], j, j+1])
    
#     ax.set_yticks(np.arange(len(todos_vetores)) + 0.5)
#     ax.set_yticklabels(nomes_eixo_y[::-1])

#     ax.set_title("Matriz Original - Vetores das Trilhas (azul) e do Usuário (vermelho)")
#     ax.set_xlabel("Dimensões do vetor")
#     ax.set_ylabel("Vetores (trilhas + usuário)")
#     plt.tight_layout()

#     plt.savefig(caminho_arquivo)
#     plt.close()


# def visualizar_matriz_original(vetores_trilhas, vetores_usuarios, caminho_arquivo="recomendarTrilhas/static/matriz_original.png"):
#     #Junta os vetores
#     todos_vetores = np.array(vetores_trilhas + vetores_usuarios)

#     #Cria a lista de cores para cada vetor
#     cores = ['Blues'] * len(vetores_trilhas) + ['Reds']

#     #Cria o heatmap linha por linha com cor personalizada
#     fig, ax = plt.subplots(figsize=(14, 6))
#     for i, linha in enumerate(todos_vetores):
#         sns.heatmap([linha], cmap=cores[i], cbar=False, ax=ax, xticklabels=False, yticklabels=False, linewidths=0.5, linecolor='gray')

#     ax.set_title("Matriz Original - Vetores das Trilhas e do Usuário")
#     ax.set_xlabel("Dimensões do vetor")
#     ax.set_ylabel("Vetores (trilhas + usuário)")
#     plt.tight_layout()

#     plt.savefig(caminho_arquivo)
#     plt.close()


# def visualizar_matriz_pca(vetoresReduzidos, nomes_trilhas, caminho_arquivo="recomendarTrilhas/static/pca_matriz_personalizada.png"):
#     if vetoresReduzidos.shape[1] < 2:
#         print("Não tem componentes suficiente")
#         return
    
#     #Separando trilhas e usuários
#     vetorTrilha_reduzido = vetoresReduzidos[:-1]
#     vetorUsuario_reduzido = vetoresReduzidos[-1]

#     # criar gráfico de dispensão
#     plt.figure(figsize=(12, 7))
#     plt.scatter(vetorTrilha_reduzido[:, 0], vetorTrilha_reduzido[:, 1], color='blue', label='Trilhas')
#     plt.scatter(vetorUsuario_reduzido[0], vetorUsuario_reduzido[1], color='red', label='Usuário', marker='X', s=120)

#     # Adiciona rótulos nas trilhas
#     textos = []
#     for i, nome in enumerate(nomes_trilhas):
#         x = vetorTrilha_reduzido[i][0]
#         y = vetorTrilha_reduzido[i][1]
#         textos.append(plt.text(x + 0.05, y, nome, fontsize=9, color='blue'))

#     # Rótulo do usuário
#     plt.text(vetorUsuario_reduzido[0] + 0.05, vetorUsuario_reduzido[1], "Usuário", fontsize=10, color='red', weight='bold')

#     # Ajusta o texto para evitar que fique embolado
#     adjust_text(textos, arrowprops=dict(arrowstyle='-', color='gray'))

#     plt.xlabel("Componentes de PCA 1 eixo x")
#     plt.ylabel("Componentes PCA 2 eixo 2")
#     plt.title("Dispersão dos Vetores PCA: Trilhas x Usuário")
#     plt.legend()
#     plt.grid(True)
#     plt.tight_layout()

#     # Salvando a imagem
#     plt.savefig(caminho_arquivo)
#     plt.close()


# #gerar a imagem sem personalização
# def visualizar_matriz_pca_semPersonalizar(vetoresReduzidos, nomes_trilha, caminho_arquivo="recomendarTrilhas/static/pca_matriz_sem_personalizacao.png"):
#     fig, ax = plt.subplots(figsize=(12, 6))

#     # Plota o heatmap
#     sns.heatmap(vetoresReduzidos, cmap="YlGnBu", cbar=True, ax=ax, yticklabels=nomes_trilha)

#     # Pega a última linha (usuário)
#     ultima_linha = vetoresReduzidos.shape[0] - 1
#     n_colunas = vetoresReduzidos.shape[1]

#     # Adiciona um retângulo vermelho em volta da últma linha
#     rect = Rectangle((0, ultima_linha), n_colunas, 1, fill=False, edgecolor="red", linewidth=2)
#     ax.add_patch(rect)

#      # Labels e título
#     ax.set_xlabel("Componentes PCA")
#     ax.set_ylabel("Vetores (trilhas + usuário)")
#     ax.set_title("Matriz PCA - Vetores Reduzidos")

#     plt.tight_layout()
#     plt.savefig(caminho_arquivo)
#     plt.close()
    
# # gerar a imagem da matriz de medição de similaridade
# def visualizar_matriz_similaridade(trilhas, similaridade, caminho_arquivo="recomendarTrilhas/static/matriz_similaridade.png"):
#     # Converte para matriz 2D (1 linha = usuário, colunas = trilhas)
#     similaridade = np.array(similaridade, dtype=float).reshape(1, -1)

#     plt.figure(figsize=(12, 6))
#     sns.heatmap(similaridade, annot=True, cmap="YlGnBu", xticklabels=trilhas, yticklabels=["Usuário"])
#     plt.title("Similaridade de cosseno entre o vetor de usuário e o vetor de trilhas")
#     plt.xlabel("Trilhas")
#     plt.ylabel("Usuário")
#     plt.tight_layout()
#     plt.savefig(caminho_arquivo)
#     plt.close()

# def visualizar_similaridade_barras(trilhas, similaridade, caminho_arquivo="recomendarTrilhas/static/grafico_barra_similaridade.png"):
#     similaridade = np.array(similaridade, dtype=float)

#     # ordena da maior similaridade para a menor
#     indices_ordenados = np.argsort(similaridade)[::-1]
#     trilhasOrdenadas = [trilhas[i] for i in indices_ordenados]
#     similaridades_ordenadas = similaridade[indices_ordenados]

#     # criar índices numericos para o eixo y
#     indice_y = np.arange(len(trilhasOrdenadas))
    
#     plt.figure(figsize=(12, 6))
#     plt.barh(indice_y, similaridades_ordenadas, color="skyblue")
#     plt.yticks(indice_y, trilhasOrdenadas) # substitui o índice pelos os nomes das trilhas
#     plt.xlabel("Similaridade de cosseno")
#     plt.title("Similaridade de cosseno entre usuários e trilhas")
#     plt.gca().invert_yaxis() # a trilha mais similar fica no topo
#     plt.tight_layout()
#     plt.savefig(caminho_arquivo)
#     plt.close()

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
