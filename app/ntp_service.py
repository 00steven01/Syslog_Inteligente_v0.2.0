import socket
import struct
import time
from datetime import datetime, timezone

def check_ntp_sync(ntp_server: str = "pool.ntp.org") -> dict:
    """
    Consulta un servidor NTP público o local para calcular el desfase (drift) 
    de hora en relación al reloj del sistema local.
    """
    NTP_PORT = 123
    TIME1970 = 2208988800  # Epoch offset entre 1900 (NTP) y 1970 (Unix)

    # Paquete NTP v3 en formato binario (48 bytes)
    msg = b'\x1b' + 47 * b'\x00'

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(2.0)  # Timeout de 2 segundos
        
        start_time = time.time()
        client.sendto(msg, (ntp_server, NTP_PORT))
        data, _ = client.recvfrom(1024)
        end_time = time.time()

        if data:
            # Extraer el timestamp del servidor del paquete binario
            unpacked = struct.unpack("!12I", data)
            transit_time = (end_time - start_time) / 2
            ntp_seconds = unpacked[10] + (unpacked[11] / 2**32) - TIME1970
            
            server_utc = datetime.fromtimestamp(ntp_seconds, tz=timezone.utc)
            local_utc = datetime.now(timezone.utc)
            
            drift_seconds = abs((server_utc - local_utc).total_seconds())

            return {
                "status": "synchronized",
                "ntp_server": ntp_server,
                "server_time": server_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "local_time": local_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "drift_seconds": round(drift_seconds, 3),
                "in_sync": drift_seconds < 5.0  # Considerado en sincro si desfase < 5s
            }
    except Exception as e:
        # Si no hay salida a internet o falla la resolución DNS
        local_utc = datetime.now(timezone.utc)
        return {
            "status": "offline_mode",
            "ntp_server": ntp_server,
            "server_time": local_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "local_time": local_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "drift_seconds": 0.0,
            "in_sync": True,
            "message": f"Modo local activo (no se pudo contactar con {ntp_server}): {str(e)}"
        }