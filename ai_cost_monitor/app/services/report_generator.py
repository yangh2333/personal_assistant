"""
报表生成服务
负责生成成本报表和趋势数据
"""
from datetime import datetime, timedelta
from app.models import Calculation, ClusterConfig

class ReportGenerator:
    """报表生成器"""
    
    def __init__(self):
        self.trend_days = 30  # 趋势数据天数
    
    def generate_summary_report(self, calculation_result):
        """
        生成汇总报表
        
        Args:
            calculation_result: 成本计算结果
            
        Returns:
            dict: 汇总报表数据
        """
        total_investment = calculation_result['total_cost']
        annual_cost = calculation_result['annual_opex']
        five_year_tco = calculation_result['five_year_tco']
        gpu_count = calculation_result.get('gpu_count', 0)
        
        return {
            'summary': {
                'total_investment': total_investment,
                'annual_cost': annual_cost,
                'five_year_tco': five_year_tco,
                'cost_per_gpu': calculation_result.get('cost_per_gpu', 0)
            },
            'breakdown': {
                'hardware': calculation_result.get('total_hardware_cost', 0),
                'software': calculation_result.get('total_software_cost', 0) * 5,
                'ops': calculation_result.get('total_ops_cost', 0)
            }
        }
    
    def generate_trend_data(self, scale='1k'):
        """
        生成成本趋势数据
        
        Args:
            scale: 集群规模
            
        Returns:
            dict: 趋势数据
        """
        # 获取不同规模的基准数据
        scale_factors = {
            '1k': 1,
            '10k': 10,
            '100k': 100
        }
        
        factor = scale_factors.get(scale, 1)
        
        # 生成30天的模拟趋势数据
        dates = []
        base_values = {
            'total': 1000000000 * factor,
            'hardware': 640000000 * factor,
            'software': 40000000 * factor,
            'ops': 320000000 * factor
        }
        
        for i in range(self.trend_days):
            date = datetime.now() - timedelta(days=self.trend_days - i - 1)
            dates.append(date.strftime('%Y-%m-%d'))
        
        # 生成带有波动的趋势数据
        import random
        random.seed(42)  # 固定种子保证数据一致性
        
        trend_data = {
            'dates': dates,
            'series': {
                'total': [],
                'hardware': [],
                'software': [],
                'ops': []
            }
        }
        
        for i in range(self.trend_days):
            # 添加小幅波动 (±5%)
            variation = 1 + (random.random() - 0.5) * 0.1
            
            trend_data['series']['total'].append(
                round(base_values['total'] * variation, 2)
            )
            trend_data['series']['hardware'].append(
                round(base_values['hardware'] * variation, 2)
            )
            trend_data['series']['software'].append(
                round(base_values['software'] * variation, 2)
            )
            trend_data['series']['ops'].append(
                round(base_values['ops'] * variation, 2)
            )
        
        return trend_data
    
    def generate_comparison_data(self):
        """
        生成不同规模集群的对比数据
        
        Returns:
            dict: 对比数据
        """
        scales = ['1k', '10k', '100k']
        scale_names = ['千卡集群', '万卡集群', '十万卡集群']
        scale_factors = [1, 10, 100]
        
        comparison = {
            'scales': scale_names,
            'gpu_counts': [1024, 10240, 102400],
            'total_costs': [],
            'hardware_costs': [],
            'software_costs': [],
            'ops_costs': []
        }
        
        base_costs = {
            'total': 1000000000,
            'hardware': 640000000,
            'software': 40000000,
            'ops': 320000000
        }
        
        for factor in scale_factors:
            comparison['total_costs'].append(base_costs['total'] * factor)
            comparison['hardware_costs'].append(base_costs['hardware'] * factor)
            comparison['software_costs'].append(base_costs['software'] * factor)
            comparison['ops_costs'].append(base_costs['ops'] * factor)
        
        return comparison
