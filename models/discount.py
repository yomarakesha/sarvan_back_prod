from extensions import db
from datetime import datetime

# Таблица связи многие-ко-многим: Скидки <-> Услуги
discount_services = db.Table('discount_services',
    db.Column('discount_id', db.Integer, db.ForeignKey('discounts.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('services.id'), primary_key=True)
)

# Таблица связи многие-ко-многим: Скидки <-> Города
discount_cities = db.Table('discount_cities',
    db.Column('discount_id', db.Integer, db.ForeignKey('discounts.id'), primary_key=True),
    db.Column('city_id', db.Integer, db.ForeignKey('cities.id'), primary_key=True)
)


class Discount(db.Model):
    __tablename__ = 'discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    
    # Тип скидки: 'fixed_amount', 'percentage', 'free_nth_order', 'fixed_price'
    discount_type = db.Column(db.String(50), nullable=False)
    
    # Значение скидки (сумма в манатах или проценты), может быть Null для free_nth_order
    value = db.Column(db.Numeric(10, 2), nullable=True) 
    
    # Лимит использований акции вообще (например, первые 20 заказов)
    limit_count = db.Column(db.Integer, nullable=True)
    # Текущее количество использований
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Для настройки "каждый N-й заказ бесплатно" (например, 5)
    nth_order = db.Column(db.Integer, nullable=True)
    
    # Настройки времени действия
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи M:M
    services = db.relationship('Service', secondary=discount_services, lazy='subquery',
        backref=db.backref('discounts', lazy=True))
    cities = db.relationship('City', secondary=discount_cities, lazy='subquery',
        backref=db.backref('discounts', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'discount_type': self.discount_type,
            'value': float(self.value) if self.value is not None else None,
            'limit_count': self.limit_count,
            'usage_count': self.usage_count,
            'nth_order': self.nth_order,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'services': [{'id': s.id, 'name': s.name} for s in self.services],
            'cities': [{'id': c.id, 'name': c.name} for c in self.cities]
        }
