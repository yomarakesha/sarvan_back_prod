from flask import jsonify, request
from extensions import db
from models.warehouse import Warehouse, WarehouseAddress, WarehousePhone
from models.location import Location
from .. import admin_bp
from utils.decorators import roles_required


@admin_bp.route('/warehouses', methods=['GET', 'POST'])
@roles_required('admin','operator','courier','warehouse')
def handle_warehouses():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"error": "Имя обязательно"}), 400

        addresses = data.get('addresses', [])
        phones = data.get('phones', [])

        w = Warehouse(name=name)
        db.session.add(w)
        db.session.flush()

        loc = Location(name=w.name, type='warehouse', warehouse_id=w.id)
        db.session.add(loc)

        for a in addresses:
            db.session.add(WarehouseAddress(warehouse_id=w.id, address_line=a))
        for ph in phones:
            db.session.add(WarehousePhone(warehouse_id=w.id, phone=ph))

        db.session.commit()
        return jsonify(w.to_dict()), 201

    ws = Warehouse.query.all()
    return jsonify([w.to_dict() for w in ws]), 200


@admin_bp.route('/warehouses/<int:w_id>', methods=['PUT'])
@roles_required('admin','operator','courier','warehouse')
def update_warehouse(w_id):
    w = Warehouse.query.get_or_404(w_id)
    data = request.get_json()
    w.name = data.get('name', w.name)

    if 'addresses' in data:
        w.addresses[:] = []
        for a in data.get('addresses', []):
            w.addresses.append(WarehouseAddress(address_line=a))
    if 'phones' in data:
        w.phones[:] = []
        for ph in data.get('phones', []):
            w.phones.append(WarehousePhone(phone=ph))

    db.session.commit()
    return jsonify(w.to_dict()), 200


@admin_bp.route('/warehouses/<int:w_id>/block', methods=['PATCH'])
@roles_required('admin','operator','courier','warehouse')
def block_warehouse(w_id):
    w = Warehouse.query.get_or_404(w_id)
    w.is_active = False
    db.session.commit()
    return jsonify(w.to_dict()), 200


@admin_bp.route('/warehouses/<int:w_id>/unblock', methods=['PATCH'])
@roles_required('admin','operator','courier','warehouse')
def unblock_warehouse(w_id):
    w = Warehouse.query.get_or_404(w_id)
    w.is_active = True
    db.session.commit()
    return jsonify(w.to_dict()), 200
