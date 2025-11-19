"""
Rutas de Clientes para QoriCash Trading V2
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.client_service import ClientService
from app.services.file_service import FileService
from app.services.notification_service import NotificationService
from app.utils.decorators import require_role

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/')
@clients_bp.route('/list')
@login_required
@require_role('Master', 'Trader')
def list_clients():
    """
    Página de listado de clientes
    """
    clients = ClientService.get_all_clients()
    return render_template('clients/list.html', user=current_user, clients=clients)


@clients_bp.route('/api/list')
@login_required
@require_role('Master', 'Trader')
def api_list():
    """
    API: Listar todos los clientes
    """
    include_stats = request.args.get('include_stats', 'false').lower() == 'true'
    clients = ClientService.get_all_clients(include_stats=include_stats)
    
    if include_stats:
        # Ya viene como diccionarios
        return jsonify({'success': True, 'clients': clients})
    else:
        return jsonify({
            'success': True,
            'clients': [client.to_dict() for client in clients]
        })


@clients_bp.route('/api/search')
@login_required
@require_role('Master', 'Trader')
def search():
    """
    API: Buscar clientes
    
    Query params:
        q: Texto de búsqueda
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': False, 'message': 'Query requerido'}), 400
    
    clients = ClientService.search_clients(query)
    return jsonify({
        'success': True,
        'clients': [client.to_dict() for client in clients]
    })


@clients_bp.route('/api/create', methods=['POST'])
@login_required
@require_role('Master', 'Trader')
def create_client():
    """
    API: Crear nuevo cliente
    
    POST JSON:
        name: string (required)
        dni: string (required)
        email: string (required)
        phone: string (optional)
        bank_account_pen: string (optional)
        bank_account_usd: string (optional)
        bank_name: string (optional)
        notes: string (optional)
    """
    data = request.get_json()
    
    # Crear cliente
    success, message, client = ClientService.create_client(
        current_user=current_user,
        name=data.get('name', '').strip(),
        dni=data.get('dni', '').strip(),
        email=data.get('email', '').strip(),
        phone=data.get('phone'),
        bank_account_pen=data.get('bank_account_pen'),
        bank_account_usd=data.get('bank_account_usd'),
        bank_name=data.get('bank_name'),
        notes=data.get('notes')
    )
    
    if success:
        # Notificar creación
        NotificationService.notify_new_client(client, current_user)
        
        return jsonify({
            'success': True,
            'message': message,
            'client': client.to_dict()
        }), 201
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@clients_bp.route('/api/update/<int:client_id>', methods=['PUT'])
@login_required
@require_role('Master', 'Trader')
def update_client(client_id):
    """
    API: Actualizar cliente
    """
    data = request.get_json()
    
    success, message, client = ClientService.update_client(
        current_user=current_user,
        client_id=client_id,
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        bank_account_pen=data.get('bank_account_pen'),
        bank_account_usd=data.get('bank_account_usd'),
        bank_name=data.get('bank_name'),
        notes=data.get('notes'),
        status=data.get('status')
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'client': client.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@clients_bp.route('/api/upload_dni/<int:client_id>', methods=['POST'])
@login_required
@require_role('Master', 'Trader')
def upload_dni(client_id):
    """
    API: Subir DNI del cliente
    
    Form data:
        dni_front: file (optional)
        dni_back: file (optional)
    """
    client = ClientService.get_client_by_id(client_id)
    if not client:
        return jsonify({'success': False, 'message': 'Cliente no encontrado'}), 404
    
    file_service = FileService()
    
    dni_front_url = None
    dni_back_url = None
    
    # Subir DNI frontal
    if 'dni_front' in request.files:
        file = request.files['dni_front']
        success, message, url = file_service.upload_dni_front(file, client.dni)
        if success:
            dni_front_url = url
        else:
            return jsonify({'success': False, 'message': f'Error DNI frontal: {message}'}), 400
    
    # Subir DNI reverso
    if 'dni_back' in request.files:
        file = request.files['dni_back']
        success, message, url = file_service.upload_dni_back(file, client.dni)
        if success:
            dni_back_url = url
        else:
            return jsonify({'success': False, 'message': f'Error DNI reverso: {message}'}), 400
    
    # Actualizar cliente con URLs
    if dni_front_url or dni_back_url:
        success, message, client = ClientService.update_client_documents(
            current_user=current_user,
            client_id=client_id,
            dni_front_url=dni_front_url,
            dni_back_url=dni_back_url
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'client': client.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo'}), 400


@clients_bp.route('/api/toggle_status/<int:client_id>', methods=['POST'])
@login_required
@require_role('Master', 'Trader')
def toggle_status(client_id):
    """
    API: Activar/Desactivar cliente
    """
    success, message, client = ClientService.toggle_client_status(current_user, client_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'client': client.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@clients_bp.route('/api/delete/<int:client_id>', methods=['DELETE'])
@login_required
@require_role('Master')
def delete_client(client_id):
    """
    API: Eliminar cliente (soft delete)
    """
    success, message = ClientService.delete_client(current_user, client_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@clients_bp.route('/api/<int:client_id>')
@login_required
@require_role('Master', 'Trader')
def get_client(client_id):
    """
    API: Obtener detalles de un cliente
    """
    client = ClientService.get_client_by_id(client_id)
    
    if not client:
        return jsonify({
            'success': False,
            'message': 'Cliente no encontrado'
        }), 404
    
    # Incluir estadísticas
    stats = ClientService.get_client_stats(client_id)
    
    return jsonify({
        'success': True,
        'client': client.to_dict(),
        'stats': stats
    })


@clients_bp.route('/api/active')
@login_required
@require_role('Master', 'Trader')
def get_active_clients():
    """
    API: Obtener solo clientes activos
    """
    clients = ClientService.get_active_clients()
    return jsonify({
        'success': True,
        'clients': [client.to_dict() for client in clients]
    })
