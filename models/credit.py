from datetime import datetime
from decimal import Decimal
from extensions import db

class ClientCredit(db.Model):
    """Информация о кредитном лимите клиента"""
    __tablename__ = 'client_credits'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, unique=True)
    
    # Кредитный лимит (максимально можно взять в кредит)
    credit_limit = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Использованная сумма кредита
    used_credit = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Доступный кредит = credit_limit - used_credit
    # Это считается как свойство
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    client = db.relationship('Client', backref='credit')
    payments = db.relationship('CreditPayment', backref='client_credit', cascade='all, delete-orphan')
    
    @property
    def available_credit(self):
        """Доступный кредит для использования"""
        return Decimal(str(self.credit_limit)) - Decimal(str(self.used_credit))
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'credit_limit': float(self.credit_limit),
            'used_credit': float(self.used_credit),
            'available_credit': float(self.available_credit),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class CreditPayment(db.Model):
    """История платежей по кредиту"""
    __tablename__ = 'credit_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    client_credit_id = db.Column(db.Integer, db.ForeignKey('client_credits.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Типы платежей: 'charge' (начисление кредита из заказа), 'payment' (оплата кредита), 'write_off' (списание)
    payment_type = db.Column(db.String(50), nullable=False)  # 'charge', 'payment', 'write_off'
    
    # Сумма операции
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Описание платежа
    description = db.Column(db.Text, nullable=True)
    
    # Временная метка
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи
    order = db.relationship('Order')
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_credit_id': self.client_credit_id,
            'order_id': self.order_id,
            'payment_type': self.payment_type,
            'amount': float(self.amount),
            'description': self.description,
            'created_at': self.created_at.isoformat(),
        }
