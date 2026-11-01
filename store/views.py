from decimal import Decimal
import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import (
    Carrito,
    CarritoDetalle,
    ConfiguracionSistema,
    Factura,
    FacturaDetalle,
    FlujoCaja,
    MovimientosProducto,
    Pedido,
    PedidoDetalle,
    Producto,
    Transaccion,
    TransaccionDetalle,
    Notificacion,
    Usuario
)


def inicio_tienda(request):
    """Vista principal del catálogo de la tienda."""
    query = request.GET.get('q', '').strip()
    if query:
        productos = Producto.objects.select_related('id_cat_producto').filter(
            Q(nombre__icontains=query) |
            Q(sku__icontains=query) |
            Q(id_cat_producto__nombre__icontains=query),
            activo=True
        )
    else:
        productos = Producto.objects.select_related('id_cat_producto').filter(activo=True)

    cart_count = 0
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(cedula_usuario=request.user)
        cart_count = sum(item.cantidad for item in CarritoDetalle.objects.filter(id_carrito=carrito))

    return render(request, 'tienda/catalogo.html', {
        'productos': productos,
        'query': query,
        'cart_count': cart_count,
    })


def carrito_api(request):
    """Endpoint API para obtener el contenido actual del carrito vía AJAX/JSON."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Usuario no autenticado'}, status=401)

    carrito, _ = Carrito.objects.get_or_create(cedula_usuario=request.user)
    detalles = CarritoDetalle.objects.filter(id_carrito=carrito).select_related('id_producto')

    items = []
    subtotal_general = Decimal('0.00')

    for d in detalles:
        precio = d.id_producto.precio_venta or Decimal('0.00')
        subtotal_item = precio * d.cantidad
        subtotal_general += subtotal_item

        items.append({
            'id_carrito_d': d.id_carrito_d,
            'id_producto': d.id_producto.id_producto,
            'nombre': d.id_producto.nombre,
            'precio_venta': float(precio),
            'cantidad': d.cantidad,
            'subtotal': float(subtotal_item),
            'stock_actual': d.id_producto.stock_actual
        })

    iva = subtotal_general * Decimal('0.16')
    total = subtotal_general + iva

    return JsonResponse({
        'items': items,
        'subtotal': float(subtotal_general),
        'iva': float(iva),
        'total': float(total),
        'cart_count': sum(i['cantidad'] for i in items)
    })


@login_required
@require_POST
def carrito_agregar(request, id_producto):
    """Añade una cantidad determinada de un producto al carrito de compras."""
    producto = get_object_or_404(Producto, pk=id_producto)

    try:
        cantidad_deseada = int(request.POST.get('cantidad', 1))
    except ValueError:
        cantidad_deseada = 1

    if cantidad_deseada < 1:
        cantidad_deseada = 1

    if producto.stock_actual is None or producto.stock_actual <= 0:
        messages.error(request, f"Lo sentimos, no hay stock disponible para '{producto.nombre}'.")
        return redirect('inicio_tienda')

    carrito, _ = Carrito.objects.get_or_create(cedula_usuario=request.user)
    detalle, d_created = CarritoDetalle.objects.get_or_create(id_carrito=carrito, id_producto=producto)

    if not d_created:
        nueva_cantidad = detalle.cantidad + cantidad_deseada
        if nueva_cantidad > producto.stock_actual:
            messages.error(request, f"No puedes añadir {cantidad_deseada} unidades más. Límite de stock: {producto.stock_actual}.")
            return redirect('inicio_tienda')
        detalle.cantidad = nueva_cantidad
        detalle.save()
    else:
        if cantidad_deseada > producto.stock_actual:
            messages.error(request, f"No puedes añadir {cantidad_deseada} unidades. Límite de stock: {producto.stock_actual}.")
            return redirect('inicio_tienda')
        detalle.cantidad = cantidad_deseada
        detalle.save()

    messages.success(request, f"Se añadieron {cantidad_deseada} unidades de '{producto.nombre}' al carrito.")
    return redirect('inicio_tienda')


@login_required
def carrito_list(request):
    """Renderiza la vista principal del carrito de compras (`carrito.html`)."""
    carrito, _ = Carrito.objects.get_or_create(cedula_usuario=request.user)
    detalles = CarritoDetalle.objects.filter(id_carrito=carrito).select_related('id_producto', 'id_producto__id_cat_producto')

    subtotal = Decimal('0.00')
    items_con_subtotal = []

    for item in detalles:
        precio = item.id_producto.precio_venta or Decimal('0.00')
        item_subtotal = precio * item.cantidad
        subtotal += item_subtotal

        items_con_subtotal.append({
            'item': item,
            'subtotal': f"{item_subtotal:.2f}"
        })

    iva = subtotal * Decimal('0.16')
    total = subtotal + iva
    cart_count = sum(i['item'].cantidad for i in items_con_subtotal)

    tasa_bcv = ConfiguracionSistema.get_tasa_actual()
    total_bs = round(total * tasa_bcv, 2)
    subtotal_bs = round(subtotal * tasa_bcv, 2)
    iva_bs = round(iva * tasa_bcv, 2)

    return render(request, 'tienda/carrito.html', {
        'items_con_subtotal': items_con_subtotal,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
        'tasa_bcv': tasa_bcv,
        'total_bs': total_bs,
        'subtotal_bs': subtotal_bs,
        'iva_bs': iva_bs,
        'cart_count': cart_count,
        'tipos_entrega': Pedido.TipoEntrega.choices,
    })


@login_required
@require_POST
def actualizar_carrito(request, id_producto, accion):
    """Suma o resta la cantidad de un ítem en el carrito respondiendo por AJAX."""
    carrito = get_object_or_404(Carrito, cedula_usuario=request.user)
    producto = get_object_or_404(Producto, pk=id_producto)
    detalle = get_object_or_404(CarritoDetalle, id_carrito=carrito, id_producto=producto)

    eliminado = False
    mensaje = None
    status = 'success'

    if accion == 'sumar':
        if detalle.cantidad >= producto.stock_actual:
            status = 'error'
            mensaje = f"Alcanzaste el límite de stock disponible para '{producto.nombre}'."
        else:
            detalle.cantidad += 1
            detalle.save()

    elif accion == 'restar':
        if detalle.cantidad <= 1:
            detalle.delete()
            eliminado = True
            mensaje = f"Se eliminó '{producto.nombre}' del carrito."
        else:
            detalle.cantidad -= 1
            detalle.save()

    # Recalcular métricas generales del carrito usando Decimal
    detalles = CarritoDetalle.objects.filter(id_carrito=carrito)
    subtotal_general = sum(item.cantidad * (item.id_producto.precio_venta or Decimal('0.00')) for item in detalles)
    
    iva_general = subtotal_general * Decimal('0.16') if subtotal_general else Decimal('0.00')
    total_general = subtotal_general + iva_general
    cart_count = sum(item.cantidad for item in detalles)

    subtotal_item = Decimal('0.00') if eliminado else (detalle.cantidad * (producto.precio_venta or Decimal('0.00')))

    tasa_bcv = ConfiguracionSistema.get_tasa_actual()
    total_bs = round(total_general * tasa_bcv, 2)

    return JsonResponse({
        'status': status,
        'mensaje': mensaje,
        'eliminado': eliminado,
        'cantidad': 0 if eliminado else detalle.cantidad,
        'subtotal_item': f"{subtotal_item:.2f}",
        'subtotal_general': f"{subtotal_general:.2f}",
        'iva_general': f"{iva_general:.2f}",
        'total_general': f"{total_general:.2f}",
        'tasa_bcv': f"{tasa_bcv:.4f}",
        'total_bs': f"{total_bs:.2f}",
        'cart_count': cart_count,
    })


@login_required
@require_POST
def eliminar_del_carrito(request, id_producto):
    """Elimina por completo un producto del carrito de compras (Compatible con alias)."""
    carrito = get_object_or_404(Carrito, cedula_usuario=request.user)
    producto = get_object_or_404(Producto, pk=id_producto)
    detalle = get_object_or_404(CarritoDetalle, id_carrito=carrito, id_producto=producto)

    detalle.delete()

    # Recalcular métricas generales del carrito usando Decimal
    detalles = CarritoDetalle.objects.filter(id_carrito=carrito)
    subtotal_general = sum(item.cantidad * (item.id_producto.precio_venta or Decimal('0.00')) for item in detalles)
    
    iva_general = subtotal_general * Decimal('0.16') if subtotal_general else Decimal('0.00')
    total_general = subtotal_general + iva_general
    cart_count = sum(item.cantidad for item in detalles)

    tasa_bcv = ConfiguracionSistema.get_tasa_actual()
    total_bs = round(total_general * tasa_bcv, 2)

    return JsonResponse({
        'status': 'success',
        'mensaje': f"Se eliminó '{producto.nombre}' del carrito.",
        'subtotal_general': f"{subtotal_general:.2f}",
        'iva_general': f"{iva_general:.2f}",
        'total_general': f"{total_general:.2f}",
        'tasa_bcv': f"{tasa_bcv:.4f}",
        'total_bs': f"{total_bs:.2f}",
        'cart_count': cart_count,
    })


# Alias por compatibilidad de URL
eliminar_carrito = eliminar_del_carrito






@login_required
@require_POST
def crear_pedido_desde_carrito(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    carrito = get_object_or_404(Carrito, cedula_usuario=request.user)
    detalles = CarritoDetalle.objects.filter(id_carrito=carrito).select_related('id_producto')

    if not detalles.exists():
        msg = "Tu carrito está vacío."
        return JsonResponse({'status': 'error', 'mensaje': msg}, status=400) if is_ajax else redirect('ver_carrito')

    tipo_entrega = request.POST.get('tipo_entrega', Pedido.TipoEntrega.RETIRO)
    if tipo_entrega not in [c[0] for c in Pedido.TipoEntrega.choices]:
        tipo_entrega = Pedido.TipoEntrega.RETIRO

    direccion_envio = request.POST.get('direccion_envio', '').strip()
    if tipo_entrega == Pedido.TipoEntrega.DELIVERY and not direccion_envio:
        msg = "Debes ingresar una dirección de entrega para la modalidad de envío a domicilio (Delivery)."
        return JsonResponse({'status': 'error', 'mensaje': msg}, status=400) if is_ajax else redirect('ver_carrito')

    try:
        costo_envio = Decimal(str(request.POST.get('costo_envio', '0.00')).strip() or '0.00')
    except Exception:
        costo_envio = Decimal('0.00')

    if tipo_entrega == Pedido.TipoEntrega.RETIRO:
        costo_envio = Decimal('0.00')
        direccion_envio = ''

    tasa_bcv = ConfiguracionSistema.get_tasa_actual()

    try:
        with transaction.atomic():
            monto_subtotal = Decimal('0.00')
            detalles_a_procesar = []

            for item in detalles:
                # Bloqueo pesimista para evitar carreras de stock (Race Conditions)
                prod = Producto.objects.select_for_update().get(pk=item.id_producto.pk)
                
                stock_res = prod.reservado if hasattr(prod, 'reservado') and prod.reservado is not None else getattr(prod, 'stock_reservado', 0) or 0
                disponible = prod.stock_actual - stock_res
                
                if disponible < item.cantidad:
                    msg = f"Stock insuficiente para '{prod.nombre}'. Disponibles: {disponible}."
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'mensaje': msg}, status=400)
                    messages.error(request, msg)
                    return redirect('ver_carrito')

                sub = (prod.precio_venta or Decimal('0.00')) * item.cantidad
                monto_subtotal += sub
                detalles_a_procesar.append((prod, item.cantidad, sub))

            monto_iva = monto_subtotal * Decimal('0.16')
            total_con_iva = monto_subtotal + monto_iva + costo_envio

            # 1. Crear Pedido (estado inicial: PENDIENTE)
            nuevo_pedido = Pedido.objects.create(
                cedula_usuario=request.user,
                estado_pedido=Pedido.EstadoPedido.PENDIENTE,
                total=total_con_iva,
                tasa_cambio=tasa_bcv,
                tipo_entrega=tipo_entrega,
                costo_envio=costo_envio,
                direccion_envio=direccion_envio
            )

            # 2. Crear detalles e incrementar reserva de stock
            for prod, cant, sub in detalles_a_procesar:
                PedidoDetalle.objects.create(
                    cod_pedido=nuevo_pedido,
                    id_producto=prod,
                    cantidad=cant,
                    precio_unitario=prod.precio_venta,
                    subtotal=sub
                )
                if hasattr(prod, 'reservado'):
                    prod.reservado = (prod.reservado or 0) + cant
                    prod.save()
                elif hasattr(prod, 'stock_reservado'):
                    prod.stock_reservado = (prod.stock_reservado or 0) + cant
                    prod.save()

            # 3. Vaciar el carrito
            detalles.delete()

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'mensaje': 'Pedido generado correctamente.',
                    'cod_pedido': str(nuevo_pedido.cod_pedido),
                    'total': f"{nuevo_pedido.total:.2f}",
                    'total_bs': f"{nuevo_pedido.total_bolivares:.2f}",
                    'tasa_cambio': f"{nuevo_pedido.tasa_cambio:.4f}",
                    'tipo_entrega': nuevo_pedido.tipo_entrega
                })

            messages.success(request, f"Pedido #{nuevo_pedido.cod_pedido} registrado.")
            return redirect('pago_reportar', cod_pedido=nuevo_pedido.cod_pedido)

    except Exception as e:
        error_msg = f"Error al generar el pedido: {str(e)}"
        if is_ajax:
            return JsonResponse({'status': 'error', 'mensaje': error_msg}, status=500)
        messages.error(request, error_msg)
        return redirect('ver_carrito')

        
import uuid

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal

# Importa tus modelos


@login_required
@require_POST
def reportar_pago_cliente(request, cod_pedido):
    pedido = get_object_or_404(Pedido, cod_pedido=cod_pedido, cedula_usuario=request.user)
    
    metodo_pago = request.POST.get('metodo_pago', 'Pago Movil')
    referencia = request.POST.get('numero_referencia', '')
    banco_origen = request.POST.get('banco_origen', '')
    # Capturar imagen/comprobante enviado vía multipart/form-data
    comprobante_archivo = request.FILES.get('comprobante_img')
    
    try:
        monto_reportado = Decimal(request.POST.get('monto_pago', str(pedido.total)))
    except Exception:
        monto_reportado = pedido.total

    try:
        with transaction.atomic():
            # 1. Generar la Factura borrador/por cobrar vinculada al pedido
            subtotal = pedido.total / Decimal('1.16')
            factura = Factura.objects.create(
                cedula_usuario=request.user,
                cod_pedido=pedido,
                subtotal=subtotal,
                total_pagado=monto_reportado
            )

            # Insertar los renglones de la factura
            for item in pedido.pedidodetalle_set.all():
                FacturaDetalle.objects.create(
                    id_factura=factura,
                    id_producto=item.id_producto,
                    cantidad=item.cantidad,
                    precio_unitario_historico=item.precio_unitario,
                    porcentaje_descuento=Decimal('0.00'),
                    impuesto_aplicado=item.subtotal * Decimal('0.16'),
                    subtotal_linea=item.subtotal
                )

            # 2. Registrar la Transacción apuntando a la Factura (Usando TextChoices)
            nueva_transaccion = Transaccion.objects.create(
                id_factura=factura,
                monto_total_a_pagar=pedido.total,
                monto_total_recibido=monto_reportado,
                estado_transaccion=Transaccion.EstadoTransaccion.EN_PROCESO,
                descripcion=f"Pago reportado para Pedido #{pedido.cod_pedido}"
            )

            # 3. Registrar el detalle del pago (Incluyendo el comprobante en imagen si se adjuntó)
            TransaccionDetalle.objects.create(
                id_transaccion=nueva_transaccion,
                metodo_pago=metodo_pago,
                monto_pago_linea=monto_reportado,
                referencia_pasarela=referencia,
                banco_origen=banco_origen,
                comprobante_img=comprobante_archivo
            )

            # 4. Actualizar estado del pedido
            pedido.estado_pedido = Pedido.EstadoPedido.EN_PROCESO
            pedido.save()

            # 5. Notificar a los Administradores en un solo Query


            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'mensaje': 'Comprobante enviado a revisión.'})

            messages.success(request, "Tu comprobante de pago ha sido enviado a revisión.")
            return redirect('inicio_tienda')

    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)
        messages.error(request, f"Error al registrar el comprobante: {str(e)}")
        return redirect('ver_carrito')


