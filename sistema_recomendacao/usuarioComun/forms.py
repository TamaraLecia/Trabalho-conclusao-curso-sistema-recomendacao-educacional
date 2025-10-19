from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioComun

#Formulário para adicionar Administrador
class UsuarioComunForm(forms.ModelForm):
    class Meta:
        model = UsuarioComun
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control py-3 border-dark-subtle bg-transparent text-dark w-70 mb-5','placeholder': 'Informe seu nome'}),
        }