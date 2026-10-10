import re
from datetime import datetime, timezone

# Mapa estándar Syslog de Severidades (RFC 3164 / RFC 5424)
SEVERITY_MAP = {
    0: "Emergency",
    1: "Alert",
    2: "Critical",
    3: "Error",
    4: "Warning",
    5: "Notice",
    6: "Info",
    7: "Debug"
}

def parse_syslog_line(line: str) -> dict:
    """
    Toma una línea de texto Syslog y extrae sus componentes clave.
    Soporta formato ISO (RFC 5424) o cadenas simples de laboratorio.
    """
    line = line.strip()
    if not line:
        return None

    # Expresión regular para capturar timestamp, IP y mensaje
    # Ejemplo: 2026-09-29T10:15:30Z 192.168.1.1 %LINK-3-UPDOWN: Interface GigabitEthernet0/1...
    iso_pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(.*)$'
    match = re.match(iso_pattern, line)

    if match:
        raw_time, source_ip, raw_message = match.groups()
        try:
            timestamp = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
        except ValueError:
            timestamp = datetime.now(timezone.utc)
    else:
        # Si no coincide con ISO, se usa una asignación por defecto
        source_ip = "127.0.0.1"
        raw_message = line
        timestamp = datetime.now(timezone.utc)

    # Inferencia de Severidad basada en palabras clave o etiquetas comunes (Cisco, Fortinet, Huawei)
    severity = 6  # Valor por defecto: Info
    
    msg_upper = raw_message.upper()
    if "%LINK-3-" in msg_upper or "LEVEL=\"CRITICAL\"" in msg_upper or "CRITICAL" in msg_upper:
        severity = 2 if "CRITICAL" in msg_upper else 3
    elif "%%01OSPF/2/" in msg_upper or "ERROR" in msg_upper:
        severity = 3
    elif "WARNING" in msg_upper or "HIGH CPU" in msg_upper:
        severity = 4
    elif "%SYS-5-" in msg_upper or "NOTICE" in msg_upper:
        severity = 5
    elif "DEBUG" in msg_upper:
        severity = 7

    severity_name = SEVERITY_MAP.get(severity, "Info")

    return {
        "timestamp": timestamp,
        "source_ip": source_ip,
        "facility": 1,
        "facility_name": "user",
        "severity": severity,
        "severity_name": severity_name,
        "message": raw_message,
        "is_synthetic": False
    }