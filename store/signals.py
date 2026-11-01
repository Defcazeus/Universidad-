from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Pedido, Notificacion, Usuario, Factura

def notificar_administradores(tipo, titulo, mensaje, objeto=None):
    """Crea una notificación para TODOS los usuarios staff/admin activos."""
    administradores = Usuario.objects.filter(is_staff=True, is_active=True)
    
    notificaciones = [
        Notificacion(
            usuario=admin,
            tipo_notificacion=tipo,
            titulo=titulo,
            mensaje=mensaje,
            objeto_destino=objeto
        )
        for admin in administradores
    ]
    # Inserta todas las notificaciones en una sola consulta SQL
    Notificacion.objects.bulk_create(notificaciones)


def notificar_cliente(usuario_cliente, tipo, titulo, mensaje, objeto=None):
    """Crea una notificación individual para un cliente específico."""
    Notificacion.objects.create(
        usuario=usuario_cliente,
        tipo_notificacion=tipo,
        titulo=titulo,
        mensaje=mensaje,
        objeto_destino=objeto
    )





@receiver(post_save, sender=Factura)
def crear_notificacion_factura(sender, instance, created, **kwargs):
    # 1. Cuando se CREA un pedido nuevo por primera vez
    user =  instance.cedula_usuario
    
    if created:
        # Notificar al cliente que su pedido fue registrado
        Notificacion.objects.create(
            usuario=user,
            tipo_notificacion=Notificacion.TipoNotificacion.ALERTA_SISTEMA,
            titulo=f"Factura #{instance.cod_pedido} creada",
            mensaje="Se ha creado una factura de pago, revisa MIS FACTURAS para mas información.",
            objeto_destino=instance
        )

@receiver(post_save, sender=Pedido)
def gestionar_notificaciones_pedido(sender, instance, created, **kwargs):
    cliente = instance.cedula_usuario

    # A. Cuando se CREA un pedido por primera vez
    if created:
        # 1. Notificar al Cliente que su pedido fue registrado
        notificar_cliente(
            usuario_cliente=cliente,
            tipo=Notificacion.TipoNotificacion.ALERTA_SISTEMA,
            titulo=f"Pedido #{instance.cod_pedido} registrado",
            mensaje="Tu pedido fue creado exitosamente. Por favor, realiza el pago y reporta tu comprobante.",
            objeto=instance
        )

        # 2. Notificar a TODOS los Admins que hay un pedido nuevo
        notificar_administradores(
            tipo=Notificacion.TipoNotificacion.PEDIDO_REQUIERE_REVISION,
            titulo=f"Nuevo Pedido #{instance.cod_pedido}",
            mensaje=f"El cliente {cliente.get_full_name()} ha creado un pedido por un total de {instance.total} BS.",
            objeto=instance
        )

    # B. Cuando el pedido CAMBIA DE ESTADO
    else:
        if instance.estado_pedido == Pedido.EstadoPedido.COMPLETADO:
            notificar_cliente(
                usuario_cliente=cliente,
                tipo=Notificacion.TipoNotificacion.PEDIDO_CONFIRMADO,
                titulo=f"¡Pedido #{instance.cod_pedido} Confirmado!",
                mensaje="Hemos validado tu pago. Tu pedido se encuentra en preparación.",
                objeto=instance
            )

        elif instance.estado_pedido == Pedido.EstadoPedido.CANCELADO:
            notificar_cliente(
                usuario_cliente=cliente,
                tipo=Notificacion.TipoNotificacion.PEDIDO_CANCELADO,
                titulo=f"Pedido #{instance.cod_pedido} Cancelado",
                mensaje="Tu pedido ha sido cancelado. Ponte en contacto con soporte si tienes dudas.",
                objeto=instance
            )