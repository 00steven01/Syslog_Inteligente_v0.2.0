from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models import User, Device, SyslogEvent, Incident, AuditLog

app = create_app()

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("[+] Base de datos limpiada y reestructurada.")

        # 0. Crear Usuario por Defecto (Cédula Ficticia: 123456789, Clave: admin123)
        admin_user = User(
            cc_number="123456789",
            full_name="Administrador NOC",
            role="Administrador de Seguridad"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        print("[+] Usuario inicial creado (CC: 123456789 | Clave: admin123).")

        # 1. Crear Dispositivos Ficticios
        d1 = Device(
            hostname="RTR-BORDER-01",
            ip_address="192.168.1.1",
            vendor="Cisco",
            model="ISR 4331",
            os_version="IOS XE 17.03",
            location="Data Center Principal - Rack 01",
            status="Active"
        )
        d2 = Device(
            hostname="FW-FORTI-EDGE",
            ip_address="192.168.1.254",
            vendor="Fortinet",
            model="FortiGate 100F",
            os_version="FortiOS 7.2.4",
            location="Sede Central - DMZ",
            status="Active"
        )
        d3 = Device(
            hostname="SW-HUAWEI-CORE",
            ip_address="10.0.0.1",
            vendor="Huawei",
            model="CloudEngine S5735",
            os_version="VRP 8.180",
            location="Piso 2 - Cuarto de Comunicaciones",
            status="Active"
        )

        db.session.add_all([d1, d2, d3])
        db.session.commit()
        print("[+] 3 Dispositivos creados.")

        now_utc = datetime.now(timezone.utc)

        # 2. Crear Eventos Iniciales
        e1 = SyslogEvent(
            device_id=d1.id,
            timestamp=now_utc - timedelta(minutes=45),
            source_ip="192.168.1.1",
            facility=20,
            severity=3,
            facility_name="local4",
            severity_name="Error",
            message="%LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down",
            is_synthetic=True
        )
        e2 = SyslogEvent(
            device_id=d2.id,
            timestamp=now_utc - timedelta(minutes=30),
            source_ip="192.168.1.254",
            facility=1,
            severity=2,
            facility_name="user",
            severity_name="Critical",
            message="High CPU usage detected (92%) on FortiGate unit",
            is_synthetic=True
        )

        db.session.add_all([e1, e2])
        db.session.commit()

        # 3. Incidente de Muestra
        inc1 = Incident(
            title="Caída de Enlace Principal GigabitEthernet0/1",
            device_id=d1.id,
            event_id=e1.id,
            priority="High",
            status="In Progress",
            assignee="Operador NOC Alfa",
            sla_deadline=now_utc + timedelta(hours=2),
            root_cause="Falla física en el cableado o transceptor SFP.",
            actions_taken="Revisión remota iniciada."
        )
        db.session.add(inc1)

        audit1 = AuditLog(
            user_action="DATABASE_SEED",
            details="Base de datos poblada con credenciales y datos de laboratorio.",
            ip_address="127.0.0.1"
        )
        db.session.add(audit1)

        db.session.commit()
        print("[✔] Sembrado completado con éxito.")

if __name__ == '__main__':
    seed_database()