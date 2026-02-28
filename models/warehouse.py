from datetime import datetime
from extensions import db

class WarehouseAddress(db.Model):
    __tablename__ = 'warehouse_addresses'
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    address_line = db.Column(db.Text, nullable=False)

class WarehousePhone(db.Model):
    __tablename__ = 'warehouse_phones'
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    phone = db.Column(db.String(30), nullable=False)

class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    addresses = db.relationship('WarehouseAddress', backref='warehouse', cascade='all, delete-orphan')
    phones = db.relationship('WarehousePhone', backref='warehouse', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "addresses": [a.address_line for a in self.addresses],
            "phones": [p.phone for p in self.phones]
        }
