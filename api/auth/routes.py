from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from extensions import db
from models.admin import Admin
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Введите логин и пароль"}), 400

    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password_hash, password):
        session.clear()
        session.permanent = True
        session['user_id'] = admin.id
        session['role'] = 'admin'
        
        return jsonify({
            "status": "success",
            "user": {
                "id": admin.id,
                "username": admin.username,
                "role": "admin"
            }
        }), 200

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session.clear()
        session.permanent = True
        session['user_id'] = user.id
        session['role'] = user.role
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "full_name": getattr(user, 'full_name', user.username)
        }

        return jsonify({
            "status": "success",
            "user": user_data
        }), 200

    return jsonify({"error": "Неверный логин или пароль"}), 401


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or not role:
        return jsonify({"authenticated": False}), 401

    if role == 'admin':
        user = Admin.query.get(user_id)
    else:
        user = User.query.get(user_id)

    if not user:
        session.clear()
        return jsonify({"authenticated": False}), 401

    user_data = {
        "id": user.id,
        "username": user.username,
        "role": role,
        "full_name": getattr(user, 'full_name', user.username)
    }

    return jsonify({
        "authenticated": True,
        "user": user_data
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    response = jsonify({"status": "success", "message": "Вышли из системы"})
    response.set_cookie('session', '', expires=0)
    return response, 200