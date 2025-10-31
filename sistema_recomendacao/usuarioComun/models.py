from django.db import models
from django.contrib.auth.models import User
from recomendarTrilhas.models import Trilha

# Create your models here.
class UsuarioComun(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    identificador = models.CharField(max_length=20, default='usuarioComun')
    trilhaUser = models.ManyToManyField(Trilha, blank=True, related_name="usuarios")

    def __str__(self):
        return self.nome
    
class NivelConhecimento(models.Model):
    usuario = models.ForeignKey("UsuarioComun", on_delete=models.CASCADE)
    conteudo = models.CharField(max_length=100)
    nivel = models.IntegerField() # 0  a 100

    def __str__(self):
        return f"{self.usuario} - {self.conteudo}: {self.nivel}%"