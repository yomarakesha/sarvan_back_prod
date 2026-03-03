from flask import jsonify, request, session
from extensions import db
from models.location import Location
from models.stock import Stock
from models.product import Product
from models.product_type import ProductType
from models.brand import Brand
from models.product_state import ProductState
from models.transaction import Transaction
from utils.transaction_types import TransactionTypes
from .. import warehouse_bp
from utils.decorators import roles_required

# Получение остатков на складе
@warehouse_bp.route('/stocks', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_warehouse_stocks():
    
    location_type = request.args.get('location_type', type=str, default=None)

    query = db.session.query(
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
    )
    
    if location_type:
        query = query.filter(Location.type == location_type)
    
    stocks = query.all()

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

#Приемка с завода на склад
@warehouse_bp.route('/stocks/receive_from_counterparty', methods=['POST'])
@roles_required('admin','operator','courier','warehouse')
def receive_stock_from_counterparty():
    
    data = request.get_json() or {}
    required = ['from_location_id', 'to_location_id', 'product_id', 'product_state_id', 'quantity']
    if not all(k in data for k in required):
        return jsonify({'error': 'Отсутствуют обязательные поля'}), 400

    try:
        from_loc_id = int(data['from_location_id'])
        to_loc_id = int(data['to_location_id'])
        product_id = int(data['product_id'])
        product_state_id = int(data['product_state_id'])
        quantity = float(data['quantity'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Неверные типы данных в полях'}), 400

    if quantity <= 0:
        return jsonify({'error': 'Количество должно быть больше нуля'}), 400

    from_loc = Location.query.get(from_loc_id)
    to_loc = Location.query.get(to_loc_id)
    if not from_loc or not to_loc:
        return jsonify({'error': 'Локация не найдена'}), 404

    if from_loc.type != 'counterparty':
        return jsonify({'error': 'from_location должен быть типа "counterparty"'}), 400
    if to_loc.type != 'warehouse':
        return jsonify({'error': 'to_location должен быть типа "warehouse"'}), 400

    product = Product.query.get(product_id)
    product_state = ProductState.query.get(product_state_id)
    if not product or not product_state:
        return jsonify({'error': 'Товар или состояние товара не найдены'}), 404

    user_id = session.get('user_id')

    transaction = Transaction(
        operation_type=TransactionTypes.INVENTORY_IN,
        from_location_id=from_loc_id,
        to_location_id=to_loc_id,
        product_id=product_id,
        product_state_id=product_state_id,
        quantity=quantity,
        user_id=user_id,
        note=data.get('note')
    )

    try:
        db.session.add(transaction)

        stock = Stock.query.filter_by(location_id=to_loc_id, product_id=product_id, product_state_id=product_state_id).first()
        if stock:
            stock.quantity = (stock.quantity or 0) + quantity
        else:
            stock = Stock(location_id=to_loc_id, product_id=product_id, product_state_id=product_state_id, quantity=quantity)
            db.session.add(stock)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при сохранении транзакции', 'detail': str(e)}), 500

    return jsonify(transaction.to_dict()), 201

