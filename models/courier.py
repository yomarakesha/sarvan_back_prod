from extensions import db

courier_districts = db.Table('courier_districts',
    db.Column('courier_id', db.Integer, db.ForeignKey('courier_profiles.user_id'), primary_key=True),
    db.Column('district_id', db.Integer, db.ForeignKey('districts.id'), primary_key=True)
)

class CourierProfile(db.Model):
    __tablename__ = 'courier_profiles'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    transport_id = db.Column(db.Integer, db.ForeignKey('transports.id'), nullable=True)
    device_info = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('courier_profile', uselist=False))
    transport = db.relationship('Transport')

    districts = db.relationship('District', secondary=courier_districts, lazy='subquery',
        backref=db.backref('couriers', lazy=True))

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "transport_number": self.transport.number if self.transport else None,
            "device_info": self.device_info,
            "districts": [d.id for d in self.districts]
        }