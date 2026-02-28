from flask import jsonify, request
from extensions import db
from models.product import Product
from models.product_type import ProductType
from models.brand import Brand
from .. import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/products', methods=['GET', 'POST'])
@admin_required
def handle_products():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        product_type_id = data.get('product_type_id')
        brand_id = data.get('brand_id')
        if not name or not product_type_id or not brand_id:
            return jsonify({"error": "name, product_type_id и brand_id обязательны"}), 400

        # validate foreign keys
        ProductType.query.get_or_404(product_type_id)
        Brand.query.get_or_404(brand_id)

        new_p = Product(
            name=name,
            product_type_id=product_type_id,
            brand_id=brand_id,
            volume=data.get('volume'),
            quantity_per_block=data.get('quantity_per_block')
        )
        db.session.add(new_p)
        db.session.commit()
        return jsonify(new_p.to_dict()), 201

    prods = Product.query.all()
    return jsonify([p.to_dict() for p in prods]), 200


@admin_bp.route('/products/<int:p_id>', methods=['PUT'])
@admin_required
def update_product(p_id):
    p = Product.query.get_or_404(p_id)
    data = request.get_json()
    if 'product_type_id' in data:
        ProductType.query.get_or_404(data.get('product_type_id'))
        p.product_type_id = data.get('product_type_id')
    if 'brand_id' in data:
        Brand.query.get_or_404(data.get('brand_id'))
        p.brand_id = data.get('brand_id')

    p.name = data.get('name', p.name)
    p.volume = data.get('volume', p.volume)
    p.quantity_per_block = data.get('quantity_per_block', p.quantity_per_block)
    db.session.commit()
    return jsonify(p.to_dict()), 200


@admin_bp.route('/products/<int:p_id>/block', methods=['PATCH'])
@admin_required
def block_product(p_id):
    p = Product.query.get_or_404(p_id)
    p.is_active = False
    db.session.commit()
    return jsonify(p.to_dict()), 200


@admin_bp.route('/products/<int:p_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_product(p_id):
    p = Product.query.get_or_404(p_id)
    p.is_active = True
    db.session.commit()
    return jsonify(p.to_dict()), 200
