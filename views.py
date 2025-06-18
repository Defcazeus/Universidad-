from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .forms import PersonalForm, HorarioForm, AsistenciaForm, JustificacionForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import CustomUserCreationForm

@login_required
def registrar_personal(request):
    if request.method == 'POST':
        form = PersonalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('personal_exito')
    else:
        form = PersonalForm()
    return render(request, 'controlasis/personal/registrar.html', {'form': form})

def personal_exito(request):
    return render(request, 'controlasis/personal/exito.html')

@login_required
def registrar_horario(request):
    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Horario registrado con éxito.')
            return redirect('registrar_horario')
        else:
            messages.error(request, '❌ Por favor corrige los errores del formulario.')
    else:
        form = HorarioForm()
    
    return render(request, 'controlasis/horario/registrar.html', {'form': form})

def horario_exito(request):
    return render(request, 'controlasis/horario/exito.html')

@login_required
def registrar_asistencia(request):
    if request.method == 'POST':
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('asistencia_exito')
    else:
        form = AsistenciaForm()
    return render(request, 'controlasis/asistencia/registrar.html', {'form': form})

def asistencia_exito(request):
    return render(request, 'controlasis/asistencia/exito.html')

@login_required
def registrar_justificacion(request):
    if request.method == 'POST':
        form = JustificacionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('justificacion_exito')
    else:
        form = JustificacionForm()
    return render(request, 'controlasis/justificacion/registrar.html', {'form': form})

def justificacion_exito(request):
    return render(request, 'controlasis/justificacion/exito.html')

def registro_usuario(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect('home')  
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/registro.html", {"form": form})

@login_required
def vista_principal(request):
    return render(request, 'controlasis/home.html')

def redireccion_login(request):
    return redirect('login')

@login_required
def home(request):
    return render(request, 'controlasis/home.html')