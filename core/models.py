import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
import re
from django.utils import timezone

# ==========================================
# MANAGER Y USUARIO
# ==========================================

class ConfiguracionSistema(models.Model):
    tasa_dolar_bcv = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=0.0000, 
        verbose_name="Tasa de Cambio Oficial (USD/VES)"
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuración del Sistema"

    @classmethod
    def get_tasa_actual(cls):
        config = cls.objects.first()
        if config and config.tasa_dolar_bcv and config.tasa_dolar_bcv > 0:
            return config.tasa_dolar_bcv
        try:
            from .context_processors import actualizar_tasa_dolar_bcv
            res = actualizar_tasa_dolar_bcv(forzar=False)
            if res and res.get('tasa') and res['tasa'] > 0:
                return res['tasa']
        except Exception:
            pass
        return Decimal('45.2000')

    def __str__(self):
        return f"Tasa USD: {self.tasa_dolar_bcv} BS (Actualizado: {self.ultima_actualizacion.strftime('%d/%m/%Y %H:%M')})"


class UsuarioManager(BaseUserManager):
    def create_user(self, correo, nombre, apellido, cedula_usuario, password=None, **extra_fields):

        if not cedula_usuario:
            raise ValueError('El usuario debe tener una cédula de identidad')

        correo = self.normalize_email(correo)
        user = self.model(
            correo=correo,
            nombre=nombre,
            apellido=apellido,
            cedula_usuario=cedula_usuario,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, nombre, apellido, cedula_usuario, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(correo, nombre, apellido, cedula_usuario, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    cedula_usuario = models.CharField(primary_key=True, max_length=20)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True, max_length=150)
    telefono = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    direccion = models.CharField(max_length=100, null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    EMAIL_FIELD = "correo"
    REQUIRED_FIELDS = ['nombre', 'apellido', 'cedula_usuario']

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"


    def clean(self):
        super().clean()
        if self.cedula_usuario:
            # Validar que cumpla con el formato: Letra + Guión + 6 a 9 dígitos
            patron = r'^(V|E|J|G|P)\d{6,9}$'
            if not re.match(patron, self.cedula_usuario.upper()):
                raise ValidationError({
                    'cedula_usuario': 'El formato de la cédula debe ser tipo V12345678 o E87654321.'
                })

    def save(self, *args, **kwargs):
        # Forzamos la letra inicial en mayúscula antes de guardar en DB
        if self.cedula_usuario:
            self.cedula_usuario = self.cedula_usuario.upper().strip()
        self.full_clean()  # Ejecuta las validaciones de clean() automáticamente
        super().save(*args, **kwargs)


class RecuperarContrasenna(models.Model):
    id_token = models.AutoField(primary_key=True)
    cedula_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='cedula_usuario')
    token = models.CharField(max_length=100, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)

    class Meta:
        db_table = 'recuperar_contrasenna'



# ==========================================
# CATÁLOGOS E INVENTARIO
# ==========================================

class CatProducto(models.Model):
    id_cat_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'cat_producto'

    def __str__(self):
        return self.nombre

class CatServicio(models.Model):
    id_cat_servicio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    duracion_estimada = models.CharField(max_length=50)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'cat_servicio'

    def __str__(self):
        return self.nombre + ' - ' + self.duracion_estimada + ' - ' + str(self.precio_base)


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    id_cat_producto = models.ForeignKey(CatProducto, on_delete=models.PROTECT, db_column='id_cat_producto', null=True, blank=True)
    nombre = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    reservado = models.IntegerField(default=0)
    imagen_url = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)

    @property
    def stock_disponible(self):
        return self.stock_actual - self.reservado 

    class Meta:
        db_table = 'producto'


class InformacionEmpresa(models.Model):
    id_info = models.AutoField(primary_key=True)
    mision = models.TextField()
    vision = models.TextField()
    telefono_taller = models.CharField(max_length=20)
    correo_contacto = models.CharField(max_length=100)
    direccion_fisica = models.TextField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'informacion_empresa'


class Galeria(models.Model):
    id_foto = models.AutoField(primary_key=True)
    titulo_foto = models.CharField(max_length=150, blank=True, null=True)
    ruta_archivo = models.CharField(max_length=255)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    id_info = models.ForeignKey(InformacionEmpresa, on_delete=models.CASCADE, db_column='id_info')

    class Meta:
        db_table = 'galeria'

# ==========================================
# VEHÍCULOS, CITAS Y TALLER
# ==========================================

class Vehiculo(models.Model):
    placa = models.CharField(primary_key=True, max_length=15)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anno = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)
    cedula_usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='cedula_usuario')
    color = models.CharField(max_length=50, blank=True, null=True)

    
    class Meta:
        db_table = 'vehiculo'

    def __str__(self):
        return self.placa + ' - ' + self.marca + ' ' + self.modelo + ' - ' + str(self.anno) + ' - ' + "Dueño: " + str(self.cedula_usuario.nombre)


class Cita(models.Model):
    cod_cita = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_entrada = models.DateTimeField()
    fecha_entrega_estimada = models.DateTimeField(blank=True, null=True)
    estado_cita = models.CharField(max_length=50, default='Pendiente')
    motivo_ingreso = models.CharField(max_length=255, blank=True, null=True)
    id_tipo_servicio = models.ForeignKey(CatServicio, on_delete=models.PROTECT, db_column='id_tipo_servicio', null=True, blank=True)
    placa = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, db_column='placa', null=True, blank=True)
    cedula_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='cedula_usuario', null=True, blank=True)

    class Meta:
        db_table = 'cita'

    def __str__(self):
        return f"Cita: {self.fecha_entrada}"

class ServicioTaller(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    estado_orden = models.CharField(max_length=40, default='En Proceso')
    cod_cita = models.OneToOneField(Cita, on_delete=models.PROTECT, db_column='cod_cita')

    class Meta:
        db_table = 'servicio_taller'



class ServicioDetalle(models.Model):
    id_servicio_detalle = models.AutoField(primary_key=True)
    cantidad_producto = models.IntegerField(default=1)
    id_cat_servicio = models.ForeignKey(CatServicio, on_delete=models.PROTECT, db_column='id_cat_servicio', null=True, blank=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_column='id_producto', null=True, blank=True)
    id_servicio = models.ForeignKey(ServicioTaller, on_delete=models.CASCADE, db_column='id_servicio')

    class Meta:
        db_table = 'servicio_detalle'

# ==========================================
# E-COMMERCE Y VENTAS
# ==========================================

class Carrito(models.Model):
    id_carrito = models.AutoField(primary_key=True)
    cedula_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='cedula_usuario')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carrito'


class CarritoDetalle(models.Model):
    id_carrito_d = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=1)
    id_carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, db_column='id_carrito')
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_producto')

    class Meta:
        db_table = 'carrito_detalle'



class Pedido(models.Model):
    class EstadoPedido(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente de Pago'
        EN_PROCESO = 'En Proceso', 'En Proceso de Pago'
        COMPLETADO = 'Completado', 'Completado'
        CANCELADO = 'Cancelado', 'Cancelado / Invalidado'

    # Tipo de entrega (Retiro en tienda por defecto)
    class TipoEntrega(models.TextChoices):
        RETIRO = 'Retiro', 'Retiro en Tienda'
        DELIVERY = 'Delivery', 'Envío a Domicilio'

    cod_pedido = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    
    estado_pedido = models.CharField(
        max_length=20,
        choices=EstadoPedido.choices,
        default=EstadoPedido.PENDIENTE
    )
    
    # Total general del pedido (Productos + IVA + Costo de Envío) en USD
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Tasa del Dólar fijada al procesar/congelar la orden
    tasa_cambio = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=Decimal('1.0000'),
        help_text="Valor de la tasa de cambio oficial (USD/VES) al momento de procesar o congelar el pedido"
    )
    
    # ==========================================
    # GESTIÓN DE DELIVERY / ENTREGA
    # ==========================================
    tipo_entrega = models.CharField(
        max_length=20,
        choices=TipoEntrega.choices,
        default=TipoEntrega.RETIRO,
        help_text="Indica si el pedido es para retirar en local o envío a domicilio"
    )

    costo_envio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costo adicional por concepto de delivery en USD (0.00 si es gratis o retiro en tienda)"
    )

    direccion_envio = models.TextField(
        blank=True,
        null=True,
        help_text="Dirección detallada y punto de referencia para la entrega (solo si es Delivery)"
    )

    cedula_usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='cedula_usuario')

    class Meta:
        db_table = 'pedido'

    @property
    def total_bolivares(self):
        """Retorna el equivalente exacto del total en Bolívares usando la tasa registrada."""
        if self.total and self.tasa_cambio:
            return round(self.total * self.tasa_cambio, 2)
        return Decimal('0.00')

    @property
    def es_delivery(self):
        """Helper para verificar fácilmente en plantillas si requiere despacho."""
        return self.tipo_entrega == self.TipoEntrega.DELIVERY

    @property
    def detalles_ventas(self):
        """Helper para compatibilidad con código o plantillas que usen detalles_ventas."""
        return self.pedidodetalle_set.all()

    def __str__(self):
        return f"Pedido {self.cod_pedido} - {self.get_estado_pedido_display()} ({self.tipo_entrega}) - ${self.total}"


class PedidoDetalle(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    descripcion_manual = models.TextField(blank=True, null=True)
    cantidad = models.IntegerField(default=1)
    
    # Fotografía histórica del precio unitario en USD
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    id_cat_servicio = models.ForeignKey(CatServicio, on_delete=models.PROTECT, db_column='id_cat_servicio', null=True, blank=True)
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='cod_pedido')
    id_producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_column='id_producto', null=True, blank=True)

    class Meta:
        db_table = 'pedido_detalle'

    def save(self, *args, **kwargs):
        # Si no tiene precio unitario definido, asigna el actual según el catálogo
        if self.precio_unitario is None or self.precio_unitario == 0:
            if self.id_producto:
                self.precio_unitario = self.id_producto.precio_venta
            elif self.id_cat_servicio:
                self.precio_unitario = self.id_cat_servicio.precio_base or Decimal('0.00')

        self.subtotal = self.cantidad * (self.precio_unitario or Decimal('0.00'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.tipo_notificacion}] Para {self.usuario.get_full_name()} - {self.titulo}"

# ==========================================
# FACTURACIÓN Y PAGOS
# ==========================================

class Factura(models.Model):
    id_factura = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, db_column='cod_pedido', null=True, blank=True)
    id_servicio = models.ForeignKey(ServicioTaller, on_delete=models.PROTECT, db_column='id_servicio', null=True, blank=True)
    cedula_usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='cedula_usuario')
    identificador = models.CharField(max_length=100, unique=True, editable=False)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.identificador:
            fecha_str = timezone.now().strftime('%Y%m%d')
            codigo_unico = uuid.uuid4().hex[:6].upper()
            self.identificador = f"FAC-{fecha_str}-{codigo_unico}"
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'factura'


class FacturaDetalle(models.Model):
    id_factura_detalle = models.AutoField(primary_key=True)
    id_factura = models.ForeignKey(Factura, on_delete=models.CASCADE, db_column='id_factura')
    id_producto = models.ForeignKey(Producto, on_delete=models.PROTECT, db_column='id_producto', null=True, blank=True)
    id_cat_servicio = models.ForeignKey(CatServicio, on_delete=models.PROTECT, db_column='id_cat_servicio', null=True, blank=True)
    cantidad = models.IntegerField()
    precio_unitario_historico = models.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    impuesto_aplicado = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    subtotal_linea = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta: 
        db_table = 'factura_detalle'


class Transaccion(models.Model):
    class EstadoTransaccion(models.TextChoices):
        EN_PROCESO = 'En Verificacion', 'En Verificación'
        APROBADA = 'Aprobada', 'Aprobada / Confirmada'
        RECHAZADA = 'Rechazada', 'Rechazada'

    id_transaccion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_factura = models.ForeignKey(Factura, on_delete=models.CASCADE, db_column='id_factura')
    monto_total_a_pagar = models.DecimalField(max_digits=10, decimal_places=2)
    monto_total_recibido = models.DecimalField(max_digits=10, decimal_places=2)
    estado_transaccion = models.CharField(
        max_length=20,
        choices=EstadoTransaccion.choices,
        default=EstadoTransaccion.EN_PROCESO
    )
    fecha_pago = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transaccion'


class TransaccionDetalle(models.Model):
    class MetodoPago(models.TextChoices):
        PAGO_MOVIL = 'Pago Movil', 'Pago Móvil'
        TRANSFERENCIA = 'Transferencia', 'Transferencia Bancaria'
        EFECTIVO = 'Efectivo', 'Efectivo en Tienda'
        PUNTO_VENTA = 'Punto de Venta', 'Punto de Venta'

    id_transaccion_detalle = models.AutoField(primary_key=True)
    id_transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE, db_column='id_transaccion')
    metodo_pago = models.CharField(max_length=30, choices=MetodoPago.choices, default=MetodoPago.PAGO_MOVIL)
    monto_pago_linea = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campo de texto (Referencia manual) -> OBLIGATORIO para Pago Móvil / Transferencia
    referencia_pasarela = models.CharField(max_length=100, blank=True, null=True)
    banco_origen = models.CharField(max_length=50, blank=True, null=True)
    
    # Campo para adjuntar la capturas o comprobante en imagen/PDF -> OPCIONAL
    comprobante_img = models.ImageField(upload_to='comprobantes_pago/%Y/%m/', blank=True, null=True)

    class Meta:
        db_table = 'transaccion_detalle'

class FlujoCaja(models.Model):
    id_bitacora_caja = models.AutoField(primary_key=True)
    cedula_usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='cedula_usuario')
    tipo_evento_financiero = models.CharField(max_length=100)
    monto_afectado = models.DecimalField(max_digits=10, decimal_places=2)
    detalles_evento = models.TextField()
    fecha_evento = models.DateTimeField(auto_now_add=True)
    id_transaccion = models.ForeignKey(Transaccion, on_delete=models.SET_NULL, db_column='id_transaccion', null=True, blank=True)

    class Meta:
        db_table = 'flujo_caja'

# ==========================================
# HISTORIALES Y MOVIMIENTOS
# ==========================================

class MovimientosProducto(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    tipo_movimiento = models.CharField(max_length=50, db_comment='ENTRADA_COMPRA, SALIDA_VENTA, ETC')
    cantidad = models.IntegerField()
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_producto')
    id_servicio = models.ForeignKey(ServicioTaller, on_delete=models.SET_NULL, db_column='id_servicio', null=True, blank=True)
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.SET_NULL, db_column='cod_pedido', null=True, blank=True)

    class Meta:
        db_table = 'movimientos_producto'


class HistorialPedido(models.Model):
    id_historial_entrega = models.AutoField(primary_key=True)
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, db_column='cod_pedido')
    telefono_contacto_momento = models.CharField(max_length=20)
    metodo_envio = models.CharField(max_length=50)
    fecha_despacho = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'historial_pedido'


class HistorialServicio(models.Model):
    id_historial_serv = models.AutoField(primary_key=True)
    id_servicio = models.ForeignKey(ServicioTaller, on_delete=models.CASCADE, db_column='id_servicio')
    estado_servicio = models.CharField(max_length=50)
    notas_progreso = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_servicio'


class HistorialVehiculo(models.Model):
    id_historial_vehiculo = models.AutoField(primary_key=True)
    placa = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, db_column='placa')
    cod_cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, db_column='cod_cita', null=True, blank=True)
    kilometraje_ingreso = models.IntegerField()
    diagnostico_final = models.TextField()
    reparaciones_realizadas = models.TextField()
    observaciones_recomendas = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_vehiculo'




import re
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notificacion(models.Model):
    # Tipos de notificaciones para clasificar los eventos
    class TipoNotificacion(models.TextChoices):
        PEDIDO_CONFIRMADO = 'PEDIDO_CONFIRMADO', 'Pedido Confirmado'
        PEDIDO_CANCELADO = 'PEDIDO_CANCELADO', 'Pedido Cancelado'
        PEDIDO_REQUIERE_REVISION = 'PEDIDO_REQUIERE_REVISION', 'Pedido Requiere Revisión'
        CITA_CADUCADA = 'CITA_CADUCADA', 'Cita Caducada'
        ALERTA_SISTEMA = 'ALERTA_SISTEMA', 'Alerta del Sistema'

    # Destinatario único (conectado a tu modelo Usuario personalizado)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    
    tipo_notificacion = models.CharField(
        max_length=50,
        choices=TipoNotificacion.choices
    )
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # --- Relación Genérica (Para vincular a Pedidos, Citas, etc.) ---
    tipo_contenido = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    # CharField de max_length=20 para coincidir con tu PK (cedula_usuario u otros IDs tipo texto)
    id_objeto = models.CharField(max_length=50, null=True, blank=True)
    objeto_destino = GenericForeignKey('tipo_contenido', 'id_objeto')

    class Meta:
        ordering = ['-fecha_creacion']
        indexes = [
            # Optimiza la consulta del contador de no leídas por usuario
            models.Index(fields=['usuario', 'leido']),
        ]

    def __str__(self):
        return f"[{self.tipo_notificacion}] Para {self.usuario.get_full_name()} - {self.titulo}"
