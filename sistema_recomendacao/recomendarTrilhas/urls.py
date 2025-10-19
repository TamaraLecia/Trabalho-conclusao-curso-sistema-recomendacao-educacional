from django.urls import path
from . import views



urlpatterns = [
    path('questionario', views.responderQuestionario, name='questionario'),
    path('verTrilhas/', views.lista_trilhas, name='verTrilha'),
    path('addTrilha/', views.criar_trilha_completa, name='addTrilha'),
    path("topico/<int:topico_id>/", views.editar_topico, name="editar_topico"),
    path('verTrilha/<int:trilha_id>/', views.caminhos_trilha, name='verTrilhaCaminho'),
    path('dadosTrilha/<int:trilha_id>/', views.dadosTrilha, name='dadosTrilha'),
    path('editarTrilha/<int:trilha_id>/', views.editarTrilha, name='editarTrilha'),
    path('deletarTrilha/<int:trilha_id>/', views.deletarTrilha, name='deletarTrilha'),
    path('capitulo/<int:capitulo_id>/', views.ver_capitulo, name="verCapitulo"),
    path('capitulo/<int:capitulo_id>/concluir/', views.concluir_capitulo, name='concluir_capitulo'),
    path("novaRecomendacao/<int:trilha_id>/", views.nova_recomendacao, name="novaRecomendacao"),
]