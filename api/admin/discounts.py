import datetime
from flask import jsonify, request
from . import admin_bp
from decorators import roles_required
from db import Db


def serialize_discount(d):
    """Приведение типов для JSON"""
    if d.get('value'): d['value'] = float(d['value'])
    if d.get('start_date'): d['start_date'] = d['start_date'].isoformat()
    if d.get('end_date'): d['end_date'] = d['end_date'].isoformat()
    
    if d.get('start_time'): d['start_time'] = d['start_time'].strftime('%H:%M')
    if d.get('end_time'): d['end_time'] = d['end_time'].strftime('%H:%M')
    
    for key in ['service_ids', 'city_ids']:
        val = d.get(key)
        d[key] = [int(x) for x in val.split(',')] if val else []
        
    return d


@admin_bp.route('/discounts', methods=['GET'])
def get_discounts():
    conn = Db.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    d.*,
                    GROUP_CONCAT(DISTINCT ds.service_id) as service_ids,
                    GROUP_CONCAT(DISTINCT dc.city_id) as city_ids
                FROM discounts d
                LEFT JOIN discount_services ds ON d.id = ds.discount_id
                LEFT JOIN discount_cities dc ON d.id = dc.discount_id
                GROUP BY d.id
                ORDER BY d.id DESC
            """
            cursor.execute(sql)
            discounts = cursor.fetchall()

            result = [serialize_discount(d) for d in discounts]

        return jsonify(result), 200
    finally:
        conn.close()


@admin_bp.route('/discounts', methods=['POST'])
@roles_required('admin')
def create_discount():
    data = request.json
    conn = Db.get_connection()
    try:
        with conn.cursor() as cursor:
            
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None
            start_time = datetime.strptime(data['start_time'], '%H:%M').time() if data.get('start_time') else None
            end_time = datetime.strptime(data['end_time'], '%H:%M').time() if data.get('end_time') else None

            sql = """
                INSERT INTO discounts 
                (name, discount_type, value, limit_count, nth_order, start_date, end_date, start_time, end_time, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                data['name'], data['discount_type'], data.get('value'),
                data.get('limit_count'), data.get('nth_order'),
                start_date, end_date, start_time, end_time, data.get('is_active', True)
            )
            cursor.execute(sql, params)
            discount_id = cursor.lastrowid

            if 'service_ids' in data and isinstance(data['service_ids'], list):
                for s_id in data['service_ids']:
                    cursor.execute("INSERT INTO discount_services (discount_id, service_id) VALUES (%s, %s)", (discount_id, s_id))

            if 'city_ids' in data and isinstance(data['city_ids'], list):
                for c_id in data['city_ids']:
                    cursor.execute("INSERT INTO discount_cities (discount_id, city_id) VALUES (%s, %s)", (discount_id, c_id))

            conn.commit()
            return jsonify({"message": "Скидка создана", "id": discount_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@admin_bp.route('/discounts/<int:id>', methods=['PUT'])
@roles_required('admin')
def update_discount(id):
    data = request.json
    conn = Db.get_connection()
    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT id FROM discounts WHERE id = %s", (id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Скидка не найдена'}), 404

            fields = []
            params = []
            
            mapping = {
                'name': 'name', 'discount_type': 'discount_type', 'value': 'value',
                'limit_count': 'limit_count', 'nth_order': 'nth_order', 'is_active': 'is_active'
            }
            
            for key, col in mapping.items():
                if key in data:
                    fields.append(f"{col} = %s")
                    params.append(data[key])
            
            if 'start_date' in data:
                fields.append("start_date = %s")
                params.append(datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None)
            if 'end_date' in data:
                fields.append("end_date = %s")
                params.append(datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None)
            if 'start_time' in data:
                fields.append("start_time = %s")
                params.append(datetime.strptime(data['start_time'], '%H:%M').time() if data['start_time'] else None)
            if 'end_time' in data:
                fields.append("end_time = %s")
                params.append(datetime.strptime(data['end_time'], '%H:%M').time() if data['end_time'] else None)

            if fields:
                sql = f"UPDATE discounts SET {', '.join(fields)} WHERE id = %s"
                params.append(id)
                cursor.execute(sql, tuple(params))

            if 'service_ids' in data and isinstance(data['service_ids'], list):
                cursor.execute("DELETE FROM discount_services WHERE discount_id = %s", (id,))
                for s_id in data['service_ids']:
                    cursor.execute("INSERT INTO discount_services (discount_id, service_id) VALUES (%s, %s)", (id, s_id))

            if 'city_ids' in data and isinstance(data['city_ids'], list):
                cursor.execute("DELETE FROM discount_cities WHERE discount_id = %s", (id,))
                for c_id in data['city_ids']:
                    cursor.execute("INSERT INTO discount_cities (discount_id, city_id) VALUES (%s, %s)", (id, c_id))

            conn.commit()
            return jsonify({"message": "Скидка обновлена"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()



@admin_bp.route('/discounts/<int:id>', methods=['DELETE'])
@roles_required('admin')
def delete_discount(id):
    conn = Db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE discounts SET is_active = 0 WHERE id = %s", (id,))
            if cursor.rowcount == 0:
                return jsonify({'error': 'Скидка не найдена'}), 404
            conn.commit()
        return jsonify({'message': 'Скидка деактивирована'}), 200
    finally:
        conn.close()

