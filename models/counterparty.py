from extensions import db

class CounterpartyAddress(db.Model):
    __tablename__ = 'counterparty_addresses'
    id = db.Column(db.Integer, primary_key=True)
    counterparty_id = db.Column(db.Integer, db.ForeignKey('counterparties.id'), nullable=False)
    address_line = db.Column(db.Text, nullable=False)

class CounterpartyPhone(db.Model):
    __tablename__ = 'counterparty_phones'
    id = db.Column(db.Integer, primary_key=True)
    counterparty_id = db.Column(db.Integer, db.ForeignKey('counterparties.id'), nullable=False)
    phone = db.Column(db.String(30), nullable=False)

class Counterparty(db.Model):
    __tablename__ = 'counterparties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    addresses = db.relationship('CounterpartyAddress', backref='counterparty', cascade='all, delete-orphan')
    phones = db.relationship('CounterpartyPhone', backref='counterparty', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
            'addresses': [a.address_line for a in self.addresses],
            'phones': [p.phone for p in self.phones]
        }
