from flask import jsonify, request
from extensions import db
from models.user import User
from models.location import Location
from .. import admin_bp
from utils.decorators import admin_required
from werkzeug.security import generate_password_hash, check_password_hash

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    #/users?role=courier
    role_param = request.args.get('role')
    query = User.query
    if role_param:
        query = query.filter_by(role=role_param)

    users = query.all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.route('/users', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()

    required = ['full_name', 'phone', 'username', 'password', 'role']
    if not all(k in data for k in required):
        return jsonify({"error": "Заполните все поля"}), 400

    if User.query.filter((User.username == data['username']) | (User.phone == data['phone'])).first():
        return jsonify({"error": "Пользователь с таким логином или телефоном уже есть"}), 400

    new_user = User(
        full_name=data['full_name'],
        phone=data['phone'],
        username=data['username'],
        role=data['role']
    )
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.flush()

    # if courier - create a Location for the courier
    if new_user.role == 'courier':
        loc = Location(name=new_user.full_name, type='courier', user_id=new_user.id)
        db.session.add(loc)

    db.session.commit()
    return jsonify(new_user.to_dict()), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    new_username = data.get('username')
    if new_username and new_username != user.username:
        exists = User.query.filter(User.username == new_username, User.id != user_id).first()
        if exists:
            return jsonify({"error": "Это имя пользователя уже занято"}), 400
        user.username = new_username

    user.full_name = data.get('full_name', user.full_name)
    user.phone = data.get('phone', user.phone)
    user.role = data.get('role', user.role)

    if data.get('password'):
        user.set_password(data['password'])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Ошибка при обновлении данных"}), 500

    return jsonify(user.to_dict()), 200


@admin_bp.route('/users/<int:user_id>/block', methods=['PATCH'])
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return jsonify({"message": f"Пользователь {user.username} заблокирован", "user": user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    return jsonify({"message": f"Пользователь {user.username} разблокирован", "user": user.to_dict()}), 200
