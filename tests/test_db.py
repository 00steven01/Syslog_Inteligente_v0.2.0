import pytest
from app import create_app, db
from app.models import Device, SyslogEvent

@pytest.fixture
def app():
    """Configura una instancia de la app utilizando base de datos en memoria para pruebas."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_device_creation(app):
    """Prueba la creación de un dispositivo en la BD."""
    with app.app_context():
        dev = Device(
            hostname="TEST-ROUTER",
            ip_address="10.10.10.1",
            vendor="Cisco",
            status="Active"
        )
        db.session.add(dev)
        db.session.commit()

        retrieved = Device.query.filter_by(hostname="TEST-ROUTER").first()
        assert retrieved is not None
        assert retrieved.ip_address == "10.10.10.1"
        assert retrieved.vendor == "Cisco"

def test_syslog_relation(app):
    """Prueba la relación de clave foránea entre dispositivo y evento."""
    with app.app_context():
        dev = Device(hostname="TEST-FW", ip_address="10.10.10.2", vendor="Fortinet")
        db.session.add(dev)
        db.session.commit()

        event = SyslogEvent(
            device_id=dev.id,
            source_ip=dev.ip_address,
            severity=2,
            severity_name="Critical",
            message="Test critical message"
        )
        db.session.add(event)
        db.session.commit()

        # Usamos dev.events porque así está definida la relación en app/models.py
        assert len(dev.events) == 1
        assert dev.events[0].message == "Test critical message"