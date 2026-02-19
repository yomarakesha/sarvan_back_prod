from flask import jsonify, request
from extensions import db
from models.price_type import PriceType
from .. import admin_bp
from .auth import admin_required


@admin_bp.route('/price-types', methods=['GET', 'POST'])
@admin_required
def handle_price_types():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        if not name: return jsonify({"error": "Имя обязательно"}), 400

        new_pt = PriceType(name=name)
        db.session.add(new_pt)
        db.session.commit()
        return jsonify(new_pt.to_dict()), 201

    pts = PriceType.query.all()
    return jsonify([pt.to_dict() for pt in pts]), 200


@admin_bp.route('/price-types/<int:pt_id>', methods=['PUT'])
@admin_required
def update_price_type(pt_id):
    pt = PriceType.query.get_or_404(pt_id)
    data = request.get_json()
    pt.name = data.get('name', pt.name)
    db.session.commit()
    return jsonify(pt.to_dict()), 200


@admin_bp.route('/price-types/<int:pt_id>/block', methods=['PATCH'])
@admin_required
def block_price_type(pt_id):
    pt = PriceType.query.get_or_404(pt_id)
    pt.is_active = False
    db.session.commit()
    return jsonify(pt.to_dict()), 200


@admin_bp.route('/price-types/<int:pt_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_price_type(pt_id):
    pt = PriceType.query.get_or_404(pt_id)
    pt.is_active = True
    db.session.commit()
    return jsonify(pt.to_dict()), 200
