# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView, LoginView
from .forms import CustomPasswordResetForm

from django.conf import settings

from django.conf.urls.static import static

from django.urls import path
from . import views

urlpatterns = [
    path('reset_password/', views.solicitar_codigo_recuperacion, name="reset_password"),
    path('verificar_codigo/', views.verificar_codigo_reset, name="verificar_codigo_reset"),
    path('cambiar_password/', views.cambiar_password_final, name="cambiar_password_final"),
    path("validar_correo_recuperacion/", views.validar_correo_recuperacion, name="validar_correo_recuperacion"),
    path("validar_cedula_recuperacion/", views.validar_cedula_recuperacion, name="validar_cedula_recuperacion"),
    path('api/notificaciones/', views.obtener_notificaciones_ajax, name='api_notificaciones'),
    path('api/notificaciones/marcar-leida/<int:notificacion_id>/', views.marcar_notificacion_leida, name='api_marcar_leida'),

    path("", views.home, name="home"),  # Esto será la página de inicio
    path("login/", views.inicio_sesion, name="login"),  # Esto será la página de iniciar sesion
    path("login/registro/", views.registro, name="registro"),  # Esto será la página de registro

    path("logout/", LogoutView.as_view(next_page='login'), name="logout"),  # Esto será la página de logout
    path('admin/', views.home_admin, name='home_admin'),  # Esto será la página del menu




    path('home_user/', views.home_user, name='home_user'),
    path('vehiculos_user/', views.vehiculos_user, name='vehiculos_user'),


    path('gestion/citas/', views.agenda_citas_list_user, name='agenda_citas_list'),
    path('gestion/citas/crear/', views.cita_crear, name='agenda_cita_crear'),
    path('gestion/citas/api/<int:cod_cita>/', views.agenda_cita_detalle_api, name='agenda_cita_detalle_api'),
    path('gestion/citas/editar/<int:cod_cita>/', views.agenda_cita_editar, name='agenda_cita_editar'),

    path('admin/clientes/', views.clientes_list, name='clientes_list'),
    path('admin/clientes/api/<str:cedula_usuario>/', views.cliente_api, name='cliente_api'),
    path('admin/clientes/crear/', views.cliente_crear, name='cliente_crear'),
    path('admin/clientes/editar/<str:pk>/', views.cliente_editar, name='cliente_editar'),

    path('admin/vehiculos/', views.vehiculos_list, name='vehiculos_list'),
    path('admin/vehiculos/api/<str:pk>/', views.vehiculo_api, name='vehiculo_api'),
    path('admin/vehiculos/crear/', views.vehiculo_crear, name='vehiculo_crear'),
    path('admin/vehiculos/editar/<str:pk>/', views.vehiculo_editar, name='vehiculo_editar'),
    path('admin/historial_vehiculos/', views.historial_vehiculo_list, name='historial_vehiculo_list'),
    path('admin/historial_vehiculos/<str:placa>/', views.historial_vehiculo_detalle, name='historial_vehiculo_detalle'),
    path('admin/historial_vehiculos/api/<str:placa>/', views.historial_vehiculo_detalle_api, name='historial_vehiculo_detalle_api'),


    path("admin/cat_servicios/", views.servicio_list, name="servicio_list"),  # Esto será la página para el módulo de catálogo de servicios
    path("admin/cat_servicios/crear/", views.servicio_crear, name="servicio_crear"),  # Esto será la página para crear un servicio
    path("admin/cat_servicios/editar/<str:pk>/", views.servicio_editar, name="servicio_editar"),  # Esto será la página para editar un servicio
    path("admin/cat_servicios/api/<str:pk>/", views.servicio_api_detalle, name="servicio_api_detalle"),  # Esto será la página para editar un servicio

    path('admin/citas/', views.citas_list, name='citas_list'),
    path('admin/citas/crear/', views.cita_crear, name='cita_crear'),
    path('admin/citas/editar/<uuid:cod_cita>/', views.cita_editar, name='cita_editar'),
    path('admin/citas/api/<uuid:cod_cita>/', views.cita_api, name='cita_api'),  # Esto será la página para el módulo de citas


    path('admin/ordenes/', views.ordenes_trabajo_list, name='ordenes_trabajo_list'),
    path('admin/ordenes/api/<int:id_servicio>/', views.orden_trabajo_api, name='orden_trabajo_api'),
    path('admin/ordenes/crear/', views.orden_trabajo_crear, name='orden_trabajo_crear'),
    path('admin/ordenes/cargar-item/', views.orden_trabajo_cargar_item, name='orden_trabajo_cargar_item'),
    path('admin/ordenes/eliminar-item/<int:id_detalle>/', views.orden_trabajo_eliminar_item, name='orden_trabajo_eliminar_item'),

    path('admin/citas/cambiar-estado/<uuid:cod_cita>/', views.cambiar_estado_cita_taller, name='cambiar_estado_cita_taller'),


    path('admin/inventario/', views.inventario_list, name='inventario_list'),
    path('admin/inventario/api/<int:id_producto>/', views.producto_api, name='producto_api'),
    path('admin/inventario/categoria/crear/', views.categoria_crear, name='categoria_crear'),
    path('admin/inventario/producto/crear/', views.producto_crear, name='producto_crear'),
    path('admin/inventario/producto/editar/<int:id_producto>/', views.producto_editar, name='producto_editar'),
    path('admin/inventario/movimiento/crear/', views.inventario_movimiento_crear, name='inventario_movimiento_crear'),
    path('admin/inventario/producto/estatus/<int:id_producto>/', views.producto_cambiar_estatus, name='producto_cambiar_estatus'),

    path("admin/venta_repuesto/", views.modulo_venta_repuestos, name="venta_repuestos"),  # Esto será la página para el módulo de venta de repuestos
    path("admin/portal_web/", views.modulo_portal_web, name="portal_web"),
    path("admin/galeria_dinamica/", views.modulo_galeria_dinamica, name="galeria_dinamica"),
    path("admin/notiacias_promociones/", views.modulo_noticias_promociones, name="noticias_promociones"),# Esto será la página para el módulo de portal web
    path("admin/finanzas/", views.modulo_finanzas, name="finanzas"),  # Esto será la página para el módulo de finanzas
    path("admin/inventario/<int:id_producto>/", views.ver_producto, name="ver_producto"),  # Esto será la página para ver un producto
    path("admin/clientes/cambiar_estado/<str:cedula>/", views.cambiar_estado_cliente, name="cambiar_estado_cliente"),  # Esto será la página para cambiar el estado de un cliente
    path("admin/servicio/<int:id_servicio>/", views.historial_servicio, name="historial_servicio"),  # Esto será la página para el historial de servicio
    path("admin/caja/", views.modulo_caja, name="modulo_caja"),  # Esto será la página para el módulo de caja
    path("admin/clientes/<str:cedula_usuario>/", views.historial_cliente, name="historial_cliente"),  # Esto será la página para el historial de cliente




    path('admin/pedidos/', views.pedido_list, name='pedido_list'),
    path('admin/pedidos/crear/', views.pedido_crear, name='pedido_crear'),
    path('admin/pedidos/editar/<uuid:cod_pedido>/', views.pedido_editar, name='pedido_editar'),
    path('admin/pedidos/api/<uuid:cod_pedido>/', views.pedido_api, name='pedido_api'),

    path('pedidos/api/<uuid:cod_pedido>/cambiar-estado/', views.cambiar_estado_pedido, name='cambiar_estado_pedido'),

    path('pedidos/api/<uuid:cod_pedido>/agregar-detalle/', views.agregar_detalle_api, name='agregar_detalle_api'),
    path('pedidos/api/eliminar-detalle/<int:id_detalle>/', views.eliminar_detalle_api, name='eliminar_detalle_api'),

    path('pedidos/api/productos/', views.listar_producto_api, name='listar_producto_api'),
    path('pedidos/api/servicios/', views.listar_servicio_api, name='listar_servicio_api'),

    path('admin/facturas/', views.factura_list, name='factura_list'),
    path('admin/facturas/<uuid:id_factura>/', views.factura_detalle_ajax, name='factura_detalle_ajax'),
    path('admin/facturas/anular/<uuid:id_factura>/', views.anular_factura, name='anular_factura'),

    path('admin/transacciones/', views.transaccion_list, name='transaccion_list'),
    path('admin/transacciones/api/<uuid:id_transaccion>/', views.transaccion_api, name='transaccion_api'),
    path('api/configuracion/actualizar-tasa/', views.actualizar_tasa_bcv_ajax, name='actualizar_tasa_bcv_ajax'),





    path('gestion/pedidos/', views.pedidos_cliente, name='pedido_clientes')

]




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
