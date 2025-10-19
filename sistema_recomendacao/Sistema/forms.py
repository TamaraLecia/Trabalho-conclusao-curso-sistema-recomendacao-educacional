from django.forms import ModelForm, fields
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django import forms
from django.utils.safestring import mark_safe

#Criar usuário 
class AdicionarUsuarioForm(UserCreationForm): 
    class Meta: 
        model = User 
        fields = ['username','email', 'password1', 'password2']

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control py-3 border-dark-subtle bg-transparent text-dark w-70 mb-5',
            'placeholder': 'nome de usuário'
            }),
            
            'email': forms.EmailInput(attrs={
                'class': 'form-control py-3  border-dark-subtle bg-transparent text-dark w-70 mb-5',
            'placeholder': 'endereço de email'
            }),
        }


        help_texts = {
            'username': 'Use apenas letras, números e os símbolos @/./+/-/_',
            'email': 'Informe um email válido para contato.',
        }


        #Adiciona estilos nos campos da senha
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Labels personalizados
        self.fields['username'].label = 'Nome de usuário'
        self.fields['email'].label = 'Endereço de email'
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Senha de confirmação'

        # Campo password1
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control py-3 border-dark-subtle bg-transparent text-dark w-70 mb-5',
            'placeholder': 'Senha'
        })
        self.fields['password1'].help_text = mark_safe(
            '<small class="form-text text-dark ">'
            ' • Use uma senha forte com pelo menos 8 caracteres.<br>'
            ' • Sua senha não pode ser totalmente numérica.'
            '</small>'
        )

        # Campo password2
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control py-3 border-dark-subtle bg-transparent text-dark w-70 mb-5',
            'placeholder': 'Confirme a senha'
        })
        self.fields['password2'].help_text = mark_safe(
            '<small class="form-text text-dark">'
            ' • Digite a mesma senha novamente para confirmação.'
            '</small>'
        )

        # Ajusta help_text de username e email também
        self.fields['username'].help_text = mark_safe(
            '<small class="form-text text-dark">'
            ' • Use apenas letras, números e os símbolos @/./+/-/_'
            '</small>'
        )
        self.fields['email'].help_text = mark_safe(
            '<small class="form-text text-dark">'
            ' • Informe um email válido para contato.'
            '</small>'
        )

class EditarUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

        widgets = {
                'email': forms.EmailInput(attrs={
                    'class': 'form-control py-3  border-dark-subtle bg-transparent text-dark w-70 mb-5',
                'placeholder': 'endereço de email'
                }),
            }


        help_texts = {
                'email': 'Informe um email válido para contato.',
            }


    #Adiciona estilos nos campos da senha
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Labels personalizados
        self.fields['email'].label = 'Endereço de email'
        # Ajusta help_text do email também
        self.fields['email'].help_text = mark_safe(
        '<small class="form-text text-dark">'
            ' • Informe um email válido para contato.'
        '</small>'
    )
        

class SenhaForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']
        
    new_password1 = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control py-3 border-dark-subtle bg-transparent text-dark w-70 mb-5',
            'placeholder': 'Informe uma nova senha'})
    )

    new_password2 = forms.CharField(
        label='Senha de confirmação',
        widget=forms.PasswordInput(attrs={'class': 'form-control py-3 border-dark-subtle bg-transparent text-dark w-70 mb-5',
            'placeholder': 'Confirme a sua senha'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_password1'].help_text = mark_safe(
            '<small class="form-text text-dark ">'
            ' • Use uma senha forte com pelo menos 8 caracteres.<br>'
            ' • Sua senha não pode ser totalmente numérica.'
            '</small>'
        )

        self.fields['new_password2'].help_text = mark_safe(
            '<small class="form-text text-dark">'
            ' • Digite a mesma senha novamente para confirmação.'
            '</small>'
        )

    def clean(self):
        cleaned_data = super(forms.Form, self).clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            self.add_error("new_password2", "As senhas precisam ser iguais")
        return cleaned_data
