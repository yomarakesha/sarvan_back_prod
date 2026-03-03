from flask import jsonify, request
from extensions import db
from models.product_type import ProductType
from .. import admin_bp
from utils.decorators import roles_required


@admin_bp.route('/product-types', methods=['GET', 'POST'])
@roles_required('admin','operator','courier','warehouse')
def handle_product_types():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"error": "Имя обязательно"}), 400

        new_pt = ProductType(name=name)
        db.session.add(new_pt)
        db.session.commit()
        return jsonify(new_pt.to_dict()), 201

    pts = ProductType.query.all()
    return jsonify([pt.to_dict() for pt in pts]), 200


@admin_bp.route('/product-types/<int:pt_id>', methods=['PUT'])
@roles_required('admin','operator','courier','warehouse')
def update_product_type(pt_id):
    pt = ProductType.query.get_or_404(pt_id)
    data = request.get_json()
    pt.name = data.get('name', pt.name)
    db.session.commit()
    return jsonify(pt.to_dict()), 200


@admin_bp.route('/product-types/<int:pt_id>/block', methods=['PATCH'])
@roles_required('admin','operator','courier','warehouse')
def block_product_type(pt_id):
    pt = ProductType.query.get_or_404(pt_id)
    pt.is_active = False
    db.session.commit()
    return jsonify(pt.to_dict()), 200


@admin_bp.route('/product-types/<int:pt_id>/unblock', methods=['PATCH'])
@roles_required('admin','operator','courier','warehouse')
def unblock_product_type(pt_id):
    pt = ProductType.query.get_or_404(pt_id)
    pt.is_active = True
    db.session.commit()
    return jsonify(pt.to_dict()), 200
