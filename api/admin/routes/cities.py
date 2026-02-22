from flask import jsonify, request
from extensions import db
from models.city import City
from .. import admin_bp
from utils.decorators import admin_required
from sqlalchemy import func
from models.district import District
from models.city import City
from models.courier import courier_districts


@admin_bp.route('/cities', methods=['GET'])
@admin_required
def get_cities():
    cities = City.query.all()
    return jsonify([c.to_dict() for c in cities]), 200


@admin_bp.route('/cities', methods=['POST'])
@admin_required
def add_city():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({"error": "Укажите название"}), 400
    new_city = City(name=data.get('name'))
    db.session.add(new_city)
    db.session.commit()
    return jsonify(new_city.to_dict()), 201


@admin_bp.route('/cities/<int:city_id>/block', methods=['PATCH'])
@admin_required
def block_city(city_id):
    city = City.query.get_or_404(city_id)
    city.is_active = False
    db.session.commit()
    return jsonify({"message": "Город заблокирован", "city": city.to_dict()}), 200

@admin_bp.route('/cities/<int:city_id>/unblock', methods=['PATCH'])
@admin_required
def unblock_city(city_id):
    city = City.query.get_or_404(city_id)
    city.is_active = True
    db.session.commit()
    return jsonify({
        "message": f"Город '{city.name}' успешно разблокирован",
        "city": city.to_dict()
    }), 200

@admin_bp.route('/cities/<int:city_id>', methods=['PUT'])
@admin_required
def update_city(city_id):
    city = City.query.get_or_404(city_id)
    data = request.get_json()

    new_name = data.get('name')
    if not new_name:
        return jsonify({"error": "Название не может быть пустым"}), 400

    duplicate = City.query.filter(City.name == new_name, City.id != city_id).first()
    if duplicate:
        return jsonify({"error": "Город с таким названием уже существует"}), 400

    city.name = new_name
    db.session.commit()
    return jsonify({"message": "Город обновлен", "city": city.to_dict()}), 200

@admin_bp.route('/cities/full-list', methods=['GET'])
@admin_required
def get_cities_full_list():
    cities = City.query.all()
    result = []

    for city in cities:
        districts_count = District.query.filter_by(city_id=city.id).count()
        couriers_count = db.session.query(func.count(func.distinct(courier_districts.c.courier_id)))\
            .join(District, District.id == courier_districts.c.district_id)\
            .filter(District.city_id == city.id)\
            .scalar()

        result.append({
            "id": city.id,
            "name": city.name,
            "is_active": city.is_active,
            "districts_count": districts_count,
            "couriers_count": couriers_count or 0
        })

    return jsonify(result), 200