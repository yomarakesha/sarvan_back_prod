from extensions import db

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    rules = db.relationship('ServiceRule', backref='service', lazy='select', cascade='all, delete-orphan')
    prices = db.relationship('ServicePrice', backref='service', lazy='select', cascade='all, delete-orphan')

class ServiceRule(db.Model):
    __tablename__ = 'service_rules'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # Значения из ServiceTypes
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    product = db.relationship('Product')

class ServicePrice(db.Model):
    __tablename__ = 'service_prices'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    price_type_id = db.Column(db.Integer, db.ForeignKey('price_types.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    city = db.relationship('City')
    price_type = db.relationship('PriceType')