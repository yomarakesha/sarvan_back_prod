from flask import request, jsonify, session
from datetime import datetime, date, timedelta
from decimal import Decimal
from extensions import db
from models.order import Order, OrderItem
from models.client import Client, ClientPhone, ClientAddress
from models.service import Service, ServicePrice
from models.courier import CourierProfile
from models.credit import ClientCredit, CreditPayment
from ...admin import admin_bp
from utils.decorators import roles_required


@admin_bp.route('/orders', methods=['GET'])
@roles_required('admin', 'operator', 'courier', 'warehouse')
def get_all_orders():
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    client_id = request.args.get('client_id', type=int)
    courier_id = request.args.get('courier_id', type=int)
    status = request.args.get('status', type=str)
    payment_type = request.args.get('payment_type', type=str)
    delivery_date = request.args.get('delivery_date', type=str)
    
    query = Order.query
    
    if client_id:
        query = query.filter(Order.client_id == client_id)
    if courier_id:
        query = query.filter(Order.courier_id == courier_id)
    if status:
        query = query.filter(Order.status == status)
    if payment_type:
        query = query.filter(Order.payment_type == payment_type)
    if delivery_date:
        try:
            delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            query = query.filter(Order.delivery_date == delivery_date_obj)
        except ValueError:
            return jsonify({'error': 'Неправильный формат даты доставки. Используйте YYYY-MM-DD'}), 400
    
    query = query.order_by(Order.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    orders_data = []
    for order in paginated.items:
        orders_data.append(order.to_dict())
    
    return jsonify({
        'orders': orders_data,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }), 200


@admin_bp.route('/orders/<int:order_id>', methods=['GET'])
@roles_required('admin', 'operator', 'courier', 'warehouse')
def get_order(order_id):
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Заказ не найден'}), 404
    
    return jsonify(order.to_dict()), 200


@admin_bp.route('/clients/<int:client_id>/orders', methods=['GET'])
@roles_required('admin', 'operator', 'courier', 'warehouse')
def get_client_orders(client_id):
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Клиент не найден'}), 404
    
    status = request.args.get('status', type=str)
    courier_id = request.args.get('courier_id', type=int)
    delivery_date = request.args.get('delivery_date', type=str)
    
    query = Order.query.filter(Order.client_id == client_id)
    
    if status:
        query = query.filter(Order.status == status)
    if courier_id:
        query = query.filter(Order.courier_id == courier_id)
    if delivery_date:
        try:
            delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            query = query.filter(Order.delivery_date == delivery_date_obj)
        except ValueError:
            return jsonify({'error': 'Неправильный формат даты доставки. Используйте YYYY-MM-DD'}), 400
    
    query = query.order_by(Order.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    orders_data = []
    for order in paginated.items:
        orders_data.append(order.to_dict())
    
    return jsonify({
        'client_id': client_id,
        'client_name': client.full_name,
        'orders': orders_data,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }), 200


@admin_bp.route('/orders', methods=['POST'])
@roles_required('admin', 'operator')
def create_order():
    
    data = request.get_json()
    
    required_fields = ['client_id', 'client_address_id', 'client_phone_id', 
                       'delivery_date', 'delivery_time_type', 'payment_type', 'items']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400
    
    try:
        delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
        
        today = date.today()
        if delivery_date not in [today, today + timedelta(days=1)]:
            return jsonify({'error': 'Delivery date must be today or tomorrow'}), 400
        
        client = Client.query.get(data['client_id'])
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        client_address = ClientAddress.query.get(data['client_address_id'])
        if not client_address or client_address.client_id != data['client_id']:
            return jsonify({'error': 'Client address not found or does not belong to client'}), 404
        
        client_phone = ClientPhone.query.get(data['client_phone_id'])
        if not client_phone or client_phone.client_id != data['client_id']:
            return jsonify({'error': 'Client phone not found or does not belong to client'}), 404
        
        courier = None
        if 'courier_id' in data and data['courier_id']:
            courier = CourierProfile.query.get(data['courier_id'])
            if not courier:
                return jsonify({'error': 'Courier not found'}), 404
        
        delivery_time = None
        if data['delivery_time_type'] == 'specific_time':
            if 'delivery_time' not in data or not data['delivery_time']:
                return jsonify({'error': 'Delivery time required for specific_time type'}), 400
            try:
                delivery_time = datetime.strptime(data['delivery_time'], '%H:%M:%S').time()
            except ValueError:
                return jsonify({'error': 'Invalid delivery_time format. Use HH:MM:SS'}), 400
        
        order = Order(
            client_id=data['client_id'],
            client_address_id=data['client_address_id'],
            client_phone_id=data['client_phone_id'],
            courier_id=data.get('courier_id'),
            user_id=session.get('user_id'),
            note=data.get('note'),
            delivery_date=delivery_date,
            delivery_time_type=data['delivery_time_type'],
            delivery_time=delivery_time,
            payment_type=data['payment_type'],
            status=data.get('status', 'pending'),
        )
        
        if not data['items'] or len(data['items']) == 0:
            return jsonify({'error': 'Order must contain at least one service'}), 400
        
        for item in data['items']:
            if 'service_id' not in item or 'quantity' not in item:
                return jsonify({'error': 'Each item must have service_id and quantity'}), 400
            
            service = Service.query.get(item['service_id'])
            if not service:
                return jsonify({'error': f"Service {item['service_id']} not found"}), 404
            
            quantity = Decimal(str(item['quantity']))
            price = None
            total_price = None
            
            try:
                city_id = client_address.city_id
                price_type_id = client.price_type_id
                
                service_price = ServicePrice.query.filter_by(
                    service_id=item['service_id'],
                    city_id=city_id,
                    price_type_id=price_type_id
                ).first()
                
                if service_price:
                    price = service_price.price
                    total_price = price * quantity
            except Exception as e:
                # Если произойдет ошибка при получении цены, продолжаем без цены
                pass
            
            order_item = OrderItem(
                service_id=item['service_id'],
                quantity=quantity,
                price=price,
                total_price=total_price
            )
            order.items.append(order_item)
            
        # --- Подключение системы скидок ---
        # Вычисляем общую сумму заказа для проверки скидок
        total_order_price = sum((item.total_price for item in order.items if item.total_price), Decimal('0.0'))
        
        if total_order_price > 0:
            from utils.discount_logic import calculate_applicable_discount, apply_discount_to_order
            
            service_ids = [item.service_id for item in order.items]
            city_id = client_address.city_id
            
            best_discount, discount_amount = calculate_applicable_discount(
                client_id=order.client_id, 
                city_id=city_id, 
                service_ids=service_ids, 
                total_price=total_order_price
            )
            
            if best_discount and discount_amount > 0:
                apply_discount_to_order(order, best_discount.id, discount_amount)
        # ------------------------------------
        
        db.session.add(order)
        db.session.commit()
        
        # Обработка кредита, если тип оплаты "кредит" и передана сумма заказа
        if data['payment_type'] == 'credit' and 'order_amount' in data:
            try:
                order_amount = Decimal(str(data['order_amount']))
                
                # Получаем или создаем кредитную информацию клиента
                client_credit = ClientCredit.query.filter_by(client_id=data['client_id']).first()
                if not client_credit:
                    client_credit = ClientCredit(client_id=data['client_id'])
                    db.session.add(client_credit)
                
                # Проверяем достаточность кредита
                if client_credit.available_credit < order_amount:
                    db.session.rollback()
                    return jsonify({
                        'error': 'Insufficient credit',
                        'available_credit': float(client_credit.available_credit)
                    }), 400
                
                # Увеличиваем использованный кредит
                client_credit.used_credit = Decimal(str(client_credit.used_credit)) + order_amount
                
                # Создаем запись платежа (начисление кредита)
                credit_payment = CreditPayment(
                    client_credit_id=client_credit.id,
                    order_id=order.id,
                    payment_type='charge',
                    amount=order_amount,
                    description=f'Charge for order #{order.id}'
                )
                db.session.add(credit_payment)
                db.session.commit()
            except (ValueError, TypeError) as e:
                db.session.rollback()
                return jsonify({'error': f'Invalid order_amount: {str(e)}'}), 400
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500
        
        return jsonify(order.to_dict()), 201
    
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/orders/<int:order_id>', methods=['PUT'])
@roles_required('admin', 'operator')
def update_order(order_id):
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    data = request.get_json()
    
    try:
        # Обновление основных полей
        if 'courier_id' in data:
            if data['courier_id']:
                courier = CourierProfile.query.get(data['courier_id'])
                if not courier:
                    return jsonify({'error': 'Courier not found'}), 404
            order.courier_id = data['courier_id']
        
        if 'note' in data:
            order.note = data['note']
        
        if 'status' in data:
            order.status = data['status']
        
        if 'payment_type' in data:
            order.payment_type = data['payment_type']
        
        if 'delivery_time_type' in data:
            order.delivery_time_type = data['delivery_time_type']
            if data['delivery_time_type'] == 'specific_time':
                if 'delivery_time' not in data or not data['delivery_time']:
                    return jsonify({'error': 'Delivery time required for specific_time type'}), 400
                try:
                    order.delivery_time = datetime.strptime(data['delivery_time'], '%H:%M:%S').time()
                except ValueError:
                    return jsonify({'error': 'Invalid delivery_time format. Use HH:MM:SS'}), 400
            else:
                order.delivery_time = None
        
        # Обновление услуг
        if 'items' in data:
            # Удаляем старые услуги
            OrderItem.query.filter_by(order_id=order_id).delete()
            
            # Добавляем новые услуги
            if data['items'] and len(data['items']) > 0:
                for item in data['items']:
                    if 'service_id' not in item or 'quantity' not in item:
                        return jsonify({'error': 'Each item must have service_id and quantity'}), 400
                    
                    service = Service.query.get(item['service_id'])
                    if not service:
                        return jsonify({'error': f"Service {item['service_id']} not found"}), 404
                    
                    # Получение цены для услуги
                    quantity = Decimal(str(item['quantity']))
                    price = None
                    total_price = None
                    
                    try:
                        # Получаем city_id из адреса доставки
                        city_id = order.client_address.city_id
                        # Получаем price_type_id из клиента
                        price_type_id = order.client.price_type_id
                        
                        # Ищем цену услуги для данного города и типа цены
                        service_price = ServicePrice.query.filter_by(
                            service_id=item['service_id'],
                            city_id=city_id,
                            price_type_id=price_type_id
                        ).first()
                        
                        if service_price:
                            price = service_price.price
                            total_price = price * quantity
                    except Exception as e:
                        # Если произойдет ошибка при получении цены, продолжаем без цены
                        pass
                    
                    order_item = OrderItem(
                        service_id=item['service_id'],
                        quantity=quantity,
                        price=price,
                        total_price=total_price
                    )
                    order.items.append(order_item)
        
        db.session.commit()
        
        return jsonify(order.to_dict()), 200
    
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@roles_required('admin')
def delete_order(order_id):
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    try:
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'message': 'Order deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
