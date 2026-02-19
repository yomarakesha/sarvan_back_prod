from extensions import db

class Transport(db.Model):
    __tablename__ = 'transports'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False) # Гос. номер
    capacity = db.Column(db.Integer, nullable=False)              # Вместимость
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "number": self.number,
            "capacity": self.capacity,
            "is_active": self.is_active
        }
