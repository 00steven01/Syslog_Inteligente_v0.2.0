import pytest
from app import create_app, db

@pytest.fixture
def app():
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

def test_create_and_get_device(client):
    """Prueba el Endpoint POST y GET /api/devices."""
    payload = {
        "hostname": "SW-TEST-01",
        "ip_address": "172.16.0.1",
        "vendor": "Cisco",
        "model": "Catalyst 2960"
    }
    response = client.post('/api/devices', json=payload)
    assert response.status_code == 201
    assert response.json['hostname'] == "SW-TEST-01"

    # Verificar que el dispositivo aparece en la lista GET
    get_res = client.get('/api/devices')
    assert get_res.status_code == 200
    assert len(get_res.json) == 1

def test_invalid_ip_device(client):
    """Prueba la validación de IP en la API."""
    payload = {
        "hostname": "SW-BAD-IP",
        "ip_address": "999.999.999.999",
        "vendor": "Cisco"
    }
    response = client.post('/api/devices', json=payload)
    assert response.status_code == 400
    assert "no es válida" in response.json['error']

def test_syslog_import_api(client):
    """Prueba la ingesta e importación de texto Syslog."""
    raw_log = "2026-09-29T10:15:30Z 192.168.1.1 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down"
    response = client.post('/api/syslog/import', json={"logs": raw_log})
    assert response.status_code == 201

    # Verificar la creación del evento
    events_res = client.get('/api/syslog/events')
    assert events_res.status_code == 200
    assert len(events_res.json) == 1
    assert events_res.json[0]['severity'] == 3