from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from Sistema.forms import AdicionarUsuarioForm, EditarUserForm, SenhaForm
from administrador.forms import AdministradorForm
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, permission_required
from .models import Administrador
from django.contrib.auth import get_user_model, logout
from django.contrib.auth import update_session_auth_hash

@login_required
def index (request):
    return render(request, 'administrador/indexAdministrador.html',)

#Adicionar administrador
def add_administrador(request):
    form_user = AdicionarUsuarioForm(request.POST or None)
    form = AdministradorForm(request.POST or None)
    if form_user.is_valid() and form.is_valid():
        user_administrador = form_user.save() #Cria o usuário do model user
        administrador = form.save(commit=False) #Criar o usuario do model Administrador
        administrador.user = user_administrador #Associar o usuario User com o Administrador
        administrador.identificador = 'administrador'
        administrador.save()

    #Adiciona o usuário ao grupo administrador -----------------------
        nomeGrupo = administrador.identificador
        grupo, _ = Group.objects.get_or_create(name='Administradores')
        user_administrador.groups.add(grupo)
        print("Administrador promovido a administrador:", administrador.nome)
    #-----------------------------------------------------------------
        print("Administrador criado:", administrador.id)

        tornarAdmin(request, user_administrador.username)
        print("Administrador salvo:", administrador.id)

        return redirect('indexAdm')
    return render(request, 'administrador/cadastrarAdminForm.html', {'form_user': form_user, 'form': form})

#tornar o usuário um administrador
def tornarAdmin(request, userName): 
    administrador = get_object_or_404(User, username = userName) 
    if administrador.is_superuser: 
        messages.error(request, "Você já é um Administrador") 
        
    else: 
        administrador.is_superuser = True #Transforma o administrador em superUsuário 
        administrador.is_staff = True #Permite que o usuário acesse o painel de administração do django 
        administrador.save() 
        # messages.success(request, "Usuário promovido a administrador") 
    
    return redirect('indexAdm')

# ver perfil do usuário logado
def verPerfil(request, username):
    usuarioAdmin = get_object_or_404(Administrador, user__username=username)
    userUsuario = usuarioAdmin.user

    return render(request, 'administrador/verPerfil_Adm.html', {'userUsuario': userUsuario, 'usuarioAdmin': usuarioAdmin})

# ver a todos o administradores cadastrados
def verAdministradores (request):
    administradores = Administrador.objects.select_related('user').all()
   
    return render(request, 'administrador/verAdministradores.html', {'administradores' : administradores})

# editar dados do administrador
def editarDadosAdmin(request, username):
    administrador = get_object_or_404(Administrador, user__username=username)
    user = administrador.user
    
    if request.method == 'POST':
        editarUserForm = EditarUserForm(request.POST, instance=user)
        editarAdministradorForm = AdministradorForm(request.POST, instance=administrador)

        if editarUserForm.is_valid() and editarAdministradorForm.is_valid():
            editarUserForm.save()
            editarAdministradorForm.save()
            return redirect('indexAdm')
    
    else:
        editarUserForm = EditarUserForm(instance=user)
        editarAdministradorForm = AdministradorForm(instance=administrador)

    return render(request, 'administrador/cadastrarAdminForm.html', {'editarUserForm' : editarUserForm, 'editarAdministradorForm' : editarAdministradorForm, 'Administrador' : administrador} )

def editarSenha(request, username):
    administrador = get_object_or_404(Administrador, user__username=username)
    user = administrador.user

    if request.method == 'POST':
        formSenha = SenhaForm(user, request.POST)
        if formSenha.is_valid():
            user = formSenha.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Senha alterada com sucesso!")
            return redirect('verPerfilAdmin', username=user.username)
    else:
        formSenha = SenhaForm(user)
    
    return render(request,  'administrador/cadastrarAdminForm.html', {'formSenha': formSenha,})

@login_required
def realizarLogout(request):
    logout(request)
    return redirect('indexSistema')
