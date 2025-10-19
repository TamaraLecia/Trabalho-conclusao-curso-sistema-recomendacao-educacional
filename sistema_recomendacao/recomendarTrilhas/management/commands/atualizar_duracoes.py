from django.core.management.base import BaseCommand
from django.conf import settings
from recomendarTrilhas.models import Capitulo

class Command(BaseCommand):
    help = "Atualiza a duração dos vídeos já cadastrados"

    def handle(self, *args, **options):
        api_key = settings.YOUTUBE_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR("YOUTUBE_API_KEY não configurada"))
            return
        
        for capitulo in Capitulo.objects.all():
            horas = capitulo.atualizar_duracao(api_key)
            capitulo.save(update_fields=["duracao_horas_video"])
            if horas is not None:
                self.stdout.write(self.style.SUCCESS(
                    f"{capitulo.nome} atualizado: {horas:.2f} horas"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"{capitulo.nome} não pôde ser atualizado"
                ))