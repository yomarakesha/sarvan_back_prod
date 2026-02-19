from flask import Flask
from config import Config
from extensions import db
from api.admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)