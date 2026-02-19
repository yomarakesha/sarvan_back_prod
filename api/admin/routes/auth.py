from flask import session, jsonify, request
from functools import wraps
from models import Admin
from .. import admin_bp

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = session.get('admin_id')
        if not admin_id or not Admin.query.get(admin_id):
            return jsonify({"error": "Доступ запрещен"}), 403
        return f(*args, **kwargs)

    return decorated_function

@admin_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    admin = Admin.query.filter_by(username=data.get('username')).first()
    if admin and admin.check_password(data.get('password')):
        session['admin_id'] = admin.id
        return jsonify({"message": "Вход выполнен"}), 200
    return jsonify({"error": "Ошибка входа"}), 401

@admin_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Вышли из системы"}), 200

