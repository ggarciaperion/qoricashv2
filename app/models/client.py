"""
Modelo de Cliente para QoriCash Trading V2
"""
from datetime import datetime
from app.extensions import db


class Client(db.Model):
    """Modelo de Cliente"""
    
    __tablename__ = 'clients'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Información personal
    name = db.Column(db.String(200), nullable=False)
    dni = db.Column(db.String(8), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    
    # Documentos (URLs de Cloudinary)
    dni_front_url = db.Column(db.String(500))
    dni_back_url = db.Column(db.String(500))
    
    # Cuentas bancarias
    bank_account_pen = db.Column(db.String(100))  # Cuenta en soles
    bank_account_usd = db.Column(db.String(100))  # Cuenta en dólares
    bank_name = db.Column(db.String(100))
    
    # Estado
    status = db.Column(
        db.String(20),
        nullable=False,
        default='Activo'
    )  # Activo, Inactivo
    
    # Notas
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    operations = db.relationship('Operation', backref='client', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(
            status.in_(['Activo', 'Inactivo']),
            name='check_client_status'
        ),
    )
    
    def to_dict(self, include_stats=False):
        """
        Convertir a diccionario
        
        Args:
            include_stats: Si incluir estadísticas de operaciones
        
        Returns:
            dict: Representación del cliente
        """
        data = {
            'id': self.id,
            'name': self.name,
            'dni': self.dni,
            'email': self.email,
            'phone': self.phone,
            'dni_front_url': self.dni_front_url,
            'dni_back_url': self.dni_back_url,
            'bank_account_pen': self.bank_account_pen,
            'bank_account_usd': self.bank_account_usd,
            'bank_name': self.bank_name,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats:
            data['total_operations'] = self.operations.count()
            completed_operations = self.operations.filter_by(status='Completada').all()
            data['total_usd_traded'] = sum(op.amount_usd for op in completed_operations)
        
        return data
    
    def is_active_client(self):
        """Verificar si está activo"""
        return self.status == 'Activo'
    
    def get_total_operations(self):
        """Obtener total de operaciones"""
        return self.operations.count()
    
    def get_completed_operations(self):
        """Obtener operaciones completadas"""
        return self.operations.filter_by(status='Completada').count()
    
    def __repr__(self):
        return f'<Client {self.name} - DNI: {self.dni}>'
