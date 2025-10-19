from . import views
from django.urls import path


urlpatterns = [
   path("index/", views.index, name="indexUsuarioComun"),
   path("addUsuario/", views.add_usuario, name="addUsuario"),
   path("minhasTrilhas/", views.minhas_trilhas, name="minhasTrilhas"),
   path("minhasTrilhasConcluidas/", views.trilhas_concluidas, name="minhasTrilhasConcluidas"),
   path("excluirContaUsuario/", views.excluirConta, name="excluirContaUsuario"),
   path('verPerfil/<str:username>/', views.verPerfil, name='verPerfil'),
   path('editarSenhaUsuario/<str:username>/', views.editarSenhaUsuario, name='editarSenhaUsuario'),
   path('editarUsuarioComun/<str:username>/', views.editarDadosUsuarioComun, name='editarUsuarioComun'),
   path("realizarlogout/", views.realizarLogout, name="realizarlogout"),
]
