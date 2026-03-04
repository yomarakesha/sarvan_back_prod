from flask import request, jsonify
from extensions import db
from models.client import Client, ClientPhone, ClientAddress
from models.client import ClientBlockReason
from models.location import Location
from .. import admin_bp
from utils.decorators import roles_required
from models.credit import ClientCredit
from models.stock import Stock
from sqlalchemy import func

@admin_bp.route('/clients', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_all_clients():
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    is_active = request.args.get('is_active', type=str)
    price_type_id = request.args.get('price_type_id', type=int)
    city_id = request.args.get('city_id', type=int)
    district_id = request.args.get('district_id', type=int)
    
    query = Client.query
    
    if is_active is not None:
        query = query.filter(Client.is_active == (is_active.lower() == 'true'))
    
    if price_type_id is not None:
        query = query.filter(Client.price_type_id == price_type_id)
    
    if city_id is not None or district_id is not None:
        query = query.join(ClientAddress, Client.id == ClientAddress.client_id)
        if city_id is not None:
            query = query.filter(ClientAddress.city_id == city_id)
        if district_id is not None:
            query = query.filter(ClientAddress.district_id == district_id)

        query = query.distinct()
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    clients_data = []
    for client in paginated.items:
        phones = [{"id": p.id, "phone": p.phone} for p in client.phones]
        addresses = [
            {
                "id": a.id,
                "city_id": a.city_id,
                "city_name": a.city.name if a.city else None,
                "district_id": a.district_id,
                "district_name": a.district.name if a.district else None,
                "address_line": a.address_line
            }
            for a in client.addresses
        ]
        
        client_dict = {
            "id": client.id,
            "full_name": client.full_name,
            "is_active": client.is_active,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "price_type_id": client.price_type_id,
            "price_type_name": client.price_type.name if client.price_type else None,
            "phones": phones,
            "addresses": addresses
        }
        clients_data.append(client_dict)
    
    return jsonify({
        "data": clients_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": paginated.total,
            "pages": paginated.pages
        }
    }), 200


@admin_bp.route('/clients', methods=['POST'])
@roles_required('admin','operator','courier','warehouse')
def create_client():
    data = request.get_json()
    if not data.get('price_type_id'):
        return jsonify({"error": "Нужно выбрать тип цены"}), 400
    
    new_client = Client(
        full_name=data.get('full_name'),
        price_type_id=data.get('price_type_id')
    )
    db.session.add(new_client)
    db.session.flush()
    
    # Автоматическое создание Location для клиента
    location = Location(
        name=new_client.full_name,
        type='client',
        client_id=new_client.id
    )
    db.session.add(location)
    new_client.location_id = location.id
    
    db.session.commit()
    return jsonify({"message": "Клиент создан", "id": new_client.id}), 201


@admin_bp.route('/clients/<int:client_id>', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    phones = [{"id": p.id, "phone": p.phone} for p in client.phones]
    addresses = [
        {
            "id": a.id,
            "city_id": a.city_id,
            "city_name": a.city.name if a.city else None,
            "district_id": a.district_id,
            "district_name": a.district.name if a.district else None,
            "address_line": a.address_line
        }
        for a in client.addresses
    ]
    
    # Получаем кредитную информацию
    credit_info = None
    client_credit = ClientCredit.query.filter_by(client_id=client.id).first()
    if client_credit:
        credit_info = {
            "credit_limit": float(client_credit.credit_limit),
            "used_credit": float(client_credit.used_credit),
            "available_credit": float(client_credit.available_credit)
        }
        
    # Считаем количество товаров в локации клиента
    total_items = 0
    if client.location_id:
        total = db.session.query(func.sum(Stock.quantity)).filter_by(location_id=client.location_id).scalar()
        if total is not None:
            total_items = float(total)
    
    client_data = {
        "id": client.id,
        "full_name": client.full_name,
        "is_active": client.is_active,
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "price_type_id": client.price_type_id,
        "price_type_name": client.price_type.name if client.price_type else None,
        "location_id": client.location_id,
        "phones": phones,
        "addresses": addresses,
        "credit": credit_info,
        "total_items_in_location": total_items
    }
    
    return jsonify(client_data), 200


@admin_bp.route('/clients/<int:client_id>/toggle-active', methods=['POST'])
@roles_required('admin','operator','courier','warehouse')
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


@admin_bp.route('/clients/<int:client_id>/block-reasons', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_client_block_reasons(client_id):
    client = Client.query.get_or_404(client_id)
    
    reasons_list = [
        {
            "id": reason.id,
            "reason": reason.reason,
            "created_at": reason.created_at.isoformat() if reason.created_at else None
        }
        for reason in client.block_reasons
    ]
    
    return jsonify(reasons_list), 200


@admin_bp.route('/clients/<int:client_id>', methods=['PATCH'])
@roles_required('admin','operator','courier','warehouse')
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
@roles_required('admin','operator','courier','warehouse')
def add_phone(client_id):
    data = request.get_json()
    new_phone = ClientPhone(client_id=client_id, phone=data.get('phone'))
    db.session.add(new_phone)
    db.session.commit()
    return jsonify({"id": new_phone.id, "message": "Телефон добавлен"}), 201


@admin_bp.route('/clients/<int:client_id>/phones', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_client_phones(client_id):
    client = Client.query.get_or_404(client_id)
    
    phones_list = [
        {"id": p.id, "phone": p.phone} 
        for p in client.phones
    ]
    
    return jsonify(phones_list), 200


@admin_bp.route('/clients/phones/<int:phone_id>', methods=['DELETE'])
@roles_required('admin','operator','courier','warehouse')
def remove_phone(phone_id):
    phone = ClientPhone.query.get_or_404(phone_id)
    db.session.delete(phone)
    db.session.commit()
    return jsonify({"message": "Телефон удален"}), 200


@admin_bp.route('/clients/<int:client_id>/addresses', methods=['POST'])
@roles_required('admin','operator','courier','warehouse')
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
@roles_required('admin','operator','courier','warehouse')
def remove_address(address_id):
    address = ClientAddress.query.get_or_404(address_id)
    db.session.delete(address)
    db.session.commit()
    return jsonify({"message": "Адрес удален"}), 200


@admin_bp.route('/clients/<int:client_id>/addresses', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
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

