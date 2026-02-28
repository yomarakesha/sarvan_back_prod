from flask import jsonify, request
from extensions import db
from models.product_state import ProductState
from .. import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/product-states', methods=['GET', 'POST'])
@admin_required
def handle_product_states():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"error": "Имя обязательно"}), 400

        new_ps = ProductState(name=name)
        db.session.add(new_ps)
        db.session.commit()
        return jsonify(new_ps.to_dict()), 201

    ps = ProductState.query.all()
    return jsonify([p.to_dict() for p in ps]), 200


@admin_bp.route('/product-states/<int:ps_id>', methods=['PUT'])
@admin_required
def update_product_state(ps_id):
    p = ProductState.query.get_or_404(ps_id)
    data = request.get_json()
    p.name = data.get('name', p.name)
    db.session.commit()
    return jsonify(p.to_dict()), 200


@admin_bp.route('/product-states/<int:ps_id>/block', methods=['PATCH'])
@admin_required
def block_product_state(ps_id):
    p = ProductState.query.get_or_404(ps_id)
    p.is_active = False
    db.session.commit()
    return jsonify(p.to_dict()), 200


@admin_bp.route('/product-states/<int:ps_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_product_state(ps_id):
    p = ProductState.query.get_or_404(ps_id)
    p.is_active = True
    db.session.commit()
    return jsonify(p.to_dict()), 200
