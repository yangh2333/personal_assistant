"""
成本相关API路由
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json

cost_bp = Blueprint('cost', __name__)

@cost_bp.route('/clusters', methods=['GET'])
def get_clusters():
    """获取集群配置列表"""
    from app.models import ClusterConfig
    clusters = ClusterConfig.query.all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in clusters]
    })

@cost_bp.route('/clusters/<int:id>', methods=['GET'])
def get_cluster(id):
    """获取指定集群配置"""
    from app.models import ClusterConfig
    cluster = ClusterConfig.query.get(id)
    if not cluster:
        return jsonify({'success': False, 'error': '集群配置不存在'}), 404
    return jsonify({
        'success': True,
        'data': cluster.to_dict()
    })

@cost_bp.route('/calculate', methods=['POST'])
def calculate_cost():
    """执行成本计算"""
    from app import db
    from app.models import CostItem, Calculation, ClusterConfig
    from app.services import CostCalculator, ReportGenerator
    
    data = request.get_json()
    
    cluster = None
    
    cluster_scale = data.get('cluster_scale')
    if cluster_scale:
        cluster = ClusterConfig.query.filter_by(cluster_scale=cluster_scale).first()
    
    if cluster:
        config = {
            'gpu_count': cluster.gpu_count,
            'gpu_model': cluster.gpu_model,
            'server_count': cluster.server_count,
            'power_consumption_kw': cluster.power_consumption_kw,
            'electricity_price': cluster.electricity_price,
            'pue_ratio': cluster.pue_ratio,
            'location_type': cluster.location_type
        }
    else:
        config = {
            'gpu_count': data.get('gpu_count', 1024),
            'gpu_model': data.get('gpu_model', 'H200'),
            'server_count': data.get('server_count', 0),
            'power_consumption_kw': data.get('power_consumption_kw', 0),
            'electricity_price': data.get('electricity_price', 0.6),
            'pue_ratio': data.get('pue_ratio', 1.3),
            'location_type': data.get('location_type', 'colocation')
        }
    
    # 获取所有启用的成本项
    cost_items = CostItem.query.filter_by(is_active=True).all()
    cost_items_data = [item.to_dict() for item in cost_items]
    
    # 执行计算
    calculator = CostCalculator(config)
    result = calculator.calculate(cost_items_data)
    result['gpu_count'] = config['gpu_count']
    
    # 保存计算结果
    calculation = Calculation(
        cluster_config_id=cluster.id if cluster_scale else None,
        total_hardware_cost=result['total_hardware_cost'],
        total_software_cost=result['total_software_cost'],
        total_ops_cost=result['total_ops_cost'],
        total_cost=result['total_cost'],
        annual_opex=result['annual_opex'],
        five_year_tco=result['five_year_tco'],
        calculation_details=json.dumps(result, ensure_ascii=False),
        calculated_at=datetime.now()
    )
    db.session.add(calculation)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'calculation_id': calculation.id,
            **result
        }
    })

@cost_bp.route('/costs/summary', methods=['GET'])
def get_cost_summary():
    """获取成本汇总数据"""
    from app.models import Calculation
    from app.services import ReportGenerator
    
    # 获取最新的计算结果
    calculation = Calculation.query.order_by(Calculation.calculated_at.desc()).first()
    
    if not calculation:
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_investment': 0,
                    'annual_cost': 0,
                    'five_year_tco': 0,
                    'cost_per_gpu': 0
                },
                'breakdown': {
                    'hardware': 0,
                    'software': 0,
                    'ops': 0
                }
            }
        })
    
    details = json.loads(calculation.calculation_details) if calculation.calculation_details else {}
    generator = ReportGenerator()
    report = generator.generate_summary_report(details)
    
    return jsonify({
        'success': True,
        'data': report
    })

@cost_bp.route('/costs/breakdown', methods=['GET'])
def get_cost_breakdown():
    """获取成本分项数据"""
    from app.models import Calculation
    from app.services import CostCalculator
    
    calculation = Calculation.query.order_by(Calculation.calculated_at.desc()).first()
    
    if not calculation:
        return jsonify({
            'success': True,
            'data': {
                'hardware_pct': 0,
                'software_pct': 0,
                'ops_pct': 0,
                'breakdown': {}
            }
        })
    
    details = json.loads(calculation.calculation_details) if calculation.calculation_details else {}
    calculator = CostCalculator({})
    breakdown = calculator.get_cost_breakdown(details)
    
    return jsonify({
        'success': True,
        'data': breakdown
    })

@cost_bp.route('/costs/trend', methods=['GET'])
def get_cost_trend():
    """获取成本趋势数据"""
    from app.services import ReportGenerator
    
    scale = request.args.get('scale', '1k')
    generator = ReportGenerator()
    trend = generator.generate_trend_data(scale)
    comparison = generator.generate_comparison_data()
    
    return jsonify({
        'success': True,
        'data': {
            'trend': trend,
            'comparison': comparison
        }
    })

@cost_bp.route('/cost-items', methods=['GET'])
def get_cost_items():
    """获取成本项列表"""
    from app.models import CostItem
    
    category = request.args.get('category')
    query = CostItem.query
    
    if category:
        query = query.filter_by(category=category)
    
    items = query.filter_by(is_active=True).all()
    return jsonify({
        'success': True,
        'data': [item.to_dict() for item in items]
    })

@cost_bp.route('/cost-items/<int:id>', methods=['PUT'])
def update_cost_item(id):
    """更新成本项配置"""
    from app import db
    from app.models import CostItem
    
    item = CostItem.query.get(id)
    if not item:
        return jsonify({'success': False, 'error': '成本项不存在'}), 404
    
    data = request.get_json()
    
    if 'unit_price' in data:
        item.unit_price = data['unit_price']
    if 'annual_maintenance_rate' in data:
        item.annual_maintenance_rate = data['annual_maintenance_rate']
    if 'is_active' in data:
        item.is_active = data['is_active']
    
    item.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': item.to_dict()
    })
