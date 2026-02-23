from flask import jsonify, request
from extensions import db
from sqlalchemy import func
from models import City
from models import District
from models import User
from models import Client
from models import courier_districts, CourierProfile
from models import Client, ClientAddress
from .. import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/districts', methods=['GET'])
@admin_required
def get_districts():
    city_id = request.args.get('city_id')
    query = District.query
    if city_id:
        query = query.filter_by(city_id=city_id)
    districts = query.all()
    return jsonify([d.to_dict() for d in districts]), 200


@admin_bp.route('/districts', methods=['POST'])
@admin_required
def add_district():
    data = request.get_json()
    name = data.get('name')
    city_id = data.get('city_id')
    if not name or not city_id:
        return jsonify({"error": "Нужны name и city_id"}), 400

    new_district = District(name=name, city_id=city_id)
    db.session.add(new_district)
    db.session.commit()
    return jsonify(new_district.to_dict()), 201


@admin_bp.route('/districts/<int:d_id>/block', methods=['PATCH'])
@admin_required
def block_district(d_id):
    district = District.query.get_or_404(d_id)
    district.is_active = False
    db.session.commit()
    return jsonify({"message": "Район заблокирован", "district": district.to_dict()}), 200


@admin_bp.route('/districts/<int:d_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_district(d_id):
    district = District.query.get_or_404(d_id)
    district.is_active = True
    db.session.commit()
    return jsonify({"message": "Район разблокирован", "district": district.to_dict()}), 200


@admin_bp.route('/districts/<int:d_id>', methods=['PUT'])
@admin_required
def update_district(d_id):
    district = District.query.get_or_404(d_id)
    data = request.get_json()

    new_name = data.get('name')
    new_city_id = data.get('city_id')

    if new_name:
        district.name = new_name

    if new_city_id:
        if not City.query.get(new_city_id):
            return jsonify({"error": "Указанный город не существует"}), 404
        district.city_id = new_city_id

    db.session.commit()
    return jsonify({"message": "Район обновлен", "district": district.to_dict()}), 200


@admin_bp.route('/districts/stats', methods=['GET'])
@admin_required
def get_districts_stats():
    client_counts = db.session.query(
        ClientAddress.district_id.label('d_id'),
        func.count(func.distinct(ClientAddress.client_id)).label('count')
    ).group_by(ClientAddress.district_id).subquery()

    courier_counts = db.session.query(
        courier_districts.c.district_id.label('d_id'),
        func.count(courier_districts.c.courier_id).label('count')
    ).group_by(courier_districts.c.district_id).subquery()

    results = db.session.query(
        District.id.label('dist_id'),
        District.name.label('dist_name'),
        City.name.label('city_name'),
        func.coalesce(courier_counts.c.count, 0).label('c_count'),
        func.coalesce(client_counts.c.count, 0).label('cl_count')
    ).join(City, District.city_id == City.id)\
     .outerjoin(courier_counts, courier_counts.c.d_id == District.id)\
     .outerjoin(client_counts, client_counts.c.d_id == District.id)\
     .order_by(City.name, District.name).all()

    stats = [
        {
            "id": r.dist_id,
            "district": r.dist_name,
            "city": r.city_name,
            "couriers_count": r.c_count,
            "clients_count": r.cl_count
        } for r in results
    ]

    return jsonify(stats), 200