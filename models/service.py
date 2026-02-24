from extensions import db

class ServiceLogisticInfo(db.Model):
    __tablename__ = 'service_logistic_info'
    id = db.Column(db.Integer, primary_key=True)
    bottle_out = db.Column(db.String(50), nullable=True)
    bottle_in = db.Column(db.String(50), nullable=True)
    water_out = db.Column(db.Boolean, default=False)
    water_in = db.Column(db.Boolean, default=False)

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    logistic_info_id = db.Column(db.Integer, db.ForeignKey('service_logistic_info.id'), nullable=True)
    logistic_info = db.relationship('ServiceLogisticInfo')
    prices = db.relationship('ServicePrice', backref='service', lazy='select')

class ServicePrice(db.Model):
    __tablename__ = 'service_prices'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    price_type_id = db.Column(db.Integer, db.ForeignKey('price_types.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    city = db.relationship('City')
    price_type = db.relationship('PriceType')