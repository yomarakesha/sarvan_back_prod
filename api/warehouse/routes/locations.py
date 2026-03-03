from flask import jsonify
from models.location import Location
from .. import warehouse_bp
from utils.decorators import roles_required

@warehouse_bp.route('/locations/counterparties', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_counterparty_locations():

    locs = Location.query.filter_by(type='counterparty').all()
    result = [{'id': l.id, 'name': l.name} for l in locs]
    return jsonify(result), 200

@warehouse_bp.route('/locations/warehouses', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_warehouse_locations():
    
    locs = Location.query.filter_by(type='warehouse').all()
    result = [{'id': l.id, 'name': l.name} for l in locs]
    return jsonify(result), 200

@warehouse_bp.route('/locations/couriers', methods=['GET'])
@roles_required('admin','operator','courier','warehouse')
def get_courier_locations():
    
    locs = Location.query.filter_by(type='courier').all()
    result = [{'id': l.id, 'name': l.name} for l in locs]
    return jsonify(result), 200
