from flask import request, jsonify
from extensions import db
from models.user import User
from models.district import District
from models.courier import CourierProfile
from models.transport import Transport
from .. import admin_bp
from utils.decorators import admin_required

def get_or_create_courier_profile(user_id):
    profile = CourierProfile.query.get(user_id)
    if not profile:
        profile = CourierProfile(user_id=user_id)
        db.session.add(profile)
    return profile

@admin_bp.route('/users/<int:user_id>/equipment', methods=['PUT'])
@admin_required
def update_courier_equipment(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'courier':
        return jsonify({"error": "Этот пользователь не является курьером"}), 400

    profile = get_or_create_courier_profile(user_id)
    data = request.get_json()

    if 'transport_number' in data:
        transport_number = data['transport_number']
        if transport_number: 
            transport = Transport.query.filter_by(number=transport_number).first()
            if not transport:
                return jsonify({"error": f"Авто с номером {transport_number} не найдено"}), 404
            profile.transport_id = transport.id
        else:
            profile.transport_id = None

    if 'device_info' in data:
        profile.device_info = data['device_info']

    db.session.commit()
    return jsonify({"message": "Оборудование обновлено", "profile": profile.to_dict()}), 200


@admin_bp.route('/couriers/full-list', methods=['GET'])
@admin_required
def get_all_couriers_data():
    #Filter-only couriers
    query = User.query.filter(User.role == 'courier')

    #Filter-is active
    #URL: ?active=true или ?active=false
    active_param = request.args.get('active')
    if active_param is not None:
        is_active = active_param.lower() == 'true'
        query = query.filter(User.is_active == is_active)

    #Filter-by city or district
    #URL: ?city_id=1 или ?district_id=5
    city_id = request.args.get('city_id', type=int)
    district_id = request.args.get('district_id', type=int)

    if city_id or district_id:
        query = query.join(CourierProfile).join(CourierProfile.districts)
        
        if district_id:
            query = query.filter(District.id == district_id)
        elif city_id:
            query = query.filter(District.city_id == city_id)

    couriers = query.distinct().all()
    
    result = []
    for courier in couriers:
        profile = courier.courier_profile
        
        cities_names = set()
        districts_data = []
        if profile:
            for d in profile.districts:
                districts_data.append({"id": d.id, "name": d.name})
                if d.city:
                    cities_names.add(d.city.name)

        result.append({
            "id": courier.id,
            "username": courier.username,
            "full_name": courier.full_name or "Не указано",
            "phone": courier.phone or "Нет номера",
            "is_active": courier.is_active,
            "cities": list(cities_names),
            "districts": districts_data,
            "transport_number": profile.transport.number if profile and profile.transport else "Не привязано",
            "device_info": profile.device_info if profile else "Не указано"
        })

    return jsonify(result), 200

@admin_bp.route('/users/<int:user_id>/districts/attach', methods=['POST'])
@admin_required
def attach_districts(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'courier':
        return jsonify({"error": "Пользователь не является курьером"}), 400
        
    profile = get_or_create_courier_profile(user_id)
    data = request.get_json()
    
    city_id = data.get('city_id')
    district_ids = data.get('district_ids') # Array [1, 2, 3] or "all"

    if district_ids == "all" or data.get('all_districts') is True:
        if not city_id:
            return jsonify({"error": "city_id обязателен для выбора всех районов"}), 400
        districts = District.query.filter_by(city_id=city_id).all()
    
    elif isinstance(district_ids, list):
        districts = District.query.filter(District.id.in_(district_ids)).all()
    
    else:
        return jsonify({"error": "Неверный формат данных"}), 400

    for d in districts:
        if d not in profile.districts:
            profile.districts.append(d)

    db.session.commit()
    return jsonify({
        "message": "Районы успешно добавлены",
        "current_districts": [d.id for d in profile.districts]
    }), 200

@admin_bp.route('/users/<int:user_id>/districts/<int:district_id>', methods=['DELETE'])
@admin_required
def detach_single_district(user_id, district_id):
    profile = CourierProfile.query.get_or_404(user_id)
    district = District.query.get_or_404(district_id)

    if district in profile.districts:
        profile.districts.remove(district)
        db.session.commit()
        return jsonify({"message": f"Район {district.name} откреплен"}), 200
    
    return jsonify({"error": "Район не был закреплен за этим курьером"}), 404