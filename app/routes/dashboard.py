"""
Rutas de Dashboard para QoriCash Trading V2
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.services.operation_service import OperationService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """
    Dashboard principal
    
    Redirige al dashboard según el rol del usuario
    """
    # Verificar rol y mostrar dashboard correspondiente
    if current_user.role == 'Master':
        return render_template('dashboard/master.html', user=current_user)
    elif current_user.role == 'Trader':
        return render_template('dashboard/trader.html', user=current_user)
    elif current_user.role == 'Operador':
        # Los operadores van directamente a operaciones
        from app.routes.operations import operations_list
        return operations_list()
    else:
        return render_template('dashboard/trader.html', user=current_user)


@dashboard_bp.route('/api/dashboard_data')
@login_required
def get_dashboard_data():
    """
    API: Obtener datos del dashboard
    
    Query params:
        month: Mes (1-12) opcional
        year: Año opcional
    
    Returns:
        JSON con estadísticas
    """
    # Obtener parámetros
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    # Obtener estadísticas
    stats = OperationService.get_dashboard_stats(month, year)
    
    # Agregar datos adicionales según rol
    if current_user.role == 'Master':
        # Master ve todo
        from app.models.user import User
        from app.models.client import Client
        
        stats['total_users'] = User.query.count()
        stats['active_users'] = User.query.filter_by(status='Activo').count()
        stats['total_clients'] = Client.query.count()
        stats['active_clients'] = Client.query.filter_by(status='Activo').count()
    
    return jsonify(stats)


@dashboard_bp.route('/api/stats/today')
@login_required
def get_today_stats():
    """
    API: Obtener estadísticas de hoy
    """
    from datetime import date
    from app.models.operation import Operation
    from sqlalchemy import func
    
    today = date.today()
    operations = Operation.query.filter(
        func.date(Operation.created_at) == today
    ).all()
    
    completed = [op for op in operations if op.status == 'Completada']
    
    return jsonify({
        'operations_count': len(operations),
        'completed_count': len(completed),
        'pending_count': sum(1 for op in operations if op.status == 'Pendiente'),
        'in_process_count': sum(1 for op in operations if op.status == 'En proceso'),
        'total_usd': float(sum(op.amount_usd for op in completed)),
        'total_pen': float(sum(op.amount_pen for op in completed))
    })


@dashboard_bp.route('/api/stats/month')
@login_required
def get_month_stats():
    """
    API: Obtener estadísticas del mes actual
    """
    from datetime import datetime
    from app.models.operation import Operation
    from sqlalchemy import and_
    
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    if now.month == 12:
        end_date = datetime(now.year + 1, 1, 1)
    else:
        end_date = datetime(now.year, now.month + 1, 1)
    
    operations = Operation.query.filter(
        and_(
            Operation.created_at >= start_date,
            Operation.created_at < end_date
        )
    ).all()
    
    completed = [op for op in operations if op.status == 'Completada']
    
    return jsonify({
        'operations_count': len(operations),
        'completed_count': len(completed),
        'pending_count': sum(1 for op in operations if op.status == 'Pendiente'),
        'in_process_count': sum(1 for op in operations if op.status == 'En proceso'),
        'canceled_count': sum(1 for op in operations if op.status == 'Cancelado'),
        'total_usd': float(sum(op.amount_usd for op in completed)),
        'total_pen': float(sum(op.amount_pen for op in completed)),
        'unique_clients': len(set(op.client_id for op in operations))
    })
