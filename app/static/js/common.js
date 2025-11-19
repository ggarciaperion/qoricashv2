/**
 * QoriCash Trading V2 - Common JavaScript Functions
 * Funciones comunes reutilizables en todo el sistema
 */

// Socket.IO connection
let socket = null;

/**
 * Conectar a SocketIO para actualizaciones en tiempo real
 */
function connectSocketIO() {
    if (socket) return; // Ya conectado
    
    socket = io();
    
    socket.on('connect', function() {
        console.log('✅ SocketIO conectado');
    });
    
    socket.on('disconnect', function() {
        console.log('⚠️  SocketIO desconectado');
    });
    
    // Escuchar eventos de operaciones
    socket.on('nueva_operacion', function(data) {
        showAlert(`Nueva operación: ${data.operation_id} - ${data.client_name}`, 'info');
        playNotificationSound();
    });
    
    socket.on('operacion_actualizada', function(data) {
        showAlert(`Operación ${data.operation_id} actualizada a: ${data.status}`, 'info');
    });
    
    socket.on('operacion_completada', function(data) {
        showAlert(`Operación ${data.operation_id} completada`, 'success');
        playNotificationSound();
    });
    
    socket.on('dashboard_update', function() {
        // Actualizar dashboard si estamos en esa página
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        }
    });
}

/**
 * Mostrar alerta (toast notification)
 */
function showAlert(message, type = 'info') {
    const alertTypes = {
        'success': 'alert-success',
        'danger': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alertClass = alertTypes[type] || 'alert-info';
    const icons = {
        'success': 'bi-check-circle',
        'danger': 'bi-x-circle',
        'warning': 'bi-exclamation-triangle',
        'info': 'bi-info-circle'
    };
    const icon = icons[type] || 'bi-info-circle';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="bi ${icon}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Agregar al contenedor de alerts
    const container = $('.container').first();
    container.prepend(alertHtml);
    
    // Auto-remover después de 5 segundos
    setTimeout(function() {
        container.find('.alert').first().fadeOut(function() {
            $(this).remove();
        });
    }, 5000);
}

/**
 * Hacer petición AJAX
 */
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    const csrfToken = $('meta[name="csrf-token"]').attr('content');
    
    $.ajax({
        url: url,
        type: method,
        contentType: 'application/json',
        data: data ? JSON.stringify(data) : null,
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (successCallback) {
                successCallback(response);
            }
        },
        error: function(xhr, status, error) {
            const errorMsg = xhr.responseJSON?.message || error || 'Error en la petición';
            showAlert(errorMsg, 'danger');
            
            if (errorCallback) {
                errorCallback(xhr, status, error);
            }
        }
    });
}

/**
 * Formatear número como moneda
 */
function formatCurrency(amount, currency = 'USD') {
    const num = parseFloat(amount);
    if (isNaN(num)) return '0.00';
    
    const formatted = num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
    return currency === 'USD' ? `$ ${formatted}` : `S/ ${formatted}`;
}

/**
 * Formatear fecha
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${day}/${month}/${year} ${hours}:${minutes}`;
}

/**
 * Validar DNI peruano (8 dígitos)
 */
function validateDNI(dni) {
    return /^[0-9]{8}$/.test(dni);
}

/**
 * Validar email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validar teléfono peruano
 */
function validatePhone(phone) {
    return /^[0-9]{9}$/.test(phone) || /^[0-9]{7}$/.test(phone);
}

/**
 * Reproducir sonido de notificación
 */
function playNotificationSound() {
    // Crear audio element
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIGGe77OecTBMEUKzj8Lf4CgABCQAAAAAAAAA');
    audio.play().catch(() => {
        // Ignorar errores de reproducción
    });
}

/**
 * Confirmar acción
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Copiar al portapapeles
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('Copiado al portapapeles', 'success');
    }).catch(function() {
        showAlert('Error al copiar', 'danger');
    });
}

/**
 * Exportar tabla a Excel
 */
function exportToExcel() {
    // Esta función requiere una librería adicional o backend
    showAlert('Función de exportación en desarrollo', 'info');
}

/**
 * Manejo de cambio de contraseña (modal global)
 */
$(document).ready(function() {
    $('#btnChangePassword').on('click', function() {
        const oldPassword = $('#old_password').val();
        const newPassword = $('#new_password').val();
        const confirmPassword = $('#confirm_password').val();
        
        // Validar
        if (!oldPassword || !newPassword || !confirmPassword) {
            showAlert('Completa todos los campos', 'warning');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            showAlert('Las contraseñas no coinciden', 'warning');
            return;
        }
        
        if (newPassword.length < 8) {
            showAlert('La contraseña debe tener al menos 8 caracteres', 'warning');
            return;
        }
        
        // Enviar
        const data = {
            old_password: oldPassword,
            new_password: newPassword
        };
        
        ajaxRequest('/change_password', 'POST', data, function(response) {
            showAlert(response.message, 'success');
            $('#changePasswordModal').modal('hide');
            $('#changePasswordForm')[0].reset();
        });
    });
});

/**
 * Cargar datos del dashboard
 */
function loadDashboardData(month = null, year = null) {
    let url = '/api/dashboard_data';
    if (month && year) {
        url += `?month=${month}&year=${year}`;
    }
    
    ajaxRequest(url, 'GET', null, function(data) {
        // Actualizar estadísticas del día
        $('#clientsToday').text(data.clients_today || 0);
        $('#operationsToday').text(data.operations_today || 0);
        $('#usdToday').text(formatCurrency(data.usd_today || 0, 'USD'));
        $('#penToday').text(formatCurrency(data.pen_today || 0, 'PEN'));
        
        // Actualizar estadísticas del mes
        $('#clientsMonth').text(data.clients_month || 0);
        $('#activeClientsMonth').text(data.active_clients_month || 0);
        $('#operationsMonth').text(data.operations_month || 0);
        $('#usdMonth').text(formatCurrency(data.usd_month || 0, 'USD'));
        $('#penMonth').text(formatCurrency(data.pen_month || 0, 'PEN'));
        $('#completedMonth').text(data.completed_count || 0);
        
        // Actualizar estado de operaciones
        $('#pendingCount').text(data.pending_count || 0);
        $('#inProcessCount').text(data.in_process_count || 0);
        $('#completedCount').text(data.completed_count || 0);
        $('#canceledCount').text(data.canceled_count || 0);
        
        // Actualizar sistema (solo para Master)
        if (data.total_users !== undefined) {
            $('#totalUsers').text(data.total_users || 0);
            $('#activeUsers').text(data.active_users || 0);
            $('#totalClients').text(data.total_clients || 0);
        }
    });
}

// Auto-conectar SocketIO al cargar la página
$(document).ready(function() {
    // Solo conectar si el usuario está autenticado
    if ($('nav.navbar').length > 0) {
        connectSocketIO();
    }
});
