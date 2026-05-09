"""
计算结果模型
存储成本计算的历史记录
"""
from datetime import datetime
from app import db
import json

class Calculation(db.Model):
    """计算结果表"""
    __tablename__ = 'calculations'
    
    id = db.Column(db.Integer, primary_key=True)
    cluster_config_id = db.Column(db.Integer, db.ForeignKey('cluster_configs.id'), nullable=True)
    total_hardware_cost = db.Column(db.Float, nullable=False, default=0)  # 硬件总成本
    total_software_cost = db.Column(db.Float, nullable=False, default=0)  # 软件总成本
    total_ops_cost = db.Column(db.Float, nullable=False, default=0)  # 运维总成本
    total_cost = db.Column(db.Float, nullable=False, default=0)  # 总成本
    annual_opex = db.Column(db.Float, nullable=False, default=0)  # 年运营成本
    five_year_tco = db.Column(db.Float, nullable=False, default=0)  # 5年TCO
    calculation_details = db.Column(db.Text, nullable=True)  # 详细计算数据JSON
    calculated_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def to_dict(self):
        details = None
        if self.calculation_details:
            try:
                details = json.loads(self.calculation_details)
            except:
                details = self.calculation_details
        
        return {
            'id': self.id,
            'cluster_config_id': self.cluster_config_id,
            'total_hardware_cost': self.total_hardware_cost,
            'total_software_cost': self.total_software_cost,
            'total_ops_cost': self.total_ops_cost,
            'total_cost': self.total_cost,
            'annual_opex': self.annual_opex,
            'five_year_tco': self.five_year_tco,
            'calculation_details': details,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }
    
    def __repr__(self):
        return f'<Calculation {self.id} - Total: {self.total_cost}>'


class ExportLog(db.Model):
    """导出日志表"""
    __tablename__ = 'export_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    calculation_id = db.Column(db.Integer, db.ForeignKey('calculations.id'), nullable=False)
    export_type = db.Column(db.String(20), nullable=False, default='excel')  # 导出类型
    file_path = db.Column(db.String(200), nullable=True)  # 导出文件路径
    exported_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'calculation_id': self.calculation_id,
            'export_type': self.export_type,
            'file_path': self.file_path,
            'exported_at': self.exported_at.isoformat() if self.exported_at else None
        }
    
    def __repr__(self):
        return f'<ExportLog {self.id}>'
