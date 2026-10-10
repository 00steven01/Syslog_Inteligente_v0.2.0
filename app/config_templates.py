def generate_vendor_config(vendor: str, syslog_ip: str, port: int = 514) -> dict:
    """
    Genera la plantilla de configuración Syslog comentada línea por línea
    para el fabricante especificado.
    
    ADVERTENCIA DE SEGURIDAD: La sintaxis exacta puede variar según la versión del SO.
    Consulte la documentación oficial del fabricante antes de aplicar en producción.
    """
    vendor = vendor.lower()

    if vendor == "cisco":
        config_text = f"""! =========================================================
! CONFIGURACION SYSLOG - CISCO IOS / IOS XE
! =========================================================
! Habilita la marca de tiempo de alta precisión en UTC
service timestamps log datetime msec localtime show-timezone

! Habilita el envío de mensajes de registro
logging on

! Define la dirección IP del servidor Syslog (NOC)
logging host {syslog_ip}

! Establece el nivel de severidad a enviar (trap warning = 0 a 4)
logging trap warning

! Define la categoría/facility para agrupamiento en el servidor (local4)
logging facility local4

! (Opcional) Especifica la interfaz origen para garantizar el enrutamiento
! logging source-interface GigabitEthernet0/0
! ========================================================="""

    elif vendor == "fortinet":
        config_text = f"""# =========================================================
# CONFIGURACION SYSLOG - FORTINET FORTIOS
# =========================================================
# Inicia la configuración del servidor Syslog remoto 1
config log syslogd setting
    # Habilita el destino Syslog
    set status enable
    
    # Define la IP del servidor receptor Syslog
    set server "{syslog_ip}"
    
    # Define el puerto UDP de escucha (Por defecto: 514)
    set port {port}
    
    # Define el nivel mínimo de severidad a transmitir (information, warning, critical)
    set minimum-sev warning
    
    # Define el formato del log como RFC 5424 estandarizado
    set format default
    
    # Asigna la categoría/facility de log local
    set facility local4
end
# ========================================================="""

    elif vendor == "huawei":
        config_text = f""";; =========================================================
;; CONFIGURACION SYSLOG - HUAWEI VRP
;; =========================================================
;; Habilita el centro de información de logs (Info-center)
info-center enable

;; Configura la dirección IP de destino y el canal de salida de logs
info-center loghost {syslog_ip} facility local4 language english

;; Define que el nivel de severidad enviado sea Warning o superior
info-center loghost {syslog_ip} level warning

;; Habilita la marca de tiempo precisa en los logs transmitidos
info-center timestamp log date
;; ========================================================="""

    else:
        return {
            "error": f"Fabricante '{vendor}' no soportado. Opciones válidas: Cisco, Fortinet, Huawei."
        }

    return {
        "vendor": vendor,
        "syslog_ip": syslog_ip,
        "port": port,
        "configuration": config_text,
        "disclaimer": "Verifique compatibilidad de sintaxis con la versión específica de su sistema operativo."
    }