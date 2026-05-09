"""
AI集群成本监控系统 - Flask应用工厂
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()

def create_app(config_name='default'):
    """创建Flask应用实例"""
    app = Flask(__name__,
                static_folder='../static',
                static_url_path='')
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-ai-cost-monitor')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URI', 
        'sqlite:////workspace/ai_cost_monitor/data/cost_monitor.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['EXPORT_DIR'] = os.environ.get('EXPORT_DIR', '/workspace/ai_cost_monitor/data/exports')
    app.config['REFRESH_INTERVAL'] = int(os.environ.get('REFRESH_INTERVAL', 30))
    
    # 初始化扩展
    db.init_app(app)
    
    # 注册蓝图
    from app.api.cost_api import cost_bp
    from app.api.export_api import export_bp
    
    app.register_blueprint(cost_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/api')
    
    # 创建导出目录
    os.makedirs(app.config['EXPORT_DIR'], exist_ok=True)
    
    # 路由
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
    
    return app

def init_database(app):
    """初始化数据库并导入预设数据"""
    with app.app_context():
        # 先导入所有模型
        from app.models.cost_item import CostItem
        from app.models.cluster_config import ClusterConfig
        from app.models.calculation import Calculation, ExportLog
        
        # 创建所有表
        db.create_all()
        
        # 检查是否已有数据
        existing_count = db.session.query(CostItem).count()
        if existing_count == 0:
            _load_default_cost_items()
            _load_default_cluster_configs()

def _load_default_cost_items():
    """加载预设成本项"""
    from app.models.cost_item import CostItem
    
    # 硬件类成本项
    hardware_items = [
        {
            'category': 'hardware',
            'sub_category': 'gpu',
            'item_name': 'NVIDIA H200 GPU',
            'unit': '张',
            'unit_price': 220000,
            'quantity_formula': 'gpu_count',
            'lifetime_years': 3,
            'annual_maintenance_rate': 0.10
        },
        {
            'category': 'hardware',
            'sub_category': 'gpu',
            'item_name': 'NVIDIA B200 GPU',
            'unit': '张',
            'unit_price': 350000,
            'quantity_formula': 'gpu_count',
            'lifetime_years': 3,
            'annual_maintenance_rate': 0.10
        },
        {
            'category': 'hardware',
            'sub_category': 'server',
            'item_name': 'DGX H200服务器',
            'unit': '台',
            'unit_price': 1800000,
            'quantity_formula': 'gpu_count/8',
            'lifetime_years': 3,
            'annual_maintenance_rate': 0.08
        },
        {
            'category': 'hardware',
            'sub_category': 'network',
            'item_name': 'InfiniBand交换机',
            'unit': '台',
            'unit_price': 150000,
            'quantity_formula': 'switch_count',
            'lifetime_years': 5,
            'annual_maintenance_rate': 0.10
        },
        {
            'category': 'hardware',
            'sub_category': 'storage',
            'item_name': '全闪存存储阵列',
            'unit': '套',
            'unit_price': 2000000,
            'quantity_formula': 'storage_count',
            'lifetime_years': 5,
            'annual_maintenance_rate': 0.08
        },
        {
            'category': 'hardware',
            'sub_category': 'cooling',
            'item_name': '液冷CDU系统',
            'unit': '套',
            'unit_price': 500000,
            'quantity_formula': 'cdu_count',
            'lifetime_years': 10,
            'annual_maintenance_rate': 0.05
        },
        {
            'category': 'hardware',
            'sub_category': 'power',
            'item_name': 'UPS不间断电源',
            'unit': '套',
            'unit_price': 300000,
            'quantity_formula': 'ups_count',
            'lifetime_years': 10,
            'annual_maintenance_rate': 0.05
        }
    ]
    
    # 软件类成本项
    software_items = [
        {
            'category': 'software',
            'sub_category': 'ai_platform',
            'item_name': 'NVIDIA AI Enterprise',
            'unit': 'GPU/年',
            'unit_price': 80000,
            'quantity_formula': 'gpu_count',
            'lifetime_years': 1,
            'annual_maintenance_rate': 0.0
        },
        {
            'category': 'software',
            'sub_category': 'container',
            'item_name': 'Kubernetes企业版',
            'unit': '节点/年',
            'unit_price': 50000,
            'quantity_formula': 'server_count',
            'lifetime_years': 1,
            'annual_maintenance_rate': 0.0
        },
        {
            'category': 'software',
            'sub_category': 'monitoring',
            'item_name': '监控告警系统',
            'unit': '套/年',
            'unit_price': 30000,
            'quantity_formula': '1',
            'lifetime_years': 1,
            'annual_maintenance_rate': 0.0
        },
        {
            'category': 'software',
            'sub_category': 'os',
            'item_name': '操作系统许可',
            'unit': '节点/年',
            'unit_price': 5000,
            'quantity_formula': 'server_count',
            'lifetime_years': 1,
            'annual_maintenance_rate': 0.0
        }
    ]
    
    # 运维类成本项
    ops_items = [
        {
            'category': 'ops',
            'sub_category': 'personnel',
            'item_name': '运维人员成本',
            'unit': '人/年',
            'unit_price': 500000,
            'quantity_formula': 'ops_staff_count',
            'lifetime_years': 1,
            'annual_maintenance_rate': 0.0
        },
        {
            'category': 'ops',
            'sub_category': 'network',
            'item_name': '网络带宽成本',
            'unit': '年',
            'unit_price': 1000000,
            'quantity_formula': 'bandwidth_count',
            'lifetime_years': 1,
            'annual_maintenance_rate': 0.0
        },
        {
            'category': 'ops',
            'sub_category': 'other',
            'item_name': '其他运营成本',
            'unit': '年',
            'unit_price': 1000000,
            'quantity_formula': '1',
            'lifetime_years': 1,
            'annual_maintenance_rate': 0.0
        }
    ]
    
    all_items = hardware_items + software_items + ops_items
    
    for item_data in all_items:
        item = CostItem(**item_data)
        db.session.add(item)
    
    db.session.commit()

def _load_default_cluster_configs():
    """加载预设集群配置"""
    from app.models.cluster_config import ClusterConfig
    
    configs = [
        {
            'cluster_name': '千卡集群',
            'cluster_scale': '1k',
            'gpu_count': 1024,
            'gpu_model': 'H200',
            'server_count': 128,
            'power_consumption_kw': 512,
            'location_type': 'colocation',
            'pue_ratio': 1.3,
            'electricity_price': 0.6
        },
        {
            'cluster_name': '万卡集群',
            'cluster_scale': '10k',
            'gpu_count': 10240,
            'gpu_model': 'H200',
            'server_count': 1280,
            'power_consumption_kw': 5120,
            'location_type': 'colocation',
            'pue_ratio': 1.3,
            'electricity_price': 0.6
        },
        {
            'cluster_name': '十万卡集群',
            'cluster_scale': '100k',
            'gpu_count': 102400,
            'gpu_model': 'H200',
            'server_count': 12800,
            'power_consumption_kw': 51200,
            'location_type': 'colocation',
            'pue_ratio': 1.3,
            'electricity_price': 0.6
        }
    ]
    
    for config_data in configs:
        config = ClusterConfig(**config_data)
        db.session.add(config)
    
    db.session.commit()
