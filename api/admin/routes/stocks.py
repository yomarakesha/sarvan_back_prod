from flask import jsonify, request
from extensions import db
from models.stock import Stock
from .. import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/stocks', methods=['GET', 'POST'])
@admin_required
def handle_stocks():
    if request.method == 'POST':
        data = request.get_json()
        location_id = data.get('location_id')
        product_id = data.get('product_id')
        product_state_id = data.get('product_state_id')
        quantity = data.get('quantity', 0)
        if not location_id or not product_id or not product_state_id:
            return jsonify({"error": "location_id, product_id и product_state_id обязательны"}), 400

        s = Stock(location_id=location_id, product_id=product_id, product_state_id=product_state_id, quantity=quantity)
        db.session.add(s)
        db.session.commit()
        return jsonify(s.to_dict()), 201

    ss = Stock.query.all()
    return jsonify([s.to_dict() for s in ss]), 200


@admin_bp.route('/stocks/<int:s_id>', methods=['PUT'])
@admin_required
def update_stock(s_id):
    s = Stock.query.get_or_404(s_id)
    data = request.get_json()
    s.quantity = data.get('quantity', s.quantity)
    db.session.commit()
    return jsonify(s.to_dict()), 200
