from codecs import escape_decode
import json
from decimal import Decimal
from lzma import is_check_supported
from django.core.serializers.json import DjangoJSONEncoder
from core.models import Usuario,Vehiculo,Cita, CatServicio,MovimientosProducto, Producto, CatProducto, Carrito, CarritoDetalle
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistroUsuarioForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.dateparse import parse_datetime
import uuid
from django.shortcuts import get_object_or_404
import json
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Usuario
from .forms import ClienteAdminForm
from django.contrib.auth.decorators import login_required
from .models import Transaccion

User = get_user_model()
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Notificacion

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notificacion

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Notificacion

@login_required
def obtener_notificaciones_ajax(request):

    """Devuelve únicamente las notificaciones NO leídas del usuario con sus enlaces seguros por nombre de ruta."""
    notificaciones = request.user.notificaciones.filter(leido=False).order_by('-fecha_creacion')[:15]


    """Devuelve las últimas 10 notificaciones del usuario en JSON"""
    notificaciones = request.user.notificaciones.all()[:10]


    data = []
    for n in notificaciones:
        url_destino = "#"

        if n.objeto_destino:
            nombre_modelo = n.objeto_destino._meta.model_name

            try:
                # 1. Si la notificación apunta a un Pedido (usa UUID: cod_pedido)
                if nombre_modelo == 'pedido':
                    # Verificamos si es para la vista de cliente o de admin según el rol o la ruta
                    if request.user.is_staff:
                        url_destino = reverse('pedido_editar', args=[n.objeto_destino.cod_pedido])
                    else:
                        url_destino = reverse('pedido_clientes') # O tu vista de detalle de cliente

                # 2. Si la notificación apunta a una Factura (usa UUID: id_factura)
                elif nombre_modelo == 'factura':
                    if request.user.is_staff:
                        url_destino = reverse('factura_detalle_ajax', args=[n.objeto_destino.pk])
                    else:
                        url_destino = reverse('factura_list') # O tu vista de "mis facturas" del cliente

                # 3. Si la notificación apunta a una Cita (usa UUID: cod_cita o int según tu modelo)
                elif nombre_modelo == 'cita':
                    if request.user.is_staff:
                        url_destino = reverse('cita_editar', args=[n.objeto_destino.pk])
                    else:
                        url_destino = reverse('agenda_citas_list')

            except Exception as e:
                # Si ocurre cualquier error al resolver la URL, mantiene '#'
                url_destino = "#"

        data.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'fecha': n.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'tipo': n.tipo_notificacion,
            'url': url_destino
        })


    return JsonResponse({
        'status': 'success',
        'notificaciones': data,
        'total_no_leidas': notificaciones.count()
    })



    return JsonResponse({'status': 'success', 'notificaciones': data})



@login_required
@require_POST
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación específica o todas como leídas"""
    if notificacion_id == 0:
        request.user.notificaciones.filter(leido=False).update(leido=True)
    else:
        request.user.notificaciones.filter(id=notificacion_id).update(leido=True)

    return JsonResponse({'status': 'success'})





import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Usuario


import random
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario, RecuperarContrasenna

def solicitar_codigo_recuperacion(request):
    if request.method == "POST":
        correo = request.POST.get('correo')
        try:
            usuario = Usuario.objects.get(correo=correo)

            # Generar código aleatorio de 6 dígitos
            codigo = str(random.randint(100000, 999999))
            expiracion = timezone.now() + timedelta(minutes=15)

            # Guardarlo en tu modelo RecuperarContrasenna
            # (Limpiamos códigos anteriores de este usuario si los hay)
            RecuperarContrasenna.objects.filter(cedula_usuario=usuario).delete()
            RecuperarContrasenna.objects.create(
                cedula_usuario=usuario,
                token=codigo,
                fecha_expiracion=expiracion,
                usado=False
            )

            # Enviar el correo con el código
            send_mail(
                subject='Código de Verificación - Serviautomotriz Fernández',
                message=f'Hola {usuario.nombre}, tu código de recuperación es: {codigo}. Es válido por 15 minutos.',
                from_email=settings.DEFAULT_FROM_EMAIL, # Usa automáticamente el correo de settings
                recipient_list=[correo],
                fail_silently=False,
            )

            # Guardamos el correo en sesión para el siguiente paso
            request.session['correo_recuperacion'] = correo
            return redirect('verificar_codigo_reset')

        except Usuario.DoesNotExist:
            messages.error(request, "El correo no está registrado.")

    return render(request, 'password_reset.html')


@csrf_exempt



def validar_correo_recuperacion(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            correo = data.get('correo', '').strip()
            # Validamos usando tu campo 'correo'
            existe = Usuario.objects.filter(correo=correo).exists()
            return JsonResponse({'existe': existe})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def validar_cedula_recuperacion(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            correo = data.get('correo', '').strip()
            cedula = data.get('cedula_usuario', '').strip().upper() # Asegúrate de que coincida con tu formato (V12345678)

            # Validamos que el correo y la cédula pertenezcan al mismo usuario
            coincide = Usuario.objects.filter(correo=correo, cedula_usuario=cedula).exists()
            return JsonResponse({'coincide': coincide})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def verificar_codigo_reset(request):
    correo = request.session.get('correo_recuperacion')
    if not correo:
        return redirect('reset_password')

    if request.method == "POST":
        codigo_ingresado = request.POST.get('codigo', '').strip()
        try:
            usuario = Usuario.objects.get(correo=correo)
            recuperacion = RecuperarContrasenna.objects.get(
                cedula_usuario=usuario,
                token=codigo_ingresado,
                usado=False
            )

            # Validar si expiró
            if recuperacion.fecha_expiracion < timezone.now():
                messages.error(request, "El código ha expirado. Solicita uno nuevo.")
            else:
                # Código válido: guardamos en sesión que ya pasó la verificación
                request.session['puede_cambiar_pass'] = True
                return redirect('cambiar_password_final')

        except (Usuario.DoesNotExist, RecuperarContrasenna.DoesNotExist):
            messages.error(request, "Código inválido o incorrecto.")

    return render(request, 'verificar_codigo.html')

from django.contrib.auth.forms import SetPasswordForm

def cambiar_password_final(request):
    correo = request.session.get('correo_recuperacion')
    if not request.session.get('puede_cambiar_pass') or not correo:
        return redirect('reset_password')

    usuario = Usuario.objects.get(correo=correo)

    if request.method == "POST":
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            # Limpiamos las variables de sesión
            del request.session['correo_recuperacion']
            del request.session['puede_cambiar_pass']

            # También marcamos el token como usado
            RecuperarContrasenna.objects.filter(cedula_usuario=usuario).update(usado=True)

            messages.success(request, "Contraseña actualizada con éxito.")
            return redirect('login')
    else:
        form = SetPasswordForm(usuario)

    return render(request, 'password_reset_form.html', {'form': form})

def home(request):


    return render(request, "core/home.html")


def inicio_sesion(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        correo = (request.POST.get('correo') or '').strip()
        password = (request.POST.get('password') or '').strip()
        remember = request.POST.get('remember_me')

        user = authenticate(request, correo=correo, password=password)
        if user is not None:
            messages.success(request, "¡Éxito! Has iniciado sesión correctamente en el taller.")

            login(request, user)
            try:
                if remember:
                    expiry = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)
                    request.session.set_expiry(int(expiry))
                    request.session.save()
                else:
                    request.session.set_expiry(0)
                    request.session.save()
            except Exception:
                pass
            return redirect('home')
        else:
            return render(request, 'core/login.html', {'form': {}, 'errors': ['Correo o contraseña incorrectos.']})

    return render(request, 'core/login.html', {})


def registro(request):
    admin_existe = Usuario.objects.filter(is_superuser=True).exists()

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            # Si no existe ningún administrador, se crea como superusuario
            if not admin_existe:
                Usuario.objects.create_superuser(
                    cedula_usuario=data['cedula_usuario'],
                    correo=data['correo'],
                    nombre=data['nombre'],
                    apellido=data['apellido'],
                    telefono=data['telefono'],
                    password=data['password1']
                )
                messages.success(request, "Se ha registrado el primer usuario como Administrador.")
            else:
                Usuario.objects.create_user(
                    cedula_usuario=data['cedula_usuario'],
                    correo=data['correo'],
                    nombre=data['nombre'],
                    apellido=data['apellido'],
                    telefono=data['telefono'],
                    password=data['password1']
                )
                messages.success(request, "El usuario se ha registrado correctamente.")

            return redirect('login')
        else:
            print(form.errors)
    else:
        form = RegistroUsuarioForm()

    return render(request, 'core/registro.html', {
        'form': form,
        "admin_existe": admin_existe
    })

from datetime import datetime
from decimal import Decimal
from django.db.models import Sum, Q, F
from django.utils import timezone
from django.shortcuts import render
from .models import Cita, ServicioTaller, Producto, Factura, Transaccion


def home_admin(request):
    hoy = timezone.now().date()
    mes_actual = hoy.month
    anio_actual = hoy.year

    # 1. Citas Pendientes (Usando 'estado_cita' de tu modelo Cita)
    total_citas_pendientes = Cita.objects.filter(
        Q(estado_cita__iexact='PENDIENTE') | Q(estado_cita__iexact='Programada')
    ).count()

    # 2. En Fosa Operativa (Usando 'estado_orden' y el modelo ServicioTaller)
    total_ordenes_activas = ServicioTaller.objects.filter(
        estado_orden__in=['En Proceso', 'En Reparacion', 'Iniciado']
    ).count()

    # 3. Stock Crítico (Productos donde stock_actual <= stock_minimo)
    stock_bajo_alertas = Producto.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).count()

    # 4. Caja del Mes (Suma de transacciones aprobadas o total pagado en facturas del mes actual)
    ingresos_mes = Factura.objects.filter(
        fecha_emision__month=mes_actual,
        fecha_emision__year=anio_actual
    ).aggregate(total=Sum('total_pagado'))['total'] or Decimal('0.00')

    # 5. Distribución de Carga en Taller (Basado en 'estado_orden' de ServicioTaller)
    ordenes_esperando_insumos = ServicioTaller.objects.filter(estado_orden__icontains='Insumos').count()
    ordenes_en_reparacion = ServicioTaller.objects.filter(estado_orden__in=['En Reparacion', 'En Proceso']).count()
    ordenes_listos = ServicioTaller.objects.filter(estado_orden__in=['Listo', 'Para Entrega', 'Completado']).count()

    context = {
        'total_citas_pendientes': total_citas_pendientes,
        'total_ordenes_activas': total_ordenes_activas,
        'stock_bajo_alertas': stock_bajo_alertas,
        'ingresos_mes': f"{ingresos_mes:,.2f}",
        'ordenes_esperando_insumos': ordenes_esperando_insumos,
        'ordenes_en_reparacion': ordenes_en_reparacion,
        'ordenes_listos': ordenes_listos,
    }

    return render(request, 'admin/home_admin.html', context)


def home_user(request):

    return render(request, 'usuario/home_usuario.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .forms import VehiculoForm
from .models import Usuario, Vehiculo


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Vehiculo
from .forms import VehiculoForm

@login_required
def vehiculos_user(request):
    if request.method == "POST":
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            # Asignación segura desde el servidor
            vehiculo.cedula_usuario = request.user
            vehiculo.save()
            return redirect("vehiculos_user")
    else:
        form = VehiculoForm()

    # Filtrar solo los vehículos del usuario con la sesión activa
    vehiculos = (
        Vehiculo.objects.filter(cedula_usuario=request.user)
        .select_related("cedula_usuario")
        .order_by("-placa")
    )

    return render(
        request,
        "usuario/vehiculos_list_user/vehiculos_list_user.html",
        {
            "vehiculos": vehiculos,
            "form": form,
            # 'clientes' se elimina por ser innecesario
        },
    )






from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def api_historial_vehiculo(request, placa):
    vehiculo = get_object_or_404(Vehiculo, placa=placa)
    fichas = HistorialVehiculo.objects.filter(placa=vehiculo).order_by('-fecha_registro')

    data_fichas = []
    for f in fichas:
        data_fichas.append({
            'id_historial_vehiculo': f.id_historial_vehiculo,
            'cod_cita': f.cod_cita.cod_cita if f.cod_cita else 'N/A',
            'kilometraje_ingreso': f.kilometraje_ingreso,
            'diagnostico_final': f.diagnostico_final,
            'reparaciones_realizadas': f.reparaciones_realizadas,
            'observaciones_recomendadas': f.observaciones_recomendadas,
            'fecha_registro': f.fecha_registro.strftime('%d/%m/%Y') if f.fecha_registro else ''
        })

    return JsonResponse({
        'vehiculo': {
            'placa': vehiculo.placa,
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'anno': vehiculo.anno,
        },
        'fichas': data_fichas
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.dateparse import parse_datetime

# Importación de modelos usando CatServicio según tu models.py
from .models import Cita, Vehiculo, CatServicio


@login_required
def agenda_citas_list_user(request):
    """
    Lista las citas del usuario y pasa vehículos y tipos de servicio (CatServicio) al template.
    """

    citas = Cita.objects.filter(placa__cedula_usuario=request.user).order_by('-fecha_entrada')
    vehiculos = Vehiculo.objects.filter(cedula_usuario=request.user)

    # Obtenemos las categorías de servicio registradas
    cat_servicios = CatServicio.objects.all()

    context = {
        'citas': citas,
        'vehiculos': vehiculos,
        'cat_servicios': cat_servicios,
    }
    # Renderiza la plantilla según tu estructura de carpetas
    return render(request, 'usuario/cita/citas.html', context)

@login_required
@require_POST
def agenda_cita_crear_user(request):
    """
    Procesa el formulario POST para crear una cita desde el panel de usuario,
    asignando automáticamente la cédula del usuario autenticado.
    """
    placa_id = request.POST.get('placa')
    id_cat_servicio = request.POST.get('id_cat_servicio')
    fecha_entrada_raw = request.POST.get('fecha_entrada')
    motivo_ingreso = request.POST.get('motivo_ingreso', '')

    try:
        vehiculo = get_object_or_404(Vehiculo, pk=placa_id)
        servicio = get_object_or_404(CatServicio, pk=id_cat_servicio)

        fecha_entrada = parse_datetime(fecha_entrada_raw) if fecha_entrada_raw else None

        if not fecha_entrada:
            messages.error(request, "La fecha y hora especificada no es válida.")
            return redirect('agenda_citas_list')

        # Obtención de la cédula del usuario autenticado
        usuario_cedula = getattr(request.user, 'cedula', None) or request.user

        Cita.objects.create(
            placa=vehiculo,
            id_cat_servicio=servicio,
            fecha_entrada=fecha_entrada,
            motivo_ingreso=motivo_ingreso,
            estado_cita='Pendiente',
            cedula_usuario=usuario_cedula  # Se asigna la cédula/usuario del request
        )
        messages.success(request, "La cita se ha programado exitosamente.")

    except Exception as e:
        messages.error(request, f"Error al agendar la cita: {str(e)}")

    return redirect('agenda_citas_list')

@login_required
def agenda_cita_detalle_api(request, cod_cita):
    """
    Retorna la información en JSON para los modales AJAX.
    """
    cita = get_object_or_404(Cita, pk=cod_cita)
    fecha_iso = cita.fecha_entrada.strftime('%Y-%m-%dT%H:%M') if cita.fecha_entrada else ''

    data = {
        'cod_cita': cita.pk,
        'placa': str(cita.placa.placa) if hasattr(cita.placa, 'placa') else str(cita.placa),
        'vehiculo_info': f"{getattr(cita.placa, 'marca', '')} {getattr(cita.placa, 'modelo', '')}".strip(),
        'id_cat_servicio': getattr(cita.id_cat_servicio, 'pk', None),
        'nom_cat_servicio': str(cita.id_cat_servicio),
        'fecha_entrada': fecha_iso,
        'motivo_ingreso': cita.motivo_ingreso or '',
        'estado_cita': cita.estado_cita
    }
    return JsonResponse({'status': 'success', 'data': data})


@login_required
@require_POST
def agenda_cita_editar(request, cod_cita):
    """
    Actualiza la cita seleccionada.
    """
    cita = get_object_or_404(Cita, pk=cod_cita)

    placa_id = request.POST.get('placa')
    id_cat_servicio = request.POST.get('id_cat_servicio')
    fecha_entrada_raw = request.POST.get('fecha_entrada')
    motivo_ingreso = request.POST.get('motivo_ingreso', '')

    try:
        if placa_id:
            cita.placa = get_object_or_404(Vehiculo, pk=placa_id)
        if id_cat_servicio:
            cita.id_cat_servicio = get_object_or_404(CatServicio, pk=id_cat_servicio)
        if fecha_entrada_raw:
            fecha_parsed = parse_datetime(fecha_entrada_raw)
            if fecha_parsed:
                cita.fecha_entrada = fecha_parsed

        cita.motivo_ingreso = motivo_ingreso
        cita.save()

        messages.success(request, f"La cita #{cod_cita} se actualizó correctamente.")
    except Exception as e:
        messages.error(request, f"Error al actualizar la cita: {str(e)}")

    return redirect('agenda_citas_list')

def menu(request):

    return render(request, "menu/menu.html")











def clientes_list(request):
    clientes = Usuario.objects.filter(is_staff=False).order_by('-cedula_usuario')
    form = ClienteAdminForm()

    # Obtener el nombre del usuario actual de forma segura
    usuario_nombre = request.user.get_full_name() or str(request.user) if request.user.is_authenticated else "Sistema"

    return render(request, 'taller/clientes/clientes_list.html', {
        'clientes': clientes,
        'form': form,
        'usuario_nombre': usuario_nombre,
    })

def cliente_api(request, cedula_usuario):
    cliente = get_object_or_404(Usuario, pk=cedula_usuario)

    # Desglose de Cédula (Ej: "V12345678" -> cod="V-", num="12345678")
    cedula_raw = cliente.cedula_usuario or ''
    match_cedula = re.match(r'^(V|E|J|G|P)(\d+)$', cedula_raw.upper())
    if match_cedula:
        cod_cedula = f"{match_cedula.group(1)}-"
        cedula_num = match_cedula.group(2)
    else:
        cod_cedula = 'V-'
        cedula_num = cedula_raw

    # Desglose de Teléfono (Ej: "04141234567" -> cod="0414", num="1234567")
    tel_raw = cliente.telefono or ''
    if len(tel_raw) >= 11:
        cod_tel = tel_raw[:4]
        num_tel = tel_raw[4:]
    else:
        cod_tel = '0414'
        num_tel = tel_raw

    return JsonResponse({
        'cedula_usuario': cliente.cedula_usuario,
        'cod_cedula': cod_cedula,
        'cedula': cedula_num,
        'nombre': cliente.nombre,
        'apellido': cliente.apellido,
        'cod_tel': cod_tel,
        'num_tel': num_tel,
        'correo': cliente.correo or '',
        'direccion': cliente.direccion or '',
    })

def cliente_crear(request):
    if request.method == 'POST':
        data = request.POST.copy()
        if not data.get('correo'):
            data['correo'] = ''

        form = ClienteAdminForm(data)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Cliente {user.nombre} registrado con éxito. Clave: {user.cedula_usuario}')
            return redirect('clientes_list')
        else:
            # Si falla, volvemos a listar pero pasamos el form con errores y la bandera para reabrir el modal
            clientes = Usuario.objects.filter(is_staff=False).order_by('-cedula_usuario')
            messages.error(request, 'Por favor corrige los errores señalados en el formulario.')
            return render(request, 'taller/clientes/clientes_list.html', {
                'clientes': clientes,
                'form': form,
                'abrir_modal_crear': True  # Banderita para el JavaScript
            })

    return redirect('clientes_list')

def cliente_editar(request, pk):
    cliente = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        data = request.POST.copy()
        if not data.get('correo'):
            data['correo'] = ''

        form = ClienteAdminForm(data, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
        else:
            errors = " | ".join([f"{v[0]}" for k, v in form.errors.items()])
            messages.error(request, f'Error al actualizar: {errors}')

    return redirect('clientes_list')




from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Vehiculo, Usuario
from .forms import VehiculoForm

@login_required
def vehiculos_list(request):
    vehiculos = Vehiculo.objects.select_related('cedula_usuario').all().order_by('-placa')
    clientes = Usuario.objects.filter(is_staff=False).order_by('nombre')
    form = VehiculoForm()

    usuario_nombre = request.user.get_full_name() or str(request.user) if request.user.is_authenticated else "Sistema"

    return render(request, 'taller/vehiculos/vehiculos_list.html', {
        'vehiculos': vehiculos,
        'clientes': clientes,
        'form': form,
        'usuario_nombre': usuario_nombre,
    })


@login_required
def vehiculo_api(request, pk):
    """Retorna la información del vehículo en JSON para consumo de JavaScript."""
    vehiculo = get_object_or_404(Vehiculo.objects.select_related('cedula_usuario'), pk=pk)

    return JsonResponse({
        'placa': vehiculo.placa,
        'marca': vehiculo.marca,
        'modelo': vehiculo.modelo,
        'anno': vehiculo.anno,
        'color': vehiculo.color or '',
        'descripcion': vehiculo.descripcion or '',
        'cedula_usuario': vehiculo.cedula_usuario.cedula_usuario,
        'nombre_propietario': f"{vehiculo.cedula_usuario.nombre} {vehiculo.cedula_usuario.apellido}",
    })


@login_required
def vehiculo_crear(request):
    if request.method == 'POST':
        data = request.POST.copy()

        form = VehiculoForm(data)
        if form.is_valid():
            vehiculo = form.save()
            messages.success(request, f'Vehículo placa {vehiculo.placa} registrado con éxito.')
            return redirect('vehiculos_list')
        else:
            vehiculos = Vehiculo.objects.select_related('cedula_usuario').all().order_by('-placa')
            clientes = Usuario.objects.filter(is_staff=False).order_by('nombre')
            messages.error(request, 'Por favor corrige los errores señalados en el formulario.')

            return render(request, 'taller/vehiculos/vehiculos_list.html', {
                'vehiculos': vehiculos,
                'clientes': clientes,
                'form': form,
                'abrir_modal_crear': True  # Banderita para reabrir el modal en JS si falla
            })

    return redirect('vehiculos_list')


@login_required
def vehiculo_editar(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)

    if request.method == 'POST':
        data = request.POST.copy()

        # En la edición la placa es la Primary Key (Readonly en interfaz)
        data['placa'] = vehiculo.placa

        form = VehiculoForm(data, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vehículo {vehiculo.placa} actualizado correctamente.')
        else:
            errors = " | ".join([f"{v[0]}" for k, v in form.errors.items()])
            messages.error(request, f'Error al actualizar: {errors}')

    return redirect('vehiculos_list')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from .models import CatServicio
from .forms import ServicioForm

@login_required
def servicio_list(request):

    servicios = CatServicio.objects.all().order_by('nombre')
    form = ServicioForm()

    # Obtener el nombre del usuario actual de forma segura
    usuario_nombre = request.user.get_full_name() or str(request.user) if request.user.is_authenticated else "Sistema"

    return render(request, 'taller/catalogo_servicios.html', {
        'servicios': servicios,
        'form': form,
        'usuario_nombre': usuario_nombre,
    })

@login_required
@require_POST
def servicio_crear(request):
    form = ServicioForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f"¡Servicio '{form.cleaned_data['nombre']}' añadido con éxito!")
    else:
        for error in form.non_field_errors():
            messages.error(request, error)
        for field in form:
            for error in field.errors:
                messages.error(request, f"{field.label}: {error}")

    return redirect('servicio_list')

@login_required
@require_POST
def servicio_editar(request, pk):
    servicio = get_object_or_404(CatServicio, pk=pk)
    form = ServicioForm(request.POST, instance=servicio)
    if form.is_valid():
        form.save()
        messages.success(request, f"¡Servicio '{servicio.nombre}' actualizado!")
    else:
        messages.error(request, "Error al actualizar el servicio. Revisa los datos.")
    return redirect('servicio_list')

@login_required
def servicio_api_detalle(request, pk):
    """Endpoint API para cargar o validar datos vía AJAX/Fetch"""
    servicio = get_object_or_404(CatServicio, pk=pk)
    data = {
        'id': servicio.id_cat_servicio,
        'nombre': servicio.nombre,
        'duracion_estimada': servicio.duracion_estimada,
        'precio_base': str(servicio.precio_base),
        'activo': servicio.activo
    }
    return JsonResponse({'success': True, 'data': data})









import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Cita, Vehiculo, CatServicio
from .forms import CitaForm

# --------------------------------------------------------------------------
# 1. RENDERIZADO DE LA LISTA PRINCIPAL
# --------------------------------------------------------------------------
@login_required
def citas_list(request):
    citas = Cita.objects.select_related('placa', 'id_tipo_servicio', 'cedula_usuario').all().order_by('-fecha_entrada')
    vehiculos = Vehiculo.objects.select_related('cedula_usuario').all().order_by('placa')
    servicios_cat = CatServicio.objects.filter(activo=True).order_by('nombre')

    form = CitaForm()

    return render(request, 'taller/citas/citas_list.html', {
        'citas': citas,
        'vehiculos': vehiculos,
        'servicios_cat': servicios_cat,
        'form': form,
    })

# --------------------------------------------------------------------------
# 2. CREAR REGISTRO
# --------------------------------------------------------------------------
@login_required
def cita_crear(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cod_cita = uuid.uuid4()
            cita.estado_cita = 'Pendiente'

            # Asignación del usuario operador activo
            # (Ajusta 'cedula' según la propiedad/relación exacta de tu User)
            cita.cedula_usuario = getattr(request.user, 'cedula', None) or request.user

            cita.save()
            messages.success(request, f"¡Cita agendada exitosamente!")
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
        return redirect('citas_list')

    return redirect('citas_list')

# --------------------------------------------------------------------------
# 3. EDITAR REGISTRO
# --------------------------------------------------------------------------
@login_required
def cita_editar(request, cod_cita):
    cita = get_object_or_404(Cita, cod_cita=cod_cita)
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cita #{str(cita.cod_cita)[:8]} actualizada con éxito.")
        else:
            messages.error(request, "Error al actualizar los datos de la cita. Verifique el formulario.")

    return redirect('citas_list')

# --------------------------------------------------------------------------
# 4. ENDPOINT API (Para peticiones dinámicas Fetch / Asíncronas)
# --------------------------------------------------------------------------
@login_required
def cita_api(request, cod_cita):
    cita = get_object_or_404(Cita, cod_cita=cod_cita)

    data = {
        'cod_cita': str(cita.cod_cita),
        'placa': cita.placa.placa if cita.placa else '',
        'id_tipo_servicio': cita.id_tipo_servicio.id_cat_servicio if cita.id_tipo_servicio else '',
        'nombre_servicio': cita.id_tipo_servicio.nombre if cita.id_tipo_servicio else 'Sin asignar',
        'fecha_entrada': cita.fecha_entrada.strftime('%Y-%m-%dT%H:%M') if cita.fecha_entrada else '',
        'fecha_entrega_estimada': cita.fecha_entrega_estimada.strftime('%Y-%m-%dT%H:%M') if cita.fecha_entrega_estimada else '',
        'motivo_ingreso': cita.motivo_ingreso or '',
        'estado_cita': cita.estado_cita,
        'operador': str(cita.cedula_usuario) if cita.cedula_usuario else 'N/A',
    }
    return JsonResponse({'status': 'success', 'data': data})









import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET

from .models import ServicioTaller, ServicioDetalle, Cita, CatServicio, Producto, MovimientosProducto
from .forms import AbrirOrdenTrabajoForm, CargarItemOrdenForm, CambiarEstatusOrdenForm


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import ServicioTaller, Cita, CatServicio, Producto, ServicioDetalle
from .forms import AbrirOrdenTrabajoForm

@login_required
def ordenes_trabajo_list(request):

    # ==========================================
    # 1. BLOQUE POST: PROCESA LOS MODALES HTML
    # ==========================================
    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # MODAL A: APERTURAR ORDEN
        if action_type == 'crear_orden':
            form = AbrirOrdenTrabajoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Orden de trabajo aperturada exitosamente.")
                return redirect('ordenes_trabajo_list')
            else:
                messages.error(request, f"Error al crear la orden: {form.errors}")

        # MODAL B: AÑADIR ÍTEM (SERVICIO O REPUESTO)
        elif action_type == 'cargar_item':
            id_servicio = request.POST.get('id_servicio')
            tipo_cargo = request.POST.get('tipo_cargo')

            try:
                orden = ServicioTaller.objects.get(pk=id_servicio)

                if tipo_cargo == 'SERVICIO':
                    id_cat = request.POST.get('id_cat_servicio')
                    cat_obj = CatServicio.objects.get(pk=id_cat)
                    ServicioDetalle.objects.create(
                        id_servicio=orden,
                        id_cat_servicio=cat_obj,
                        cantidad_producto=1
                    )
                elif tipo_cargo == 'PRODUCTO':
                    id_prod = request.POST.get('id_producto')
                    cant = int(request.POST.get('cantidad_producto', 1))
                    prod_obj = Producto.objects.get(pk=id_prod)

                    # Descontar stock
                    prod_obj.stock_actual -= cant
                    prod_obj.save()

                    ServicioDetalle.objects.create(
                        id_servicio=orden,
                        id_producto=prod_obj,
                        cantidad_producto=cant
                    )

                messages.success(request, "Ítem cargado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al registrar ítem: {e}")

            return redirect('ordenes_trabajo_list')

        # MODAL C: CAMBIAR ESTATUS
        elif action_type == 'cambiar_estatus':
            id_servicio = request.POST.get('id_servicio')
            nuevo_estado = request.POST.get('estado_orden')

            orden = ServicioTaller.objects.get(pk=id_servicio)
            orden.estado_orden = nuevo_estado
            orden.save()

            messages.success(request, "Estatus actualizado.")
            return redirect('ordenes_trabajo_list')

        # ACCIÓN D: ANULAR / ELIMINAR ORDEN
        elif action_type == 'eliminar_orden':
            id_servicio = request.POST.get('id_servicio')
            ServicioTaller.objects.filter(pk=id_servicio).delete()

            messages.success(request, "Orden de trabajo anulada.")
            return redirect('ordenes_trabajo_list')

    # ==========================================
    # 2. BLOQUE GET: CARGA LA PANTALLA GENERAL
    # ==========================================
    ordenes = ServicioTaller.objects.select_related('cod_cita__placa', 'cod_cita__id_tipo_servicio').prefetch_related(
        'serviciodetalle_set__id_cat_servicio',
        'serviciodetalle_set__id_producto'
    ).order_by('-fecha_inicio')

    citas_disponibles = Cita.objects.filter(
        estado_cita__in=['Pendiente', 'Aprobada']
    ).exclude(
        cod_cita__in=ServicioTaller.objects.values_list('cod_cita', flat=True)
    ).select_related('placa', 'id_tipo_servicio')

    form_abrir = AbrirOrdenTrabajoForm()
    form_abrir.fields['cod_cita'].queryset = citas_disponibles
    citas = Cita.objects.select_related('placa', 'id_tipo_servicio', 'cedula_usuario').all().order_by('-fecha_entrada')
    vehiculos = Vehiculo.objects.select_related('cedula_usuario').all().order_by('placa')
    servicios_cat = CatServicio.objects.filter(activo=True).order_by('nombre')

    servicios_catalogo = CatServicio.objects.filter(activo=True).order_by('nombre')
    productos_catalogo = Producto.objects.filter(activo=True, stock_actual__gt=0).order_by('nombre')

    return render(request, 'taller/ordenes/ordenes_trabajo.html', {
        'ordenes': ordenes,
        'citas_disponibles': citas_disponibles,
        'servicios_catalogo': servicios_catalogo,
        'productos_catalogo': productos_catalogo,
        'form_abrir': form_abrir,
        'citas': citas,
        'vehiculos': vehiculos,
        'servicios_cat': servicios_cat,
    })

# 2. DETALLE DE ORDEN EN JSON
@login_required
@require_GET
def orden_trabajo_api(request, id_servicio):
    ot = get_object_or_404(
        ServicioTaller.objects.select_related('cod_cita__placa', 'cod_cita__id_tipo_servicio'),
        id_servicio=id_servicio
    )
    detalles = ServicioDetalle.objects.filter(id_servicio=ot).select_related('id_cat_servicio', 'id_producto')

    items = []
    total_acumulado = 0

    for item in detalles:
        if item.id_cat_servicio:
            nombre = item.id_cat_servicio.nombre
            tipo = "Servicio"
            precio = float(item.id_cat_servicio.precio_base or 0)
            cant = 1
        else:
            nombre = item.id_producto.nombre if item.id_producto else "Ítem Desconocido"
            tipo = "Repuesto"
            precio = float(item.id_producto.precio_venta or 0) if item.id_producto else 0
            cant = item.cantidad_producto

        subtotal = precio * cant
        total_acumulado += subtotal

        items.append({
            'id_detalle': item.id_servicio_detalle,
            'nombre': nombre,
            'tipo': tipo,
            'cantidad': cant,
            'precio_unitario': precio,
            'subtotal': subtotal,

        })

    data = {
        'id_servicio': ot.id_servicio,
        'fecha_inicio': ot.fecha_inicio.strftime("%d/%m/%Y %I:%M %p"),
        'fecha_entrega': ot.fecha_entrega.strftime("%d/%m/%Y %I:%M %p") if ot.fecha_entrega else "En taller",
        'estado_orden': ot.estado_orden,
        'placa': ot.cod_cita.placa.placa if ot.cod_cita and ot.cod_cita.placa else "N/A",
        'vehiculo': f"{ot.cod_cita.placa.marca} {ot.cod_cita.placa.modelo}" if ot.cod_cita and ot.cod_cita.placa else "N/A",
        'items': items,
        'total': total_acumulado

    }

    return JsonResponse({'status': 'success', 'data': data})


# 3. CREAR / APERTURAR ORDEN DESDE CITA
@login_required
@require_POST
def orden_trabajo_crear(request):
    form = AbrirOrdenTrabajoForm(request.POST)
    if form.is_valid():
        cita_obj = form.cleaned_data['cod_cita']
        try:
            with transaction.atomic():
                nueva_orden = ServicioTaller.objects.create(cod_cita=cita_obj)

                # Anexar servicio principal inicial
                if cita_obj.id_tipo_servicio:
                    ServicioDetalle.objects.create(
                        id_servicio=nueva_orden,
                        id_cat_servicio=cita_obj.id_tipo_servicio,
                        cantidad_producto=1
                    )

                cita_obj.estado_cita = 'Ejecutada'
                cita_obj.save()

            return JsonResponse({
                'status': 'success',
                'message': f"¡Vehículo recibido! Se aperturó la Orden de Trabajo #{nueva_orden.id_servicio}.",
                'id_servicio': nueva_orden.id_servicio
            }, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Error de procesador: {str(e)}"}, status=500)

    errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
    return JsonResponse({'status': 'error', 'errors': errors}, status=400)


# 4. CARGAR ÍTEM (SERVICIO O REPUESTO CON DESCUENTO Y KARDEX)
@login_required
@require_POST
def orden_trabajo_cargar_item(request):
    form = CargarItemOrdenForm(request.POST)
    if form.is_valid():
        ot = form.cleaned_data['id_servicio']
        tipo_cargo = form.cleaned_data['tipo_cargo']

        try:
            with transaction.atomic():
                if tipo_cargo == 'SERVICIO':
                    servicio = form.cleaned_data['id_cat_servicio']
                    ServicioDetalle.objects.create(
                        id_servicio=ot,
                        id_cat_servicio=servicio,
                        cantidad_producto=1
                    )
                    msg = f"Servicio '{servicio.nombre}' anexado a la O.T #{ot.id_servicio}."

                elif tipo_cargo == 'PRODUCTO':
                    producto = form.cleaned_data['id_producto']
                    cantidad = form.cleaned_data['cantidad_producto']

                    # 1. Descontar Stock
                    producto.stock_actual = (producto.stock_actual or 0) - cantidad
                    producto.save()

                    # 2. Registrar Renglón de Detalle
                    ServicioDetalle.objects.create(
                        id_servicio=ot,
                        id_producto=producto,
                        cantidad_producto=cantidad
                    )

                    # 3. Registrar Movimiento en Kardex
                    MovimientosProducto.objects.create(
                        tipo_movimiento='SALIDA_TALLER',
                        cantidad=cantidad,
                        fecha_movimiento=timezone.now(),
                        descripcion=f"Consumo en foso mecánico O.T #{ot.id_servicio}",
                        id_producto=producto,
                        id_servicio=ot
                    )

                    msg = f"¡Repuesto '{producto.nombre}' (x{cantidad}) cargado a la O.T #{ot.id_servicio}!"

            return JsonResponse({'status': 'success', 'message': msg})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Error al procesar cargo: {str(e)}"}, status=500)

    errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
    return JsonResponse({'status': 'error', 'errors': errors}, status=400)


# 5. ELIMINAR ÍTEM (REVERTIR CARGO / REINTEGRAR STOCK)
@login_required
@require_POST
def orden_trabajo_eliminar_item(request, id_detalle):
    detalle = get_object_or_404(ServicioDetalle, id_servicio_detalle=id_detalle)
    ot = detalle.id_servicio

    try:
        with transaction.atomic():
            # Si era un producto, devolvemos el stock y registramos la devolución
            if detalle.id_producto:
                producto = detalle.id_producto
                cant_devuelta = detalle.cantidad_producto

                producto.stock_actual = (producto.stock_actual or 0) + cant_devuelta
                producto.save()

                MovimientosProducto.objects.create(
                    tipo_movimiento='ENTRADA_AJUSTE',
                    cantidad=cant_devuelta,
                    fecha_movimiento=timezone.now(),
                    descripcion=f"Devolución / Corrección de ítem desde O.T #{ot.id_servicio}",
                    id_producto=producto,
                    id_servicio=ot
                )

            detalle.delete()

        return JsonResponse({
            'status': 'success',
            'message': f"Ítem eliminado correctamente de la O.T #{ot.id_servicio}."
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Error al eliminar ítem: {str(e)}"}, status=500)


# 6. CAMBIAR ESTATUS

@login_required
@require_POST
def cambiar_estado_cita_taller(request, cod_cita):
    cita = get_object_or_404(Cita, cod_cita=cod_cita)
    nuevo_estado = request.POST.get('estado')

    if nuevo_estado:
        cita.estado_cita = nuevo_estado
        cita.save()

        # Sincronizar o crear el registro en el taller si aplica
        if nuevo_estado == 'En Reparacion':
            ServicioTaller.objects.get_or_create(
                cod_cita=cita,
                defaults={'estado_orden': 'En Reparacion'}
            )
        elif nuevo_estado == 'Finalizado':
            ServicioTaller.objects.filter(cod_cita=cita).update(
                estado_orden='Finalizado',
                fecha_entrega=timezone.now()
            )

        return JsonResponse({'status': 'success', 'nuevo_estado': cita.estado_cita})

    return JsonResponse({'status': 'error', 'mensaje': 'Estado no válido'}, status=400)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from .models import Producto, CatProducto, MovimientosProducto
from .forms import (
    CrearCategoriaForm,
    CrearProductoForm,
    EditarProductoForm,
    MovimientoInventarioForm
)

# ==========================================
# 1. PANTALLA PRINCIPAL (ÚNICO HTML REQUEST)
# ==========================================
@login_required
def inventario_list(request):
    productos = Producto.objects.select_related('id_cat_producto').all().order_by('nombre')
    categorias = CatProducto.objects.all().order_by('nombre')

    ultimos_movimientos = MovimientosProducto.objects.select_related(
        'id_producto', 'id_servicio', 'cod_pedido'
    ).order_by('-fecha_movimiento')[:50]

    form_categoria = CrearCategoriaForm()
    form_producto = CrearProductoForm()
    form_movimiento = MovimientoInventarioForm()

    # Obtener el nombre del usuario actual de forma segura
    usuario_nombre = request.user.get_full_name() or str(request.user) if request.user.is_authenticated else "Sistema"


    return render(request, 'taller/inventario/inventario.html', {
        'productos': productos,
        'categorias': categorias,
        'ultimos_movimientos': ultimos_movimientos,
        'form_categoria': form_categoria,
        'form_producto': form_producto,
        'form_movimiento': form_movimiento,
        'usuario_nombre': usuario_nombre,
    })


# ==========================================
# 2. DETALLE DE PRODUCTO EN JSON (API GET)
# ==========================================
@login_required
@require_GET
def producto_api(request, id_producto):
    producto = get_object_or_404(
        Producto.objects.select_related('id_cat_producto'),
        pk=id_producto
    )

    data = {
        'id_producto': producto.id_producto,
        'sku': producto.sku,
        'nombre': producto.nombre,
        'precio_venta': float(producto.precio_venta or 0),
        'stock_actual': producto.stock_actual,
        'stock_minimo': producto.stock_minimo,
        'imagen_url': producto.imagen_url or '',
        'activo': producto.activo,
        'id_cat_producto': producto.id_cat_producto.id_cat_producto if producto.id_cat_producto else None,
        'categoria_nombre': producto.id_cat_producto.nombre if producto.id_cat_producto else "Sin Categoría"
    }

    return JsonResponse({'status': 'success', 'data': data})


# ==========================================
# 3. CREAR CATEGORÍA
# ==========================================
@login_required
@require_POST
def categoria_crear(request):
    form = CrearCategoriaForm(request.POST)
    if form.is_valid():
        try:
            categoria = form.save()
            return JsonResponse({
                'status': 'success',
                'message': f"Categoría '{categoria.nombre}' creada exitosamente.",
                'id_cat_producto': categoria.id_cat_producto,
                'nombre': categoria.nombre
            }, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Error al guardar categoría: {str(e)}"}, status=500)

    errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
    return JsonResponse({'status': 'error', 'errors': errors}, status=400)


# ==========================================
# 4. CREAR PRODUCTO / REPUESTO (CON KARDEX INICIAL)
# ==========================================
@login_required
@require_POST
def producto_crear(request):
    form = CrearProductoForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                nuevo_producto = form.save()
                stock_ini = nuevo_producto.stock_actual or 0

                # Si ingresa con stock inicial, se audita automáticamente en Kardex
                if stock_ini > 0:
                    MovimientosProducto.objects.create(
                        id_producto=nuevo_producto,
                        tipo_movimiento='ENTRADA_COMPRA',
                        cantidad=stock_ini,
                        fecha_movimiento=timezone.now(),
                        descripcion="Carga inicial automática al aperturar producto en sistema."
                    )

            return JsonResponse({
                'status': 'success',
                'message': f"Repuesto '{nuevo_producto.nombre}' (SKU: {nuevo_producto.sku}) registrado con éxito.",
                'id_producto': nuevo_producto.id_producto
            }, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Error procesador: {str(e)}"}, status=500)

    errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
    return JsonResponse({'status': 'error', 'errors': errors}, status=400)


# ==========================================
# 5. EDITAR PRODUCTO
# ==========================================
@login_required
@require_POST
def producto_editar(request, id_producto):
    producto = get_object_or_404(Producto, pk=id_producto)
    form = EditarProductoForm(request.POST, instance=producto)

    if form.is_valid():
        try:
            form.save()
            return JsonResponse({
                'status': 'success',
                'message': f"Producto '{producto.nombre}' actualizado correctamente."
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Error al editar producto: {str(e)}"}, status=500)

    errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
    return JsonResponse({'status': 'error', 'errors': errors}, status=400)


# ==========================================
# 6. REGISTRAR MOVIMIENTO MANUAL DE INVENTARIO (AJUSTE DE STOCK / KARDEX)
# ==========================================
@login_required
@require_POST
def inventario_movimiento_crear(request):
    form = MovimientoInventarioForm(request.POST)
    if form.is_valid():
        producto = form.cleaned_data['id_producto']
        tipo_mov = form.cleaned_data['tipo_movimiento']
        cant = form.cleaned_data['cantidad']
        descripcion = form.cleaned_data['descripcion']

        try:
            with transaction.atomic():
                # Actualización estricta del stock
                if tipo_mov.startswith('ENTRADA_'):
                    producto.stock_actual = (producto.stock_actual or 0) + cant
                elif tipo_mov.startswith('SALIDA_'):
                    if (producto.stock_actual or 0) < cant:
                        return JsonResponse({
                            'status': 'error',
                            'message': f"Stock insuficiente para retirar {cant} unidades. Stock actual: {producto.stock_actual}"
                        }, status=400)
                    producto.stock_actual -= cant

                producto.save()

                # Auditoría de inventario
                MovimientosProducto.objects.create(
                    id_producto=producto,
                    tipo_movimiento=tipo_mov,
                    cantidad=cant,
                    fecha_movimiento=timezone.now(),
                    descripcion=descripcion or f"Ajuste manual de {tipo_mov} desde módulo inventario."
                )

            return JsonResponse({
                'status': 'success',
                'message': f"Movimiento {tipo_mov} (x{cant}) aplicado a '{producto.nombre}'. Nuevo stock: {producto.stock_actual}.",
                'nuevo_stock': producto.stock_actual
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f"Error al procesar movimiento: {str(e)}"}, status=500)

    errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
    return JsonResponse({'status': 'error', 'errors': errors}, status=400)


# ==========================================
# 7. CAMBIAR ESTATUS (ACTIVAR / INACTIVAR PRODUCTO)
# ==========================================
@login_required
@require_POST
def producto_cambiar_estatus(request, id_producto):
    producto = get_object_or_404(Producto, pk=id_producto)

    try:
        producto.activo = not producto.activo
        producto.save()

        nuevo_estado = "activado" if producto.activo else "desactivado"
        return JsonResponse({
            'status': 'success',
            'message': f"El producto '{producto.nombre}' ha sido {nuevo_estado}.",
            'activo': producto.activo
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Error al cambiar estatus: {str(e)}"}, status=500)






from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Pedido, PedidoDetalle, Producto, Usuario, ConfiguracionSistema

def modulo_venta_repuestos(request):
    # 1. Consultas para alimentar la pantalla
    ventas = Pedido.objects.select_related('cedula_usuario').prefetch_related('pedidodetalle_set__id_producto').all().order_by('-fecha_pedido')
    productos_disponibles = Producto.objects.filter(stock_actual__gt=0).order_by('nombre')
    clientes = Usuario.objects.filter(id_rol__nombre_rol__icontains='Cliente').order_by('first_name')

    campos_venta = [
            {
                'name': 'action_type',
                'tipo': 'hidden',
                'value': 'concluir_venta_mostrador'
            },
            {
                'label': 'Seleccionar Comprador (Cliente)',
                'name': 'cedula_usuario',
                'tipo': 'select',
                'placeholder': '-- Seleccione Cliente --',
                'required': True,
                'opciones': [
                    {
                        'id': cliente.cedula_usuario,
                        'texto': f"{cliente.first_name} {cliente.last_name} (C.I: {cliente.cedula_usuario})"
                    } for cliente in clientes
                ]
            },
            {
                'label': 'Repuesto Requerido',
                'name': 'id_producto',
                'tipo': 'select',
                'placeholder': '-- Buscar pieza con existencia --',
                'required': True,
                'opciones': [
                    {
                        'id': prod.id_producto,
                        'texto': f"{prod.nombre} — ${prod.precio_venta} (Disp: {prod.stock_actual} uds)"
                    } for prod in productos_disponibles
                ]
            },
            {
                'label': 'Cantidad a Despachar',
                'name': 'cantidad',
                'tipo': 'number',
                'value': '1',
                'min': '1',
                'required': True
            }
        ]
    # 2. Procesar la venta por mostrador (POST)
    if request.method == 'POST':
        cedula_cliente = request.POST.get('cedula_usuario')
        id_prod = request.POST.get('id_producto')
        cantidad = int(request.POST.get('cantidad', 1))

        try:
            with transaction.atomic():
                producto_obj = Producto.objects.select_for_update().get(id_producto=id_prod)
                cliente_obj = Usuario.objects.get(cedula_usuario=cedula_cliente)

                if producto_obj.stock_actual < cantidad:
                    messages.error(request, f"Stock insuficiente para '{producto_obj.nombre}'. Disponibles: {producto_obj.stock_actual} unidades.")
                    return redirect('venta_repuestos')

                monto_total = producto_obj.precio_venta * cantidad

                # A. Crear la cabecera
                nueva_venta = Pedido.objects.create(
                    total=monto_total,
                    estado_pedido=Pedido.EstadoPedido.COMPLETADO,
                    tipo_entrega=Pedido.TipoEntrega.RETIRO,
                    tasa_cambio=ConfiguracionSistema.get_tasa_actual(),
                    cedula_usuario=cliente_obj
                )

                # B. Crear el desglose
                PedidoDetalle.objects.create(
                    cod_pedido=nueva_venta,
                    id_producto=producto_obj,
                    cantidad=cantidad,
                    precio_unitario=producto_obj.precio_venta,
                    subtotal=monto_total
                )

                # C. Restar del inventario
                producto_obj.stock_actual -= cantidad
                producto_obj.save()

                messages.success(request, f"¡Venta procesada con éxito! Inventario actualizado.")
                return redirect('venta_repuestos')

        except (Producto.DoesNotExist, Usuario.DoesNotExist):
            messages.error(request, "El producto o el cliente seleccionado no es válido.")
            return redirect('venta_repuestos')
        except Exception as e:
            messages.error(request, f"Error crítico al procesar la transacción: {str(e)}")
            return redirect('venta_repuestos')

    return render(request, 'taller/venta_repuestos.html', {
        'ventas': ventas,
        'productos_disponibles': productos_disponibles,
        'clientes': clientes,
        'campos_venta': campos_venta,
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import  Galeria
from django.contrib.auth.decorators import login_required

@login_required
def modulo_portal_web(request):

    return render(request, 'web/portal_web.html', {

    })

@login_required
def modulo_galeria_dinamica(request):

    return render(request, 'web/galeria_dinamica.html', {

    })

@login_required
def modulo_noticias_promociones(request):

    return render(request, 'web/noticias_promociones.html', {

    })




from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Factura, Transaccion, ServicioTaller
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

@login_required
def modulo_finanzas(request):
    # 1. Consultas comerciales y logs de auditoría
    facturas = Factura.objects.select_related('id_pedido').all()

    # Traemos las órdenes que están listas para facturar y que no tengan factura previa
    ordenes_listas = ServicioTaller.objects.filter(estado_orden='Listo')

    # Traemos las últimas 50 operaciones de auditoría del sistema

    # 2. Procesar Factura u Operación de Pago (POST)
    if request.method == 'POST':
        action = request.POST.get('action_finanzas')

        # CASO A: Generar Factura de una Orden de Trabajo Lista
        if action == 'generar_factura':
            id_orden = request.POST.get('id_servicio')

            try:
                orden_obj = ServicioTaller.objects.get(id_servicio=id_orden)

                # Calculamos la suma de todos los servicios cargados en el detalle de la orden
                total_calculado = orden_obj.detalles.aggregate(total=Sum('precio_unitario'))['total'] or 0.00

                nueva_factura = Factura.objects.create(
                    id_servicio=orden_obj,
                    monto_total=total_calculado,
                    estado_pago='Por Cobrar'
                )

                # AUDITORÍA AUTOMÁTICA (log_sistema)


                messages.success(request, f"Factura #{nueva_factura.id_factura} generada exitosamente.")
                return redirect('modulo_finanzas')
            except Exception as e:
                messages.error(request, f"Error al facturar la orden: {str(e)}")
                return redirect('modulo_finanzas')

        # CASO B: Registrar un Pago/Abono (transaccion)
        elif action == 'registrar_pago':
            id_fact = request.POST.get('id_factura')
            metodo = request.POST.get('metodo_pago')
            monto = float(request.POST.get('monto_pagado', 0))
            ref = request.POST.get('referencia', '').strip()

            try:
                factura_obj = Factura.objects.get(id_factura=id_fact)

                # Registramos el cobro en la tabla transaccion
                Transaccion.objects.create(
                    id_factura=factura_obj,
                    metodo_pago=metodo,
                    monto_pagado=monto,
                    referencia=ref
                )

                # Actualizar el estado si pagó el total
                # En un sistema real puedes sumar transacciones parciales, aquí la marcamos como pagada de inmediato
                factura_obj.estado_pago = 'Pagada'
                factura_obj.save()

                # AUDITORÍA AUTOMÁTICA (log_sistema)

                messages.success(request, f"¡Pago a la factura #{id_fact} registrado con éxito!")
                return redirect('modulo_finanzas')
            except Exception as e:
                messages.error(request, f"Error operativo en caja: {str(e)}")
                return redirect('modulo_finanzas')

    return render(request, 'taller/finanzas.html', {
        'facturas': facturas,
        'ordenes_listas': ordenes_listas,
       # 'logs': logs
    })



def ver_producto(request, id_producto):
    """
    Vista para renderizar la Hoja de Vida / Kardex de un producto específico.
    Filtra los movimientos reales asociados al producto desde la base de datos.
    """
    # 1. Buscar el producto usando la PK real
    producto = get_object_or_404(Producto, id_producto=id_producto)

    # 2. Traer los movimientos reales desde tu tabla 'movimientos_producto'
    # Ordenamos por fecha_movimiento de forma descendente para ver los más recientes primero
    movimientos = MovimientosProducto.objects.filter(id_producto=producto).order_by('-fecha_movimiento')

    # 3. Contexto directo a la plantilla
    context = {
        'producto': producto,
        'movimientos': movimientos,
    }

    return render(request, 'inventario/ver_producto.html', context)


def cambiar_estado_cliente(request, cedula):
    cliente = get_object_or_404(Usuario, cedula_usuario=cedula)
        # Volteamos el estado actual (Si es True pasa a False, si es False pasa a True)
    cliente.is_active = not cliente.is_active
    cliente.save()
    return redirect('modulo_clientes') # Te regresa a la tabla con el cambio hecho



from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import HistorialVehiculo  # Ajusta según la ubicación de tu modelo
from django.shortcuts import render
from django.db.models import Q
from .models import HistorialVehiculo

def historial_vehiculo_list(request):
    """
    Vista informativa global (Solo Lectura) para consultar el historial de todos los vehículos.
    """
    query = request.GET.get('q', '').strip()

    # select_related optimiza las consultas haciendo JOIN con la Cita
    historiales = HistorialVehiculo.objects.select_related('cod_cita').order_by('-fecha_registro')

    if query:
        historiales = historiales.filter(
            Q(cod_cita__placa__icontains=query) |
            Q(cod_cita__cod_cita__icontains=query) |
            Q(diagnostico_final__icontains=query) |
            Q(reparaciones_realizadas__icontains=query)
        )

    context = {
        'historiales': historiales,
        'query': query,
    }
    return render(request, 'historial/historial_cliente.html', context)



from django.shortcuts import render, get_object_or_404
from .models import Vehiculo, HistorialVehiculo

def historial_vehiculo_detalle(request, placa):
    """
    Vista informativa individual (HTML) para la ficha clínica de un vehículo específico.
    """
    # 1. Verificamos que el vehículo exista por su placa (string)
    vehiculo = get_object_or_404(Vehiculo, placa=placa)

    # 2. Obtenemos las fichas con .filter() para no lanzar 404 si está vacío
    fichas = HistorialVehiculo.objects.filter(
        cod_cita__placa=vehiculo
    ).select_related('cod_cita').order_by('-fecha_registro')

    context = {
        'vehiculo': vehiculo,
        'fichas': fichas,
    }
    return render(request, 'historial/historial_vehiculo.html', context)



def historial_vehiculo_detalle_api(request, placa):
    """
    API informativa: devuelve el listado o detalle de historiales por placa.
    """
    vehiculo = get_object_or_404(Vehiculo, placa=placa)

    # Obtenemos los historiales (puede ser más de uno por vehículo)
    historiales = HistorialVehiculo.objects.filter(
        cod_cita__placa=vehiculo
    ).select_related('cod_cita').order_by('-fecha_registro')

    if not historiales.exists():
        return JsonResponse({
            'status': 'success',
            'mensaje': 'Este vehículo no posee registros de historial aún.',
            'data': []
        })

    data_list = []
    for h in historiales:
        data_list.append({
            'id_historial': h.id_historial_vehiculo,
            'cod_cita': h.cod_cita.cod_cita if h.cod_cita else 'N/A',
            'placa': vehiculo.placa,
            'kilometraje': h.kilometraje_ingreso,
            'diagnostico': h.diagnostico_final,
            'reparaciones': h.reparaciones_realizadas,
            'observaciones': h.observaciones_recomendadas,
            'fecha_registro': h.fecha_registro.strftime('%d/%m/%Y %H:%M'),
        })

    return JsonResponse({
        'status': 'success',
        'data': data_list
    })







def historial_servicio(request, id_servicio):
    # MOCK DE CAMPOS PARA HISTORIAL SERVICIO
    campos_historial_servicio = [
        {'name': 'action_type', 'tipo': 'hidden', 'value': 'guardar_historial_servicio'},
        {'label': 'ID de la Orden de Trabajo', 'name': 'id_servicio', 'tipo': 'number', 'placeholder': 'Ej: 550', 'required': True},
        {
            'label': 'Estado Técnico Asignado',
            'name': 'estado_servicio',
            'tipo': 'select',
            'placeholder': '-- Seleccione Estatus --',
            'required': True,
            'opciones': [
                {'id': 'En Diagnóstico', 'texto': 'En Diagnóstico'},
                {'id': 'Reparando', 'texto': 'Reparando'},
                {'id': 'Finalizado', 'texto': 'Finalizado'},
            ]
        },
        {'label': 'Notas de Progreso / Avances del Taller', 'name': 'notas_progreso', 'tipo': 'text', 'placeholder': 'Ej: Caja de cambios bajada con éxito...', 'required': True}
    ]
    context = {
        'campos_historial_servicio': campos_historial_servicio,
    }
    return render(request, 'servicio/historial_servicio.html', context)


def historial_cliente(request, cedula_usuario):
    # 1. Obtenemos el cliente o tiramos un 404 si no existe
    cliente = get_object_or_404(Usuario, cedula_usuario=cedula_usuario)

    # 2. Traemos todos sus pedidos optimizando la consulta de sus detalles.
    # Usamos prefetch_related porque un pedido tiene muchos detalles (Relación inversa).
    # Reemplaza 'pedido_detalle_set' o 'detalles' según el related_name que tengan tus modelos.
    pedidos = Pedido.objects.filter(cedula_usuario=cliente).prefetch_related(
        'pedidodetalle_set', # O 'detalles' si usaste related_name en la FK de pedido_detalle
        'pedidodetalle_set__id_producto',  # Si quieres el nombre del producto en el detalle
        'pedidodetalle_set__id_cat_servicio' # Si quieres el nombre del servicio en el detalle
    ).order_by('-fecha_pedido')

    # 3. Calculamos la métrica rápida del total de pedidos
    total_pedidos = pedidos.count()

    # 4. Metemos todo al contexto para que el HTML lo renderice dinámicamente
    context = {
        'cliente': cliente,
        'pedidos': pedidos,
        'total_pedidos': total_pedidos,
    }

    return render(request, 'historial/historial_cliente.html', context)




def modulo_caja(request):
    # MOCK DE CAMPOS PARA FLUJO CAJA
    campos_flujo_caja = [
        {'name': 'action_type', 'tipo': 'hidden', 'value': 'guardar_flujo_caja'},
        {'label': 'Cédula del Administrador', 'name': 'cedula_admin', 'tipo': 'text', 'placeholder': 'Ej: V-25894331', 'required': True},
        {
            'label': 'Tipo de Evento Financiero',
            'name': 'tipo_evento_financiero',
            'tipo': 'select',
            'placeholder': '-- Seleccione Flujo --',
            'required': True,
            'opciones': [
                {'id': 'INGRESO', 'texto': 'Ingreso (Entrada de Dinero)'},
                {'id': 'EGRESO', 'texto': 'Egreso / Gasto (Salida de Dinero)'},
            ]
        },
        {'label': 'Monto Afectado (USD)', 'name': 'monto_affected', 'tipo': 'number', 'step': '0.01', 'placeholder': '0.00', 'required': True},
        {'label': 'Detalles / Concepto del Evento', 'name': 'detalles_evento', 'tipo': 'text', 'placeholder': 'Ej: Pago de agua para el personal...', 'required': True},
        {'label': 'ID Transacción Asociada (Opcional)', 'name': 'id_transaccion', 'tipo': 'number', 'placeholder': 'Dejar en blanco si es manual', 'required': False}
    ]
    context = {
        'campos_flujo_caja': campos_flujo_caja,
    }
    return render(request, 'taller/modulo_caja.html', context)










import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Pedido, PedidoDetalle, Usuario, ConfiguracionSistema
from .forms import PedidoForm

# --------------------------------------------------------------------------
# 1. LISTAR REGISTROS
# --------------------------------------------------------------------------
@login_required
def pedido_list(request):
    """
    Vista principal para consultar, filtrar y renderizar el listado de pedidos.
    """
    query = request.GET.get('q', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    pedidos = Pedido.objects.select_related('cedula_usuario').order_by('-fecha_pedido')

    if query:
        pedidos = pedidos.filter(
            Q(cod_pedido__icontains=query) |
            Q(cedula_usuario__cedula__icontains=query) |
            Q(cedula_usuario__nombre__icontains=query) |
            Q(cedula_usuario__apellido__icontains=query)
        )

    if estado_filtro:
        pedidos = pedidos.filter(estado_pedido__iexact=estado_filtro)

    usuarios = Usuario.objects.filter(is_active=True).order_by('nombre', 'apellido')
    form = PedidoForm()

    context = {
        'pedidos': pedidos,
        'usuarios': usuarios,
        'form': form,
        'query': query,
        'estado_filtro': estado_filtro,
    }
    return render(request, 'taller/pedidos/pedido_list.html', context)


# --------------------------------------------------------------------------
# 2. CREAR REGISTRO
# --------------------------------------------------------------------------
@login_required
def pedido_crear(request):
    """
    Crea una nueva cabecera de pedido.
    """
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            pedido = form.save(commit=False)
            if not pedido.cod_pedido:
                pedido.cod_pedido = uuid.uuid4()

            # Asignación del cliente o usuario operador
            # Si el formulario no especifica cliente, asigna el usuario autenticado
            if not getattr(pedido, 'cedula_usuario', None):
                pedido.cedula_usuario = getattr(request.user, 'cedula', None) or request.user

            if not pedido.tasa_cambio or pedido.tasa_cambio <= 0:
                pedido.tasa_cambio = ConfiguracionSistema.get_tasa_actual()

            if pedido.total is None:
                pedido.total = Decimal('0.00')

            pedido.save()
            messages.success(request, f"¡Pedido #{str(pedido.cod_pedido)[:8]} registrado exitosamente!")
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")

        return redirect('pedido_list')

    return redirect('pedido_list')


# --------------------------------------------------------------------------
# 3. EDITAR REGISTRO
# --------------------------------------------------------------------------
@login_required
def pedido_editar(request, cod_pedido):
    """
    Actualiza la información básica o estado de un pedido existente.
    """
    pedido = get_object_or_404(Pedido, cod_pedido=cod_pedido)
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, f"Pedido #{str(pedido.cod_pedido)[:8]} actualizado con éxito.")
        else:
            messages.error(request, "Error al actualizar los datos del pedido. Verifique el formulario.")

    return redirect('pedido_list')


# --------------------------------------------------------------------------
# 4. ENDPOINT API (Para peticiones dinámicas Fetch / Asíncronas)
# --------------------------------------------------------------------------
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Pedido, PedidoDetalle, TransaccionDetalle

@login_required
def pedido_api(request, cod_pedido):
    """
    Devuelve los datos generales del pedido, la lista de ítems de PedidoDetalle
    y la información del reporte de pago/transacción en formato JSON.
    """
    pedido = get_object_or_404(Pedido.objects.select_related('cedula_usuario'), cod_pedido=cod_pedido)

    # 1. Desglose de productos y servicios asociados al pedido
    detalles = PedidoDetalle.objects.filter(cod_pedido=pedido).select_related('id_producto', 'id_cat_servicio')
    detalles_data = []
    for d in detalles:
        detalles_data.append({
            'id_detalle': d.id_detalle,
            'tipo': 'Producto' if d.id_producto else ('Servicio' if d.id_cat_servicio else 'Manual'),
            'item_nombre': d.id_producto.nombre if d.id_producto else (d.id_cat_servicio.nombre if d.id_cat_servicio else 'Manual'),
            'descripcion_manual': d.descripcion_manual or '',
            'cantidad': d.cantidad,
            'precio_unitario': str(d.precio_unitario),
            'subtotal': str(d.subtotal),
        })

    # 2. Consultar la transacción y el detalle de pago enlazado a la factura del pedido
    transaccion_det = TransaccionDetalle.objects.filter(
        id_transaccion__id_factura__cod_pedido=pedido
    ).select_related('id_transaccion').first()

    pago_data = None
    if transaccion_det:
        pago_data = {
            'metodo_pago': transaccion_det.metodo_pago,
            'banco_origen': transaccion_det.banco_origen or '',
            'referencia': transaccion_det.referencia_pasarela or '',
            'monto_pago': str(transaccion_det.monto_pago_linea),
            'estado_transaccion': transaccion_det.id_transaccion.estado_transaccion,
            'comprobante_url': transaccion_det.comprobante_img.url if transaccion_det.comprobante_img else None
        }

    # 3. Construir respuesta final
    data = {
        'cod_pedido': str(pedido.cod_pedido),
        'fecha_pedido': pedido.fecha_pedido.strftime('%Y-%m-%dT%H:%M') if pedido.fecha_pedido else '',
        'estado_pedido': pedido.estado_pedido,
        'estado_pedido_display': pedido.get_estado_pedido_display() if hasattr(pedido, 'get_estado_pedido_display') else pedido.estado_pedido,
        'tipo_entrega': pedido.tipo_entrega,
        'tipo_entrega_display': pedido.get_tipo_entrega_display() if hasattr(pedido, 'get_tipo_entrega_display') else pedido.tipo_entrega,
        'costo_envio': str(pedido.costo_envio),
        'direccion_envio': pedido.direccion_envio or '',
        'tasa_cambio': str(pedido.tasa_cambio),
        'total': str(pedido.total),
        'total_bolivares': str(pedido.total_bolivares),
        'es_delivery': pedido.es_delivery,
        'cliente_cedula': str(getattr(pedido.cedula_usuario, 'cedula', getattr(pedido.cedula_usuario, 'cedula_usuario', str(pedido.cedula_usuario)))),
        'cliente_nombre': getattr(pedido.cedula_usuario, 'nombre', str(pedido.cedula_usuario)),
        'detalles': detalles_data,
        'pago': pago_data  # Retorna dict con el pago o None si no se ha reportado
    }
    return JsonResponse({'status': 'success', 'data': data})





from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required





@login_required
def agregar_detalle_api(request, cod_pedido):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, cod_pedido=cod_pedido)

        # Validar estado del pedido
        if pedido.estado_pedido.upper() in ['COMPLETADO', 'CANCELADO']:
            return JsonResponse({'status': 'error', 'message': 'No se pueden agregar ítems a un pedido finalizado.'}, status=400)

        tipo = request.POST.get('tipo')  # 'producto', 'servicio' o 'manual'
        item_id = request.POST.get('id_item') or request.POST.get('id_producto') or request.POST.get('id_cat_servicio')
        descripcion_manual = request.POST.get('descripcion_manual', '').strip()

        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': 'Cantidad inválida.'}, status=400)

        if cantidad <= 0:
            return JsonResponse({'status': 'error', 'message': 'La cantidad debe ser mayor a 0.'}, status=400)

        precio_unitario = Decimal('0.00')

        with transaction.atomic():
            detalle = PedidoDetalle(
                cod_pedido=pedido,
                cantidad=cantidad
            )

            if tipo == 'producto' and item_id:
                producto = get_object_or_404(Producto, pk=item_id)
                detalle.id_producto = producto
                # Toma el precio registrado en el catálogo de productos
                precio_unitario = getattr(producto, 'precio', getattr(producto, 'precio_venta', Decimal('0.00')))

            elif tipo == 'servicio' and item_id:
                servicio = get_object_or_404(CatServicio, pk=item_id)
                detalle.id_cat_servicio = servicio
                precio_unitario = getattr(servicio, 'precio_base', getattr(servicio, 'precio', Decimal('0.00')))

            elif tipo == 'manual' and descripcion_manual:
                detalle.descripcion_manual = descripcion_manual
                # Solo en tipo manual se lee el precio enviado por el usuario
                try:
                    precio_unitario = Decimal(str(request.POST.get('precio_unitario', '0.00')))
                except (ValueError, TypeError):
                    precio_unitario = Decimal('0.00')
            else:
                return JsonResponse({'status': 'error', 'message': 'Selección no válida.'}, status=400)

            detalle.precio_unitario = precio_unitario
            detalle.subtotal = detalle.cantidad * detalle.precio_unitario
            detalle.save()

            # Recalcular el total del pedido (Subtotal + IVA 16% + Costo de Envío)
            detalles = PedidoDetalle.objects.filter(cod_pedido=pedido)
            subtotal_items = sum(d.subtotal for d in detalles)
            monto_iva = subtotal_items * Decimal('0.16')
            costo_envio = pedido.costo_envio or Decimal('0.00')
            pedido.total = subtotal_items + monto_iva + costo_envio
            pedido.save()

        return JsonResponse({'status': 'success', 'message': 'Ítem agregado correctamente.'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

@login_required
def eliminar_detalle_api(request, id_detalle):
        if request.method == 'POST':
            detalle = get_object_or_404(PedidoDetalle, pk=id_detalle)
            pedido = detalle.cod_pedido

            if pedido.estado_pedido.upper() in ['COMPLETADO', 'CANCELADO']:
                return JsonResponse({'status': 'error', 'message': 'No se pueden modificar ítems de un pedido finalizado.'}, status=400)

            with transaction.atomic():
                detalle.delete()

                # Recalcular total de la cabecera
                detalles = PedidoDetalle.objects.filter(cod_pedido=pedido)
                subtotal_items = sum(d.subtotal for d in detalles)
                monto_iva = subtotal_items * Decimal('0.16') if subtotal_items else Decimal('0.00')
                costo_envio = pedido.costo_envio or Decimal('0.00')
                pedido.total = subtotal_items + monto_iva + costo_envio
                pedido.save()

            return JsonResponse({'status': 'success', 'message': 'Ítem eliminado.'})

        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)



def listar_producto_api(request):
    productos = Producto.objects.all()
    data = [{'id': p.id_producto, 'nombre': p.nombre} for p in productos]
    return JsonResponse(data, safe=False)


def listar_servicio_api(request):
    servicios = CatServicio.objects.all()
    data = [{'id': s.id_cat_servicio, 'nombre': s.nombre} for s in servicios]
    return JsonResponse(data, safe=False)







from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Factura, FacturaDetalle

@login_required
def factura_list(request):
    """
    Lista las facturas emitidas permitiendo filtrar por identificador o usuario.
    """
    query = request.GET.get('q', '')

    facturas = Factura.objects.all().select_related(
        'cedula_usuario', 'cod_pedido', 'id_servicio'
    ).order_by('-fecha_emision')

    if query:
        facturas = facturas.filter(
            identificador__icontains=query
        ) | facturas.filter(
            cedula_usuario__nombre__icontains=query
        )

    context = {
        'facturas': facturas,
        'query': query,
    }
    return render(request, 'taller/facturas/factura_list.html', context)


@login_required
def factura_detalle_ajax(request, id_factura):
    """
    Retorna los datos de la factura y sus detalles en JSON usando
    las relaciones exactas del modelo FacturaDetalle.
    """
    factura = get_object_or_404(Factura.objects.select_related('cedula_usuario'), pk=id_factura)
    detalles = FacturaDetalle.objects.filter(id_factura=factura).select_related('id_producto', 'id_cat_servicio')

    items = []
    for item in detalles:
        # Determina la descripción según si es un producto o un servicio del taller
        if item.id_producto:
            descripcion = item.id_producto.nombre
        elif item.id_cat_servicio:
            descripcion = item.id_cat_servicio.nombre
        else:
            descripcion = 'N/A'

        items.append({
            'nombre': item.id_producto.nombre if item.id_producto else item.id_cat_servicio.nombre,
            'descripcion': descripcion,
            'cantidad': item.cantidad,
            'precio_unitario': float(item.precio_unitario_historico),
            'descuento': float(item.porcentaje_descuento),
            'impuesto': float(item.impuesto_aplicado),
            'subtotal_linea': float(item.subtotal_linea),
        })

    # Construcción de string representativo para el usuario/cliente
    usuario_str = str(factura.cedula_usuario)

    data = {
        'estado': "PAGADA",
        'identificador': factura.identificador,
        'fecha_emision': factura.fecha_emision.strftime('%d/%m/%Y %H:%M'),
        'usuario': usuario_str,
        'subtotal': float(factura.subtotal),
        'total_pagado': float(factura.total_pagado),
        'items': items,
    }
    return JsonResponse(data)

@login_required
def anular_factura(request, id_factura):
    """
    Anula una factura emitida cambiando su estado.
    """
    factura = get_object_or_404(Factura, pk=id_factura)
    if request.method == 'POST':
        if factura.estado != 'ANULADA':
            factura.estado = 'ANULADA'
            factura.save()
            messages.success(request, f'La factura {factura.numero_factura} fue anulada correctamente.')
        else:
            messages.warning(request, 'La factura ya se encuentra anulada.')
    return redirect('factura_list')




from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Transaccion


@login_required
def transaccion_list(request):
    """Muestra la lista general de transacciones optimizada con select_related."""
    # Se utiliza select_related para traer la información de la factura relacionada sin hacer consultas extra
    transacciones = (
        Transaccion.objects.select_related('id_factura')
        .all()
        .order_by('-fecha_pago')
    )
    # Obtener el nombre del usuario actual de forma segura
    usuario_nombre = request.user.get_full_name() or str(request.user) if request.user.is_authenticated else "Sistema"


    return render(
        request,
        'taller/transacciones/transacciones_list.html',
        {
            'transacciones': transacciones,
            'usuario_nombre': usuario_nombre,
        },
    )

@login_required
def transaccion_api(request, id_transaccion):
    """Retorna la información detallada de una transacción (incluyendo factura y sus detalles) en JSON."""

    # 1. Usamos prefetch_related con 'transacciondetalle_set' para evitar consultas adicionales a la BD
    transaccion = get_object_or_404(
        Transaccion.objects.select_related('id_factura').prefetch_related('transacciondetalle_set'),
        pk=id_transaccion
    )

    # 2. Corregido el nombre del accessor reverso: transacciondetalle_set[cite: 1]
    detalles = transaccion.transacciondetalle_set.all()
    detalles_data = [
        {
            'id_transaccion_detalle': d.id_transaccion_detalle,
            'metodo_pago': d.metodo_pago,
            'monto_pago_linea': float(d.monto_pago_linea),
            'referencia_pasarela': d.referencia_pasarela or '',
            'banco_origen': d.banco_origen or '',
        }
        for d in detalles
    ]

    return JsonResponse({
        'id_transaccion': str(transaccion.id_transaccion),
        'monto_total_a_pagar': float(transaccion.monto_total_a_pagar),
        'monto_total_recibido': float(transaccion.monto_total_recibido),
        'estado_transaccion': transaccion.estado_transaccion,
        'fecha_pago': transaccion.fecha_pago.strftime('%Y-%m-%d %H:%M:%S')
        if transaccion.fecha_pago
        else '',
        'descripcion': transaccion.descripcion or '',
        # Información de la factura asociada[cite: 1]
        'factura': {
            'id_factura': transaccion.id_factura.id_factura,
            'numero_factura': transaccion.id_factura.identificador,
            'fecha_emision': transaccion.id_factura.fecha_emision.strftime(
                '%Y-%m-%d'
            )
            if transaccion.id_factura.fecha_emision
            else '',
            'subtotal': float(transaccion.id_factura.subtotal),
            'total_pagado': float(transaccion.id_factura.total_pagado),
        }
        if transaccion.id_factura
        else None,
        # Lista de detalles de pago (transaccion_detalle)[cite: 1]
        'detalles_pago': detalles_data,
    })




from django.contrib.admin.views.decorators import staff_member_required
from .models import Factura, FacturaDetalle, MovimientosProducto, FlujoCaja






from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Pedido, Transaccion, TransaccionDetalle
@login_required
@require_POST

def cambiar_estado_pedido(request, cod_pedido):
    """
    Aprueba o Cancela un pedido vía AJAX desde el modal.
    Al aprobar: valida la Transacción existente, liquida el inventario (Kardex) y asienta en Flujo de Caja.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'mensaje': 'No tienes permisos para realizar esta acción.'}, status=403)

    accion = request.POST.get('accion') # 'aprobar' o 'cancelar'
    pedido = get_object_or_404(Pedido, cod_pedido=cod_pedido)

    try:
        with transaction.atomic():
            # Buscar la transacción existente mediante la Factura vinculada al Pedido
            transaccion_obj = Transaccion.objects.filter(id_factura__cod_pedido=pedido).first()

            if accion == 'aprobar':
                # 1. Aprobar Pedido y Transacción
                pedido.estado_pedido = Pedido.EstadoPedido.COMPLETADO

                if transaccion_obj:
                    transaccion_obj.estado_transaccion = Transaccion.EstadoTransaccion.APROBADA
                    transaccion_obj.save()

                    # 2. Asentar en Flujo de Caja
                    FlujoCaja.objects.create(
                        id_transaccion=transaccion_obj,
                        cedula_usuario=request.user,
                        tipo_evento_financiero='INGRESO_VENTA',
                        monto_afectado=pedido.total,
                        detalles_evento=f"Venta Aprobada Pedido #{str(pedido.cod_pedido)[:8]}",
                        fecha_evento=timezone.now()
                    )

                # 3. Descontar Stock Físico, Liberar Reserva y Crear Movimientos (Kardex)
                for item in pedido.pedidodetalle_set.all():
                    if item.id_producto:
                        prod = Producto.objects.select_for_update().get(pk=item.id_producto.pk)

                        # Quitar de reserva y restar del stock real
                        if hasattr(prod, 'reservado') and prod.reservado:
                            prod.reservado = max(0, prod.reservado - item.cantidad)
                        elif hasattr(prod, 'stock_reservado') and prod.stock_reservado:
                            prod.stock_reservado = max(0, prod.stock_reservado - item.cantidad)
                        prod.stock_actual = max(0, prod.stock_actual - item.cantidad)
                        prod.save()

                        # Registrar salida en Kardex/Movimientos
                        MovimientosProducto.objects.create(
                            id_producto=prod,
                            tipo_movimiento='SALIDA_VENTA',
                            cantidad=item.cantidad,
                            fecha_movimiento=timezone.now(),
                            descripcion=f"Venta Confirmada Pedido #{str(pedido.cod_pedido)[:8]}"
                        )

                msg = f"Pedido #{pedido.cod_pedido} aprobado, pago verificado y stock liquidado."

            elif accion == 'cancelar':
                # 1. Cancelar Pedido y Rechazar Transacción
                pedido.estado_pedido = Pedido.EstadoPedido.CANCELADO

                if transaccion_obj:
                    transaccion_obj.estado_transaccion = Transaccion.EstadoTransaccion.RECHAZADA
                    transaccion_obj.save()

                # 2. Liberar únicamente el stock reservado
                for item in pedido.pedidodetalle_set.all():
                    if item.id_producto:
                        prod = Producto.objects.select_for_update().get(pk=item.id_producto.pk)
                        if hasattr(prod, 'reservado') and prod.reservado:
                            prod.reservado = max(0, prod.reservado - item.cantidad)
                        elif hasattr(prod, 'stock_reservado') and prod.stock_reservado:
                            prod.stock_reservado = max(0, prod.stock_reservado - item.cantidad)
                            prod.save()

                msg = f"Pedido #{pedido.cod_pedido} cancelado y reserva de stock liberada."

            else:
                return JsonResponse({'status': 'error', 'mensaje': 'Acción no válida.'}, status=400)

            pedido.save()
            return JsonResponse({'status': 'success', 'mensaje': msg})

    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': f"Error al procesar la solicitud: {str(e)}"}, status=500)

from .context_processors import actualizar_tasa_dolar_bcv


def actualizar_tasa_bcv_ajax(request):
    """
    Endpoint AJAX para actualizar el precio del dólar utilizando directamente
    la función de context_processors y retornar la última vez actualizado.
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'}, status=405)

    try:
        # Llama directamente a la función de context_processors con forzar=True
        resultado = actualizar_tasa_dolar_bcv(forzar=True)
        ultima_act = resultado.get('ultima_actualizacion')

        if ultima_act:
            fecha_str = timezone.localtime(ultima_act).strftime('%d/%m/%Y %I:%M %p')
        else:
            fecha_str = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %I:%M %p')

        return JsonResponse({
            'status': 'success' if resultado.get('exito') else 'warning',
            'tasa': f"{resultado['tasa']:.4f}",
            'tasa_display': f"{resultado['tasa']:.2f}",
            'ultima_actualizacion': fecha_str,
            'mensaje': resultado.get('mensaje', 'Tasa actualizada con éxito.'),
            'origen': resultado.get('origen', '')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'mensaje': f'Error al sincronizar con el BCV: {str(e)}'
        }, status=500)




@login_required
def pedidos_cliente(request):
    """
    Lista de pedidos exclusiva para el cliente autenticado.
    """
    # Pedidos que requieren atención inmediata (Pendientes)
    pedidos_pendientes = Pedido.objects.filter(
        cedula_usuario=request.user,
        estado_pedido=Pedido.EstadoPedido.PENDIENTE
    ).order_by('-fecha_pedido')

    # Historial de pedidos procesados o finalizados
    pedidos_historial = Pedido.objects.filter(
        cedula_usuario=request.user
    ).exclude(
        estado_pedido=Pedido.EstadoPedido.PENDIENTE
    ).order_by('-fecha_pedido')

    context = {
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_historial': pedidos_historial,
    }
    return render(request, 'usuario/pedido_list.html', context)
