from .import views
from django.urls import path


urlpatterns = [
    path("index/", views.index, name="indexAdm"),
    path("add/", views.add_administrador, name="add"),
    path('verPerfilAdmin/<str:username>/', views.verPerfil, name='verPerfilAdmin'),
    path('verAdministradores/', views.verAdministradores, name='verAdministradores'),
    path('editarAdmin/<str:username>/', views.editarDadosAdmin, name='editarAdmin'),
    path('editarSenha/<str:username>/', views.editarSenha, name='editarSenha'),
    path("realizarlogout/", views.realizarLogout, name="realizarlogout"),
    
]