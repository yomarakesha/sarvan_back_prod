from flask import Blueprint, request, jsonify
from extensions import db
from models.service import Service, ServiceLogisticInfo, ServicePrice
from models.city import City
from models.price_type import PriceType
from utils.decorators import admin_required
from .. import admin_bp


@admin_bp.route('/services', methods=['POST'])
@admin_required('admin')
def add_service():
    data = request.get_json()
    logistic_id = None
    log_data = data.get('logistic_info')
    if log_data:
        new_log = ServiceLogisticInfo(
            bottle_out=log_data.get('bottle_out'),
            bottle_in=log_data.get('bottle_in'),
            water_out=log_data.get('water_out', False),
            water_in=log_data.get('water_in', False)
        )
        db.session.add(new_log)
        db.session.flush()
        logistic_id = new_log.id
    new_service = Service(
        name=data.get('name'),
        is_active=data.get('is_active', True),
        logistic_info_id=logistic_id
    )
    db.session.add(new_service)
    db.session.commit()
    return jsonify({"message": "Услуга добавлена", "id": new_service.id}), 201


@admin_bp.route('/services/<int:service_id>', methods=['PUT'])
@admin_required('admin')
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    service.name = data.get('name', service.name)
    log_data = data.get('logistic_info')
    if log_data:
        if service.logistic_info:
            service.logistic_info.bottle_out = log_data.get('bottle_out', service.logistic_info.bottle_out)
            service.logistic_info.bottle_in = log_data.get('bottle_in', service.logistic_info.bottle_in)
            service.logistic_info.water_out = log_data.get('water_out', service.logistic_info.water_out)
            service.logistic_info.water_in = log_data.get('water_in', service.logistic_info.water_in)
        else:
            new_log = ServiceLogisticInfo(**log_data)
            db.session.add(new_log)
            db.session.flush()
            service.logistic_info_id = new_log.id
    db.session.commit()
    return jsonify({"message": "Услуга обновлена"}), 200

@admin_bp.route('/services/<int:service_id>/toggle', methods=['PATCH'])
@admin_required('admin')
def toggle_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()
    
    status = "активна" if service.is_active else "заблокирована"
    return jsonify({"message": f"Услуга теперь {status}", "is_active": service.is_active}), 200

@admin_bp.route('/services/prices', methods=['POST'])
@admin_required('admin')
def add_or_update_price():
    data = request.get_json()
    service_id = data.get('service_id')
    city_id = data.get('city_id')
    price_type_id = data.get('price_type_id')
    price_entry = ServicePrice.query.filter_by(
        service_id=service_id,
        city_id=city_id,
        price_type_id=price_type_id
    ).first() 
    if price_entry:
        price_entry.price = data.get('price')
        message = "Цена обновлена"
    else:
        price_entry = ServicePrice(
            service_id=service_id,
            city_id=city_id,
            price_type_id=price_type_id,
            price=data.get('price')
        )
        db.session.add(price_entry)
        message = "Цена добавлена"
    db.session.commit()
    return jsonify({"message": message}), 201


@admin_bp.route('/services/prices/<int:price_id>', methods=['DELETE'])
@admin_required('admin')
def delete_price(price_id):
    price_entry = ServicePrice.query.get_or_404(price_id)
    db.session.delete(price_entry)
    db.session.commit()
    return jsonify({"message": "Ценовое правило удалено"}), 200