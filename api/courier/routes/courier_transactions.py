from flask import jsonify, request, session
from datetime import datetime, date
from extensions import db
from models.transaction import Transaction
from models.user import User
from models.product import Product
from models.product_type import ProductType
from models.brand import Brand
from models.product_state import ProductState
from models.location import Location
from models.stock import Stock
from utils.transaction_types import TransactionTypes
from .. import courier_bp
from utils.decorators import roles_required


@courier_bp.route('/transactions', methods=['GET'])
@roles_required('courier')
def get_courier_transactions():
    user_id = session.get('user_id')
    
    user = User.query.get(user_id)
    if not user or user.role != 'courier':
        return jsonify({'error': 'Unauthorized'}), 403
    
    date_str = request.args.get('date', type=str)
    
    if not date_str:
        return jsonify({'error': 'Date parameter is required (format: YYYY-MM-DD)'}), 400
    
    try:
        transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    transactions = db.session.query(
        Transaction.id,
        Transaction.created_at,
        Transaction.operation_type,
        Transaction.quantity,
        Transaction.note,
        Product.name.label('product_name'),
        ProductType.name.label('product_type_name'),
        Brand.name.label('brand_name'),
        ProductState.name.label('product_state_name'),
        Location.name.label('from_location_name'),
        db.func.coalesce(Location.name, 'N/A').label('to_location_name')
    ).join(
        Product, Transaction.product_id == Product.id
    ).join(
        ProductType, Product.product_type_id == ProductType.id
    ).join(
        Brand, Product.brand_id == Brand.id
    ).join(
        ProductState, Transaction.product_state_id == ProductState.id
    ).outerjoin(
        Location, Transaction.from_location_id == Location.id
    ).filter(
        Transaction.user_id == user_id,
        db.func.cast(Transaction.created_at, db.Date) == transaction_date
    ).all()
    
    result = [
        {
            'id': transaction.id,
            'created_at': transaction.created_at.isoformat(),
            'operation_type': transaction.operation_type,
            'product_name': transaction.product_name,
            'product_type_name': transaction.product_type_name,
            'brand_name': transaction.brand_name,
            'product_state_name': transaction.product_state_name,
            'from_location_name': transaction.from_location_name,
            'quantity': transaction.quantity,
            'note': transaction.note
        }
        for transaction in transactions
    ]
    
    return jsonify(result), 200


@courier_bp.route('/transactions', methods=['POST'])
@roles_required('courier')
def create_courier_to_courier_transaction():
    user_id = session.get('user_id')
    
    current_user = User.query.get(user_id)
    if not current_user or current_user.role != 'courier':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    required = ['to_user_id', 'product_id', 'product_state_id', 'quantity']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        to_user_id = int(data['to_user_id'])
        product_id = int(data['product_id'])
        product_state_id = int(data['product_state_id'])
        quantity = float(data['quantity'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid data types'}), 400
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be greater than zero'}), 400
    
    target_user = User.query.get(to_user_id)
    if not target_user or target_user.role != 'courier':
        return jsonify({'error': 'Target user not found or is not a courier'}), 404
    
    from_location = Location.query.filter_by(user_id=user_id, type='courier').first()
    to_location = Location.query.filter_by(user_id=to_user_id, type='courier').first()
    
    if not from_location or not to_location:
        return jsonify({'error': 'Courier location not found'}), 404
    
    product = Product.query.get(product_id)
    product_state = ProductState.query.get(product_state_id)
    if not product or not product_state:
        return jsonify({'error': 'Product or product state not found'}), 404
    
    from_stock = Stock.query.filter_by(
        location_id=from_location.id,
        product_id=product_id,
        product_state_id=product_state_id
    ).first()
    
    if not from_stock or from_stock.quantity < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    try:
        transaction = Transaction(
            operation_type=TransactionTypes.TRANSFER,
            from_location_id=from_location.id,
            to_location_id=to_location.id,
            product_id=product_id,
            product_state_id=product_state_id,
            quantity=quantity,
            user_id=user_id,
            note=data.get('note')
        )
        
        db.session.add(transaction)
        
        from_stock.quantity -= quantity
        
        to_stock = Stock.query.filter_by(
            location_id=to_location.id,
            product_id=product_id,
            product_state_id=product_state_id
        ).first()
        
        if to_stock:
            to_stock.quantity += quantity
        else:
            to_stock = Stock(
                location_id=to_location.id,
                product_id=product_id,
                product_state_id=product_state_id,
                quantity=quantity
            )
            db.session.add(to_stock)
        
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating transaction', 'detail': str(e)}), 500


@courier_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
@roles_required('courier')
def get_transaction_details(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    from_location = Location.query.get(transaction.from_location_id) if transaction.from_location_id else None
    to_location = Location.query.get(transaction.to_location_id) if transaction.to_location_id else None
    product = Product.query.get(transaction.product_id)
    product_state = ProductState.query.get(transaction.product_state_id)
    
    product_type = None
    brand = None
    if product:
        product_type = ProductType.query.get(product.product_type_id)
        brand = Brand.query.get(product.brand_id)
    
    result = {
        'id': transaction.id,
        'created_at': transaction.created_at.isoformat(),
        'operation_type': transaction.operation_type,
        'quantity': transaction.quantity,
        'note': transaction.note,
        'user_id': transaction.user_id,
        'from_location': {
            'id': from_location.id,
            'name': from_location.name,
            'type': from_location.type
        } if from_location else None,
        'to_location': {
            'id': to_location.id,
            'name': to_location.name,
            'type': to_location.type
        } if to_location else None,
        'product': {
            'id': product.id,
            'name': product.name,
            'type': {
                'id': product_type.id,
                'name': product_type.name
            } if product_type else None,
            'brand': {
                'id': brand.id,
                'name': brand.name
            } if brand else None
        } if product else None,
        'product_state': {
            'id': product_state.id,
            'name': product_state.name
        } if product_state else None
    }
    
    return jsonify(result), 200
