from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Create your views here.
def index(request):
    return render(request, 'index.html')

# def teste2(request):
#     return render(request, 'index.html')

# Create your views here.
def login_usuario(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        usuario = form.get_user()
        login(request, usuario)

        if hasattr(usuario, 'usuariocomun'):
            if usuario.usuariocomun.identificador == 'usuarioComun':
                return redirect('redirecionarParausuarioComun')
        
        elif hasattr(usuario, 'administrador'):
            if usuario.administrador.identificador == 'administrador':
                return redirect('redirecionarParaAdministrador')
        
        else:
            return redirect('indexSistema')

    return render(request, 'registration/login.html', {'loginForm': form})

@login_required
def redireciona_pos_login(request):
    usuario = request.user

    if hasattr(usuario, 'administrador'):
        return redirect('redirecionarParaAdministrador')
    elif hasattr(usuario, 'usuariocomun'):
        return redirect('redirecionarParausuarioComun')
    else:
        messages.error(request, "Seu perfil não está configurado corretamente.")
        return redirect('indexSistema')



#Redireciona para a pagina de Administrador 
def redirecionarParaAdministrador(request):
    return redirect(reverse('indexAdm')) 
        
#Redireciona para a pagina de Cliente 
def redirecionarParausuarioComun(request): 
    return redirect(reverse('indexUsuarioComun'))