
function renderPieAsistencia(ctx, data) {
  return new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Asistencias', 'Inasistencias', 'Retrasos', 'Justificadas'],
      datasets: [{
        data: [
          data.asistencias,
          data.inasistencias,
          data.retrasos,
          data.justificadas
        ],
        backgroundColor: ['#28a745', '#dc3545', '#ffc107', '#17a2b8']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

function renderLineIndicePeriodo(ctx, data, labels) {
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Índice de asistencia',
        data: data,
        borderColor: '#007bff',
        fill: false,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true, max: 100 }
      }
    }
  });
}

function renderBarComparativa(ctx, docenteIndice, promedioInstitucional) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Docente', 'Promedio Institucional'],
      datasets: [{
        label: 'Índice de asistencia (%)',
        data: [docenteIndice, promedioInstitucional],
        backgroundColor: ['#007bff', '#6c757d']
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true, max: 100 }
      }
    }
  });
}

function renderBarHistorialInasistencias(ctx, labels, data) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Inasistencias',
        data: data,
        backgroundColor: '#dc3545'
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

function renderBarPorMateria(ctx, labels, data) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Índice de asistencia (%)',
        data: data,
        backgroundColor: '#17a2b8'
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true, max: 100 }
      }
    }
  });
}

window.renderPieAsistencia = renderPieAsistencia;
window.renderLineIndicePeriodo = renderLineIndicePeriodo;
window.renderBarComparativa = renderBarComparativa;
window.renderBarHistorialInasistencias = renderBarHistorialInasistencias;
window.renderBarPorMateria = renderBarPorMateria;