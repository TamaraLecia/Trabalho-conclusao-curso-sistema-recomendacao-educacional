from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None):
        User = get_user_model()
        try:
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).first()
            if user and user.check_password(password) and user.is_active:
                return user
        except User.DoesNotExist:
            return None
        
    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None