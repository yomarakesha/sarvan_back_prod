from extensions import db

class Stock(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_state_id = db.Column(db.Integer, db.ForeignKey('product_states.id'), nullable=False)
    quantity = db.Column(db.Float, default=0.0, nullable=False)

    location = db.relationship('Location')
    product = db.relationship('Product')
    product_state = db.relationship('ProductState')

    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'product_id': self.product_id,
            'product_state_id': self.product_state_id,
            'quantity': self.quantity
        }
