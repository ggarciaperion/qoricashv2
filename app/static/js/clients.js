/**
 * QoriCash Trading V2 - Clients Management JavaScript
 */

/**
 * Crear cliente
 */
function createClient() {
    const formData = {
        name: $('input[name="name"]').val().trim(),
        dni: $('input[name="dni"]').val().trim(),
        email: $('input[name="email"]').val().trim(),
        phone: $('input[name="phone"]').val().trim(),
        bank_name: $('select[name="bank_name"]').val(),
        bank_account_pen: $('input[name="bank_account_pen"]').val().trim(),
        bank_account_usd: $('input[name="bank_account_usd"]').val().trim(),
        notes: $('textarea[name="notes"]').val().trim()
    };
    
    // Validar campos requeridos
    if (!formData.name || !formData.dni || !formData.email) {
        showAlert('Completa todos los campos requeridos', 'warning');
        return;
    }
    
    if (!validateDNI(formData.dni)) {
        showAlert('DNI inválido (debe ser 8 dígitos)', 'warning');
        return;
    }
    
    if (!validateEmail(formData.email)) {
        showAlert('Email inválido', 'warning');
        return;
    }
    
    // Enviar
    ajaxRequest('/clients/api/create', 'POST', formData, function(response) {
        showAlert(response.message, 'success');
        $('#createClientModal').modal('hide');
        $('#createClientForm')[0].reset();
        setTimeout(() => location.reload(), 1000);
    });
}

/**
 * Ver cliente
 */
function viewClient(clientId) {
    ajaxRequest(`/clients/api/${clientId}`, 'GET', null, function(response) {
        const client = response.client;
        const stats = response.stats;
        
        const html = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Información Personal</h6>
                    <p><strong>Nombre:</strong> ${client.name}</p>
                    <p><strong>DNI:</strong> ${client.dni}</p>
                    <p><strong>Email:</strong> ${client.email}</p>
                    <p><strong>Teléfono:</strong> ${client.phone || 'No registrado'}</p>
                    <p><strong>Estado:</strong> <span class="badge bg-${client.status === 'Activo' ? 'success' : 'secondary'}">${client.status}</span></p>
                </div>
                <div class="col-md-6">
                    <h6>Información Bancaria</h6>
                    <p><strong>Banco:</strong> ${client.bank_name || 'No registrado'}</p>
                    <p><strong>Cuenta PEN:</strong> ${client.bank_account_pen || 'No registrada'}</p>
                    <p><strong>Cuenta USD:</strong> ${client.bank_account_usd || 'No registrada'}</p>
                </div>
            </div>
            <hr>
            <div class="row">
                <div class="col-md-12">
                    <h6>Estadísticas</h6>
                    <p><strong>Total Operaciones:</strong> ${stats.total_operations}</p>
                    <p><strong>Operaciones Completadas:</strong> ${stats.completed_operations}</p>
                    <p><strong>Total USD Operado:</strong> ${formatCurrency(stats.total_usd_traded, 'USD')}</p>
                    <p><strong>Total PEN Operado:</strong> ${formatCurrency(stats.total_pen_traded, 'PEN')}</p>
                </div>
            </div>
            ${client.notes ? `<hr><p><strong>Notas:</strong> ${client.notes}</p>` : ''}
        `;
        
        $('#clientDetails').html(html);
        $('#viewClientModal').modal('show');
    });
}

/**
 * Editar cliente
 */
function editClient(clientId) {
    // Similar a editUser, implementar según necesidad
    showAlert('Función de edición en desarrollo', 'info');
}

/**
 * Toggle estado de cliente
 */
function toggleClientStatus(clientId) {
    if (confirm('¿Cambiar el estado de este cliente?')) {
        ajaxRequest(`/clients/api/toggle_status/${clientId}`, 'POST', null, function(response) {
            showAlert(response.message, 'success');
            setTimeout(() => location.reload(), 1000);
        });
    }
}

/**
 * Subir DNI
 */
function uploadDNI(clientId) {
    ajaxRequest(`/clients/api/${clientId}`, 'GET', null, function(response) {
        const client = response.client;
        
        $('#upload_client_id').val(client.id);
        $('#upload_client_name').text(client.name);
        
        $('#uploadDNIModal').modal('show');
    });
}

/**
 * Confirmar upload de DNI
 */
function confirmUploadDNI() {
    const clientId = $('#upload_client_id').val();
    const formData = new FormData($('#uploadDNIForm')[0]);
    
    // Validar que al menos un archivo fue seleccionado
    if (!formData.get('dni_front') && !formData.get('dni_back')) {
        showAlert('Selecciona al menos un archivo', 'warning');
        return;
    }
    
    $.ajax({
        url: `/clients/api/upload_dni/${clientId}`,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            showAlert('DNI subido exitosamente', 'success');
            $('#uploadDNIModal').modal('hide');
            setTimeout(() => location.reload(), 1000);
        },
        error: function(xhr) {
            showAlert('Error: ' + (xhr.responseJSON?.message || 'Error al subir DNI'), 'danger');
        }
    });
}
