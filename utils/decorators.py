from functools import wraps
from flask import session, jsonify

def roles_required(*allowed_roles):
    """
    Использование: @roles_required('admin', 'director')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({
                    "authenticated": False, 
                    "error": "Необходима авторизация"
                }), 401
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                return jsonify({
                    "error": f"Доступ запрещен. Требуемая роль: {allowed_roles}, ваша роль: {user_role}"
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Быстрый декоратор только для админов
    """
    return roles_required('admin')(f)