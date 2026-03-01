from flask import jsonify, request, session
from datetime import datetime
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
from utils.decorators import admin_required, roles_required

#Запросы по локациям
@warehouse_bp.route('/locations/counterparties', methods=['GET'])
@roles_required('warehouse')
def get_counterparty_locations():

    locs = Location.query.filter_by(type='counterparty').all()
    result = [{'id': l.id, 'name': l.name} for l in locs]
    return jsonify(result), 200

@warehouse_bp.route('/locations/warehouses', methods=['GET'])
@roles_required('warehouse')
def get_warehouse_locations():
    
    locs = Location.query.filter_by(type='warehouse').all()
    result = [{'id': l.id, 'name': l.name} for l in locs]
    return jsonify(result), 200

@warehouse_bp.route('/locations/couriers', methods=['GET'])
@roles_required('warehouse')
def get_courier_locations():
    
    locs = Location.query.filter_by(type='courier').all()
    result = [{'id': l.id, 'name': l.name} for l in locs]
    return jsonify(result), 200

#Вернуть типы транзакций
@warehouse_bp.route('/transaction-types', methods=['GET'])
@roles_required('warehouse')
def get_transaction_types():
    types = {}
    for attr_name in dir(TransactionTypes):
        if attr_name.isupper():
            code = getattr(TransactionTypes, attr_name)
            if isinstance(code, str):
                types[attr_name] = {
                    'code': code,
                    'labels': TransactionTypes.LABELS.get(code, {})
                }
    return jsonify(types), 200


#Запросы по приемке с завода на склад

#Показывает остатки на складах (я использую зная что склад будет один)
@warehouse_bp.route('/stocks', methods=['GET'])
@roles_required('warehouse')
def get_warehouse_stocks():

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
        Location.type == 'warehouse'
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

#Приемка с завода на склад
@warehouse_bp.route('/stocks/receive_from_counterparty', methods=['POST'])
@roles_required('warehouse')
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


#Показывает транзакции по приемке с завода на склад
@warehouse_bp.route('/transactions_from_counterparties', methods=['GET'])
@roles_required('warehouse')
def list_incoming_transactions_from_counterparties():
    
    query = Transaction.query.filter_by(operation_type=TransactionTypes.INVENTORY_IN)

    start = request.args.get('start_date')
    end = request.args.get('end_date')
    if start:
        try:
            dt = datetime.fromisoformat(start)
        except ValueError:
            return jsonify({'error': 'Неверный формат start_date'}), 400
        query = query.filter(Transaction.created_at >= dt)
    if end:
        try:
            dt = datetime.fromisoformat(end)
        except ValueError:
            return jsonify({'error': 'Неверный формат end_date'}), 400
        query = query.filter(Transaction.created_at <= dt)

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        return jsonify({'error': 'page и per_page должны быть числами'}), 400

    pag = query.order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for t in pag.items:
        items.append({
            'id': t.id,
            'created_at': t.created_at.isoformat(),
            'operation_type': t.operation_type,
            'from_location_id': t.from_location_id,
            'from_location_name': t.from_location.name if t.from_location else None,
            'to_location_id': t.to_location_id,
            'to_location_name': t.to_location.name if t.to_location else None,
            'product_id': t.product_id,
            'product_name': t.product.name if t.product else None,
            'product_state_id': t.product_state_id,
            'product_state_name': t.product_state.name if t.product_state else None,
            'quantity': t.quantity,
            'user_id': t.user_id,
            'user_name': t.user.full_name if t.user else None,
            'note': t.note
        })

    return jsonify({
        'transactions': items,
        'page': pag.page,
        'per_page': pag.per_page,
        'total': pag.total,
        'pages': pag.pages
    }), 200

#Транзакции (перемещение товара между локациями)

#Создать транзакцию (перемещение товара между локациями).
@warehouse_bp.route('/transaction', methods=['POST'])
@roles_required('warehouse')
def create_transaction():
    
    data = request.get_json() or {}
    required = ['from_location_id', 'to_location_id', 'product_id', 'product_state_id', 'quantity', 'operation_type']
    if not all(k in data for k in required):
        return jsonify({'error': 'Отсутствуют обязательные поля'}), 400

    try:
        from_loc_id = int(data['from_location_id'])
        to_loc_id = int(data['to_location_id'])
        product_id = int(data['product_id'])
        product_state_id = int(data['product_state_id'])
        quantity = float(data['quantity'])
        operation_type = str(data['operation_type'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Неверные типы данных в полях'}), 400

    if quantity <= 0:
        return jsonify({'error': 'Количество должно быть больше нуля'}), 400

    from_loc = Location.query.get(from_loc_id)
    to_loc = Location.query.get(to_loc_id)
    if not from_loc or not to_loc:
        return jsonify({'error': 'Локация не найдена'}), 404

    product = Product.query.get(product_id)
    product_state = ProductState.query.get(product_state_id)
    if not product or not product_state:
        return jsonify({'error': 'Товар или состояние товара не найдены'}), 404

    user_id = session.get('user_id')

    transaction = Transaction(
        operation_type=operation_type,
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

        # Уменьшаем количество на локации отправителя
        from_stock = Stock.query.filter_by(location_id=from_loc_id, product_id=product_id, product_state_id=product_state_id).first()
        if from_stock:
            if from_stock.quantity < quantity:
                db.session.rollback()
                return jsonify({'error': 'Недостаточно товара на исходной локации'}), 400
            from_stock.quantity -= quantity
        else:
            db.session.rollback()
            return jsonify({'error': 'Товар не найден на исходной локации'}), 404

        # Увеличиваем количество на локации получателя
        to_stock = Stock.query.filter_by(location_id=to_loc_id, product_id=product_id, product_state_id=product_state_id).first()
        if to_stock:
            to_stock.quantity += quantity
        else:
            to_stock = Stock(location_id=to_loc_id, product_id=product_id, product_state_id=product_state_id, quantity=quantity)
            db.session.add(to_stock)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при сохранении транзакции', 'detail': str(e)}), 500

    return jsonify(transaction.to_dict()), 201

#Удалить транзакцию (отмена перемещения товара между локациями).
@warehouse_bp.route('/transaction/<int:transaction_id>', methods=['DELETE'])
@roles_required('warehouse')
def delete_transaction(transaction_id):
    
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'error': 'Транзакция не найдена'}), 404

    from_loc_id = transaction.from_location_id
    to_loc_id = transaction.to_location_id
    product_id = transaction.product_id
    product_state_id = transaction.product_state_id
    quantity = transaction.quantity

    try:
        # Вернуть товар на исходную локацию (уменьшить на локации получателя)
        to_stock = Stock.query.filter_by(location_id=to_loc_id, product_id=product_id, product_state_id=product_state_id).first()
        if to_stock:
            if to_stock.quantity < quantity:
                db.session.rollback()
                return jsonify({'error': 'Недостаточно товара для отмены транзакции'}), 400
            to_stock.quantity -= quantity
        else:
            db.session.rollback()
            return jsonify({'error': 'Товар не найден на локации получателя'}), 404

        # Увеличить на исходной локации
        from_stock = Stock.query.filter_by(location_id=from_loc_id, product_id=product_id, product_state_id=product_state_id).first()
        if from_stock:
            from_stock.quantity += quantity
        else:
            from_stock = Stock(location_id=from_loc_id, product_id=product_id, product_state_id=product_state_id, quantity=quantity)
            db.session.add(from_stock)

        db.session.delete(transaction)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при отмене транзакции', 'detail': str(e)}), 500

    return jsonify({'message': 'Транзакция успешно отменена'}), 200

#Показать все транзакции (перемещение товара между локациями) с фильтром по дате и по пользователю (курьеру или складчику).
@warehouse_bp.route('/transactions', methods=['GET'])
@roles_required('warehouse')
def list_transactions():
    
    query = Transaction.query

    start = request.args.get('start_date')
    end = request.args.get('end_date')
    if start:
        try:
            dt = datetime.fromisoformat(start)
        except ValueError:
            return jsonify({'error': 'Неверный формат start_date'}), 400
        query = query.filter(Transaction.created_at >= dt)
    if end:
        try:
            dt = datetime.fromisoformat(end)
        except ValueError:
            return jsonify({'error': 'Неверный формат end_date'}), 400
        query = query.filter(Transaction.created_at <= dt)

    user_id = request.args.get('user_id')
    if user_id:
        try:
            uid = int(user_id)
            query = query.filter(Transaction.user_id == uid)
        except ValueError:
            return jsonify({'error': 'user_id должен быть числом'}), 400

    operation_type = request.args.get('operation_type')
    if operation_type:
        query = query.filter(Transaction.operation_type == operation_type)

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        return jsonify({'error': 'page и per_page должны быть числами'}), 400

    pag = query.order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for t in pag.items:
        items.append({
            'id': t.id,
            'created_at': t.created_at.isoformat(),
            'operation_type': t.operation_type,
            'from_location_id': t.from_location_id,
            'from_location_name': t.from_location.name if t.from_location else None,
            'to_location_id': t.to_location_id,
            'to_location_name': t.to_location.name if t.to_location else None,
            'product_id': t.product_id,
            'product_name': t.product.name if t.product else None,
            'product_state_id': t.product_state_id,
            'product_state_name': t.product_state.name if t.product_state else None,
            'quantity': t.quantity,
            'user_id': t.user_id,
            'user_name': t.user.full_name if t.user else None,
            'note': t.note
        })

    return jsonify({
        'transactions': items,
        'page': pag.page,
        'per_page': pag.per_page,
        'total': pag.total,
        'pages': pag.pages
    }), 200
