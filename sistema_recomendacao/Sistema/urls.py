from django.urls import path

from . import views


urlpatterns = [
    # path('indexTeste/', views.teste2, name='indexTeste'),
    path("", views.index, name="indexSistema"), #roda da página inicial do sistema
    path("login/", views.login_usuario, name="login"),
    path('login_usuario/', views.login_usuario, name='login_usuario'),
    path('redirecionarParaAdministrador/', views.redirecionarParaAdministrador, name="redirecionarParaAdministrador"),
    path('redirecionarParausuarioComun/', views.redirecionarParausuarioComun, name="redirecionarParausuarioComun"),

]