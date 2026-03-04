from flask import request, jsonify
from decimal import Decimal
from extensions import db
from models.credit import ClientCredit, CreditPayment
from models.client import Client
from models.order import Order
from .. import admin_bp
from utils.decorators import roles_required


@admin_bp.route('/clients/<int:client_id>/credit', methods=['GET'])
@roles_required('admin', 'operator', 'warehouse')
def get_client_credit(client_id):
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    client_credit = ClientCredit.query.filter_by(client_id=client_id).first()
    
    if not client_credit:
        return jsonify({'error': 'Client credit information not found'}), 404
    
    return jsonify(client_credit.to_dict()), 200


@admin_bp.route('/clients/<int:client_id>/credit', methods=['POST'])
@roles_required('admin')
def set_client_credit_limit(client_id):
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    data = request.get_json()
    
    if 'credit_limit' not in data:
        return jsonify({'error': 'credit_limit is required'}), 400
    
    try:
        credit_limit = Decimal(str(data['credit_limit']))
        
        if credit_limit < 0:
            return jsonify({'error': 'credit_limit cannot be negative'}), 400
        
        client_credit = ClientCredit.query.filter_by(client_id=client_id).first()
        
        if not client_credit:
            client_credit = ClientCredit(client_id=client_id)
            db.session.add(client_credit)
        
        client_credit.credit_limit = credit_limit
        db.session.commit()
        
        return jsonify(client_credit.to_dict()), 200
    
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid credit_limit: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/clients/<int:client_id>/credit/payments', methods=['GET'])
@roles_required('admin', 'operator', 'warehouse')
def get_client_credit_payments(client_id):
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    client_credit = ClientCredit.query.filter_by(client_id=client_id).first()
    if not client_credit:
        return jsonify({'error': 'Client credit information not found'}), 404
    
    paginated = CreditPayment.query.filter_by(client_credit_id=client_credit.id)\
        .order_by(CreditPayment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    payments_data = [payment.to_dict() for payment in paginated.items]
    
    return jsonify({
        'client_id': client_id,
        'payments': payments_data,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }), 200


@admin_bp.route('/credit-payments', methods=['POST'])
@roles_required('admin', 'operator')
def create_credit_payment():
    
    data = request.get_json()
    
    required_fields = ['client_credit_id', 'amount', 'payment_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        client_credit = ClientCredit.query.get(data['client_credit_id'])
        if not client_credit:
            return jsonify({'error': 'Client credit not found'}), 404
        
        amount = Decimal(str(data['amount']))
        payment_type = data['payment_type']  # 'payment', 'write_off'
        
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        if payment_type not in ['payment', 'write_off']:
            return jsonify({'error': "payment_type must be 'payment' or 'write_off'"}), 400
        
        if client_credit.used_credit >= amount:
            client_credit.used_credit = Decimal(str(client_credit.used_credit)) - amount
        else:
            return jsonify({'error': 'Payment amount exceeds used credit'}), 400
        
        credit_payment = CreditPayment(
            client_credit_id=data['client_credit_id'],
            payment_type=payment_type,
            amount=amount,
            description=data.get('description'),
        )
        
        db.session.add(credit_payment)
        db.session.commit()
        
        return jsonify({
            'payment': credit_payment.to_dict(),
            'client_credit': client_credit.to_dict(),
        }), 201
    
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
