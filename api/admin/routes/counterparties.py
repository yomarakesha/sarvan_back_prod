from flask import jsonify, request
from extensions import db
from models.counterparty import Counterparty, CounterpartyAddress, CounterpartyPhone
from models.location import Location
from .. import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/counterparties', methods=['GET', 'POST'])
@admin_required
def handle_counterparties():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"error": "Имя обязательно"}), 400

        addresses = data.get('addresses', [])
        phones = data.get('phones', [])

        c = Counterparty(name=name)
        db.session.add(c)
        db.session.flush()

        loc = Location(name=c.name, type='counterparty', counterparty_id=c.id)
        db.session.add(loc)

        for a in addresses:
            db.session.add(CounterpartyAddress(counterparty_id=c.id, address_line=a))
        for ph in phones:
            db.session.add(CounterpartyPhone(counterparty_id=c.id, phone=ph))

        db.session.commit()
        return jsonify(c.to_dict()), 201

    cs = Counterparty.query.all()
    return jsonify([c.to_dict() for c in cs]), 200


@admin_bp.route('/counterparties/<int:c_id>', methods=['PUT'])
@admin_required
def update_counterparty(c_id):
    c = Counterparty.query.get_or_404(c_id)
    data = request.get_json()
    c.name = data.get('name', c.name)

    if 'addresses' in data:
        c.addresses[:] = []
        for a in data.get('addresses', []):
            c.addresses.append(CounterpartyAddress(address_line=a))

    if 'phones' in data:
        c.phones[:] = []
        for ph in data.get('phones', []):
            c.phones.append(CounterpartyPhone(phone=ph))

    db.session.commit()
    return jsonify(c.to_dict()), 200


@admin_bp.route('/counterparties/<int:c_id>/block', methods=['PATCH'])
@admin_required
def block_counterparty(c_id):
    c = Counterparty.query.get_or_404(c_id)
    c.is_active = False
    db.session.commit()
    return jsonify(c.to_dict()), 200


@admin_bp.route('/counterparties/<int:c_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_counterparty(c_id):
    c = Counterparty.query.get_or_404(c_id)
    c.is_active = True
    db.session.commit()
    return jsonify(c.to_dict()), 200
