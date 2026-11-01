document.addEventListener('DOMContentLoaded', () => {

    // 1. Restringir a SOLO NÚMEROS y limitar a maxLen
    const soloNumeros = (input, maxLen) => {
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '');
            if (maxLen && e.target.value.length > maxLen) {
                e.target.value = e.target.value.slice(0, maxLen);
            }
        });
    };

    // 2. Restringir a SOLO LETRAS y espacios
    const soloLetras = (input) => {
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
        });
    };

    // --- Aplicar restricciones de caracteres ---
    document.querySelectorAll('input[name="num_tel"]').forEach(input => soloNumeros(input, 7));
    document.querySelectorAll('input[name="cedula"]').forEach(input => soloNumeros(input, 8));
    document.querySelectorAll('input[name="nombre"], input[name="apellido"]').forEach(input => soloLetras(input));

    // --- Validación estricta de envío (Garantiza 7 dígitos en teléfono y entre 6 y 8 en cédula) ---
    const formularios = document.querySelectorAll('form');
    formularios.forEach(form => {
        form.addEventListener('submit', (e) => {
            const inputTel = form.querySelector('input[name="num_tel"]');
            const inputCedula = form.querySelector('input[name="cedula"]');

            if (inputTel && inputTel.value.trim().length !== 7) {
                e.preventDefault();
                alert('El número de teléfono debe tener exactamente 7 dígitos.');
                inputTel.focus();
                return false;
            }

            if (inputCedula && (inputCedula.value.trim().length < 6 || inputCedula.value.trim().length > 8)) {
                e.preventDefault();
                alert('La cédula debe contener entre 6 y 8 dígitos.');
                inputCedula.focus();
                return false;
            }
        });
    });
});