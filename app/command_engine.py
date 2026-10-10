import re

# Comandos permitidos exclusivamente de solo lectura (Allowlist por fabricante)
ALLOWED_COMMANDS = {
    "cisco": [
        r"^show ip interface brief$",
        r"^show interfaces description$",
        r"^show version$",
        r"^show running-config \| include logging$",
        r"^show logging$"
    ],
    "fortinet": [
        r"^get system status$",
        r"^get system interface physical$",
        r"^get log syslogd setting$"
    ],
    "huawei": [
        r"^display ip interface brief$",
        r"^display version$",
        r"^display info-center$"
    ]
}

# Comandos simulados y sus respuestas fijas para laboratorio
SIMULATED_RESPONSES = {
    "show ip interface brief": """Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0         192.168.1.1     YES NVRAM  up                    up      
GigabitEthernet0/1         10.0.0.1        YES NVRAM  down                  down    
Loopback0                  1.1.1.1         YES NVRAM  up                    up""",
    
    "show logging": """Syslog logging: enabled (0 messages dropped, 3 messages rewritten)
    Console logging: disabled
    Buffer logging: level debugging, 4 messages logged
    Logging Exception size: 4096 bytes
    Simple Logging to 192.168.1.254: enabled""",

    "get system status": """Version: FortiGate-100F v7.2.4,build1396,230310 (GA.M)
Virus-DB: 1.00000(2026-10-10 09:00)
Extended DB: 1.00000(2026-10-10 09:00)
System time: Sat Oct 10 10:45:00 2026""",

    "display ip interface brief": """*down: administratively down
^down: standby
Interface                  IP Address/Mask      Physical   Protocol 
Vlanif10                   10.0.0.1/24          up         up       
GE0/0/1                    unassigned           up         down"""
}

def execute_simulated_command(vendor: str, command: str) -> dict:
    """
    Valida si un comando ingresado está explícitamente en la Allowlist del fabricante.
    Si es seguro, devuelve la respuesta simulada. De lo contrario, lo bloquea.
    """
    vendor = vendor.lower()
    command = command.strip()

    if vendor not in ALLOWED_COMMANDS:
        return {"success": False, "output": f"Error: Fabricante '{vendor}' no soportado."}

    # Verificar si el comando coincide con algún patrón permitido
    is_allowed = False
    for pattern in ALLOWED_COMMANDS[vendor]:
        if re.match(pattern, command, re.IGNORECASE):
            is_allowed = True
            break

    if not is_allowed:
        return {
            "success": False,
            "output": f"SECURITY BLOCK: El comando '{command}' fue DENEGADO.\n"
                      f"Razón: No pertenece a la lista de comandos de consulta autorizados (Allowlist) para {vendor.upper()}.\n"
                      f"Operación de escritura o no permitida detectada."
        }

    # Buscar respuesta simulada
    output = SIMULATED_RESPONSES.get(
        command.lower(),
        f"Comando '{command}' autorizado. [Simulación Alfa: Respuesta predeterminada de {vendor.upper()} OK]"
    )

    return {
        "success": True,
        "vendor": vendor,
        "command": command,
        "output": output
    }