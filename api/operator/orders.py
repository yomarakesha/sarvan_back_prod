from flask import Blueprint, jsonify, request, session
from datetime import datetime, date, timedelta
from decimal import Decimal
from db import Db
from . import operator_bp
from decorators import roles_required
from all_types_description import PaymentTypes, DeliveryTimes, OrderStatuses

# -------------------------------------------------------------
# Создание заказа
# -------------------------------------------------------------
@operator_bp.route('/orders', methods=['POST'])
@roles_required('admin', 'operator')
def create_order():
    data = request.get_json()
    
    required_fields = ['client_id', 'client_address_id', 'client_phone_id', 
                       'delivery_date', 'delivery_time_type', 'payment_type', 'items']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400
        
    if not data['items'] or len(data['items']) == 0:
        return jsonify({'error': 'Заказ должен содержать хотя бы одну услугу'}), 400

    if data['payment_type'] not in PaymentTypes.CHOICES:
        return jsonify({'error': f"Недопустимый тип оплаты. Допустимые: {', '.join(PaymentTypes.CHOICES)}"}), 400
        
    if data['delivery_time_type'] not in DeliveryTimes.CHOICES:
        return jsonify({'error': f"Недопустимый тип времени доставки. Допустимые: {', '.join(DeliveryTimes.CHOICES)}"}), 400
        
    try:
        delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
        today = date.today()
        if delivery_date < today:
            return jsonify({'error': 'Дата доставки не может быть в прошлом'}), 400
            
        delivery_time = None
        if data['delivery_time_type'] == DeliveryTimes.SPECIFIC_TIME:
            if not data.get('delivery_time'):
                return jsonify({'error': 'Для указанного типа времени доставки требуется точное время (delivery_time)'}), 400
            delivery_time = datetime.strptime(data['delivery_time'], '%H:%M:%S').time()
    except ValueError as e:
        return jsonify({'error': f'Неправильный формат даты или времени: {str(e)}'}), 400

    conn = Db.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Загрузка данных клиента, проверка адреса, телефона
            cursor.execute("SELECT price_type_id FROM clients WHERE id = %s AND is_active = 1", (data['client_id'],))
            client = cursor.fetchone()
            if not client:
                return jsonify({'error': 'Активный клиент не найден'}), 404
            client_price_type_id = client['price_type_id']
                
            cursor.execute("""
                SELECT city_id FROM client_addresses 
                WHERE id = %s AND client_id = %s
            """, (data['client_address_id'], data['client_id']))
            address_info = cursor.fetchone()
            if not address_info:
                return jsonify({'error': 'Адрес клиента не найден или не принадлежит указанному клиенту'}), 404
            client_city_id = address_info['city_id']
                
            cursor.execute("""
                SELECT id FROM client_phones 
                WHERE id = %s AND client_id = %s
            """, (data['client_phone_id'], data['client_id']))
            if not cursor.fetchone():
                return jsonify({'error': 'Телефон клиента не найден или не принадлежит указанному клиенту'}), 404
                
            # Проверка курьера (если передан)
            if data.get('courier_id'):
                cursor.execute("SELECT user_id FROM courier_profiles WHERE user_id = %s", (data['courier_id'],))
                if not cursor.fetchone():
                    return jsonify({'error': 'Профиль курьера не найден'}), 404

            # 2. Создание заголовка заказа
            sql_order = """
                INSERT INTO orders (client_id, client_address_id, client_phone_id, courier_id, 
                                  user_id, note, delivery_date, delivery_time_type, 
                                  delivery_time, payment_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            user_id = session.get('user_id', 1)  # Дефолт 1 
            order_params = (
                data['client_id'], data['client_address_id'], data['client_phone_id'], 
                data.get('courier_id'), user_id, data.get('note'), 
                delivery_date, data['delivery_time_type'], delivery_time, 
                data['payment_type'], OrderStatuses.PENDING
            )
            cursor.execute(sql_order, order_params)
            order_id = cursor.lastrowid
            
            # 3. Добавление услуг (items) и расчет суммы
            total_order_price = Decimal('0.0')
            items_for_insert = []
            
            # Вспомогательный массив для расчета скидок
            order_items_calculated = []

            for item in data['items']:
                if 'service_id' not in item or 'quantity' not in item:
                    conn.rollback()
                    return jsonify({'error': 'Каждая позиция (item) должна содержать service_id и quantity'}), 400
                    
                service_id = item['service_id']
                quantity = Decimal(str(item['quantity']))
                
                # Поиск цены для данной услуги в данном городе по данному типу прайса клиента
                cursor.execute("""
                    SELECT price FROM service_prices 
                    WHERE service_id = %s AND city_id = %s AND price_type_id = %s
                """, (service_id, client_city_id, client_price_type_id))
                price_row = cursor.fetchone()
                
                price = None
                total_item_price = None
                
                if price_row and price_row['price'] is not None:
                    price = Decimal(str(price_row['price']))
                    total_item_price = price * quantity
                    total_order_price += total_item_price
                    
                items_for_insert.append((order_id, service_id, quantity, price, total_item_price))
                order_items_calculated.append({
                    'service_id': service_id,
                    'quantity': quantity,
                    'price': price,
                    'total_price': total_item_price or Decimal('0.0')
                })
            
            sql_items = """
                INSERT INTO order_items (order_id, service_id, quantity, price, total_price)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.executemany(sql_items, items_for_insert)
            
            # 4. Система скидок
            applied_discounts = []
            if total_order_price > 0:
                now = datetime.now()
                current_date = now.date()
                current_time = now.time()
                
                # Загружаем все потенциально доступные скидки (активные + подходящие по времени и лимитам)
                discount_sql = """
                    SELECT 
                        d.*,
                        GROUP_CONCAT(DISTINCT dc.city_id) as city_ids,
                        GROUP_CONCAT(DISTINCT ds.service_id) as service_ids,
                        GROUP_CONCAT(DISTINCT dp.price_type_id) as price_type_ids
                    FROM discounts d
                    LEFT JOIN discount_cities dc ON d.id = dc.discount_id
                    LEFT JOIN discount_services ds ON d.id = ds.discount_id
                    LEFT JOIN discount_price_types dp ON d.id = dp.discount_id
                    WHERE d.is_active = 1
                      AND (d.start_date IS NULL OR d.start_date <= %s)
                      AND (d.end_date IS NULL OR d.end_date >= %s)
                      AND (d.start_time IS NULL OR d.start_time <= %s)
                      AND (d.end_time IS NULL OR d.end_time >= %s)
                      AND (d.limit_count IS NULL OR d.usage_count < d.limit_count)
                    GROUP BY d.id
                """
                cursor.execute(discount_sql, (current_date, current_date, current_time, current_time))
                potential_discounts = cursor.fetchall()
                
                valid_discounts = []
                client_order_count = None  # Кэш для N-го заказа
                
                for d in potential_discounts:
                    # Разбираем GROUP_CONCAT
                    d_cities = [int(x) for x in d['city_ids'].split(',')] if d['city_ids'] else []
                    d_services = [int(x) for x in d['service_ids'].split(',')] if d['service_ids'] else []
                    d_prices = [int(x) for x in d['price_type_ids'].split(',')] if d['price_type_ids'] else []
                    
                    # Проверка города
                    if d_cities and client_city_id not in d_cities:
                        continue
                        
                    # Проверка типа прайс-листа
                    if d_prices and client_price_type_id not in d_prices:
                        continue
                        
                    # Определение базовой суммы для скидки (eligible_amount)
                    eligible_amount = Decimal('0.0')
                    if d_services:
                        # Если скидка привязана к услугам — считаем сумму только по этим услугам
                        has_service = False
                        for item in order_items_calculated:
                            if item['service_id'] in d_services:
                                has_service = True
                                eligible_amount += item['total_price']
                        if not has_service:
                            continue
                    else:
                        # Если не привязана, скидка применяется ко всему заказу
                        eligible_amount = total_order_price

                    if eligible_amount <= 0:
                        continue

                    # Расчет размера самой скидки
                    amount = Decimal('0.0')
                    d_type = d['discount_type']
                    val = Decimal(str(d['value'])) if d.get('value') is not None else Decimal('0.0')
                    
                    if d_type == 'fixed_amount':
                        amount = min(val, eligible_amount)
                    elif d_type == 'percentage':
                        amount = (eligible_amount * val) / Decimal('100.0')
                    elif d_type == 'fixed_price':
                        if eligible_amount > val:
                            amount = eligible_amount - val
                    elif d_type == 'free_n_th_order':
                        nth = d.get('nth_order')
                        if nth and nth > 0:
                            if client_order_count is None:
                                cursor.execute("SELECT COUNT(*) as count FROM orders WHERE client_id = %s", (data['client_id'],))
                                client_order_count = cursor.fetchone()['count']
                            if (client_order_count + 1) % nth == 0:
                                amount = eligible_amount
                    
                    if amount > 0:
                        valid_discounts.append({
                            'discount_id': d['id'],
                            'amount': amount,
                            'is_combinable': bool(d['is_combinable'])
                        })
                
                # Выбор оптимальной комбинации скидок
                combinable = [d for d in valid_discounts if d['is_combinable']]
                non_combinable = [d for d in valid_discounts if not d['is_combinable']]
                
                combinable_total = sum(d['amount'] for d in combinable)
                best_nc = max(non_combinable, key=lambda x: x['amount']) if non_combinable else None
                best_nc_amount = best_nc['amount'] if best_nc else Decimal('0.0')
                
                chosen_discounts = []
                if combinable_total > best_nc_amount:
                    # Применяем все комбинируемые скидки, следим чтобы общая скидка не превысила сумму заказа
                    remaining = total_order_price
                    for d in combinable:
                        amt = min(d['amount'], remaining)
                        if amt > 0:
                            chosen_discounts.append({'id': d['discount_id'], 'amount': amt})
                            remaining -= amt
                elif best_nc:
                    # Применяем лучшую некомбинируемую скидку
                    amt = min(best_nc_amount, total_order_price)
                    if amt > 0:
                        chosen_discounts.append({'id': best_nc['discount_id'], 'amount': amt})

                # Запись скидок в БД
                for cd in chosen_discounts:
                    cursor.execute("""
                        INSERT INTO order_discounts (order_id, discount_id, discount_amount) 
                        VALUES (%s, %s, %s)
                    """, (order_id, cd['id'], cd['amount']))
                    cursor.execute("UPDATE discounts SET usage_count = usage_count + 1 WHERE id = %s", (cd['id'],))
                    applied_discounts.append(cd)

            # Вычисляем финальную сумму заказа с учетом скидок
            total_discount_amount = sum(d['amount'] for d in applied_discounts)
            final_order_price = total_order_price - total_discount_amount
            if final_order_price < 0:
                final_order_price = Decimal('0.0')

            # 5. Обработка кредита
            if data['payment_type'] == PaymentTypes.CREDIT and final_order_price > 0:
                cursor.execute("SELECT id, credit_limit, used_credit FROM client_credits WHERE client_id = %s FOR UPDATE", 
                              (data['client_id'],))
                credit_row = cursor.fetchone()
                
                if not credit_row:
                    # Разрешен овердрафт или мы просто создаем нулевой лимит?
                    # В прошлой версии создавался нулевой лимит:
                    cursor.execute("INSERT INTO client_credits (client_id, credit_limit, used_credit) VALUES (%s, %s, %s)",
                                  (data['client_id'], 0, 0))
                    credit_id = cursor.lastrowid
                    available = Decimal('0.0')
                    used = Decimal('0.0')
                else:
                    credit_id = credit_row['id']
                    limit = Decimal(str(credit_row.get('credit_limit') or 0)) 
                    used = Decimal(str(credit_row.get('used_credit') or 0))
                    available = limit - used
                    
                if available < final_order_price:
                    conn.rollback()
                    return jsonify({
                        'error': 'Недостаточно кредитного лимита',
                        'available_credit': float(available),
                        'required_amount': float(final_order_price)
                    }), 400
                    
                new_used = used + final_order_price
                cursor.execute("UPDATE client_credits SET used_credit = %s WHERE id = %s", (new_used, credit_id))
                
                cursor.execute("""
                    INSERT INTO credit_payments (client_credit_id, order_id, payment_type, amount, description)
                    VALUES (%s, %s, %s, %s, %s)
                """, (credit_id, order_id, 'charge', final_order_price, f'Списание за заказ #{order_id}'))

            conn.commit()
            
            # 6. Возвращаем созданный заказ со всеми деталями
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            new_order = cursor.fetchone()
            
            # Форматирование дат для JSON
            if new_order.get('delivery_date'): new_order['delivery_date'] = new_order['delivery_date'].isoformat()
            if new_order.get('created_at'): new_order['created_at'] = new_order['created_at'].isoformat()
            if new_order.get('delivery_time') and hasattr(new_order['delivery_time'], 'seconds'):
                hours, remainder = divmod(new_order['delivery_time'].seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                new_order['delivery_time'] = f"{hours:02}:{minutes:02}:{seconds:02}"
                
            new_order['total_order_price'] = float(total_order_price)
            new_order['total_discount_amount'] = float(total_discount_amount)
            new_order['final_order_price'] = float(final_order_price)
            
            # Добавим для полноты ответа скидки и услуги
            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
            new_order['items'] = cursor.fetchall()
            for it in new_order['items']:
                if it.get('created_at'): it['created_at'] = it['created_at'].isoformat()
                
            cursor.execute("SELECT * FROM order_discounts WHERE order_id = %s", (order_id,))
            new_order['applied_discounts'] = cursor.fetchall()
            for dc in new_order['applied_discounts']:
                if dc.get('created_at'): dc['created_at'] = dc['created_at'].isoformat()
                
            return jsonify(new_order), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
