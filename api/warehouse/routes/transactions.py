from flask import jsonify, request, session
from datetime import datetime
from extensions import db
from models.location import Location
from models.stock import Stock
from models.product import Product
from models.product_state import ProductState
from models.transaction import Transaction
from utils.transaction_types import TransactionTypes
from .. import warehouse_bp
from utils.decorators import roles_required


@warehouse_bp.route('/transaction-types', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
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


#Показывает транзакции по приемке с завода на склад
@warehouse_bp.route('/transactions_from_counterparties', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
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


#Создать транзакцию (перемещение товара между локациями).
@warehouse_bp.route('/transaction', methods=['POST'])
@roles_required('admin','operator','courier','warehouse')
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
@roles_required('admin','operator','courier','warehouse')
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

#Показать все транзакции (перемещение товара между локациями) с фильтром по дате и по пользователю (курьеру или складчику) и по типу операции.
@warehouse_bp.route('/transactions', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
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

