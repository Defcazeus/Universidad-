
import re
from django.core.exceptions import ValidationError
from .models import Usuario
from django.core.validators import validate_email

def val_email(valor):
    """
    Valida el formato del correo si este fue proporcionado.
    Si viene vacío o es None, no hace nada (lo ignora).
    """
    if not valor:
        return # Al ser opcional, permitimos valores vacíos

    # 1. Forzar minúsculas y quitar espacios extra
    email_limpio = valor.strip().lower()

    # 2. Usar el validador nativo de Django para verificar la sintaxis
    try:
        validate_email(email_limpio)
    except ValidationError:
        raise ValidationError("Ingrese una dirección de correo electrónico válida.")

    return email_limpio

def val_cedula(valor):
    if not valor:
        raise ValidationError("La cédula no puede estar vacía.")
    
    """Sanitiza el número dejando solo dígitos."""
    cedula_limpia = re.sub(r'[^0-9]', '', str(valor))


    if not cedula_limpia or len(cedula_limpia) < 6:
        raise ValidationError("La cédula debe contener entre 6 y 9 dígitos numéricos.")

    return cedula_limpia

def val_telefono(valor):
    """Valida que los 7 dígitos del teléfono sean estrictamente numéricos."""
    if not valor:
        raise ValidationError("El número telefónico no puede estar vacío.")
    
    num_limpio = re.sub(r'[^0-9]', '', str(valor))

    if len(num_limpio) != 7:
        raise ValidationError("El número telefónico debe contener exactamente 7 dígitos.")

    return num_limpio



def val_solo_letras(valor):
    """
    Valida que el texto contenga solo letras (incluyendo Ñ, tildes) y espacios.
    """
    if not valor:
        return "vacio"

    # Expresión regular: solo letras (a-z, A-Z), acentos, Ñ/ñ y espacios
    patron = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
    
    if not re.match(patron, valor.strip()):
        raise ValidationError("Este campo solo debe contener letras y espacios.")
        
    return valor