"""
导出相关API路由
"""
from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime
import os

export_bp = Blueprint('export', __name__)

@export_bp.route('/export/excel', methods=['GET'])
def export_excel():
    """导出Excel文件"""
    from app import db
    from app.models import Calculation, ExportLog
    from app.utils.excel_exporter import ExcelExporter
    from app.services import CostCalculator
    
    # 获取最新的计算结果
    calculation = Calculation.query.order_by(Calculation.calculated_at.desc()).first()
    
    if not calculation:
        return jsonify({'success': False, 'error': '没有可导出的计算结果'}), 400
    
    # 生成Excel文件
    export_dir = current_app.config['EXPORT_DIR']
    os.makedirs(export_dir, exist_ok=True)
    
    exporter = ExcelExporter(export_dir)
    file_path = exporter.export(calculation)
    
    # 记录导出日志
    export_log = ExportLog(
        calculation_id=calculation.id,
        export_type='excel',
        file_path=file_path,
        exported_at=datetime.now()
    )
    db.session.add(export_log)
    db.session.commit()
    
    # 返回文件
    return send_file(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'ai_cost_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@export_bp.route('/export/logs', methods=['GET'])
def get_export_logs():
    """获取导出日志列表"""
    from app.models import ExportLog
    
    logs = ExportLog.query.order_by(ExportLog.exported_at.desc()).limit(50).all()
    return jsonify({
        'success': True,
        'data': [log.to_dict() for log in logs]
    })
