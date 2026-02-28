from extensions import db

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_types.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    volume = db.Column(db.String(100), nullable=True)
    quantity_per_block = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    product_type = db.relationship('ProductType')
    brand = db.relationship('Brand')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "product_type_id": self.product_type_id,
            "brand_id": self.brand_id,
            "volume": self.volume,
            "quantity_per_block": self.quantity_per_block,
            "is_active": self.is_active
        }
