from flask import Flask, app
from config import Config
from extensions import db
from api.admin import admin_bp
from api.auth.routes import auth_bp
from api.warehouse import warehouse_bp
from api.courier import courier_bp
from api.operator import operator_bp
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app,supports_credentials=True)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(warehouse_bp, url_prefix='/api/warehouse')
    app.register_blueprint(courier_bp, url_prefix='/api/courier')
    app.register_blueprint(operator_bp, url_prefix='/api/operator')
    
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)