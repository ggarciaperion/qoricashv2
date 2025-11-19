"""
Rutas de Operaciones para QoriCash Trading V2
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.operation_service import OperationService
from app.services.file_service import FileService
from app.services.notification_service import NotificationService
from app.utils.decorators import require_role

operations_bp = Blueprint('operations', __name__)


@operations_bp.route('/')
@operations_bp.route('/list')
@login_required
def operations_list():
    """
    Página de listado de operaciones
    
    Según el rol:
    - Master/Trader: Todas las operaciones
    - Operador: Solo operaciones en proceso
    """
    if current_user.role == 'Operador':
        operations = OperationService.get_operations_for_operator()
        return render_template('operations/operator_list.html', 
                             user=current_user, 
                             operations=operations)
    else:
        operations = OperationService.get_all_operations(include_relations=False)
        return render_template('operations/list.html', 
                             user=current_user, 
                             operations=operations)


@operations_bp.route('/create')
@login_required
@require_role('Master', 'Trader')
def create_page():
    """
    Página de creación de operación
    """
    from app.services.client_service import ClientService
    clients = ClientService.get_active_clients()
    return render_template('operations/create.html', 
                         user=current_user, 
                         clients=clients)


@operations_bp.route('/api/list')
@login_required
def api_list():
    """
    API: Listar operaciones
    
    Query params:
        status: Filtrar por estado (opcional)
        client_id: Filtrar por cliente (opcional)
    """
    status = request.args.get('status')
    client_id = request.args.get('client_id', type=int)
    
    if status:
        operations = OperationService.get_operations_by_status(status)
    elif client_id:
        operations = OperationService.get_operations_by_client(client_id)
    else:
        operations = OperationService.get_all_operations(include_relations=True)
        # Ya viene como diccionarios
        return jsonify({'success': True, 'operations': operations})
    
    return jsonify({
        'success': True,
        'operations': [op.to_dict(include_relations=True) for op in operations]
    })


@operations_bp.route('/api/create', methods=['POST'])
@login_required
@require_role('Master', 'Trader')
def create_operation():
    """
    API: Crear nueva operación
    
    POST JSON:
        client_id: int (required)
        operation_type: string (required) - 'Compra' o 'Venta'
        amount_usd: float (required)
        exchange_rate: float (required)
        source_account: string (optional)
        destination_account: string (optional)
        notes: string (optional)
    """
    data = request.get_json()
    
    # Crear operación
    success, message, operation = OperationService.create_operation(
        current_user=current_user,
        client_id=data.get('client_id'),
        operation_type=data.get('operation_type'),
        amount_usd=data.get('amount_usd'),
        exchange_rate=data.get('exchange_rate'),
        source_account=data.get('source_account'),
        destination_account=data.get('destination_account'),
        notes=data.get('notes')
    )
    
    if success:
        # Notificar creación
        NotificationService.notify_new_operation(operation)
        NotificationService.notify_dashboard_update()
        
        return jsonify({
            'success': True,
            'message': message,
            'operation': operation.to_dict(include_relations=True)
        }), 201
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@operations_bp.route('/api/update_status/<int:operation_id>', methods=['PATCH'])
@login_required
def update_status(operation_id):
    """
    API: Actualizar estado de operación
    
    PATCH JSON:
        status: string (required) - 'Pendiente', 'En proceso', 'Completada', 'Cancelado'
        notes: string (optional)
    """
    data = request.get_json()
    new_status = data.get('status')
    notes = data.get('notes')
    
    if not new_status:
        return jsonify({
            'success': False,
            'message': 'El estado es requerido'
        }), 400
    
    # Obtener operación para guardar estado anterior
    operation = OperationService.get_operation_by_id(operation_id)
    old_status = operation.status if operation else None
    
    # Actualizar estado
    success, message, operation = OperationService.update_operation_status(
        current_user=current_user,
        operation_id=operation_id,
        new_status=new_status,
        notes=notes
    )
    
    if success:
        # Notificar según el nuevo estado
        NotificationService.notify_operation_updated(operation, old_status)
        
        if new_status == 'Completada':
            NotificationService.notify_operation_completed(operation)
        
        NotificationService.notify_dashboard_update()
        
        return jsonify({
            'success': True,
            'message': message,
            'operation': operation.to_dict(include_relations=True)
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@operations_bp.route('/api/upload_proof/<int:operation_id>', methods=['POST'])
@login_required
def upload_proof(operation_id):
    """
    API: Subir comprobantes de operación
    
    Form data:
        payment_proof: file (optional)
        operator_proof: file (optional)
    """
    operation = OperationService.get_operation_by_id(operation_id)
    if not operation:
        return jsonify({'success': False, 'message': 'Operación no encontrada'}), 404
    
    file_service = FileService()
    
    payment_proof_url = None
    operator_proof_url = None
    
    # Subir comprobante de pago (cliente)
    if 'payment_proof' in request.files:
        file = request.files['payment_proof']
        success, message, url = file_service.upload_payment_proof(file, operation.operation_id)
        if success:
            payment_proof_url = url
        else:
            return jsonify({'success': False, 'message': f'Error comprobante de pago: {message}'}), 400
    
    # Subir comprobante del operador
    if 'operator_proof' in request.files:
        file = request.files['operator_proof']
        success, message, url = file_service.upload_operator_proof(file, operation.operation_id)
        if success:
            operator_proof_url = url
        else:
            return jsonify({'success': False, 'message': f'Error comprobante del operador: {message}'}), 400
    
    # Actualizar operación con URLs
    if payment_proof_url or operator_proof_url:
        success, message, operation = OperationService.update_operation_proofs(
            current_user=current_user,
            operation_id=operation_id,
            payment_proof_url=payment_proof_url,
            operator_proof_url=operator_proof_url
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'operation': operation.to_dict(include_relations=True)
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo'}), 400


@operations_bp.route('/api/cancel/<int:operation_id>', methods=['POST'])
@login_required
@require_role('Master', 'Trader')
def cancel_operation(operation_id):
    """
    API: Cancelar operación
    
    POST JSON:
        reason: string (required)
    """
    data = request.get_json()
    reason = data.get('reason', '').strip()
    
    if not reason:
        return jsonify({
            'success': False,
            'message': 'La razón de cancelación es requerida'
        }), 400
    
    # Cancelar operación
    success, message, operation = OperationService.cancel_operation(
        current_user=current_user,
        operation_id=operation_id,
        reason=reason
    )
    
    if success:
        # Notificar cancelación
        NotificationService.notify_operation_canceled(operation, reason)
        NotificationService.notify_dashboard_update()
        
        return jsonify({
            'success': True,
            'message': message,
            'operation': operation.to_dict(include_relations=True)
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@operations_bp.route('/api/<string:operation_id>')
@login_required
def get_operation(operation_id):
    """
    API: Obtener detalles de una operación
    
    Args:
        operation_id: Puede ser ID numérico o operation_id (EXP-XXXX)
    """
    # Intentar como ID numérico
    try:
        op_id = int(operation_id)
        operation = OperationService.get_operation_by_id(op_id)
    except ValueError:
        # Buscar por operation_id string
        operation = OperationService.get_operation_by_operation_id(operation_id)
    
    if not operation:
        return jsonify({
            'success': False,
            'message': 'Operación no encontrada'
        }), 404
    
    return jsonify({
        'success': True,
        'operation': operation.to_dict(include_relations=True)
    })


@operations_bp.route('/api/today')
@login_required
def get_today_operations():
    """
    API: Obtener operaciones de hoy
    """
    operations = OperationService.get_today_operations()
    return jsonify({
        'success': True,
        'operations': [op.to_dict(include_relations=True) for op in operations]
    })


@operations_bp.route('/api/for_operator')
@login_required
@require_role('Operador')
def get_for_operator():
    """
    API: Obtener operaciones para operador (Pendientes y En proceso)
    """
    operations = OperationService.get_operations_for_operator()
    return jsonify({
        'success': True,
        'operations': [op.to_dict(include_relations=True) for op in operations]
    })
