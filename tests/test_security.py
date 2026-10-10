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

def test_sql_injection_prevention(client):
    """Prueba de inyección SQL en la creación de dispositivos."""
    malicious_payload = {
        "hostname": "RTR-INJECT' OR '1'='1",
        "ip_address": "10.0.0.99",
        "vendor": "Cisco"
    }
    response = client.post('/api/devices', json=malicious_payload)
    assert response.status_code == 201

    # Verificar que el hostname se guardó como string literal seguro y no ejecutó SQL
    get_res = client.get('/api/devices')
    assert len(get_res.json) == 1
    assert get_res.json[0]['hostname'] == "RTR-INJECT' OR '1'='1"

def test_allowlist_command_blocking(client):
    """Prueba que la consola bloquee comandos destructivos o de configuración."""
    destructive_commands = [
        "reload",
        "delete flash:config.cfg",
        "configure terminal",
        "rm -rf /"
    ]
    for cmd in destructive_commands:
        response = client.post('/api/console/execute', json={"vendor": "cisco", "command": cmd})
        assert response.status_code == 200
        assert response.json['success'] is False
        assert "SECURITY BLOCK" in response.json['output']