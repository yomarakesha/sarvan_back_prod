from datetime import datetime
from extensions import db

class ClientBlockReason(db.Model):
    __tablename__ = 'client_block_reasons'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClientPhone(db.Model):
    __tablename__ = 'client_phones'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

class ClientAddress(db.Model):
    __tablename__ = 'client_addresses'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
    address_line = db.Column(db.Text, nullable=False)

    city = db.relationship('City')
    district = db.relationship('District')

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    price_type_id = db.Column(db.Integer, db.ForeignKey('price_types.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    price_type = db.relationship('PriceType')
    phones = db.relationship('ClientPhone', backref='client', cascade="all, delete-orphan")
    addresses = db.relationship('ClientAddress', backref='client', cascade="all, delete-orphan")
    block_reasons = db.relationship('ClientBlockReason', backref='client', cascade="all, delete-orphan")
