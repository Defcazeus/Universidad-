
from django.urls import path
from . import views

urlpatterns = [
    path("inicio_tienda/", views.inicio_tienda, name="inicio_tienda"),  # Esto será la página para la venta de repuestos
    path("tienda/carrito/", views.carrito_list, name="ver_carrito"),
    path("tienda/carrito/agregar/<int:id_producto>/", views.carrito_agregar, name="agregar_al_carrito"),
    path("tienda/carrito/eliminar/<int:id_producto>/", views.eliminar_carrito, name="eliminar_del_carrito"),
    path("tienda/carrito/actualizar/<int:id_producto>/<str:accion>/", views.actualizar_carrito, name="actualizar_carrito"),
    path('pedido/crear-desde-carrito/', views.crear_pedido_desde_carrito, name='procesar_compra'),
    path('pedido/<uuid:cod_pedido>/reportar-pago/', views.reportar_pago_cliente, name='pago_reportar'),




]