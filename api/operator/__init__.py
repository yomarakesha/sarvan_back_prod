from flask import Blueprint

operator_bp = Blueprint('operator', __name__, url_prefix='/api/operator')

from . import routes