from flask import jsonify, session
from extensions import db
from models.location import Location
from models.stock import Stock
from models.product import Product
from models.product_type import ProductType
from models.brand import Brand
from models.product_state import ProductState
from models.user import User
from .. import courier_bp
from utils.decorators import roles_required


@courier_bp.route('/stocks', methods=['GET'])
@roles_required('courier')
def get_courier_stocks():
    user_id = session.get('user_id')
    
    user = User.query.get(user_id)
    if not user or user.role != 'courier':
        return jsonify({'error': 'Unauthorized'}), 403
    
    stocks = db.session.query(
        Location.name.label('location_name'),
        Product.name.label('product_name'),
        ProductType.name.label('product_type_name'),
        Brand.name.label('brand_name'),
        ProductState.name.label('product_state_name'),
        Stock.quantity
    ).join(
        Location, Stock.location_id == Location.id
    ).join(
        Product, Stock.product_id == Product.id
    ).join(
        ProductType, Product.product_type_id == ProductType.id
    ).join(
        Brand, Product.brand_id == Brand.id
    ).join(
        ProductState, Stock.product_state_id == ProductState.id
    ).filter(
        Location.type == 'courier',
        Location.user_id == user_id
    ).all()

    result = [
        {
            'location_name': stock.location_name,
            'product_name': stock.product_name,
            'product_type_name': stock.product_type_name,
            'brand_name': stock.brand_name,
            'product_state_name': stock.product_state_name,
            'quantity': stock.quantity
        }
        for stock in stocks
    ]

    return jsonify(result), 200
