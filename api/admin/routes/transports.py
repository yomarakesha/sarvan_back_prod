from flask import jsonify, request
from extensions import db
from models.transport import Transport
from .. import admin_bp
from utils.decorators import admin_required

@admin_bp.route('/transports', methods=['GET', 'POST'])
@admin_required
def handle_transports():
    if request.method == 'POST':
        data = request.get_json()
        number = data.get('number')
        capacity = data.get('capacity')

        if not number or not capacity:
            return jsonify({"error": "Номер и вместимость обязательны"}), 400

        new_t = Transport(number=number, capacity=int(capacity))
        db.session.add(new_t)
        db.session.commit()
        return jsonify(new_t.to_dict()), 201

    transports = Transport.query.all()
    return jsonify([t.to_dict() for t in transports]), 200


@admin_bp.route('/transports/<int:t_id>', methods=['PUT'])
@admin_required
def update_transport(t_id):
    t = Transport.query.get_or_404(t_id)
    data = request.get_json()

    t.number = data.get('number', t.number)
    if data.get('capacity'):
        t.capacity = int(data.get('capacity'))

    db.session.commit()
    return jsonify(t.to_dict()), 200


@admin_bp.route('/transports/<int:t_id>/block', methods=['PATCH'])
@admin_required
def block_transport(t_id):
    t = Transport.query.get_or_404(t_id)
    t.is_active = False
    db.session.commit()
    return jsonify(t.to_dict()), 200


@admin_bp.route('/transports/<int:t_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_transport(t_id):
    t = Transport.query.get_or_404(t_id)
    t.is_active = True
    db.session.commit()
    return jsonify(t.to_dict()), 200
