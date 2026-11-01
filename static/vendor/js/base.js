document.addEventListener("DOMContentLoaded", () => {

  if (localStorage.getItem('animacionesActivadas') === 'false') {
    document.body.classList.add('sin-animaciones');
  }

  const densidad = localStorage.getItem('densidadUI');
  if (densidad === 'Compacto') {
    document.body.classList.add('densidad-compacta');
  } else if (densidad === 'Amplio') {
    document.body.classList.add('densidad-amplia');
  }

  if (localStorage.getItem('altoContraste') === 'true') {
    document.body.classList.add('alto-contraste');
  }

  if (localStorage.getItem('tipografiaGrande') === 'true') {
    document.body.classList.add('tipografia-grande');
  }

  if (localStorage.getItem('cierreAutomatico') === 'true') {
    let inactividad = 0;
    const limite = 20 * 60;
    setInterval(() => {
      inactividad++;
      if (inactividad >= limite) {
        window.location.href = "/login/";
      }
    }, 1000);
    ['mousemove', 'keydown', 'click'].forEach(evt => {
      document.addEventListener(evt, () => inactividad = 0);
    });
  }

  if (localStorage.getItem('confirmarSalida') === 'true') {
    const enlacesLogout = document.querySelectorAll('a[href$="logout"]');
    enlacesLogout.forEach(enlace => {
      enlace.addEventListener('click', (e) => {
        e.preventDefault();
        Swal.fire({
          title: '¿Cerrar sesión?',
          text: 'Se cerrará tu sesión actual.',
          icon: 'warning',
          showCancelButton: true,
          confirmButtonText: 'Sí, salir',
          cancelButtonText: 'Cancelar'
        }).then((result) => {
          if (result.isConfirmed) {
            window.location.href = enlace.href;
          }
        });
      });
    });
  }

  const campos = [
    'animacionesActivadas',
    'densidadUI',
    'altoContraste',
    'tipografiaGrande',
    'cierreAutomatico',
    'confirmarSalida'
  ];

  if (document.getElementById('animacionesActivadas')) {
    campos.forEach(id => {
      const el = document.getElementById(id);
      const valor = localStorage.getItem(id);
      if (!el || valor === null) return;
      if (el.type === 'checkbox') el.checked = valor === 'true';
      else el.value = valor;
    });
  }
});