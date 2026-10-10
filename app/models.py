from datetime import datetime, timezone
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """
    Tabla de Usuarios autenticados mediante Cédula de Ciudadanía (CC).
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    cc_number = db.Column(db.String(20), unique=True, nullable=False)  # Cédula (Solo dígitos)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='Operador NOC')
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Utiliza hash seguro contra inyecciones y ataques de tiempo
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'cc_number': self.cc_number,
            'full_name': self.full_name,
            'role': self.role
        }

class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    vendor = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=True)
    os_version = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='Active')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    events = db.relationship('SyslogEvent', backref='device', lazy=True, cascade="all, delete-orphan")
    incidents = db.relationship('Incident', backref='device', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'vendor': self.vendor,
            'model': self.model,
            'os_version': self.os_version,
            'location': self.location,
            'status': self.status,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SyslogEvent(db.Model):
    __tablename__ = 'syslog_events'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    source_ip = db.Column(db.String(45), nullable=False)
    facility = db.Column(db.Integer, default=1)
    severity = db.Column(db.Integer, nullable=False)
    facility_name = db.Column(db.String(50), default='user')
    severity_name = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_synthetic = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    incidents = db.relationship('Incident', backref='event', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_hostname': self.device.hostname if self.device else 'Desconocido',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source_ip': self.source_ip,
            'facility': self.facility,
            'severity': self.severity,
            'facility_name': self.facility_name,
            'severity_name': self.severity_name,
            'message': self.message,
            'is_synthetic': self.is_synthetic,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('syslog_events.id'), nullable=True)
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(20), default='Open')
    assignee = db.Column(db.String(100), default='Sin Asignar')
    sla_deadline = db.Column(db.DateTime, nullable=True)
    root_cause = db.Column(db.Text, nullable=True)
    actions_taken = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'device_id': self.device_id,
            'device_hostname': self.device.hostname if self.device else 'Desconocido',
            'event_id': self.event_id,
            'priority': self.priority,
            'status': self.status,
            'assignee': self.assignee,
            'sla_deadline': self.sla_deadline.isoformat() if self.sla_deadline else None,
            'root_cause': self.root_cause,
            'actions_taken': self.actions_taken,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_action': self.user_action,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }