from django.shortcuts import get_object_or_404, redirect, render
from Sistema.forms import AdicionarUsuarioForm, SenhaForm, EditarUserForm
from usuarioComun.forms import UsuarioComunForm
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from .models import UsuarioComun
from administrador.models import Administrador
from recomendarTrilhas.models import Capitulo, ProgressoCapitulo
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum

# Create your views here.
@login_required
def index (request):
    user = request.user
    # Se o usuário for administrador, redireciona para a tela de administrador
    if hasattr(user, 'administrador'):
        return redirect('indexAdm')
    
    usuario, _ = UsuarioComun.objects.get_or_create(
        user=request.user,defaults={
            "nome": request.user.first_name or request.user.username or request.user.email,
            "identificador": "usuarioComun"
        }
    )
    # usuario = get_object_or_404(UsuarioComun, user=request.user)
    trilha = usuario.trilhaUser.all() if hasattr(usuario, "trilhaUser") else []
    # trilha = usuario.trilhaUser if usuario.trilhaUser_id else None
    return render(request, 'usuarioComun/indexUsuarioComun.html',{"usuario": usuario, "trilha": trilha, "userUsuario": usuario}) 

def add_usuario(request):
    form_user = AdicionarUsuarioForm(request.POST or None)
    form = UsuarioComunForm(request.POST or None)
    if form_user.is_valid() and form.is_valid():
        user_usuarioComun = form_user.save()
        usuarioComun = form.save(commit=False)
        usuarioComun.user = user_usuarioComun
        usuarioComun.identificador = 'usuarioComun'
        usuarioComun.save()

    #Adiciona o usuário ao grupo usuarioComun -----------------------

        nomeGrupo = usuarioComun.identificador
        grupo, _ = Group.objects.get_or_create(name='UsuarioComun')
        user_usuarioComun.groups.add(grupo)
        print("Cliente promovido a usuarioComun:", usuarioComun.nome)


    #-----------------------------------------------------------------
        usuario_autenticado = authenticate(request, username = user_usuarioComun.username, password = form_user.cleaned_data['password1'])
        if usuario_autenticado:
            login(request, usuario_autenticado)
        return redirect('indexUsuarioComun')

    
    return render(request, 'usuarioComun/criarContaForm.html', {'form_user': form_user, 'form': form})

def minhas_trilhas(request):
    usuario = request.user.usuariocomun
    trilhas = usuario.trilhaUser.all()

    trilhas_em_andamento = []

    for trilha in trilhas:
        capitulos = Capitulo.objects.filter(topico__trilha=trilha)
        total = capitulos.count()

        concluidos = ProgressoCapitulo.objects.filter(usuario=usuario, capitulo__in=capitulos, concluido=True).count()

        if concluidos < total:
            trilhas_em_andamento.append(trilha)

         # soma geral de pontos do usuário
    resultado = ProgressoCapitulo.objects.filter(usuario=usuario).aggregate(Sum("pontuacao"))
    pontos_gerais = resultado["pontuacao__sum"] or 0

    return render(request, "usuarioComun/minhas_trilhas.html", {
        "trilhas": trilhas_em_andamento,
        "pontos_gerais": pontos_gerais
    })

def trilhas_concluidas(request):
    usuario = request.user.usuariocomun
    todasTrilhas = usuario.trilhaUser.all()

    trilha_concluida = []

    for trilha in todasTrilhas:
        capitulos = Capitulo.objects.filter(topico__trilha=trilha)
        total = capitulos.count()

        concluido = ProgressoCapitulo.objects.filter(usuario=usuario, capitulo__in=capitulos, concluido=True).count()

        if total > 0 and total == concluido:
            trilha_concluida.append(trilha)
        
    return render(request, "usuarioComun/trilhasConcluidas.html",{
        "trilhas_concluidas": trilha_concluida,
    })

def excluirConta(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        messages.success(request, "Sua conta foi excluída com sucesso.")
        return redirect("indexSistema")
    
def verPerfil(request, username):
    usuarioComun = UsuarioComun.objects.get(user__username=username)
    userUsuario = usuarioComun.user

    return render(request, 'usuarioComun/verPerfil.html', {'userUsuario': userUsuario, 'usuarioComun': usuarioComun})

# editar senha
def editarSenhaUsuario(request, username):
    usuario_comun = get_object_or_404(UsuarioComun, user__username=username)
    user = usuario_comun.user

    if request.method == 'POST':
        formSenha = SenhaForm(user, request.POST)
        if formSenha.is_valid():
            user = formSenha.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Senha alterada com sucesso!")
            return redirect('verPerfil', username=user.username)
    else:
        formSenha = SenhaForm(user)
    
    return render(request,  'usuarioComun/gerenciarContaForm.html', {'formSenha': formSenha,})


def editarDadosUsuarioComun(request, username):
    usuarioComun = get_object_or_404(UsuarioComun, user__username=username)
    user = usuarioComun.user
    
    if request.method == 'POST':
        editarUserForm = EditarUserForm(request.POST, instance=user)
        editarUsuarioComunForm = UsuarioComunForm(request.POST, instance=usuarioComun)

        if editarUserForm.is_valid() and editarUsuarioComunForm.is_valid():
            editarUserForm.save()
            editarUsuarioComunForm.save()
            return redirect('verPerfil', username=usuarioComun.user.username)
    
    else:
        editarUserForm = EditarUserForm(instance=user)
        editarUsuarioComunForm = UsuarioComunForm(instance=usuarioComun)

    return render(request, 'usuarioComun/gerenciarContaForm.html', {'editarUserForm' : editarUserForm, 'editarUsuarioComunForm' : editarUsuarioComunForm, 'usuarioComun' : usuarioComun})

@login_required
def realizarLogout(request):
    logout(request)
    return redirect('indexSistema')


# def pontuacao_geral(request):
#     usuario = request.user.usuariocomun

#     # soma todas as pontuações dos capítulos concluídos desse usuário
#     resultado = ProgressoCapitulo.objects.filter(usuario=usuario).aggregate(Sum("pontuacao"))
#     pontos_gerais = resultado["pontuacao__sum"] or 0

#     return render(request, "usuarioComun/minhas_trilhas.html", {
#         "pontos_gerais": pontos_gerais
#     })