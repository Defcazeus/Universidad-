from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),

    # Registro de usuario
    path('registro/', views.registro_usuario, name='registro'),

    # Formularios de datos
    path('personal/registrar/', views.registrar_personal, name='registrar_personal'),
    path('personal/exito/', views.personal_exito, name='personal_exito'),

    path('horario/registrar/', views.registrar_horario, name='registrar_horario'),
    path('horario/exito/', views.horario_exito, name='horario_exito'),

    path('asistencia/registrar/', views.registrar_asistencia, name='registrar_asistencia'),
    path('asistencia/exito/', views.asistencia_exito, name='asistencia_exito'),

    path('justificacion/registrar/', views.registrar_justificacion, name='registrar_justificacion'),
    path('justificacion/exito/', views.justificacion_exito, name='justificacion_exito'),

    # Login
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
]
