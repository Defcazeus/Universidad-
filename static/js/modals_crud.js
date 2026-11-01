// static/js/modals_crud.js
async function openCrudModal(url, title, borderAccent = 'border-warning') {
  const modalEl = document.getElementById('crudMasterModal');
  const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
  const bodyContent = document.getElementById('modalBodyContent');
  
  document.getElementById('modalTitle').querySelector('span').innerText = title;
  document.getElementById('modalHeaderAccent').className = `modal-header border-bottom border-secondary border-opacity-25 border-top border-4 ${borderAccent} px-4 py-3`;
  
  bodyContent.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-warning" role="status"></div>
      <p class="text-muted small mt-2 mb-0">Cargando formulario...</p>
    </div>`;
  
  bsModal.show();

  try {
    const response = await fetch(url, { 
      headers: { 'X-Requested-With': 'XMLHttpRequest' } 
    });
    const html = await response.text();
    bodyContent.innerHTML = html;
    document.getElementById('crudDynamicForm').action = url;
  } catch (err) {
    bodyContent.innerHTML = '<div class="alert alert-danger my-3">Error al cargar la información. Intente de nuevo.</div>';
  }
}