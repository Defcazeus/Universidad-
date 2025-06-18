from django.contrib import admin
from .models import Personal, Horario, Asistencia, Justificacion

admin.site.register(Personal)
admin.site.register(Horario)
admin.site.register(Asistencia)
admin.site.register(Justificacion)
