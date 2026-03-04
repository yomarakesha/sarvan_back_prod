from datetime import datetime
from decimal import Decimal
from models.discount import Discount
from models.order import Order
from extensions import db

def calculate_applicable_discount(client_id: int, city_id: int, service_ids: list[int], total_price: Decimal):
    """
    Вычисляет максимальную доступную скидку для клиента по заданным параметрам.
    Возвращает кортеж: (discount_object, discount_amount)
    Если скидок нет, возвращает (None, Decimal('0.0'))
    """
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    
    # Ищем все активные скидки
    query = Discount.query.filter(Discount.is_active == True)
    
    # Фильтруем по датам
    query = query.filter(
        db.or_(Discount.start_date == None, Discount.start_date <= current_date),
        db.or_(Discount.end_date == None, Discount.end_date >= current_date)
    )
    
    potential_discounts = query.all()
    
    best_discount = None
    max_discount_amount = Decimal('0.0')
    
    for discount in potential_discounts:
        # 1. Проверка времени (счастливые часы и т.д.)
        if discount.start_time and current_time < discount.start_time:
            continue
        if discount.end_time and current_time > discount.end_time:
            continue
            
        # 2. Проверка глобально лимита использований
        if discount.limit_count is not None and discount.usage_count >= discount.limit_count:
            continue
            
        # 3. Проверка целевых городов (если список пуст - скидка действует во всех городах)
        if discount.cities:
            city_ids = [c.id for c in discount.cities]
            if city_id not in city_ids:
                continue
                
        # 4. Проверка целевых услуг (если список пуст - скидка действует на все услуги)
        if discount.services:
            discount_service_ids = [s.id for s in discount.services]
            if not any(sid in discount_service_ids for sid in service_ids):
                continue
                
        # 5. Рассчитываем сумму скидки для данного типа
        amount = Decimal('0.0')
        
        if discount.discount_type == 'fixed_amount':
            # Фиксированная сумма скидки (например, 10 манат)
            amount = Decimal(str(discount.value)) if discount.value else Decimal('0.0')
            if amount > total_price:
                amount = total_price  # Скидка не может быть больше суммы заказа
                
        elif discount.discount_type == 'percentage':
            # Скидка в процентах (например, 5%)
            percentage = Decimal(str(discount.value)) if discount.value else Decimal('0.0')
            amount = (total_price * percentage) / Decimal('100.0')
            
        elif discount.discount_type == 'fixed_price':
            # Фиксированная цена за заказ (например, все за 10 манат -> скидка это разница)
            fixed = Decimal(str(discount.value)) if discount.value else Decimal('0.0')
            if total_price > fixed:
                amount = total_price - fixed
                
        elif discount.discount_type == 'free_nth_order':
            # Каждый N-ый заказ бесплатно
            if discount.nth_order and discount.nth_order > 0:
                # Считаем количество предыдущих заказов клиента
                orders_count = Order.query.filter_by(client_id=client_id).count()
                current_order_number = orders_count + 1
                if current_order_number % discount.nth_order == 0:
                    amount = total_price  # Полностью бесплатно
                    
        # 6. Выбираем максимальную скидку среди всех доступных
        if amount > max_discount_amount:
            max_discount_amount = amount
            best_discount = discount
            
    return best_discount, max_discount_amount

def apply_discount_to_order(order: Order, discount_id: int, discount_amount: Decimal):
    """
    Применяет скидку к заказу и увеличивает счетчик использований.
    """
    if discount_id:
        discount = db.session.get(Discount, discount_id)
        if discount:
            discount.usage_count += 1
            order.applied_discount_id = discount_id
            order.discount_amount = discount_amount
