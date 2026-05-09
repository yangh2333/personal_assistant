"""
集群配置模型
存储千卡/万卡/十万卡集群的配置模板
"""
from datetime import datetime
from app import db

class ClusterConfig(db.Model):
    """集群配置表"""
    __tablename__ = 'cluster_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    cluster_name = db.Column(db.String(50), nullable=False)  # 集群名称
    cluster_scale = db.Column(db.String(20), nullable=False)  # 规模：1k/10k/100k
    gpu_count = db.Column(db.Integer, nullable=False)  # GPU总数量
    gpu_model = db.Column(db.String(50), nullable=False)  # GPU型号
    server_count = db.Column(db.Integer, nullable=False)  # 服务器数量
    power_consumption_kw = db.Column(db.Float, nullable=False)  # 总功耗(KW)
    location_type = db.Column(db.String(20), nullable=False)  # 场地类型：自建/托管/云
    pue_ratio = db.Column(db.Float, nullable=False, default=1.3)  # PUE值
    electricity_price = db.Column(db.Float, nullable=False, default=0.6)  # 电价（元/度）
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cluster_name': self.cluster_name,
            'cluster_scale': self.cluster_scale,
            'gpu_count': self.gpu_count,
            'gpu_model': self.gpu_model,
            'server_count': self.server_count,
            'power_consumption_kw': self.power_consumption_kw,
            'location_type': self.location_type,
            'pue_ratio': self.pue_ratio,
            'electricity_price': self.electricity_price,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ClusterConfig {self.cluster_name}>'
