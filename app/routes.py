import random
import ipaddress
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template, session
from app import db
from app.models import User, Device, SyslogEvent, Incident, AuditLog
from app.syslog_parser import parse_syslog_line
from app.config_templates import generate_vendor_config
from app.command_engine import execute_simulated_command
from app.ntp_service import check_ntp_sync

api_bp = Blueprint('api', __name__)

def log_audit(action: str, details: str):
    audit = AuditLog(
        user_action=action,
        details=details,
        ip_address=request.remote_addr or '127.0.0.1'
    )
    db.session.add(audit)
    db.session.commit()

@api_bp.route('/')
def index():
    return render_template('index.html')

# --- AUTENTICACIÓN SEGUIRA Y GESTIÓN DE USUARIOS (CÉDULA) ---

@api_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    cc_number = str(data.get('cc_number', '')).strip()
    password = str(data.get('password', '')).strip()

    # Validar que la CC sea estrictamente de dígitos numéricos
    if not cc_number.isdigit():
        return jsonify({"error": "La Cédula (CC) debe contener únicamente números enteros sin puntos ni espacios."}), 400

    # Consulta parametrizada segura ORM (Inmune a SQL Injection)
    user = User.query.filter_by(cc_number=cc_number).first()

    if not user or not user.check_password(password):
        log_audit("LOGIN_FAILED", f"Intento fallido para CC: {cc_number}")
        return jsonify({"error": "Credenciales inválidas. Verifique su CC y contraseña."}), 401

    session['user_id'] = user.id
    session['cc_number'] = user.cc_number
    log_audit("LOGIN_SUCCESS", f"Usuario {user.full_name} (CC: {cc_number}) inició sesión.")

    return jsonify({"message": "Autenticación exitosa", "user": user.to_dict()}), 200

@api_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    cc_number = str(data.get('cc_number', '')).strip()
    full_name = str(data.get('full_name', '')).strip()
    password = str(data.get('password', '')).strip()

    if not cc_number.isdigit():
        return jsonify({"error": "La Cédula de Ciudadanía debe contener únicamente números enteros."}), 400

    if not full_name or not password:
        return jsonify({"error": "Todos los campos son obligatorios."}), 400

    if User.query.filter_by(cc_number=cc_number).first():
        return jsonify({"error": f"La Cédula {cc_number} ya se encuentra registrada."}), 409

    new_user = User(cc_number=cc_number, full_name=full_name, role="Operador NOC")
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    log_audit("USER_REGISTER", f"Nuevo usuario registrado: {full_name} (CC: {cc_number})")
    return jsonify({"message": "Usuario creado con éxito", "user": new_user.to_dict()}), 201

# --- SIMULADOR INTERACTIVO Y VARIADO DE FALLAS DE RED ---

FAILURE_TEMPLATES = {
    "bgp_down": {
        "severity": 2, "name": "Critical",
        "templates": [
            "%BGP-5-ADJCHANGE: neighbor {ip} Down - Peer closed session",
            "devname=\"FG-CORE-01\" level=\"critical\" msg=\"BGP Neighbor {ip} state changed to Established -> Down\"",
            "%%01BGP/2/BGP_STATE_CHANGED: BGP Peer {ip} status changed to Down"
        ]
    },
    "cpu_spike": {
        "severity": 3, "name": "Error",
        "templates": [
            "%SYS-3-CPU_RISING_THRESHOLD: CPU utilization exceeds threshold (98%) on module {slot}",
            "devname=\"FG-CORE-01\" level=\"error\" msg=\"High CPU usage detected (96%) in process 'wad'\"",
            "%%01CPU/3/CPU_OVERLOAD: CPU usage reached 99% on slot {slot}"
        ]
    },
    "link_flap": {
        "severity": 2, "name": "Critical",
        "templates": [
            "%LINK-2-DOWN: Core Interface GigabitEthernet0/{slot} changed state to down",
            "devname=\"FG-CORE-01\" level=\"critical\" msg=\"Link status change: port{slot} changed to DOWN\"",
            "%%01PHY/2/PHY_LINK_DOWN: Interface GigabitEthernet1/0/{slot} physical link down"
        ]
    },
    "ospf_error": {
        "severity": 4, "name": "Warning",
        "templates": [
            "%OSPF-4-ERRRCV: Received invalid OSPF packet from {ip} on interface Vlan10",
            "devname=\"FG-CORE-01\" level=\"warning\" msg=\"OSPF Neighbor {ip} MTU mismatch detected\"",
            "%%01OSPF/3/IF_CFG_ERROR: OSPF configuration mismatch on interface Vlanif10"
        ]
    }
}

@api_bp.route('/api/syslog/simulate', methods=['POST'])
def simulate_failures():
    """Genera e inyecta fallas usando exactamente la hora local de Colombia/Servidor (sin UTC)."""
    data = request.get_json() or {}
    fail_type = data.get('fail_type', 'link_flap')
    vendor = data.get('vendor', 'Cisco')
    severity = int(data.get('severity', 2))
    count = int(data.get('count', 3))

    severity_names = {
        2: "Critical",
        3: "Error",
        4: "Warning",
        6: "Info"
    }
    sev_name = severity_names.get(severity, "Critical")

    fail_catalog = {
        "link_flap": "%LINK-2-DOWN: Core Interface GigabitEthernet0/1 changed state to down",
        "bgp_down": "%BGP-5-ADJCHANGE: neighbor 192.168.1.254 Down - Peer closed session",
        "cpu_spike": "%SYS-3-CPU_RISING: CPU utilization exceeded threshold (98%)",
        "ospf_error": "%%01OSPF/3/IF_CFG_ERROR: OSPF configuration MTU mismatch on Vlanif10"
    }

    base_msg = fail_catalog.get(fail_type, fail_catalog["link_flap"])
    
    device = Device.query.filter_by(vendor=vendor).first()
    if not device:
        device = Device.query.first()

    source_ip = device.ip_address if device else "192.168.1.1"
    
    # HORA LOCAL NATIVA DEL SERVIDOR (Coincide exacto con la 1:13 PM / tu reloj de Windows)
    now_local = datetime.now()

    for i in range(count):
        event = SyslogEvent(
            device_id=device.id if device else None,
            timestamp=now_local,
            source_ip=source_ip,
            facility=1,
            severity=severity,
            facility_name="user",
            severity_name=sev_name,
            message=f"[{vendor.upper()}] {base_msg} (Evento #{i+1})",
            is_synthetic=True
        )
        db.session.add(event)

    db.session.commit()
    log_audit("SIMULATION_RUN", f"Se inyectaron {count} eventos ({vendor} - Hora Local: {now_local.strftime('%H:%M:%S')}).")

    return jsonify({
        "status": "success",
        "message": "Falla(s) creada(s) satisfactoriamente",
        "count": count
    }), 201

# --- OTROS ENDPOINTS (DISPOSITIVOS, SYSLOG, INCIDENTES) ---

@api_bp.route('/api/devices', methods=['GET'])
def get_devices():
    devices = Device.query.all()
    return jsonify([d.to_dict() for d in devices]), 200

@api_bp.route('/api/devices', methods=['POST'])
def create_device():
    data = request.get_json() or {}
    hostname = data.get('hostname', '').strip()
    ip_addr = data.get('ip_address', '').strip()
    vendor = data.get('vendor', '').strip()

    if not hostname or not ip_addr or not vendor:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    try:
        ipaddress.ip_address(ip_addr)
    except ValueError:
        return jsonify({"error": "La dirección IP no es válida"}), 400

    if Device.query.filter_by(hostname=hostname).first():
        return jsonify({"error": f"El dispositivo '{hostname}' ya existe"}), 409

    device = Device(
        hostname=hostname,
        ip_address=ip_addr,
        vendor=vendor,
        model=data.get('model', 'Desconocido'),
        os_version=data.get('os_version', 'N/A'),
        location=data.get('location', 'Sin asignar'),
        status=data.get('status', 'Active')
    )
    db.session.add(device)
    db.session.commit()
    log_audit("CREATE_DEVICE", f"Creado: {hostname} ({ip_addr})")
    return jsonify(device.to_dict()), 201

@api_bp.route('/api/syslog/events', methods=['GET'])
def get_syslog_events():
    severity_filter = request.args.get('severity', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = SyslogEvent.query

    if severity_filter is not None:
        query = query.filter_by(severity=severity_filter)

    if start_date and start_date.strip():
        try:
            s_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(SyslogEvent.timestamp >= s_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            e_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(SyslogEvent.timestamp <= e_dt)
        except ValueError:
            pass

    # Ordenado por ID descendente para que el más nuevo salga de primero arriba
    events = query.order_by(SyslogEvent.id.desc()).limit(100).all()
    return jsonify([e.to_dict() for e in events]), 200

    if severity_filter is not None:
        query = query.filter_by(severity=severity_filter)

    if start_date and start_date.strip():
        try:
            s_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            query = query.filter(SyslogEvent.timestamp >= s_dt)
        except ValueError:
            pass

    if end_date and end_date.strip():
        try:
            e_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(SyslogEvent.timestamp <= e_dt)
        except ValueError:
            pass

    events = query.order_by(SyslogEvent.timestamp.desc()).limit(100).all()
    return jsonify([e.to_dict() for e in events]), 200

@api_bp.route('/api/syslog/import', methods=['POST'])
def import_syslog_file():
    data = request.get_json() or {}
    raw_logs = data.get('logs', '')

    if not raw_logs:
        return jsonify({"error": "No se recibió texto de logs"}), 400

    lines = raw_logs.strip().split('\n')
    imported_count = 0

    for line in lines:
        parsed = parse_syslog_line(line)
        if parsed:
            dev = Device.query.filter_by(ip_address=parsed['source_ip']).first()
            event = SyslogEvent(
                device_id=dev.id if dev else None,
                timestamp=parsed['timestamp'],
                source_ip=parsed['source_ip'],
                facility=parsed['facility'],
                severity=parsed['severity'],
                facility_name=parsed['facility_name'],
                severity_name=parsed['severity_name'],
                message=parsed['message'],
                is_synthetic=False
            )
            db.session.add(event)
            imported_count += 1

    db.session.commit()
    log_audit("IMPORT_SYSLOG", f"Importados {imported_count} eventos.")
    return jsonify({"message": f"Se procesaron {imported_count} eventos."}), 201

@api_bp.route('/api/incidents', methods=['GET'])
def get_incidents():
    incidents = Incident.query.order_by(Incident.created_at.desc()).all()
    return jsonify([i.to_dict() for i in incidents]), 200

@api_bp.route('/api/incidents', methods=['POST'])
def create_incident():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    device_id = data.get('device_id')

    if not title or not device_id:
        return jsonify({"error": "El título y el dispositivo son obligatorios"}), 400

    dev = Device.query.get(device_id)
    if not dev:
        return jsonify({"error": "El dispositivo no existe"}), 404

    incident = Incident(
        title=title,
        device_id=device_id,
        event_id=data.get('event_id'),
        priority=data.get('priority', 'Medium'),
        status='Open',
        assignee=data.get('assignee', 'Sin Asignar'),
        root_cause=data.get('root_cause', '')
    )
    db.session.add(incident)
    db.session.commit()
    log_audit("CREATE_INCIDENT", f"Incidente #{incident.id} creado para {dev.hostname}")
    return jsonify(incident.to_dict()), 201

@api_bp.route('/api/templates/generate', methods=['POST'])
def get_config_template():
    data = request.get_json() or {}
    vendor = data.get('vendor', '')
    syslog_ip = data.get('syslog_ip', '')

    if not vendor or not syslog_ip:
        return jsonify({"error": "Especifique vendor e IP"}), 400

    result = generate_vendor_config(vendor, syslog_ip)
    return jsonify(result), 200

@api_bp.route('/api/console/execute', methods=['POST'])
def run_console_command():
    data = request.get_json() or {}
    vendor = (data.get('vendor') or 'cisco').lower()
    command = (data.get('command') or '').strip().lower()

    if not command:
        return jsonify({"output": "Error: Comando vacío."}), 400

    if command in ["clear", "cls"]:
        return jsonify({"output": "__CLEAR__"}), 200

    output = ""

    # 1. ENTORNO CISCO IOS / IOS XE
    if vendor == 'cisco':
        if "show ip int" in command or "show ip interface brief" in command:
            output = """Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.1.1     YES NVRAM  up                    up      
GigabitEthernet0/1     10.0.0.1        YES NVRAM  up                    up      
GigabitEthernet0/2     unassigned      YES unset  administratively down down    
Loopback0              1.1.1.1         YES NVRAM  up                    up      """
        elif "show logging" in command or "show log" in command:
            events = SyslogEvent.query.order_by(SyslogEvent.id.desc()).limit(5).all()
            logs_text = "\n".join([f"*Oct 10 {e.timestamp.strftime('%H:%M:%S')}.102: %SYS-3-LOG: {e.message}" for e in events])
            output = f"Syslog logging: enabled (0 messages dropped)\nBuffer logging: level debugging, 5 messages logged\n\n{logs_text or 'No logging events in buffer.'}"
        elif "show bgp" in command:
            output = """BGP table version is 14, local router ID is 1.1.1.1
Status codes: s suppressed, d damped, h history, * valid, > best, i - internal
Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
192.168.1.254   4 65001   10421   10400       14    0    0 03:21:44        12
10.0.0.2        4 65002    5211    5190       14    0    0 00:15:10         4"""
        elif "show ver" in command:
            output = """Cisco IOS XE Software, Version 17.03.04a
Cisco ISR4331/K9 (1RU) processor with 1798380K/6147K bytes of memory.
3 Gigabit Ethernet interfaces
2048K bytes of non-volatile configuration memory.
System image file is "bootflash:isr4300-universalk9.17.03.04a.SPA.bin"
Uptime is 42 days, 18 hours, 12 minutes"""
        elif "show proc" in command or "show cpu" in command:
            output = """CPU utilization for five seconds: 8%/1%; one minute: 9%; five minutes: 7%
 PID Runtime(ms)     Invoked      uSecs   5Sec   1Min   5Min TTY Process
   1          20          12       1666  0.00%  0.00%  0.00%   0 Init              
  84     1204810     4120190        292  2.10%  2.05%  2.00%   0 BGP Router        
 112      840120     2104000        399  1.50%  1.40%  1.45%   0 OSPF Hello        """
        elif "help" in command or "?" in command:
            output = "Comandos Cisco permitidos:\n - show ip interface brief\n - show logging\n - show bgp summary\n - show version\n - show processes cpu\n - clear"
        else:
            output = f"% Syntax error or unknown command: '{command}'. Escriba 'help' o '?' para ver comandos disponibles."

    # 2. ENTORNO FORTINET FORTIOS
    elif vendor == 'fortinet':
        if "get sys status" in command or "get system status" in command:
            output = """Version: FortiGate-100F v7.2.4,build1396,230309 (GA.F)
Virus-DB: 91.02380(2026-10-10 08:12)
Extended DB: 1.00000(2026-10-10 08:12)
IPS-DB: 6.00741(2026-10-10 02:15)
Serial-Number: FG100FTK20001234
Operation Mode: NAT
Current virtual domain: root
Max number of virtual domains: 10
Log status: Far-end server logging enabled (Syslog 192.168.1.254)"""
        elif "get sys perf" in command or "performance" in command:
            output = """CPU usage: 12%
Memory usage: 48%
Session count: 1420 active sessions
Session setup rate: 35 sessions/sec
Virus caught: 0
IPS attacks blocked: 14
Uptime: 18 days, 4 hours"""
        elif "get router info bgp" in command or "bgp" in command:
            output = """VRF table:(default)
BGP table version is 8, local router ID is 192.168.1.254
Status codes: s suppressed, d damped, h history, * valid, > best, i - internal
Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.0.0.1        4 65000     820     815        8    0    0 01:45:12         8"""
        elif "diagnose sys top" in command or "top" in command:
            output = """Run Time: 18 days, 4 hours and 12 minutes
0U, 0N, 12S, 88I; 7980T, 3820F
       cmdbsvr      112      S       2.1     1.2
        miglogd      204      S       1.8     2.4
         httpsd      412      S       1.1     3.0
       fortidss      810      S       0.5     1.1"""
        elif "help" in command or "?" in command:
            output = "Comandos Fortinet permitidos:\n - get system status\n - get system performance status\n - get router info bgp summary\n - diagnose sys top\n - clear"
        else:
            output = f"Unknown command: '{command}'. Type 'help' for available commands."

    # 3. ENTORNO HUAWEI VRP
    elif vendor == 'huawei':
        if "display ip int" in command or "display ip interface brief" in command:
            output = """*down: administratively down
^down: standby
(l): loopback
(s): spoofing
Interface                  IP Address/Mask      Physical   Protocol 
GE0/0/1                    10.0.0.1/24          up         up       
GE0/0/2                    192.168.1.2/24       up         up       
MEth0/0/1                  unassigned           down       down     
Vlanif10                   172.16.10.1/24       up         up       """
        elif "display logbuffer" in command or "display log" in command:
            events = SyslogEvent.query.order_by(SyslogEvent.id.desc()).limit(5).all()
            logs_text = "\n".join([f"Oct 10 2026 {e.timestamp.strftime('%H:%M:%S')} HUAWEI %%01{e.message}" for e in events])
            output = f"Logging buffer configuration and contents:\nAllowed max buffer size : 1024\nActual buffer size : 512\n\n{logs_text or 'No logs recorded.'}"
        elif "display bgp peer" in command or "bgp" in command:
            output = """ BGP local router ID : 10.0.0.1
 Local AS number : 65000
 Total number of peers : 1              Peers in established state : 1

  Peer            V          AS  MsgRcvd  MsgSent  OutQ  Up/Down       State PrefRcv
  192.168.1.1     4       65001     1205     1198     0 05:12:30 Established       15"""
        elif "display cpu" in command:
            output = """CPU Usage Stat. Cycle: 60 (Second)
CPU Usage         : 11% Max: 89%
CPU bit map : 1100000000000000
TaskName        CPU  Runtime(ms)  Invoke Count
VIDL           89%            0            0
OSPF            4%          120         5200
BGP             3%           95         4100
ROUT            2%           60         2100"""
        elif "help" in command or "?" in command:
            output = "Comandos Huawei permitidos:\n - display ip interface brief\n - display logbuffer\n - display bgp peer\n - display cpu-usage\n - clear"
        else:
            output = f"Error: Unrecognized command '{command}'. Type 'help' for command list."

    return jsonify({"output": output}), 200

@api_bp.route('/api/audit', methods=['GET'])
def get_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all()
    return jsonify([l.to_dict() for l in logs]), 200

@api_bp.route('/api/ntp/sync', methods=['GET'])
def sync_ntp_status():
    server = request.args.get('server', 'pool.ntp.org')
    ntp_info = check_ntp_sync(server)
    return jsonify(ntp_info), 200