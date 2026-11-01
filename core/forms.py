import email
import re
from decimal import Decimal

from typing_extensions import Required
from django import forms
from .models import Usuario
from .validators import val_cedula, val_telefono, val_email, val_solo_letras
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        # Mapea lo que el usuario escribe al campo 'correo' de tu modelo personalizado
        correo = self.cleaned_data.get('email')
        if not Usuario.objects.filter(correo=correo).exists():
            # Por seguridad de Django a veces se ignora, pero puedes validar aquí
            pass
        return correo

        
class RegistroUsuarioForm(forms.ModelForm):
    cod_cedula = forms.ChoiceField(
        choices=[('V-', 'V-'), ('E-', 'E-'), ('J-', 'J-')], 
        initial='V-'
    )
    cedula = forms.CharField(max_length=9, min_length=6, validators=[val_cedula])
    
    cod_tel = forms.ChoiceField(
        choices=[('0412','0412'), ('0414','0414'), ('0424','0424'), ('0416','0416'), ('0426','0426')]
    )
    num_tel = forms.CharField(max_length=7, min_length=7, validators=[val_telefono])

    # En el autoregistro la contraseña SIEMPRE es obligatoria
    password1 = forms.CharField(
        widget=forms.PasswordInput, 
        min_length=8,
        required=True,
        error_messages={'required': 'Debes ingresar una contraseña.'}
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput, 
        required=True,
        error_messages={'required': 'Debes confirmar tu contraseña.'}
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'direccion']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].validators.append(val_solo_letras)
        self.fields['apellido'].validators.append(val_solo_letras)
        self.fields['correo'].validators.append(val_email)
        # Para crearse una cuenta pública se requiere correo obligatoriamente
        self.fields['correo'].required = True 

    def clean(self):
        
        cleaned_data = super().clean()
        
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        cod_cedula = cleaned_data.get("cod_cedula")
        cedula_num = cleaned_data.get("cedula")
        cod_tel = cleaned_data.get("cod_tel")
        num_tel = cleaned_data.get("num_tel")
        correo = cleaned_data.get("correo")

        # 1. Cédula unificada sin guion (ej: V12345678)
        if cod_cedula and cedula_num:
            cedula_completa = f"{cod_cedula.replace('-', '')}{cedula_num.strip()}".upper()
            if Usuario.objects.filter(cedula_usuario=cedula_completa).exists():
                self.add_error('cedula', 'Esta cédula de identidad ya se encuentra registrada.')
            else:
                cleaned_data['cedula_usuario'] = cedula_completa

        # 2. Teléfono unificado (ej: 04121234567)
        if cod_tel and num_tel:
            cleaned_data['telefono'] = f"{cod_tel}{num_tel}"

        # 3. Validación estricta de coincidencia de contraseñas
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', "Las contraseñas no coinciden.")

        # 4. Verificación de correo único
        if correo:
            correo_limpio = correo.strip().lower()
            if Usuario.objects.filter(correo=correo_limpio).exists():
                self.add_error('correo', 'Este correo electrónico ya se encuentra registrado.')
            else:
                cleaned_data['correo'] = correo_limpio

        return cleaned_data



class ClienteAdminForm(RegistroUsuarioForm):
    # Desactivamos campos que no se usan o se manejan de forma compuesta
    password1 = forms.CharField(required=False, widget=forms.HiddenInput())
    password2 = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El correo es opcional para el admin
        self.fields['correo'].required = False
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        
        # Le aplicamos la clase CSS oscura directamente al campo por si Django lo invoca
        self.fields['cedula'].widget.attrs.update({
            'class': 'form-control text-white border-secondary',
            'style': 'background-color: #13131d !important;'
        })

    def clean(self):
        cleaned_data = super().clean()
        
        # Eliminamos errores de contraseñas ya que el admin no las usa
        if 'password2' in self._errors:
            del self._errors['password2']
        if 'password1' in self._errors:
            del self._errors['password1']

        if self.instance:
            cedula_unificada = cleaned_data.get('cedula_usuario')
            telefono_unificado = cleaned_data.get('telefono')

            if cedula_unificada:
                self.instance.cedula_usuario = cedula_unificada
            if telefono_unificado:
                self.instance.telefono = telefono_unificado
            
            if cedula_unificada:
                self.instance.set_password(cedula_unificada)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.cedula_usuario:
            user.set_password(user.cedula_usuario)
            
        if commit:
            user.save()
        return user




from .models import Vehiculo, Usuario

class VehiculoForm(forms.ModelForm):
    # Campo auxiliar para asociar la cédula del propietario desde la vista/modal
    cedula_usuario = forms.CharField(
        max_length=20,
        required=True,
        error_messages={'required': 'La cédula del propietario es obligatoria.'}
    )

    class Meta:
        model = Vehiculo
        fields = ['placa', 'marca', 'modelo', 'anno', 'color', 'descripcion']

    def clean_placa(self):
        placa = self.cleaned_data.get('placa', '').strip().upper()
        if not placa:
            raise forms.ValidationError("La placa es obligatoria.")
        return placa

    def clean_cedula_usuario(self):
        cedula = self.cleaned_data.get('cedula_usuario', '').strip()
        try:
            usuario = Usuario.objects.get(cedula_usuario=cedula)
            return usuario
        except Usuario.DoesNotExist:
            raise forms.ValidationError("El propietario con la cédula ingresada no existe.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.cedula_usuario = self.cleaned_data['cedula_usuario']
        if commit:
            instance.save()
        return instance

from .models import CatServicio

class ServicioForm(forms.ModelForm):
    class Meta:
        model = CatServicio
        fields = ['nombre', 'duracion_estimada', 'precio_base']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cambio de Pastillas de Freno'}),
            'duracion_estimada': forms.TimeInput(
                            format='%H:%M',
                            attrs={
                                'type': 'time',
                                'step': '60',  # Oculta los segundos
                                'class': 'input-time-24h w-full px-3 py-2 bg-slate-100 border-2 border-slate-300 rounded-xl text-xs font-mono font-bold text-slate-900 outline-none focus:border-orange-500 focus:bg-white cursor-pointer'
                            }
                        ),            
                        'precio_base': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
        }


    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        instance_pk = self.instance.pk
        
        # Validar duplicados ignorando mayúsculas/minúsculas
        query = CatServicio.objects.filter(nombre__iexact=nombre)
        if instance_pk:
            query = query.exclude(pk=instance_pk)
            
        if query.exists():
            raise forms.ValidationError(f"El servicio '{nombre}' ya existe en el catálogo.")
        return nombre

from .models import Cita, Vehiculo, CatServicio

from django import forms
from django.utils import timezone
from .models import Cita

class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['placa', 'id_tipo_servicio', 'fecha_entrada', 'fecha_entrega_estimada', 'motivo_ingreso']
        widgets = {
            'fecha_entrada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_entrega_estimada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'motivo_ingreso': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_fecha_entrada(self):
        fecha_entrada = self.cleaned_data.get('fecha_entrada')

        if fecha_entrada:
            # 1. Validar que la fecha de entrada no sea menor a la fecha/hora actual
            if fecha_entrada < timezone.now():
                raise forms.ValidationError("No se pueden agendar citas en fechas u horas pasadas.")

            # 2. Validar solapamiento / coincidencia exacta de fecha y hora
            # Si estamos editando una cita existente (self.instance.pk), la excluimos del chequeo
            query = Cita.objects.filter(fecha_entrada=fecha_entrada)
            
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)

            # Si el modelo Cita maneja estados (ej. Cancelada), puedes ignorar citas canceladas agregando:
            # query = query.exclude(estado_cita='Cancelada')

            if query.exists():
                raise forms.ValidationError("Ya existe otra cita programada para esta misma fecha y hora.")

        return fecha_entrada

    def clean(self):
        cleaned_data = super().clean()
        fecha_entrada = cleaned_data.get('fecha_entrada')
        fecha_entrega = cleaned_data.get('fecha_entrega_estimada')

        if fecha_entrada and fecha_entrega and fecha_entrada >= fecha_entrega:
            raise forms.ValidationError("La fecha de entrega estimada debe ser posterior a la fecha de entrada.")
        
        return cleaned_data


from django import forms
from .models import ServicioTaller, Cita, CatServicio, Producto


class AbrirOrdenTrabajoForm(forms.ModelForm):
    class Meta:
        model = ServicioTaller
        fields = ['cod_cita']  # Único campo presente en tu modelo ServicioTaller

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cod_cita'].queryset = Cita.objects.filter(
            estado_cita__in=['Pendiente', 'Aprobada']
        ).exclude(
            cod_cita__in=ServicioTaller.objects.values_list('cod_cita', flat=True)
        ).select_related('placa', 'id_tipo_servicio')

class CargarItemOrdenForm(forms.Form):
    TIPO_CARGO_CHOICES = [\
        ('SERVICIO', 'Servicio'),
        ('PRODUCTO', 'Producto'),
    ]
    
    id_servicio = forms.ModelChoiceField(queryset=ServicioTaller.objects.all())
    tipo_cargo = forms.ChoiceField(choices=TIPO_CARGO_CHOICES)
    id_cat_servicio = forms.ModelChoiceField(queryset=CatServicio.objects.filter(activo=True), required=False)
    id_producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True, stock_actual__gt=0), required=False)
    cantidad_producto = forms.IntegerField(min_value=1, initial=1, required=False)
    precio_unitario = forms.DecimalField(max_digits=10, decimal_places=2, required=False)

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_cargo')
        servicio = cleaned_data.get('id_cat_servicio')
        producto = cleaned_data.get('id_producto')
        cantidad = cleaned_data.get('cantidad_producto')

        if tipo == 'SERVICIO' and not servicio:
            self.add_error('id_cat_servicio', 'Seleccione un servicio válido.')
        
        elif tipo == 'PRODUCTO':
            if not producto:
                self.add_error('id_producto', 'Seleccione un repuesto válido.')
            if not cantidad or cantidad < 1:
                self.add_error('cantidad_producto', 'Ingrese una cantidad válida mayor a cero.')
            elif producto and cantidad > producto.stock_actual:
                self.add_error('cantidad_producto', f'Stock insuficiente. Disponible: {producto.stock_actual}')

        return cleaned_data


class CambiarEstatusOrdenForm(forms.ModelForm):
    class Meta:
        model = ServicioTaller
        fields = ['estado_orden']


from django import forms
from .models import Producto, CatProducto, MovimientosProducto


class CrearCategoriaForm(forms.ModelForm):
    class Meta:
        model = CatProducto
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lubricantes, Frenos, Suspensión',
                'required': True
            })
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if CatProducto.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError(f"La categoría '{nombre}' ya existe.")
        return nombre


class CrearProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'sku', 
            'nombre', 
            'id_cat_producto', 
            'precio_venta', 
            'stock_actual', 
            'stock_minimo', 
            'imagen_url', 
            'activo'
        ]
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: REP-78945',
                'required': True
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Pastillas de Freno Delanteras Corolla',
                'required': True
            }),
            'id_cat_producto': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'stock_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '0',
                'min': '0',
                'required': True
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '2',
                'min': '1',
                'required': True
            }),
            'imagen_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: https://imagenes.com/foto.jpg'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'checked': True
            })
        }

    def clean_sku(self):
        sku = self.cleaned_data.get('sku', '').strip().upper()
        if Producto.objects.filter(sku=sku).exists():
            raise forms.ValidationError(f"El código/SKU [{sku}] ya está asignado a otro producto.")
        return sku


class EditarProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre', 
            'id_cat_producto', 
            'precio_venta', 
            'stock_minimo', 
            'imagen_url', 
            'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'id_cat_producto': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'required': True}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'required': True}),
            'imagen_url': forms.URLInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class MovimientoInventarioForm(forms.Form):
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA_COMPRA', 'Entrada por Compra / Reabastecimiento'),
        ('ENTRADA_AJUSTE', 'Entrada por Ajuste / Corrección'),
        ('SALIDA_AJUSTE', 'Salida por Ajuste / Mermas / Daño'),
        ('SALIDA_TALLER', 'Salida Manual a Taller'),
    ]

    id_producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select', 'required': True}),
        error_messages={'required': 'Debe seleccionar un producto.'}
    )
    tipo_movimiento = forms.ChoiceField(
        choices=TIPO_MOVIMIENTO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'required': True}),
        error_messages={'required': 'Debe seleccionar el tipo de movimiento.'}
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'value': '1',
            'min': '1',
            'required': True
        }),
        error_messages={'required': 'Ingrese una cantidad válida mayor a 0.'}
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Motivo o justificación del ajuste de inventario...'
        })
    )


from django import forms
from .models import Pedido, Usuario, ConfiguracionSistema

class PedidoForm(forms.ModelForm):
    estado_pedido = forms.ChoiceField(
        choices=Pedido.EstadoPedido.choices,
        initial=Pedido.EstadoPedido.PENDIENTE,
        widget=forms.Select(attrs={'class': 'form-select w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium'})
    )

    tipo_entrega = forms.ChoiceField(
        choices=Pedido.TipoEntrega.choices,
        initial=Pedido.TipoEntrega.RETIRO,
        widget=forms.Select(attrs={'class': 'form-select w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium', 'id': 'id_tipo_entrega'})
    )

    costo_envio = forms.DecimalField(
        initial=Decimal('0.00'),
        min_value=Decimal('0.00'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )

    direccion_envio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium',
            'rows': 2,
            'placeholder': 'Dirección detallada para delivery (si aplica)...'
        })
    )

    tasa_cambio = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-xs font-bold text-slate-600',
            'readonly': 'readonly',
            'tabindex': '-1',
            'style': 'pointer-events: none; background-color: #f1f5f9; cursor: not-allowed;',
            'placeholder': 'Tasa Oficial BCV'
        })
    )

    total = forms.DecimalField(
        initial=Decimal('0.00'),
        min_value=Decimal('0.00'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )

    class Meta:
        model = Pedido
        fields = [
            'cedula_usuario',
            'estado_pedido',
            'tipo_entrega',
            'costo_envio',
            'direccion_envio',
            'tasa_cambio',
            'total',
        ]
        widgets = {
            'cedula_usuario': forms.Select(attrs={'class': 'form-select select2 w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium'}),
        }
        labels = {
            'cedula_usuario': 'Cliente / Usuario',
            'estado_pedido': 'Estado del Pedido',
            'tipo_entrega': 'Tipo de Entrega',
            'costo_envio': 'Costo de Envío ($)',
            'direccion_envio': 'Dirección de Entrega',
            'tasa_cambio': 'Tasa de Cambio (USD/VES)',
            'total': 'Monto Total ($)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cedula_usuario'].queryset = Usuario.objects.all().order_by('nombre', 'apellido')
        # La tasa de cambio oficial se toma siempre de la Configuración del Sistema y no es tipeable
        self.fields['tasa_cambio'].initial = ConfiguracionSistema.get_tasa_actual()
        self.fields['tasa_cambio'].widget.attrs.update({
            'readonly': 'readonly',
            'tabindex': '-1',
            'style': 'pointer-events: none; background-color: #f1f5f9; cursor: not-allowed;'
        })

        if not self.instance or not self.instance.pk:
            if not self.initial.get('costo_envio'):
                self.fields['costo_envio'].initial = Decimal('0.00')
            if not self.initial.get('total'):
                self.fields['total'].initial = Decimal('0.00')
            if not self.initial.get('tipo_entrega'):
                self.fields['tipo_entrega'].initial = Pedido.TipoEntrega.RETIRO

    def clean(self):
        cleaned_data = super().clean()
        tipo_entrega = cleaned_data.get('tipo_entrega')
        direccion_envio = cleaned_data.get('direccion_envio')
        costo_envio = cleaned_data.get('costo_envio')
        tasa_cambio = cleaned_data.get('tasa_cambio')
        total = cleaned_data.get('total')

        if tipo_entrega == Pedido.TipoEntrega.DELIVERY:
            if not direccion_envio or not direccion_envio.strip():
                self.add_error('direccion_envio', 'Debe especificar la dirección de entrega para pedidos con delivery.')
        else:
            cleaned_data['direccion_envio'] = ''
            cleaned_data['costo_envio'] = Decimal('0.00')

        # La tasa no es tipeable de ninguna forma; siempre agarra el valor de ConfiguracionSistema
        cleaned_data['tasa_cambio'] = ConfiguracionSistema.get_tasa_actual()

        if total is None:
            cleaned_data['total'] = Decimal('0.00')

        return cleaned_data
