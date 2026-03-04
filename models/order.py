from datetime import datetime
from extensions import db

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Основные данные
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    client_address_id = db.Column(db.Integer, db.ForeignKey('client_addresses.id'), nullable=False)
    client_phone_id = db.Column(db.Integer, db.ForeignKey('client_phones.id'), nullable=False)
    courier_id = db.Column(db.Integer, db.ForeignKey('courier_profiles.user_id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Пользователь, оформивший заказ
    
    # Заметка к заказу
    note = db.Column(db.Text, nullable=True)
    
    # Дата и время доставки
    delivery_date = db.Column(db.Date, nullable=False)  # Дата доставки (сегодня или завтра)
    delivery_time_type = db.Column(db.String(50), nullable=False)  # Тип времени: 'urgent', 'during_day', 'specific_time'
    delivery_time = db.Column(db.Time, nullable=True)  # Конкретное время, если выбран 'specific_time'
    
    # Оплата
    payment_type = db.Column(db.String(50), nullable=False)  # Тип оплаты: 'cash', 'card', 'cash_and_card', 'credit', 'free'
    
    # Статус
    status = db.Column(db.String(50), default='pending', nullable=False)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    client = db.relationship('Client', backref='orders')
    client_address = db.relationship('ClientAddress')
    client_phone = db.relationship('ClientPhone')
    courier = db.relationship('CourierProfile', backref='orders')
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_address_id': self.client_address_id,
            'user_id': self.user_id,
            'client_phone_id': self.client_phone_id,
            'courier_id': self.courier_id,
            'note': self.note,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'delivery_time_type': self.delivery_time_type,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'payment_type': self.payment_type,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)  # Количество товара/услуги
    
    # Цены, сохраняемые при создании заказа
    price = db.Column(db.Numeric(10, 2), nullable=True)  # Цена за единицу в момент создания заказа
    total_price = db.Column(db.Numeric(10, 2), nullable=True)  # Итоговая цена (price * quantity)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи
    service = db.relationship('Service')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'service_id': self.service_id,
            'quantity': float(self.quantity),
            'price': float(self.price) if self.price else None,
            'total_price': float(self.total_price) if self.total_price else None,
            'created_at': self.created_at.isoformat(),
            'service': {
                'id': self.service.id,
                'name': self.service.name,
            } if self.service else None,
        }
