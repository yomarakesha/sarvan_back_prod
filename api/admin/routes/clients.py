from flask import request, jsonify
from extensions import db
from models.client import Client, ClientPhone, ClientAddress
from models.client import ClientBlockReason
from models.price_type import PriceType
from .. import admin_bp
from utils.decorators import admin_required

@admin_bp.route('/clients', methods=['POST'])
@admin_required
def create_client():
    data = request.get_json()
    if not data.get('price_type_id'):
        return jsonify({"error": "Нужно выбрать тип цены"}), 400
    
    new_client = Client(
        full_name=data.get('full_name'),
        price_type_id=data.get('price_type_id')
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify({"message": "Клиент создан", "id": new_client.id}), 201


@admin_bp.route('/clients/<int:client_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_client_active(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json() or {}
    
    target_status = data.get('is_active')
    if target_status is None:
        target_status = not client.is_active

    if client.is_active and not target_status:
        reason_text = data.get('reason')
        if not reason_text or not reason_text.strip():
            return jsonify({"error": "При блокировке необходимо указать причину"}), 400

        new_reason = ClientBlockReason(
            client_id=client.id,
            reason=reason_text.strip()
        )
        db.session.add(new_reason)

    elif not client.is_active and target_status:
        pass

    client.is_active = target_status
    db.session.commit()
    
    return jsonify({
        "message": "Статус успешно обновлен", 
        "is_active": client.is_active
    }), 200


@admin_bp.route('/clients/<int:client_id>', methods=['PATCH'])
@admin_required
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    
    if 'full_name' in data:
        client.full_name = data['full_name']
    if 'price_type_id' in data:
        client.price_type_id = data['price_type_id']
        
    db.session.commit()
    return jsonify({"message": "Данные обновлены"}), 200


@admin_bp.route('/clients/<int:client_id>/phones', methods=['POST'])
@admin_required
def add_phone(client_id):
    data = request.get_json()
    new_phone = ClientPhone(client_id=client_id, phone=data.get('phone'))
    db.session.add(new_phone)
    db.session.commit()
    return jsonify({"id": new_phone.id, "message": "Телефон добавлен"}), 201


@admin_bp.route('/clients/<int:client_id>/phones', methods=['GET'])
@admin_required
def get_client_phones(client_id):
    client = Client.query.get_or_404(client_id)
    
    phones_list = [
        {"id": p.id, "phone": p.phone} 
        for p in client.phones
    ]
    
    return jsonify(phones_list), 200


@admin_bp.route('/clients/phones/<int:phone_id>', methods=['DELETE'])
@admin_required
def remove_phone(phone_id):
    phone = ClientPhone.query.get_or_404(phone_id)
    db.session.delete(phone)
    db.session.commit()
    return jsonify({"message": "Телефон удален"}), 200


@admin_bp.route('/clients/<int:client_id>/addresses', methods=['POST'])
@admin_required
def add_address(client_id):
    data = request.get_json()
    new_addr = ClientAddress(
        client_id=client_id,
        city_id=data.get('city_id'),
        district_id=data.get('district_id'),
        address_line=data.get('address_line')
    )
    db.session.add(new_addr)
    db.session.commit()
    return jsonify({"id": new_addr.id, "message": "Адрес добавлен"}), 201


@admin_bp.route('/clients/addresses/<int:address_id>', methods=['DELETE'])
@admin_required
def remove_address(address_id):
    address = ClientAddress.query.get_or_404(address_id)
    db.session.delete(address)
    db.session.commit()
    return jsonify({"message": "Адрес удален"}), 200


@admin_bp.route('/clients/<int:client_id>/addresses', methods=['GET'])
@admin_required
def get_client_addresses(client_id):
    client = Client.query.get_or_404(client_id)
    
    addresses_list = [
        {
            "id": a.id,
            "city_id": a.city_id,
            "city_name": a.city.name if a.city else "Неизвестно",
            "district_id": a.district_id,
            "district_name": a.district.name if a.district else "Неизвестно",
            "address_line": a.address_line
        } for a in client.addresses
    ]
    
    return jsonify(addresses_list), 200
