from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if request.user.is_authenticated:
            return

        email = sociallogin.account.extra_data.get('email')
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                if not sociallogin.is_existing:
                    sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def is_open_for_signup(self, request, sociallogin):
        return True

    def save_user(self, request, sociallogin, form=None):
        User = get_user_model()

        # Gera um username único baseado no e-mail
        email = sociallogin.account.extra_data.get('email', '')
        base_username = email.split('@')[0] if email else 'user'
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Define o username antes de salvar
        sociallogin.user.username = username

        # Salva o usuário normalmente
        user = super().save_user(request, sociallogin, form)

        # Gera senha aleatória se não tiver senha
        if not user.has_usable_password():
            random_password = User.objects.make_random_password()
            user.set_password(random_password)
            #user.set_password(User.objects.create_user(username='temp').make_random_password())
            user.save()

        # Atribui permissão automaticamente
        try:
            permission = Permission.objects.get(codename='acessar_trilha')
            user.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass

        # Cria perfil de usuário comum se necessário
        if not hasattr(user, 'administrador'):
            from Sistema.signals import criar_usario_comun
            criar_usario_comun(user)

        return user

