"""
Servicio de Clientes para QoriCash Trading V2

Maneja CRUD de clientes y carga de documentos.
"""
from app.extensions import db
from app.models.client import Client
from app.models.audit_log import AuditLog
from app.utils.validators import validate_dni, validate_email, validate_phone
from app.utils.formatters import now_peru


class ClientService:
    """Servicio de gestión de clientes"""
    
    @staticmethod
    def get_all_clients(include_stats=False):
        """
        Obtener todos los clientes
        
        Args:
            include_stats: Si incluir estadísticas de operaciones
        
        Returns:
            list: Lista de clientes
        """
        clients = Client.query.order_by(Client.created_at.desc()).all()
        
        if include_stats:
            return [client.to_dict(include_stats=True) for client in clients]
        
        return clients
    
    @staticmethod
    def get_client_by_id(client_id):
        """
        Obtener cliente por ID
        
        Args:
            client_id: ID del cliente
        
        Returns:
            Client: Cliente o None
        """
        return Client.query.get(client_id)
    
    @staticmethod
    def get_active_clients():
        """
        Obtener solo clientes activos
        
        Returns:
            list: Lista de clientes activos
        """
        return Client.query.filter_by(status='Activo').order_by(Client.name).all()
    
    @staticmethod
    def search_clients(query):
        """
        Buscar clientes por nombre, DNI o email
        
        Args:
            query: Texto de búsqueda
        
        Returns:
            list: Lista de clientes que coinciden
        """
        search_pattern = f'%{query}%'
        return Client.query.filter(
            (Client.name.ilike(search_pattern)) |
            (Client.dni.like(search_pattern)) |
            (Client.email.ilike(search_pattern))
        ).all()
    
    @staticmethod
    def create_client(current_user, name, dni, email, phone=None, bank_account_pen=None,
                     bank_account_usd=None, bank_name=None, notes=None):
        """
        Crear nuevo cliente
        
        Args:
            current_user: Usuario que crea
            name: Nombre completo
            dni: DNI
            email: Email
            phone: Teléfono (opcional)
            bank_account_pen: Cuenta en soles (opcional)
            bank_account_usd: Cuenta en dólares (opcional)
            bank_name: Banco (opcional)
            notes: Notas (opcional)
        
        Returns:
            tuple: (success: bool, message: str, client: Client|None)
        """
        # Validar permisos
        if not current_user or current_user.role not in ['Master', 'Trader']:
            return False, 'No tienes permiso para crear clientes', None
        
        # Validar datos
        if not name or not name.strip():
            return False, 'El nombre es requerido', None
        
        is_valid, error = validate_dni(dni)
        if not is_valid:
            return False, error, None
        
        is_valid, error = validate_email(email)
        if not is_valid:
            return False, error, None
        
        if phone:
            is_valid, error = validate_phone(phone)
            if not is_valid:
                return False, error, None
        
        # Validar que DNI no existe
        if Client.query.filter_by(dni=dni).first():
            return False, 'El DNI ya está registrado', None
        
        # Validar que email no existe
        if Client.query.filter_by(email=email).first():
            return False, 'El email ya está registrado', None
        
        # Crear cliente
        client = Client(
            name=name.strip(),
            dni=dni,
            email=email.lower(),
            phone=phone,
            bank_account_pen=bank_account_pen,
            bank_account_usd=bank_account_usd,
            bank_name=bank_name,
            notes=notes,
            status='Activo',
            created_at=now_peru()
        )
        
        db.session.add(client)
        db.session.commit()
        
        # Registrar en auditoría
        AuditLog.log_action(
            user_id=current_user.id,
            action='CREATE_CLIENT',
            entity='Client',
            entity_id=client.id,
            details=f'Cliente {name} (DNI: {dni}) creado'
        )
        
        return True, 'Cliente creado exitosamente', client
    
    @staticmethod
    def update_client(current_user, client_id, name=None, email=None, phone=None,
                     bank_account_pen=None, bank_account_usd=None, bank_name=None,
                     notes=None, status=None):
        """
        Actualizar cliente
        
        Args:
            current_user: Usuario que actualiza
            client_id: ID del cliente
            name: Nuevo nombre (opcional)
            email: Nuevo email (opcional)
            phone: Nuevo teléfono (opcional)
            bank_account_pen: Nueva cuenta soles (opcional)
            bank_account_usd: Nueva cuenta dólares (opcional)
            bank_name: Nuevo banco (opcional)
            notes: Nuevas notas (opcional)
            status: Nuevo estado (opcional)
        
        Returns:
            tuple: (success: bool, message: str, client: Client|None)
        """
        # Validar permisos
        if not current_user or current_user.role not in ['Master', 'Trader']:
            return False, 'No tienes permiso para actualizar clientes', None
        
        # Obtener cliente
        client = Client.query.get(client_id)
        if not client:
            return False, 'Cliente no encontrado', None
        
        # Actualizar nombre
        if name and name != client.name:
            if not name.strip():
                return False, 'El nombre no puede estar vacío', None
            client.name = name.strip()
        
        # Actualizar email
        if email and email != client.email:
            is_valid, error = validate_email(email)
            if not is_valid:
                return False, error, None
            
            # Verificar que no existe
            existing = Client.query.filter_by(email=email).first()
            if existing and existing.id != client_id:
                return False, 'El email ya está registrado', None
            
            client.email = email.lower()
        
        # Actualizar teléfono
        if phone is not None:  # Puede ser vacío para limpiar
            if phone:
                is_valid, error = validate_phone(phone)
                if not is_valid:
                    return False, error, None
            client.phone = phone
        
        # Actualizar cuentas bancarias
        if bank_account_pen is not None:
            client.bank_account_pen = bank_account_pen
        
        if bank_account_usd is not None:
            client.bank_account_usd = bank_account_usd
        
        if bank_name is not None:
            client.bank_name = bank_name
        
        # Actualizar notas
        if notes is not None:
            client.notes = notes
        
        # Actualizar estado
        if status and status != client.status:
            if status not in ['Activo', 'Inactivo']:
                return False, 'Estado inválido', None
            client.status = status
        
        client.updated_at = now_peru()
        db.session.commit()
        
        # Registrar en auditoría
        AuditLog.log_action(
            user_id=current_user.id,
            action='UPDATE_CLIENT',
            entity='Client',
            entity_id=client.id,
            details=f'Cliente {client.name} actualizado'
        )
        
        return True, 'Cliente actualizado exitosamente', client
    
    @staticmethod
    def update_client_documents(current_user, client_id, dni_front_url=None, dni_back_url=None):
        """
        Actualizar URLs de documentos del cliente
        
        Args:
            current_user: Usuario que actualiza
            client_id: ID del cliente
            dni_front_url: URL de DNI frontal (Cloudinary)
            dni_back_url: URL de DNI reverso (Cloudinary)
        
        Returns:
            tuple: (success: bool, message: str, client: Client|None)
        """
        # Validar permisos
        if not current_user or current_user.role not in ['Master', 'Trader']:
            return False, 'No tienes permiso para actualizar documentos', None
        
        # Obtener cliente
        client = Client.query.get(client_id)
        if not client:
            return False, 'Cliente no encontrado', None
        
        # Actualizar URLs
        if dni_front_url:
            client.dni_front_url = dni_front_url
        
        if dni_back_url:
            client.dni_back_url = dni_back_url
        
        client.updated_at = now_peru()
        db.session.commit()
        
        # Registrar en auditoría
        AuditLog.log_action(
            user_id=current_user.id,
            action='UPDATE_CLIENT_DOCUMENTS',
            entity='Client',
            entity_id=client.id,
            details=f'Documentos de {client.name} actualizados'
        )
        
        return True, 'Documentos actualizados exitosamente', client
    
    @staticmethod
    def toggle_client_status(current_user, client_id):
        """
        Activar/Desactivar cliente
        
        Args:
            current_user: Usuario que realiza la acción
            client_id: ID del cliente
        
        Returns:
            tuple: (success: bool, message: str, client: Client|None)
        """
        # Validar permisos
        if not current_user or current_user.role not in ['Master', 'Trader']:
            return False, 'No tienes permiso para cambiar el estado de clientes', None
        
        # Obtener cliente
        client = Client.query.get(client_id)
        if not client:
            return False, 'Cliente no encontrado', None
        
        # Cambiar estado
        new_status = 'Inactivo' if client.status == 'Activo' else 'Activo'
        client.status = new_status
        client.updated_at = now_peru()
        db.session.commit()
        
        # Registrar en auditoría
        AuditLog.log_action(
            user_id=current_user.id,
            action='TOGGLE_CLIENT_STATUS',
            entity='Client',
            entity_id=client.id,
            details=f'Cliente {client.name} {new_status.lower()}'
        )
        
        return True, f'Cliente {new_status.lower()} exitosamente', client
    
    @staticmethod
    def delete_client(current_user, client_id):
        """
        Eliminar cliente (soft delete)
        
        Args:
            current_user: Usuario que elimina
            client_id: ID del cliente
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Solo Master puede eliminar
        if not current_user or current_user.role != 'Master':
            return False, 'Solo el Master puede eliminar clientes'
        
        # Obtener cliente
        client = Client.query.get(client_id)
        if not client:
            return False, 'Cliente no encontrado'
        
        # Verificar que no tenga operaciones en proceso
        active_operations = client.operations.filter(
            Client.status.in_(['Pendiente', 'En proceso'])
        ).count()
        
        if active_operations > 0:
            return False, 'No se puede eliminar. El cliente tiene operaciones activas'
        
        # Soft delete
        client.status = 'Inactivo'
        client.updated_at = now_peru()
        db.session.commit()
        
        # Registrar en auditoría
        AuditLog.log_action(
            user_id=current_user.id,
            action='DELETE_CLIENT',
            entity='Client',
            entity_id=client.id,
            details=f'Cliente {client.name} eliminado (soft delete)'
        )
        
        return True, 'Cliente eliminado exitosamente'
    
    @staticmethod
    def get_client_stats(client_id):
        """
        Obtener estadísticas de un cliente
        
        Args:
            client_id: ID del cliente
        
        Returns:
            dict: Estadísticas del cliente
        """
        client = Client.query.get(client_id)
        if not client:
            return None
        
        operations = client.operations.all()
        completed = [op for op in operations if op.status == 'Completada']
        
        return {
            'total_operations': len(operations),
            'completed_operations': len(completed),
            'pending_operations': client.operations.filter_by(status='Pendiente').count(),
            'in_process_operations': client.operations.filter_by(status='En proceso').count(),
            'total_usd_traded': sum(op.amount_usd for op in completed),
            'total_pen_traded': sum(op.amount_pen for op in completed)
        }
