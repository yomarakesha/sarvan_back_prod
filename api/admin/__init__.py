from flask import Blueprint
admin_bp = Blueprint('admin_api', __name__)
from .routes import cities, users, districts, price_types, transports
from .routes import couriers
from .routes import clients
from .routes import services
from .routes import product_types, brands, products, product_states, warehouses
from .routes import counterparties, locations, stocks, transactions