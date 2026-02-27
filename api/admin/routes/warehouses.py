from flask import Blueprint, request, jsonify, session
from extensions import db
from models.warehouse import Warehouse, WarehouseSupply
from .. import admin_bp
from utils.decorators import admin_required
from datetime import datetime


@admin_bp.route('/warehouses/<int:warehouse_id>/supplies', methods=['POST'])
@admin_required
def add_warehouse_supply(warehouse_id):

    warehouse = Warehouse.query.get_or_404(warehouse_id)
    data = request.get_json() or {}
    
    quantity = data.get('quantity')
    bottle_type = data.get('bottle_type', 'SARWAN').upper()
    note = data.get('note', '')
    
    if not quantity or int(quantity) <= 0:
        return jsonify({"error": "Укажите корректное количество тар"}), 400
        
    if bottle_type not in ['HAYYAT', 'SARWAN', 'ARCHALYK']:
        return jsonify({"error": "Неверный тип тары. Допустимые значения: HAYYAT, SARWAN, ARCHALYK"}), 400
        
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Не удалось определить текущего пользователя"}), 401
    
    if bottle_type == 'HAYYAT':
        warehouse.hayyat_full += int(quantity)
    elif bottle_type == 'SARWAN':
        warehouse.sarwan_full += int(quantity)
    elif bottle_type == 'ARCHALYK':
        warehouse.archalyk_full += int(quantity)
        
    supply = WarehouseSupply(
        warehouse_id=warehouse.id,
        user_id=user_id,
        bottle_type=bottle_type,
        quantity=int(quantity),
        note=note
    )
    
    db.session.add(supply)
    db.session.commit()
    
    return jsonify({
        "message": "Поставка успешно записана",
        "supply": supply.to_dict(),
        "warehouse": warehouse.to_dict()
    }), 201

@admin_bp.route('/warehouses/<int:warehouse_id>/supplies', methods=['GET'])
@admin_required
def get_warehouse_supplies(warehouse_id):

    warehouse = Warehouse.query.get_or_404(warehouse_id)
    query = WarehouseSupply.query.filter_by(warehouse_id=warehouse.id)
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(WarehouseSupply.created_at >= start_dt)
        except ValueError:
            return jsonify({"error": "Неверный формат start_date (ожидается YYYY-MM-DD)"}), 400
            
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(WarehouseSupply.created_at <= end_dt)
        except ValueError:
            return jsonify({"error": "Неверный формат end_date (ожидается YYYY-MM-DD)"}), 400
            
    
    query = query.order_by(WarehouseSupply.created_at.desc())
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        return jsonify({"error": "Неверный формат page или per_page (ожидается число)"}), 400
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    supplies = pagination.items
    
    return jsonify({
        "items": [s.to_dict() for s in supplies],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@admin_bp.route('/warehouses', methods=['GET'])
@admin_required
def get_warehouses():
    warehouses = Warehouse.query.all()
    return jsonify([w.to_dict() for w in warehouses]), 200

@admin_bp.route('/warehouses/<int:warehouse_id>', methods=['GET'])
@admin_required
def get_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    return jsonify(warehouse.to_dict()), 200
