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
        user = super().save_user(request, sociallogin, form)

        if not user.has_usable_password():
            # gerar senha aleátoria para o usuário que fizer login com o google
            user.set_password(User.objects.create_user(username='temp').make_random_password())
            user.save()
        # Atribuir permissão automaticamente
        try:
            permission = Permission.objects.get(codename='acessar_trilha')
            user.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass

        if not hasattr(user, 'administrador'):
            from Sistema.signals import criar_usario_comun
            criar_usario_comun(user)

        return user
