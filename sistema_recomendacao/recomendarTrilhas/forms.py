from django import forms
from django.forms import inlineformset_factory
from .models import Trilha, Topico, Capitulo

class TrilhaForm(forms.ModelForm):
    class Meta:
        model = Trilha
        fields = ["nome", "descricao"]
        labels = {
            "nome": "Nome da trilha",
            "descricao": "Descrição da Trilha",
        }
        widgets = {
            "nome": forms.TextInput(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Informe o nome da trilha'}),
            "descricao": forms.Textarea(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Descreva a trilha' }),
        }

class TopicoForm(forms.ModelForm):
    class Meta:
        model = Topico
        fields = ["nome", "descricao", "nivel"]
        labels = {
            "nome": "Nome do tópico",
            "descricao": "Descrição do tópico",
            "nivel" : "Nível do tópico",
        }
        widgets = {
            "nome": forms.TextInput(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Informe o nome da tópico'}),
            "descricao": forms.Textarea(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Descreva o tópico'}),
            "nivel": forms.Select(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Selecione o nível do tópico'}),
        }

class CapituloForm(forms.ModelForm):
    class Meta:
        model = Capitulo
        fields = ["nome", "link_video", "nivel"]
        labels = {
            "nome": "Nome do capítulo",
            "descricao": "Descrição do capítulo",
            "nivel" : "Nível do capítulo",
        }
        widgets = {
            "nome": forms.TextInput(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Informe o nome da capítulo'}),
            "link_video": forms.URLInput(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Cole o link do vídeo referente ao capítulo'}),
            "nivel": forms.Select(attrs={'class': 'form-control py-3 border-dark-subtle  bg-transparent text-dark w-70', 'placeholder': 'Informe o nível do capítulo'}),
        }

TopicoFormSet = inlineformset_factory(
    Trilha, Topico,
    form=TopicoForm,
    extra=0,
    can_delete=False
)

CapituloFormSet = inlineformset_factory(
    Topico, Capitulo,
    form=CapituloForm,
    extra=0,
    can_delete=False
)
