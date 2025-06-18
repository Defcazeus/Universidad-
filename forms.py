from django import forms
from .models import Personal, Horario, Asistencia, Justificacion
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        fields = ['cedula', 'nombres', 'apellidos', 'movil', 'correo', 'tipo']
        widgets = {
            'cedula': forms.TextInput(attrs={'placeholder': 'Ej: V-12345678'}),
            'nombres': forms.TextInput(attrs={'placeholder': 'Nombres completos'}),
            'apellidos': forms.TextInput(attrs={'placeholder': 'Apellidos completos'}),
            'movil': forms.TextInput(attrs={'placeholder': 'Número de contacto'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} form-control'


class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['personal', 'hora_entrada', 'hora_salida', 'fecha_entrada', 'fecha_salida']
        widgets = {
            'hora_entrada': forms.TimeInput(attrs={'type': 'time'}),
            'hora_salida': forms.TimeInput(attrs={'type': 'time'}),
            'fecha_entrada': forms.DateInput(attrs={'type': 'date'}),
            'fecha_salida': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} form-control'


class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['personal', 'fecha', 'hora', 'estado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} form-control'


class JustificacionForm(forms.ModelForm):
    class Meta:
        model = Justificacion
        fields = ['asistencia', 'motivo', 'documento_soporte', 'estado']
        widgets = {
            'motivo': forms.Textarea(attrs={'placeholder': 'Explique la razón de la justificación', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} form-control'
