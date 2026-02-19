from extensions import db

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    districts = db.relationship('District', backref='city', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "is_active": self.is_active}
