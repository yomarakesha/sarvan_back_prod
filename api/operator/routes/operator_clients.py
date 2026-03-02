from flask import jsonify, request
from extensions import db
from models.client import Client, ClientPhone
from .. import operator_bp
from utils.decorators import roles_required


@operator_bp.route('/clients/search', methods=['GET'])
@roles_required('operator')
def search_clients_by_phone():
    phone_query = request.args.get('phone', type=str)
    
    if not phone_query:
        return jsonify({'error': 'Phone parameter is required'}), 400
    
    clients = db.session.query(
        Client.id,
        Client.full_name,
        ClientPhone.phone
    ).join(
        ClientPhone, Client.id == ClientPhone.client_id
    ).filter(
        ClientPhone.phone.ilike(f'%{phone_query}%')
    ).all()
    
    result = [
        {
            'id': client.id,
            'full_name': client.full_name,
            'phone': client.phone
        }
        for client in clients
    ]
    
    return jsonify(result), 200
