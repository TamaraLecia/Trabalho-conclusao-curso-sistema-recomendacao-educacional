from django.urls import path

from . import views


urlpatterns = [
    # path('indexTeste/', views.teste2, name='indexTeste'),
    path("indexSistema/", views.index, name="indexSistema"),
    path("login/", views.login_usuario, name="login"),
    path('login_usuario/', views.login_usuario, name='login_usuario'),
    path('redirecionarParaAdministrador/', views.redirecionarParaAdministrador, name="redirecionarParaAdministrador"),
    path('redirecionarParausuarioComun/', views.redirecionarParausuarioComun, name="redirecionarParausuarioComun"),

]