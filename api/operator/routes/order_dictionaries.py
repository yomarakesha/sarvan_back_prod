from flask import jsonify
from ...admin import admin_bp
from utils.decorators import roles_required
from utils.payment_types import PaymentTypes
from utils.delivery_times import DeliveryTimes
from utils.order_statuses import OrderStatuses


@admin_bp.route('/payment-types', methods=['GET'])
@roles_required('admin', 'operator', 'courier', 'warehouse')
def get_payment_types():
    
    payment_types = []
    for payment_type in PaymentTypes.CHOICES:
        payment_types.append({
            'value': payment_type,
            'label_ru': PaymentTypes.LABELS[payment_type].get('ru'),
            'label_tm': PaymentTypes.LABELS[payment_type].get('tm'),
        })
    
    return jsonify({
        'payment_types': payment_types
    }), 200


@admin_bp.route('/delivery-times', methods=['GET'])
@roles_required('admin', 'operator', 'courier', 'warehouse')
def get_delivery_times():
    
    delivery_times = []
    for delivery_time in DeliveryTimes.CHOICES:
        delivery_times.append({
            'value': delivery_time,
            'label_ru': DeliveryTimes.LABELS[delivery_time].get('ru'),
            'label_tm': DeliveryTimes.LABELS[delivery_time].get('tm'),
        })
    
    return jsonify({
        'delivery_times': delivery_times
    }), 200


@admin_bp.route('/order-statuses', methods=['GET'])
@roles_required('admin', 'operator', 'courier', 'warehouse')
def get_order_statuses():
    
    order_statuses = []
    for status in OrderStatuses.CHOICES:
        order_statuses.append({
            'value': status,
            'label_ru': OrderStatuses.LABELS[status].get('ru'),
            'label_tm': OrderStatuses.LABELS[status].get('tm'),
        })
    
    return jsonify({
        'order_statuses': order_statuses
    }), 200
