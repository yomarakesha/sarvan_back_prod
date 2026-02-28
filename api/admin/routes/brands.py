from flask import jsonify, request
from extensions import db
from models.brand import Brand
from .. import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/brands', methods=['GET', 'POST'])
@admin_required
def handle_brands():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"error": "Имя обязательно"}), 400

        new_b = Brand(name=name)
        db.session.add(new_b)
        db.session.commit()
        return jsonify(new_b.to_dict()), 201

    bs = Brand.query.all()
    return jsonify([b.to_dict() for b in bs]), 200


@admin_bp.route('/brands/<int:b_id>', methods=['PUT'])
@admin_required
def update_brand(b_id):
    b = Brand.query.get_or_404(b_id)
    data = request.get_json()
    b.name = data.get('name', b.name)
    db.session.commit()
    return jsonify(b.to_dict()), 200


@admin_bp.route('/brands/<int:b_id>/block', methods=['PATCH'])
@admin_required
def block_brand(b_id):
    b = Brand.query.get_or_404(b_id)
    b.is_active = False
    db.session.commit()
    return jsonify(b.to_dict()), 200


@admin_bp.route('/brands/<int:b_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_brand(b_id):
    b = Brand.query.get_or_404(b_id)
    b.is_active = True
    db.session.commit()
    return jsonify(b.to_dict()), 200
