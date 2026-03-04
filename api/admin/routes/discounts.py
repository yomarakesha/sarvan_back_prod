from flask import jsonify, request
from extensions import db
from models.discount import Discount
from models.service import Service
from models.city import City
from .. import admin_bp
from utils.decorators import admin_required
from datetime import datetime

@admin_bp.route('/discounts', methods=['GET'])
@admin_required
def get_discounts():
    discounts = Discount.query.order_by(Discount.created_at.desc()).all()
    return jsonify([d.to_dict() for d in discounts]), 200

@admin_bp.route('/discounts', methods=['POST'])
@admin_required
def create_discount():
    data = request.json
    try:
        discount = Discount(
            name=data['name'],
            discount_type=data['discount_type'],
            value=data.get('value'),
            limit_count=data.get('limit_count'),
            nth_order=data.get('nth_order'),
            is_active=data.get('is_active', True)
        )
        
        if data.get('start_date'):
            discount.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('end_date'):
            discount.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if data.get('start_time'):
            discount.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if data.get('end_time'):
            discount.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            
        if 'service_ids' in data and isinstance(data['service_ids'], list) and data['service_ids']:
            services = Service.query.filter(Service.id.in_(data['service_ids'])).all()
            discount.services.extend(services)
            
        if 'city_ids' in data and isinstance(data['city_ids'], list) and data['city_ids']:
            cities = City.query.filter(City.id.in_(data['city_ids'])).all()
            discount.cities.extend(cities)
            
        db.session.add(discount)
        db.session.commit()
        return jsonify(discount.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/discounts/<int:id>', methods=['PUT'])
@admin_required
def update_discount(id):
    discount = db.session.get(Discount, id)
    if not discount:
        return jsonify({'error': 'Скидка не найдена'}), 404
        
    data = request.json
    try:
        if 'name' in data: 
            discount.name = data['name']
        if 'discount_type' in data: 
            discount.discount_type = data['discount_type']
        if 'value' in data: 
            discount.value = data['value']
        if 'limit_count' in data: 
            discount.limit_count = data['limit_count']
        if 'nth_order' in data: 
            discount.nth_order = data['nth_order']
        if 'is_active' in data: 
            discount.is_active = data['is_active']
            
        if 'start_date' in data:
            discount.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
        if 'end_date' in data:
            discount.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
        if 'start_time' in data:
            discount.start_time = datetime.strptime(data['start_time'], '%H:%M').time() if data['start_time'] else None
        if 'end_time' in data:
            discount.end_time = datetime.strptime(data['end_time'], '%H:%M').time() if data['end_time'] else None
            
        if 'service_ids' in data and isinstance(data['service_ids'], list):
            services = Service.query.filter(Service.id.in_(data['service_ids'])).all()
            discount.services = services
            
        if 'city_ids' in data and isinstance(data['city_ids'], list):
            cities = City.query.filter(City.id.in_(data['city_ids'])).all()
            discount.cities = cities
            
        db.session.commit()
        return jsonify(discount.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/discounts/<int:id>', methods=['DELETE'])
@admin_required
def delete_discount(id):
    discount = db.session.get(Discount, id)
    if not discount:
        return jsonify({'error': 'Скидка не найдена'}), 404
    
    # We don't hard delete to preserve order history, we just deactivate
    discount.is_active = False
    db.session.commit()
    return jsonify({'message': 'Скидка деактивирована'}), 200
