from app import create_app

# Creamos la instancia de la aplicación usando nuestra función fábrica
app = create_app()

if __name__ == '__main__':
    # Ejecutamos el servidor de desarrollo local en el puerto 5000
    # debug=True permite que la aplicación se recargue automáticamente si cambias el código
    print("--------------------------------------------------")
    print(" Iniciando NOC Syslog Inteligente (Versión Alfa)")
    print(" Servidor escuchando en: http://127.0.0.1:5000")
    print(" Endpoint de prueba: http://127.0.0.1:5000/health")
    print("--------------------------------------------------")
    app.run(host='127.0.0.1', port=5000, debug=True)