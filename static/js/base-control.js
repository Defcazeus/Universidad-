/**
 * SERVIAUTOMOTRIZ FERNÁNDEZ - CONTROLADOR GLOBAL DE INTERFAZ (UI)
 * Gestiona accesibilidad, navegación dinámica, mensajes flash y confirmaciones.
 */

document.addEventListener("DOMContentLoaded", function() {
    
    // ==========================================================================
    // 1. PREFERENCIAS DE UI Y ACCESIBILIDAD (Fondo Sólido, Contraste, Tipografía)
    // ==========================================================================
    const backgroundBlurElement = document.querySelector('.background-blur');
    
    function aplicarFondoGlobal() {
        const activado = localStorage.getItem('fondoSolidoActivado') === 'true';
        const color = localStorage.getItem('colorFondoSolido') || '#f8f9fa';

        // Limpiamos propiedades previas del body de forma segura
        document.body.style.removeProperty('background');
        document.body.style.removeProperty('background-color');
        document.body.style.removeProperty('background-image');

        if (activado) {
            if (backgroundBlurElement) {
                backgroundBlurElement.style.setProperty('display', 'none', 'important');
            }
            document.body.style.setProperty('background-color', color, 'important');
        } else {
            if (backgroundBlurElement) {
                backgroundBlurElement.style.setProperty('display', 'block', 'important');
            }
        }
    }
    
    // Ejecutamos la configuración inicial del fondo y clases estéticas
    aplicarFondoGlobal(); 

    if (localStorage.getItem('altoContraste') === 'true') {
        document.body.classList.add('alto-contraste');
    }
    if (localStorage.getItem('tipografiaGrande') === 'true') {
        document.body.classList.add('tipografia-grande');
    }

    // ==========================================================================
    // 2. CONTROL DEL MENÚ DESPLEGABLE DEL PERFIL (DROPDOWN)
    // ==========================================================================
    const dropdownBtn = document.getElementById("profileDropdownBtn");
    const dropdownMenu = document.getElementById("profileDropdownMenu");

    if (dropdownBtn && dropdownMenu) {
        // Abrir / Cerrar al hacer clic en el botón de perfil
        dropdownBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            const isExpanded = dropdownBtn.getAttribute("aria-expanded") === "true";
            dropdownBtn.setAttribute("aria-expanded", !isExpanded);
            dropdownBtn.classList.toggle("active");
            dropdownMenu.classList.toggle("show");
        });

        // Cerrar el menú si se hace clic fuera de él
        document.addEventListener("click", function(e) {
            if (!dropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownBtn.setAttribute("aria-expanded", "false");
                dropdownBtn.classList.remove("active");
                dropdownMenu.classList.remove("show");
            }
        });

        // Cerrar el menú de forma accesible presionando la tecla Escape
        document.addEventListener("keydown", function(e) {
            if (e.key === "Escape" && dropdownMenu.classList.contains("show")) {
                dropdownBtn.setAttribute("aria-expanded", "false");
                dropdownBtn.classList.remove("active");
                dropdownMenu.classList.remove("show");
                dropdownBtn.focus();
            }
        });
    }

    // ==========================================================================
    // 3. INTERCEPTOR SEGURO PARA EL CIERRE DE SESIÓN (LOGOUT)
    // ==========================================================================
    const logoutBtn = document.getElementById("logoutBtn");
    const logoutForm = document.getElementById("logoutForm");
    
    if (logoutBtn && logoutForm) {
        logoutBtn.addEventListener("click", function(e) {
            e.preventDefault(); // Frena el envío directo del formulario
            
            Swal.fire({
                title: "¿Cerrar sesión?",
                text: "¿Estás seguro de que deseas salir del sistema?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#ff6600",
                cancelButtonColor: "#444444",
                confirmButtonText: "Sí, salir",
                cancelButtonText: "Cancelar",
                background: '#1e1e1e',
                color: '#ffffff'
            }).then((result) => { 
                if (result.isConfirmed) {
                    logoutForm.submit(); // Envía el POST seguro a Django
                }
            });
        });
    }

    // ==========================================================================
    // 4. PROCESAMIENTO AUTOMÁTICO DE MENSAJES DJANGO (Formatos Flotantes)
    // ==========================================================================
    const msgElem = document.getElementById("django-msgs");
    if (msgElem) {
        try {
            const datos = JSON.parse(msgElem.textContent);
            
            datos.forEach(({ texto, tag }) => {
                // Configuración por defecto tipo Notificación Flotante (Toast)
                let configuracion = {
                    text: texto,
                    background: '#1e1e1e',
                    color: '#ffffff',
                    timer: 300,
                    timerProgressBar: true,
                    showConfirmButton: false,
                    toast: true,
                    position: 'top-end'
                };

                // Personalización de iconos y tiempos según la etiqueta de Django
                if (tag === 'success') {
                    configuracion.icon = 'success';
                    configuracion.iconColor = '#28a745'; // Check verde
                } else if (tag === 'error' || tag === 'danger') {
                    configuracion.icon = 'error';
                    configuracion.iconColor = '#dc3545'; // Equis roja
                    configuracion.timer = 4000;          // Un segundo más para lectura de fallos
                } else if (tag === 'warning') {
                    configuracion.icon = 'warning';
                    configuracion.iconColor = '#ffc107'; // Advertencia amarilla
                } else {
                    configuracion.icon = 'info';
                    configuracion.iconColor = '#00bcd4'; // Azul informativo
                }

                // Dispara la notificación en pantalla
                Swal.fire(configuracion);
            });
        } catch (e) { 
            console.error("Error al procesar el bloque JSON de mensajes:", e); 
        }
    }
});

// ==========================================================================
// 5. CONTROLADORES DE RUTEO DINÁMICO E HISTORIAL (Funciones Globales)
// ==========================================================================
let previousPath = null;

function goTo(path) { 
    previousPath = window.location.pathname; 
    window.location.href = path; 
}

function goBack() {
    if (previousPath) { 
        window.location.href = previousPath; 
        return; 
    }
    try {
        if (document.referrer && new URL(document.referrer).origin === location.origin) {
            history.back(); 
            return;
        }
    } catch (e) {}
    window.location.href = "/";
}

// ==========================================================================
// 6. ADVERTENCIAS DE ACCIÓN REUTILIZABLES (Para Eliminaciones/Modificaciones)
// ==========================================================================
function confirmarAccion(event, titulo = "¿Estás seguro?", texto = "Confirma si deseas realizar esta acción", botonConfirmar = "Confirmar") {
    event.preventDefault(); 
    
    const formulario = event.target.closest('form');
    
    if (!formulario) {
        console.error("No se encontró ningún formulario asociado a esta acción.");
        return;
    }

    Swal.fire({
        title: titulo,
        text: texto,
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#ff6600",
        cancelButtonColor: "#444444",
        confirmButtonText: botonConfirmar,
        cancelButtonText: "Cancelar",
        background: '#1e1e1e',
        color: '#ffffff'
    }).then((result) => {
        if (result.isConfirmed) {
            formulario.submit(); 
        }
    });
}