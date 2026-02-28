from datetime import datetime
from extensions import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)  # 'incoming','move','writeoff'
    from_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    to_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_state_id = db.Column(db.Integer, db.ForeignKey('product_states.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    note = db.Column(db.Text, nullable=True)

    from_location = db.relationship('Location', foreign_keys=[from_location_id])
    to_location = db.relationship('Location', foreign_keys=[to_location_id])
    product = db.relationship('Product')
    product_state = db.relationship('ProductState')
    user = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'operation_type': self.operation_type,
            'from_location_id': self.from_location_id,
            'to_location_id': self.to_location_id,
            'product_id': self.product_id,
            'product_state_id': self.product_state_id,
            'quantity': self.quantity,
            'user_id': self.user_id,
            'note': self.note
        }
