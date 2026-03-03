from flask import Blueprint, request, jsonify
from extensions import db
from models.service import Service, ServiceRule, ServicePrice
from models.city import City
from models.price_type import PriceType
from models.product import Product
from utils.decorators import admin_required, roles_required
from utils.service_types import ServiceTypes
from .. import admin_bp
from sqlalchemy.orm import joinedload, selectinload


@admin_bp.route('/service-types', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_service_types():
    service_types_list = [
        {
            "code": ServiceTypes.INCOMING,
            "labels": ServiceTypes.LABELS[ServiceTypes.INCOMING]
        },
        {
            "code": ServiceTypes.OUTCOMING,
            "labels": ServiceTypes.LABELS[ServiceTypes.OUTCOMING]
        },
        {
            "code": ServiceTypes.TRANSFORMATION,
            "labels": ServiceTypes.LABELS[ServiceTypes.TRANSFORMATION]
        }
    ]
    
    return jsonify(service_types_list), 200


@admin_bp.route('/services', methods=['POST'])
@admin_required
def add_service():
    data = request.get_json()
    new_service = Service(
        name=data.get('name'),
        is_active=data.get('is_active', True)
    )
    db.session.add(new_service)
    db.session.commit()
    return jsonify({"message": "Услуга добавлена", "id": new_service.id}), 201


@admin_bp.route('/services/<int:service_id>/toggle', methods=['PATCH'])
@admin_required
def toggle_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()
    
    status = "активна" if service.is_active else "заблокирована"
    return jsonify({"message": f"Услуга теперь {status}", "is_active": service.is_active}), 200


@admin_bp.route('/services/prices', methods=['POST'])
@admin_required
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
    
    return jsonify({
        "message": message, 
        "id": price_entry.id
    }), 201


@admin_bp.route('/services/prices/<int:price_id>', methods=['DELETE'])
@admin_required
def delete_price(price_id):
    price_entry = ServicePrice.query.get_or_404(price_id)
    db.session.delete(price_entry)
    db.session.commit()
    return jsonify({"message": "Ценовое правило удалено"}), 200


@admin_bp.route('/services', methods=['GET'])
@admin_required
def get_services():
    city_id = request.args.get('city_id', type=int)
    is_active_str = request.args.get('is_active') 

    query = Service.query.options(
        selectinload(Service.rules).joinedload(ServiceRule.product),
        selectinload(Service.prices).joinedload(ServicePrice.city),
        selectinload(Service.prices).joinedload(ServicePrice.price_type)
    )

    if is_active_str is not None:
        is_active_bool = is_active_str.lower() == 'true'
        query = query.filter(Service.is_active == is_active_bool)

    if city_id:
        query = query.join(Service.prices).filter(ServicePrice.city_id == city_id).distinct()

    services = query.all()
    
    result = []
    for service in services:
        prices_data = []
        
        for p in service.prices:
            if city_id and p.city_id != city_id:
                continue
                
            prices_data.append({
                "id": p.id,
                "city_id": p.city_id,
                "city_name": p.city.name if p.city else "N/A",
                "price_type_id": p.price_type_id,
                "price_type_name": p.price_type.name if p.price_type else "N/A",
                "price": float(p.price)
            })
        
        rules_data = []
        for rule in service.rules:
            rules_data.append({
                "id": rule.id,
                "product_id": rule.product_id,
                "product_name": rule.product.name if rule.product else "N/A",
                "service_type": rule.service_type,
                "quantity": float(rule.quantity)
            })

        result.append({
            "id": service.id,
            "name": service.name,
            "is_active": service.is_active,
            "rules": rules_data,
            "prices": prices_data
        })

    return jsonify(result), 200


@admin_bp.route('/services/<int:service_id>', methods=['PUT'])
@admin_required
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    service.name = data.get('name', service.name)
    service.is_active = data.get('is_active', service.is_active)
    db.session.commit()
    return jsonify({"message": "Услуга обновлена"}), 200


@admin_bp.route('/services/<int:service_id>/rules', methods=['POST'])
@admin_required
def add_service_rule(service_id):
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    
    product = Product.query.get_or_404(data.get('product_id'))
    
    new_rule = ServiceRule(
        service_id=service_id,
        product_id=data.get('product_id'),
        service_type=data.get('service_type'),
        quantity=data.get('quantity')
    )
    db.session.add(new_rule)
    db.session.commit()
    
    return jsonify({
        "message": "Правило добавлено",
        "id": new_rule.id
    }), 201


@admin_bp.route('/services/rules/<int:rule_id>', methods=['DELETE'])
@admin_required
def delete_service_rule(rule_id):
    rule = ServiceRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({"message": "Правило удалено"}), 200




