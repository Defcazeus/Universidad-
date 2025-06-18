from django.db import models

class Personal(models.Model):
    TIPO_CHOICES = [
        ('obrero', 'Obrero'),
        ('administrativo', 'Administrativo'),
        ('vigilante', 'Vigilante'),
    ]

    cedula = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    movil = models.CharField(max_length=15)
    correo = models.EmailField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Horario(models.Model):
    personal = models.ForeignKey(Personal, on_delete=models.CASCADE)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()

    def __str__(self):
        return f"Horario de {self.personal}"


class Asistencia(models.Model):
    personal = models.ForeignKey(Personal, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    
    ESTADOS = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('justificado', 'Justificado'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADOS, default='presente')

    def __str__(self):
        return f"{self.personal} - {self.fecha} - {self.estado}"

class Justificacion(models.Model):
    asistencia = models.OneToOneField(Asistencia, on_delete=models.CASCADE)
    motivo = models.TextField()
    documento_soporte = models.ImageField(upload_to='justificaciones/', blank=True, null=True)
    
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar automáticamente el estado de la asistencia si la justificación es aprobada
        if self.estado == 'aprobado':
            self.asistencia.estado = 'justificado'
            self.asistencia.save()