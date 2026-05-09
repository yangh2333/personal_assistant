"""
成本项配置模型
存储所有硬件/软件/运维成本项的配置
"""
from datetime import datetime
from app import db

class CostItem(db.Model):
    """成本项配置表"""
    __tablename__ = 'cost_items'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # hardware/software/ops
    sub_category = db.Column(db.String(50), nullable=False)  # gpu/cpu/memory/storage...
    item_name = db.Column(db.String(100), nullable=False)  # 成本项名称
    unit = db.Column(db.String(20), nullable=False)  # 单位：个/台/套/年
    unit_price = db.Column(db.Float, nullable=False)  # 单价（元）
    quantity_formula = db.Column(db.String(200), nullable=True)  # 数量公式
    lifetime_years = db.Column(db.Integer, nullable=False, default=1)  # 生命周期（年）
    annual_maintenance_rate = db.Column(db.Float, nullable=False, default=0)  # 年维保费率
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'sub_category': self.sub_category,
            'item_name': self.item_name,
            'unit': self.unit,
            'unit_price': self.unit_price,
            'quantity_formula': self.quantity_formula,
            'lifetime_years': self.lifetime_years,
            'annual_maintenance_rate': self.annual_maintenance_rate,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<CostItem {self.item_name}>'
