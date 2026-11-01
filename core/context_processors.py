import ssl
import urllib.request
import logging
from decimal import Decimal
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.utils import timezone
from .models import ConfiguracionSistema, Notificacion

logger = logging.getLogger(__name__)


def obtener_tasa_bcv_en_vivo():
    """
    Realiza scraping directo a la página web del Banco Central de Venezuela (BCV).
    Utiliza urllib.request de la librería estándar para evitar dependencias externas.
    Retorna la tasa como Decimal o None si ocurre un error.
    """
    url = "https://www.bcv.org.ve/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
            if response.status == 200:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')
                dolar_container = soup.find('div', id='dolar')
                if dolar_container:
                    strong = dolar_container.find('strong')
                    if strong:
                        raw = strong.text.strip()
                        # Normalizar formato venezolano (punto miles, coma decimal)
                        if '.' in raw and ',' in raw:
                            clean_str = raw.replace('.', '').replace(',', '.')
                        else:
                            clean_str = raw.replace(',', '.')
                        val = Decimal(clean_str)
                        if val > 0:
                            return round(val, 4)
    except Exception as e:
        logger.warning(f"Error al consultar tasa en BCV: {e}")
    return None


def actualizar_tasa_dolar_bcv(forzar=False):
    """
    Función central para consultar o refrescar la tasa del BCV y sincronizarla
    con el modelo ConfiguracionSistema y la caché de Django.
    Si forzar=True, ignora la caché y consulta directamente el portal del BCV.
    """
    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)

    if not forzar:
        tasa_cache = cache.get('tasa_dolar_bcv')
        if tasa_cache:
            try:
                return {
                    'tasa': Decimal(str(tasa_cache)),
                    'ultima_actualizacion': config.ultima_actualizacion,
                    'exito': True,
                    'origen': 'cache',
                    'mensaje': 'Tasa obtenida de la memoria caché.'
                }
            except Exception:
                pass

        # Si en la base de datos la tasa es válida y se actualizó hace menos de 6 horas
        if config.tasa_dolar_bcv and config.tasa_dolar_bcv > 0:
            ahora = timezone.now()
            if config.ultima_actualizacion and (ahora - config.ultima_actualizacion).total_seconds() < 21600:
                cache.set('tasa_dolar_bcv', str(config.tasa_dolar_bcv), 21600)
                return {
                    'tasa': config.tasa_dolar_bcv,
                    'ultima_actualizacion': config.ultima_actualizacion,
                    'exito': True,
                    'origen': 'database',
                    'mensaje': 'Tasa vigente en base de datos.'
                }

    # Intentar obtener la tasa en vivo desde el BCV
    tasa_nueva = obtener_tasa_bcv_en_vivo()
    if tasa_nueva and tasa_nueva > 0:
        config.tasa_dolar_bcv = tasa_nueva
        config.save()
        cache.set('tasa_dolar_bcv', str(config.tasa_dolar_bcv), 21600)
        return {
            'tasa': config.tasa_dolar_bcv,
            'ultima_actualizacion': config.ultima_actualizacion,
            'exito': True,
            'origen': 'bcv_en_vivo',
            'mensaje': 'Tasa oficial del BCV sincronizada con éxito.'
        }
    else:
        # Si falló la conexión al BCV, mantener la que ya esté en BD si es válida
        if config.tasa_dolar_bcv and config.tasa_dolar_bcv > 0:
            cache.set('tasa_dolar_bcv', str(config.tasa_dolar_bcv), 3600)
            return {
                'tasa': config.tasa_dolar_bcv,
                'ultima_actualizacion': config.ultima_actualizacion,
                'exito': False,
                'origen': 'fallback_bd',
                'mensaje': 'No se pudo conectar al portal del BCV. Se mantiene la última tasa registrada.'
            }
        
        # Valor base de respaldo extremo
        tasa_respaldo = Decimal('45.2000')
        config.tasa_dolar_bcv = tasa_respaldo
        config.save()
        cache.set('tasa_dolar_bcv', str(tasa_respaldo), 3600)
        return {
            'tasa': tasa_respaldo,
            'ultima_actualizacion': config.ultima_actualizacion,
            'exito': False,
            'origen': 'fallback_defecto',
            'mensaje': 'No se pudo conectar al portal del BCV. Se utilizó valor de respaldo.'
        }


def tasa_dolar_context(request):
    """
    Context processor de Django que inyecta la tasa BCV y la configuración en todos los templates.
    """
    res = actualizar_tasa_dolar_bcv(forzar=False)
    config = ConfiguracionSistema.objects.first()

    return {
        'tasa_dolar': res['tasa'],
        'tasa_dolar_ultima_actualizacion': res.get('ultima_actualizacion'),
        'configuracion_sistema': config,
    }


def notificaciones_processor(request):
    if request.user.is_authenticated:
        no_leidas = request.user.notificaciones.filter(leido=False).count()
        return {'notificaciones_no_leidas_count': no_leidas}
    return {'notificaciones_no_leidas_count': 0}
