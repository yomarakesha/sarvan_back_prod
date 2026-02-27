from extensions import db

class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, default="Главный склад")
    
    # HAYYAT
    hayyat_full = db.Column(db.Integer, default=0, nullable=False)
    hayyat_empty = db.Column(db.Integer, default=0, nullable=False)
    hayyat_defective = db.Column(db.Integer, default=0, nullable=False)
    
    # SARWAN
    sarwan_full = db.Column(db.Integer, default=0, nullable=False)
    sarwan_empty = db.Column(db.Integer, default=0, nullable=False)
    sarwan_defective = db.Column(db.Integer, default=0, nullable=False)
    
    # ARCHALYK
    archalyk_full = db.Column(db.Integer, default=0, nullable=False)
    archalyk_empty = db.Column(db.Integer, default=0, nullable=False)
    archalyk_defective = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "inventory": {
                "hayyat": {
                    "full": self.hayyat_full,
                    "empty": self.hayyat_empty,
                    "defective": self.hayyat_defective
                },
                "sarwan": {
                    "full": self.sarwan_full,
                    "empty": self.sarwan_empty,
                    "defective": self.sarwan_defective
                },
                "archalyk": {
                    "full": self.archalyk_full,
                    "empty": self.archalyk_empty,
                    "defective": self.archalyk_defective
                }
            }
        }

class WarehouseSupply(db.Model):
    __tablename__ = 'warehouse_supplies'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bottle_type = db.Column(db.String(50), nullable=False) # 'HAYYAT', 'SARWAN', 'ARCHALYK'
    quantity = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    warehouse = db.relationship('Warehouse', backref=db.backref('supplies', lazy=True))
    user = db.relationship('User', backref=db.backref('supplies', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "warehouse_id": self.warehouse_id,
            "user_id": self.user_id,
            "user_full_name": self.user.full_name if self.user else None,
            "bottle_type": self.bottle_type,
            "quantity": self.quantity,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
