import pandas as pd
import os
import json

from django.shortcuts import render, redirect, get_object_or_404
from .recomendador import recomendar_trilha, recomendar_proxima_trilha
from django.conf import settings
from django.forms import inlineformset_factory
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum
from django.contrib.auth.decorators import permission_required


from .forms import TrilhaForm, TopicoFormSet, CapituloFormSet, TopicoForm, CapituloForm
from .models import Topico, Trilha, Capitulo, ProgressoCapitulo
from usuarioComun.models import UsuarioComun

DATA_PATH = os.path.join(settings.BASE_DIR, 'recomendarTrilhas', 'data', 'tecnologiasPergunta1.csv')

@permission_required('recomendarTrilhas.acessar_trilha', login_url='/accounts/login/')
def responderQuestionario(request):
    inicio = int(request.POST.get("inicio", 1)) #controla eu qual etapa o formulário está
    conteudos = []
    conteudos_relacionados = []
    conteudos_selecionados = []
    nivel_conhecimento = {}
    objetivo = ""
    conteudos_recomendados = []

    if inicio == 1:
        df = pd.read_csv(DATA_PATH, encoding='utf-8')
        conteudos = df[['Conteudo']].drop_duplicates().to_dict(orient="records")

    if request.method == "POST":

        if inicio == 2:
            conteudos = request.POST.getlist("Conteudo")
            conteudos_selecionados = conteudos

        elif inicio == 3:
            conteudos = request.POST.getlist("Conteudo")
            conteudos_selecionados = conteudos
            for key, value in request.POST.items():
                if key.startswith("nivel_"):
                    conteudoConhecimento = key.replace("nivel_", "")
                    nivel_conhecimento[conteudoConhecimento] = int(value)

        elif inicio == 4:
            conteudos_selecionados = request.POST.getlist("Conteudo")
            objetivo = request.POST.get("objetivo", "")

            nivel_conhecimento = {}
            for key, value in request.POST.items():
                if key.startswith("nivel_"):
                    conteudoConhecimento = key.replace("nivel_", "")
                    nivel_conhecimento[conteudoConhecimento] = int(value)

            conteudos_recomendados = recomendar_trilha(
                conteudos_usuario=conteudos_selecionados,
                nivel_conhecimento=nivel_conhecimento,
                objetivo=objetivo
            )
            
            trilha_id = request.POST.get("trilha_id")
            if trilha_id:
                usuario = get_object_or_404(UsuarioComun, user=request.user)
                trilha = get_object_or_404(Trilha, id=trilha_id)
                usuario.trilhaUser.add(trilha)
                return redirect("minhasTrilhas")

    return render(request, "recomendarTrilhas/questionario.html", {
        "inicio": inicio,
        "conteudos": conteudos,
        "conteudos_relacionados": conteudos_relacionados,
        "conteudos_selecionados": conteudos_selecionados,
        "nivel_conhecimento": nivel_conhecimento,
        "objetivo": objetivo,
        "conteudos_recomendados": conteudos_recomendados
    })

def criar_trilha_completa(request):
    if request.method == "POST":
        form = TrilhaForm(request.POST)
        formset = TopicoFormSet(request.POST, instance=Trilha())
        if form.is_valid() and formset.is_valid():
            trilha = form.save()
            formset.instance = trilha
            formset.save()
            return redirect("verTrilha")
    else:
        form = TrilhaForm()
        formset = TopicoFormSet(instance=Trilha())

    return render(request, "recomendarTrilhas/trilha_form.html", {"form": form, "formset": formset})


def editar_topico(request, topico_id):
    topico = get_object_or_404(Topico, id=topico_id)
    formset = CapituloFormSet(request.POST or None, instance=topico)

    if request.method == "POST" and formset.is_valid():
        formset.save()
        return redirect("verTrilha")

    return render(request, "recomendarTrilhas/editar_topico.html", {"topico": topico, "formset": formset})


def lista_trilhas(request):
    query = request.GET.get('q') # pega o valor do campo de busca
    if query:
        trilhas = Trilha.objects.filter(nome__icontains=query)
    else:
        trilhas = Trilha.objects.all()
    return render(request, "recomendarTrilhas/verTrilha.html", {"trilhas": trilhas})

def dadosTrilha(request, trilha_id):
    trilha = get_object_or_404(Trilha, id=trilha_id)

    # contagem de tópicos
    total_topicos = trilha.topicos.count()

    # contagem de capítulos da trilha
    total_capitulos = sum(topico.capitulos.count() for topico in trilha.topicos.all())

    return render(request, "recomendarTrilhas/lista_trilhas.html", {"trilhas": [trilha], "total_topicos": total_topicos, "total_capitulos": total_capitulos})

    
@login_required
def caminhos_trilha(request, trilha_id):
    trilha = get_object_or_404(Trilha, id=trilha_id)
    topicos = trilha.topicos.prefetch_related("capitulos").all().order_by("id")
    usuario = request.user.usuariocomun

    # progresso por capítulo
    progresso_qs = ProgressoCapitulo.objects.filter(
        usuario=usuario, capitulo__topico__in=topicos
    ).select_related("capitulo")

    creditos_sem_tratamento = sum(p.capitulo.duracao_horas_video for p in progresso_qs if p.concluido)
    # creditosAlinhados = creditos_sem_tratamento * 10

    # creditos, nivel = nivel_por_creditos(creditos_sem_tratamento)

    progresso_dict = {p.capitulo.id: p.concluido for p in progresso_qs}
    ultimo_topico_id = None

    # progresso por tópico (total e concluídos)
    progresso_topicos = {}
    for topico in topicos:
        capitulos = topico.capitulos.all()
        total = capitulos.count()
        concluidos = sum(1 for c in capitulos if progresso_dict.get(c.id))
        
            # definir a cor conforme o status
        if concluidos == 0:
            status = "nao-iniciado" #Cor laranja
        elif concluidos == total:
            status = "concluido"   #Cor verde
        else:
            status = "andamento"    #Cor azul

        topico.status = status

        # guarda o progresso no dicionário
        progresso_topicos[topico.id] = {
            "total": total,
            "concluidos": concluidos
        }

         # encontra os tópicos que o usuário parou, para quando ele entrar na página ir direto para o tópico que ele estava
        if not ultimo_topico_id and concluidos < total:
            ultimo_topico_id = topico.id
    
    #se não encontrou nemhum tópico em andamento, pega o último da trilha
    if not ultimo_topico_id and topicos:
        ultimo_topico_id = None

    # definir se o tópico está liberado
    topicos_liberados = {}
    topicos_ordenados = list(topicos)
    for idx, topico in enumerate(topicos_ordenados):
        if idx == 0:
            # primeiro tópico sempre liberado
            topicos_liberados[topico.id] = True
        else:
            anterior = topicos_ordenados[idx - 1]
            # progresso_anterior = progresso_topicos.get(anterior.id, {"concluidos":0, "total": 1})
            topicos_liberados[topico.id] = (
                progresso_topicos[anterior.id]["concluidos"] == progresso_topicos[anterior.id]["total"]
            )

    # mapa de capítulo anterior (para desbloqueio dentro do tópico)
    anterior_por_capitulo = {}
    for topico in topicos:
        caps = list(topico.capitulos.all().order_by("ordem"))
        for idx, cap in enumerate(caps):
            anterior_por_capitulo[cap.id] = caps[idx - 1].id if idx > 0 else None

    capitulos = [cap for triLHA in topicos for cap in triLHA.capitulos.all()]
    pontos_totais = len(capitulos) * 10 # cada capítulo vale 10 pontos
    pontos_usuario = sum((p.pontuacao or 0) for p in progresso_qs)
    percentual = (pontos_usuario / pontos_totais * 100) if pontos_totais > 0 else 0


    return render(request, "recomendarTrilhas/trilhaAprendizado.html", {
        "trilha": trilha,
        "topicos": topicos,
        "progresso": progresso_dict,
        "progresso_topicos": progresso_topicos,
        "topicos_liberados": topicos_liberados,
        "anterior_por_capitulo": anterior_por_capitulo,
        "pontos_usuario": pontos_usuario,
        "pontos_totais": pontos_totais,
        "percentual": percentual,
        "ultimo_topico_id": ultimo_topico_id,
    })


def editarTrilha(request, trilha_id):
    trilha = get_object_or_404(Trilha, id=trilha_id)
    formTrilha = TrilhaForm(request.POST or None, instance=trilha)
    TopicoFormSet = inlineformset_factory(Trilha, Topico, form=TopicoForm, extra=0, can_delete=False)
    formsetTopico = TopicoFormSet(request.POST or None, instance=trilha, prefix='topico_set')

    formsetCapitulos = []
    
    if request.method == 'POST':
        if formTrilha.is_valid() and formsetTopico.is_valid():
            trilha = formTrilha.save()
            topico_forms = formsetTopico.save(commit=False)

            for topico in topico_forms:
                topico.trilha = trilha
                topico.save()

            formsetTopico.save_m2m()

            for i, topicoForm in enumerate(formsetTopico.forms):
                topico = topicoForm.instance
                CapituloFormSet = inlineformset_factory(Topico, Capitulo, form=CapituloForm, extra=0, can_delete=False)
                prefix = f'capitulo_{i}'
                formsetCapitulo = CapituloFormSet(request.POST, instance=topico, prefix=prefix)

                for form in formsetCapitulo.forms:
                    form.empty_permitted = False

                if formsetCapitulo.is_valid():
                    formsetCapitulo.save()
                else:
                    print(f"Erros no formsetCapitulo {i}: {formsetCapitulo.errors}")
                
                formsetCapitulos.append(formsetCapitulo)

            return redirect('verTrilha')
    print("POST RECEBIDO:")
    for key, value in request.POST.items():
     print(f"{key} = {value}")

    else:
        for i, topicoForm in enumerate(formsetTopico.forms):
            topico = topicoForm.instance
            CapituloFormSet = inlineformset_factory(Topico, Capitulo, form=CapituloForm, extra=0, can_delete=False)
            prefix = f'capitulo_{i}'
            formsetCapitulo = CapituloFormSet(instance=topico, prefix=prefix)
            formsetCapitulos.append(formsetCapitulo)
    
    topicoCapitulo = zip(formsetTopico.forms, formsetCapitulos)

    CapituloFormSetModelo = inlineformset_factory(Topico, Capitulo, form=CapituloForm, extra=1, can_delete=False)
    formModeloCapitulo = CapituloFormSetModelo()

    return render(request, 'recomendarTrilhas/editarTrilha.html', {'formTrilha': formTrilha, 
                                                                   'formsetTopico': formsetTopico,
                                                                   'topicoCapitulo': topicoCapitulo,
                                                                   'formModeloCapitulo': formModeloCapitulo})


def deletarTrilha(request, trilha_id):
    trilha = get_object_or_404(Trilha, id=trilha_id)
    trilha.delete()
    return redirect('verTrilha')

@login_required
def ver_capitulo(request, capitulo_id):
    capitulo = get_object_or_404(Capitulo, id=capitulo_id)
    usuario = request.user.usuariocomun

    # pega todos os tópicos da trilha do capítulo
    topicos = capitulo.topico.trilha.topicos.all().order_by("id")

    # progresso do usuário
    progresso_qs = ProgressoCapitulo.objects.filter(
        usuario=usuario, capitulo__topico__in=topicos
    )
    progresso_dict = {p.capitulo.id: p.concluido for p in progresso_qs}

    # encontra posição do tópico atual
    topicos_ordenados = list(topicos)
    idx = topicos_ordenados.index(capitulo.topico)

    # se não for o primeiro tópico, verifica se o anterior está 100% concluído
    if idx > 0:
        anterior = topicos_ordenados[idx - 1]
        concluidos = sum(1 for c in anterior.capitulos.all() if progresso_dict.get(c.id))
        if concluidos < anterior.capitulos.count():
            # renderiza o template com aviso de bloqueio
            return render(request, "recomendarTrilhas/capitulo.html", {
                "capitulo": capitulo,
                "bloqueado": True
            })

    # se liberado, renderiza normalmente
    return render(request, "recomendarTrilhas/capitulo.html", {
        "capitulo": capitulo,
        "bloqueado": False
    })

@login_required
def concluir_capitulo(request, capitulo_id):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=400)

    capitulo = get_object_or_404(Capitulo, id=capitulo_id)
    usuario = request.user.usuariocomun

    #Ler a requisição (tempo assistido e duração)
    try:
        data = json.loads(request.body)
        tempo_assitido = float(data.get("tempo_assistido", 0))
        duracao = float(data.get("duracao", 1))
    except Exception:
        tempo_assitido, duracao = 0, 1
    
    percentual = (tempo_assitido / duracao) * 100 if duracao > 0 else 0

    progresso, _ = ProgressoCapitulo.objects.get_or_create(
        usuario=usuario,
        capitulo=capitulo
    )

    if percentual >= 90:
        progresso.concluido = True
        progresso.pontuacao = 10
    elif percentual >= 50:
        progresso.concluido = True
        progresso.pontuacao = 5
    else:
        progresso.concluido = False
        progresso.pontuacao = 0

    progresso.save()

    trilha = capitulo.topico.trilha

    # Último tópico e último capítulo pelo maior id
    ultimo_topico = trilha.topicos.order_by("id").last()
    ultimo_capitulo = ultimo_topico.capitulos.order_by("id").last() if ultimo_topico else None

    if ultimo_capitulo and capitulo.id == ultimo_capitulo.id:
        # Redireciona para a trilha com parâmetro indicando conclusão
        return JsonResponse({
            "status": "trilha_concluida",
            "redirect_url": reverse("verTrilhaCaminho", args=[trilha.id]) + "?concluida=1"
        })

    return JsonResponse({
        "status": "ok",
        "redirect_url": reverse("verTrilhaCaminho", args=[trilha.id])
    })

def nova_recomendacao(request, trilha_id):
    usuario = get_object_or_404(UsuarioComun, user=request.user)
    trilha_concluida = get_object_or_404(Trilha, id=trilha_id)

    # Verifica se o usuário concluiu todos os capítulos da trilha
    total_capitulos = trilha_concluida.total_capitulos
    concluidos = ProgressoCapitulo.objects.filter(
        usuario=usuario,
        capitulo__topico__trilha=trilha_concluida,
        concluido=True
    ).count()

    # Se ainda não concluiu tudo, redireciona de volta para a trilha
    if concluidos < total_capitulos:
        return redirect(reverse("verTrilhaCaminho", args=[trilha_concluida.id]))
    
    if request.method == "POST":
        nova_trilha_id = request.POST.get("trilha_id")
        if nova_trilha_id:
            nova_trilha = get_object_or_404(Trilha, id=nova_trilha_id)
            usuario.trilhaUser.add(nova_trilha)
            return redirect("minhasTrilhas")

    # Caso contrário, chama o recomendador passando a trilha concluída
    trilhas_recomendadas = recomendar_proxima_trilha(trilha_concluida, usuario=usuario)
    nenhumaTrilhaNova = len(trilhas_recomendadas) == 0

    return render(request, "recomendarTrilhas/nova_recomendacao.html", {
        "trilha_concluida": trilha_concluida,
        "trilhas_recomendadas": trilhas_recomendadas,
        "nenhumaTrilhaNova": nenhumaTrilhaNova,
    })

# def pontuacao_geral(request):
#     usuario = request.user.usuariocomun

#     # soma todas as pontuações dos capítulos concluídos desse usuário
#     resultado = ProgressoCapitulo.objects.filter(usuario=usuario).aggregate(Sum("pontuacao"))
#     pontos_gerais = resultado["pontuacao__sum"] or 0

#     return render(request, "usuarioComun/minhas_trilhas.html", {
#         "pontos_gerais": pontos_gerais
#     })