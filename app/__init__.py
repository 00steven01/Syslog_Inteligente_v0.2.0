from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    with app.app_context():
        from app import models
        db.create_all()

    # Registrar las rutas API Blueprint
    from app.routes import api_bp
    app.register_blueprint(api_bp)
    
    @app.route('/health')
    def health_check():
        return {
            "status": "ok",
            "message": "NOC Syslog Inteligente - Servidor Alfa Operativo",
            "environment": "desarrollo_simulado"
        }, 200

    return app