from flask import Blueprint

warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/api/warehouse')

from . import routes
