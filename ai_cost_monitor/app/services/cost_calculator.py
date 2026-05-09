"""
成本计算服务
核心业务逻辑层，负责成本计算
"""

class CostCalculator:
    """成本计算引擎"""
    
    def __init__(self, config):
        self.config = config
        self.gpu_count = config.get('gpu_count', 0)
        self.gpu_model = config.get('gpu_model', 'H200')
        self.server_count = config.get('server_count', 0)
        self.power_consumption_kw = config.get('power_consumption_kw', 0)
        self.electricity_price = config.get('electricity_price', 0.6)
        self.pue_ratio = config.get('pue_ratio', 1.3)
        self.location_type = config.get('location_type', 'colocation')
        
        # 根据GPU数量计算其他设备数量
        self._calculate_device_counts()
    
    def _calculate_device_counts(self):
        """根据GPU数量计算各设备数量"""
        # InfiniBand交换机（每台交换机可连接64个GPU）
        self.switch_count = max(1, self.gpu_count // 64)
        
        # 存储设备（每个PB存储对应一定数量的GPU）
        self.storage_count = max(1, self.gpu_count // 256)
        
        # 液冷CDU系统
        self.cdu_count = max(1, self.gpu_count // 256)
        
        # UPS不间断电源
        self.ups_count = max(1, self.gpu_count // 256)
        
        # 服务器数量（每台服务器8个GPU）
        if self.server_count == 0:
            self.server_count = self.gpu_count // 8
        
        # 运维人员数量（每100台服务器配1个运维人员）
        self.ops_staff_count = max(1, self.server_count // 100)
        
        # 网络带宽（Gbps）
        self.bandwidth_count = max(1, self.gpu_count // 128)
    
    def calculate(self, cost_items):
        """
        执行成本计算
        
        Args:
            cost_items: 成本项列表
            
        Returns:
            dict: 成本计算结果
        """
        result = {
            'hardware': [],
            'software': [],
            'ops': [],
            'total_hardware_cost': 0,
            'total_software_cost': 0,
            'total_ops_cost': 0
        }
        
        for item in cost_items:
            if not item.get('is_active', True):
                continue
            
            item_cost = self._calculate_item_cost(item)
            item_result = {
                'item_name': item['item_name'],
                'category': item['category'],
                'sub_category': item['sub_category'],
                'unit': item['unit'],
                'unit_price': item['unit_price'],
                'quantity': item_cost['quantity'],
                'subtotal': item_cost['subtotal'],
                'lifetime_cost': item_cost['lifetime_cost'],
                'annual_cost': item_cost['annual_cost']
            }
            
            result[item['category']].append(item_result)
            
            if item['category'] == 'hardware':
                result['total_hardware_cost'] += item_cost['lifetime_cost']
            elif item['category'] == 'software':
                result['total_software_cost'] += item_cost['annual_cost']
            elif item['category'] == 'ops':
                result['total_ops_cost'] += item_cost['annual_cost']
        
        # 计算电力成本
        electricity_cost = self._calculate_electricity_cost()
        result['electricity'] = electricity_cost
        result['total_ops_cost'] += electricity_cost['lifetime_cost']
        
        # 计算总计
        result['total_cost'] = (
            result['total_hardware_cost'] + 
            result['total_software_cost'] * 5 +  # 5年软件成本
            result['total_ops_cost']
        )
        
        # 计算年度运营成本
        result['annual_opex'] = (
            result['total_software_cost'] +  # 年软件成本
            result['total_ops_cost'] / 5     # 年运维成本（5年平均）
        )
        
        # 计算5年TCO
        result['five_year_tco'] = result['total_cost']
        
        # 计算单卡成本
        result['cost_per_gpu'] = result['total_cost'] / self.gpu_count if self.gpu_count > 0 else 0
        
        return result
    
    def _calculate_item_cost(self, item):
        """计算单个成本项的费用"""
        quantity = self._evaluate_quantity_formula(
            item.get('quantity_formula', '1'),
            item['category']
        )
        
        unit_price = item['unit_price']
        lifetime_years = item.get('lifetime_years', 1)
        maintenance_rate = item.get('annual_maintenance_rate', 0)
        
        # 基础成本
        base_cost = unit_price * quantity
        
        # 年维保系数 = 1 + (年维保费率 × 分摊年数)
        maintenance_factor = 1 + (maintenance_rate * lifetime_years)
        
        # 生命周期成本
        lifetime_cost = base_cost * maintenance_factor
        
        # 年度成本
        annual_cost = base_cost * (1 + maintenance_rate)
        
        return {
            'quantity': quantity,
            'subtotal': base_cost,
            'lifetime_cost': lifetime_cost,
            'annual_cost': annual_cost
        }
    
    def _evaluate_quantity_formula(self, formula, category):
        """
        计算数量公式
        
        支持的变量:
        - gpu_count: GPU数量
        - server_count: 服务器数量
        - switch_count: 交换机数量
        - storage_count: 存储数量
        - cdu_count: 液冷系统数量
        - ups_count: UPS数量
        - ops_staff_count: 运维人员数量
        - bandwidth_count: 带宽数量
        """
        if not formula:
            return 1
        
        try:
            # 替换变量
            formula = formula.replace('gpu_count', str(self.gpu_count))
            formula = formula.replace('server_count', str(self.server_count))
            formula = formula.replace('switch_count', str(self.switch_count))
            formula = formula.replace('storage_count', str(self.storage_count))
            formula = formula.replace('cdu_count', str(self.cdu_count))
            formula = formula.replace('ups_count', str(self.ups_count))
            formula = formula.replace('ops_staff_count', str(self.ops_staff_count))
            formula = formula.replace('bandwidth_count', str(self.bandwidth_count))
            
            # 安全评估（只允许数字和基本运算符）
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in formula):
                result = eval(formula)
                return max(0, int(result) if result == int(result) else result)
            else:
                return 1
        except:
            return 1
    
    def _calculate_electricity_cost(self):
        """
        计算电力成本
        
        年电力成本 = 总功耗(KW) × 24 × 365 × 电价 × PUE
        """
        hours_per_year = 24 * 365
        annual_electricity = (
            self.power_consumption_kw * 
            hours_per_year * 
            self.electricity_price * 
            self.pue_ratio
        )
        
        return {
            'item_name': '电力成本',
            'category': 'ops',
            'sub_category': 'electricity',
            'unit': '年',
            'unit_price': annual_electricity,
            'quantity': 5,  # 5年
            'subtotal': annual_electricity * 5,
            'lifetime_cost': annual_electricity * 5,
            'annual_cost': annual_electricity,
            'details': {
                'power_kw': self.power_consumption_kw,
                'pue_ratio': self.pue_ratio,
                'electricity_price': self.electricity_price,
                'hours_per_year': hours_per_year
            }
        }
    
    def get_cost_breakdown(self, calculation_result):
        """
        获取成本构成分析
        
        Args:
            calculation_result: 成本计算结果
            
        Returns:
            dict: 成本构成分析
        """
        total = calculation_result['total_cost']
        
        if total == 0:
            return {
                'hardware_pct': 0,
                'software_pct': 0,
                'ops_pct': 0,
                'breakdown': {}
            }
        
        hardware_cost = calculation_result['total_hardware_cost']
        software_cost = calculation_result['total_software_cost'] * 5
        ops_cost = calculation_result['total_ops_cost']
        
        breakdown = {}
        
        # 硬件子项分析
        for item in calculation_result.get('hardware', []):
            sub_cat = item['sub_category']
            if sub_cat not in breakdown:
                breakdown[sub_cat] = {'cost': 0, 'items': []}
            breakdown[sub_cat]['cost'] += item['lifetime_cost']
            breakdown[sub_cat]['items'].append(item)
        
        # 软件子项分析
        for item in calculation_result.get('software', []):
            sub_cat = item['sub_category']
            if sub_cat not in breakdown:
                breakdown[sub_cat] = {'cost': 0, 'items': []}
            breakdown[sub_cat]['cost'] += item['annual_cost'] * 5
            breakdown[sub_cat]['items'].append(item)
        
        # 运维子项分析
        for item in calculation_result.get('ops', []):
            if item['sub_category'] == 'electricity':
                continue
            sub_cat = item['sub_category']
            if sub_cat not in breakdown:
                breakdown[sub_cat] = {'cost': 0, 'items': []}
            breakdown[sub_cat]['cost'] += item['annual_cost'] * 5
            breakdown[sub_cat]['items'].append(item)
        
        # 电力成本单独列出
        if 'electricity' in calculation_result:
            breakdown['electricity'] = {
                'cost': calculation_result['electricity']['lifetime_cost'],
                'items': [calculation_result['electricity']]
            }
        
        return {
            'hardware_pct': round(hardware_cost / total * 100, 1),
            'software_pct': round(software_cost / total * 100, 1),
            'ops_pct': round(ops_cost / total * 100, 1),
            'breakdown': breakdown
        }
