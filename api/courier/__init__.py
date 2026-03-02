from flask import Blueprint

courier_bp = Blueprint('courier', __name__, url_prefix='/api/courier')

from . import routes