from extensions import db

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'warehouse', 'courier', 'counterparty','client'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    counterparty_id = db.Column(db.Integer, db.ForeignKey('counterparties.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)

    user = db.relationship('User')
    warehouse = db.relationship('Warehouse')
    counterparty = db.relationship('Counterparty')
    client = db.relationship('Client')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'user_id': self.user_id,
            'warehouse_id': self.warehouse_id,
            'counterparty_id': self.counterparty_id,
            'client_id': self.client_id
        }
