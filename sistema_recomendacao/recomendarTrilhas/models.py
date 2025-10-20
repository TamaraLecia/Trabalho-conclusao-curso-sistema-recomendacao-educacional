from django.db import models
from urllib.parse import urlparse, parse_qs
from django.conf import settings
import requests, isodate

# Create your models here.

class Trilha(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        permissions = [
            ("acessar_trilha", "Pode acessar trilhas recomendadas"),
        ]
    
    @property
    def total_capitulos(self):
        return Capitulo.objects.filter(topico__trilha=self).count()


class Topico(models.Model):
    trilha = models.ForeignKey(
        Trilha,
        on_delete=models.CASCADE,
        related_name="topicos"
    )
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)

    NIVEL_CHOICES = [
        ("iniciante", "Iniciante"),
        ("intermediario", "Intermediário"),
        ("avancado", "Avançado"),
    ]

    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        default="iniciante"
    )

    def __str__(self):
        return f"{self.trilha.nome} - {self.nome}"


class Capitulo(models.Model):
    NIVEL_CHOICES = [
        ("iniciante", "Iniciante"),
        ("intermediario", "Intermediário"),
        ("avancado", "Avançado"),
    ]

    topico = models.ForeignKey(
        Topico,
        on_delete=models.CASCADE,
        related_name="capitulos"
    )
    nome = models.CharField(max_length=200)
    link_video = models.URLField()
    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        default="iniciante"
    )
    ordem = models.PositiveIntegerField(default=0) #ordem dentro do tópico
    duracao_horas_video = models.FloatField(default=0, blank=True)
    
    def __str__(self):
        return f"{self.topico.nome} - {self.nome}"
    
    @property
    def youtube_id(self):
        url_data = urlparse(self.link_video)
        if url_data.hostname in ["www.youtube.com", "youtube.com"]:
            return parse_qs(url_data.query).get("v", [None])[0]
        elif url_data.hostname == "youtu.be":
            return url_data.path[1:]
        return None
    
    @property
    def youtube_embed_url(self):
        if self.youtube_id:
            return f"https://www.youtube.com/embed/{self.youtube_id}"
        return None
    
    def atualizar_duracao(self, api_key: str | None = None):
        api_key = api_key or settings.YOUTUBE_API_KEY
        if not api_key or not self.youtube_id:
            return None
        url = (
            f"https://www.googleapis.com/youtube/v3/videos"
            f"?id={self.youtube_id}&part=contentDetails&key={api_key}"
        )
        try:
            resposta = requests.get(url, timeout=10)
            resposta.raise_for_status()
            data = resposta.json()
        except requests.RequestException:
            return None
        
        items = data.get("items")
        if items:
            duration_iso = items[0]["contentDetails"]["duration"]
            duration = isodate.parse_duration(duration_iso)
            self.duracao_horas_video = duration.total_seconds() / 3600
            return self.duracao_horas_video
        return None
    
    def save(self, *args, **kwargs):
        if self.pk:
            old = Capitulo.objects.filter(pk=self.pk).only("link_video").first()
            if old and old.link_video != self.link_video:
                self.atualizar_duracao()
        else:
            self.atualizar_duracao()
        super().save(*args, **kwargs)
    
class ProgressoCapitulo(models.Model):
    usuario = models.ForeignKey("usuarioComun.UsuarioComun", on_delete=models.CASCADE)
    capitulo = models.ForeignKey("recomendarTrilhas.Capitulo", on_delete=models.CASCADE)
    concluido = models.BooleanField(default=False)
    atualizado_em = models.DateField(auto_now=True)
    pontuacao = models.IntegerField(default=0)

    class Meta:
        unique_together = ("usuario", "capitulo")

    def __str__(self):
        return f"{self.usuario} - {self.capitulo} - {'✔' if self.concluido else '✘'}"
    


    
    
