from allauth.account.signals import user_signed_up, user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import Group
from usuarioComun.models import UsuarioComun
from administrador.models import Administrador

def criar_usario_comun(user):
    """
    Decide se o usuário logado é Administrador ou UsuarioComun.
    """
    # Se já existe um Administrador vinculado, não cria o UsuarioComun
    if Administrador.objects.filter(user=user).exists():
        return "administrador"
    
    # Se já existe um Administrador vinculado, não cria o UsuarioComun
    if UsuarioComun.objects.filter(user=user).exists():
        return "usuarioComun"
    
    # Caso contrário, garante que exista um UsuarioComun
    usuario_comun, created = UsuarioComun.objects.get_or_create(
        user=user,
        defaults={
            "nome": user.first_name or user.username,
            "identificador": "usuarioComun"
        }
    )

    # Adiciona ao grupo de UsuarioComun
    grupo, _ = Group.objects.get_or_create(name="UsuarioComun")
    user.groups.add(grupo)
    user.save()

    return  "usuarioComun"

@receiver(user_signed_up)
def criar_usuario_comun_no_signup(sender, request, user, **kwargs):
    criar_usario_comun(user)

@receiver(user_logged_in)
def criar_usuario_comun_no_login(sender, request, user, **kwargs):
    criar_usario_comun(user)

# def criar_usario_comun(user):
#     """
#     Sempre que alguém entrar pela primeira vez com Google,
#     cria um UsuarioComun por padrão.
#     """

#     usuario_comun, created = UsuarioComun.objects.get_or_create(
#         user=user,
#         defaults={
#         "nome": user.first_name or user.username,
#         "identificador": "usuarioComun"
#         }
#     )

#     # Adicona o usuário logado ao grupo UsuarioComun
#     grupo, _ = Group.objects.get_or_create(name="UsuarioComun")
#     user.groups.add(grupo)
#     user.save()
#     return usuario_comun

# @receiver(user_signed_up)
# def criar_usuario_comun_no_signup(sender, request, user, **kwargs):
#     criar_usario_comun(user)

# @receiver(user_logged_in)
# def criar_usuario_comun_no_login(sender, request, user, **kwargs):
#     criar_usario_comun(user)