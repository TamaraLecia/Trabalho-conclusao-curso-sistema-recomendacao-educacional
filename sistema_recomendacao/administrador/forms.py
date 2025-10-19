from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from .models import Administrador
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

#Formulário para adicionar Administrador
class AdministradorForm(forms.ModelForm):
    class Meta:
        model = Administrador
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control py-3 border-dark-subtle bg-transparent text-dark w-70 mb-5','placeholder': 'Informe seu nome'}),
        }
