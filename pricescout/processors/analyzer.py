import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.product import Product, ComparisonResult, SearchResult
from models.trend import PriceTrend, TrendSummary


class Analyzer:
    """数据分析与性价比分析"""
    
    def __init__(self):
        self.performance_weights = {
            'vram': 25,
            'cores': 20,
            'speed': 15,
            'pcie': 10,
            'tdp': 5,
        }
        
        self.gpu_performance_map = {
            'RTX 4090': 100,
            'RTX 4080': 85,
            'RTX 4070': 70,
            'RTX 4060': 55,
            'RTX 3090': 90,
            'RTX 3080': 80,
            'RTX 3070': 65,
            'RTX 3060': 50,
            'GTX 1080': 60,
            'GTX 1070': 50,
            'A100': 150,
            'H100': 200,
            'A6000': 110,
            'A5000': 90,
        }
    
    def analyze(self, products: List[Product]) -> List[Product]:
        """分析并计算性价比指数"""
        if not products:
            return products
        
        price_stats = self._calculate_price_stats(products)
        sales_stats = self._calculate_sales_stats(products)
        
        for product in products:
            product.performance_score = self._calculate_performance_score(product)
            product.price_score = self._calculate_price_score(product.price, price_stats)
            product.heat_score = self._calculate_heat_score(product.sales_count, sales_stats)
            product.credit_score = self._calculate_credit_score(product.shop_score)
            product.value_index = self._calculate_value_index(product)
        
        return products
    
    def _calculate_price_stats(self, products: List[Product]) -> Dict[str, float]:
        prices = [p.price for p in products if p.price > 0]
        if not prices:
            return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}
        
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        return {
            'min': min(prices),
            'max': max(prices),
            'avg': sum(prices) / n,
            'median': sorted_prices[n // 2],
        }
    
    def _calculate_sales_stats(self, products: List[Product]) -> Dict[str, float]:
        sales = [p.sales_count for p in products if p.sales_count > 0]
        if not sales:
            return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}
        
        sorted_sales = sorted(sales)
        n = len(sorted_sales)
        
        return {
            'min': min(sales),
            'max': max(sales),
            'avg': sum(sales) / n,
            'median': sorted_sales[n // 2],
        }
    
    def _calculate_performance_score(self, product: Product) -> float:
        score = 50
        
        model_upper = product.model.upper().replace(' ', '') if product.model else ''
        for gpu, perf in self.gpu_performance_map.items():
            if gpu.upper().replace(' ', '') in model_upper:
                return perf
        
        if product.specs.get('vram'):
            vram_match = re.search(r'(\d+)', product.specs.get('vram', ''))
            if vram_match:
                vram = int(vram_match.group(1))
                if vram >= 80:
                    score += 50
                elif vram >= 40:
                    score += 40
                elif vram >= 24:
                    score += 35
                elif vram >= 16:
                    score += 25
                elif vram >= 8:
                    score += 15
        
        if product.specs.get('cores'):
            cores_match = re.search(r'(\d+)', product.specs.get('cores', ''))
            if cores_match:
                cores = int(cores_match.group(1))
                if cores >= 10000:
                    score += 40
                elif cores >= 5000:
                    score += 30
                elif cores >= 2000:
                    score += 20
        
        if product.specs.get('pcie'):
            pcie = product.specs.get('pcie', '').upper()
            if 'PCIE 5' in pcie or 'PCI-E 5' in pcie:
                score += 10
            elif 'PCIE 4' in pcie or 'PCI-E 4' in pcie:
                score += 7
            elif 'PCIE 3' in pcie or 'PCI-E 3' in pcie:
                score += 4
        
        return min(score, 200)
    
    def _calculate_price_score(self, price: float, stats: Dict[str, float]) -> float:
        if price <= 0 or stats['avg'] == 0:
            return 50
        
        ratio = price / stats['avg']
        
        if ratio <= 0.5:
            return 100
        elif ratio <= 0.7:
            return 90
        elif ratio <= 0.85:
            return 80
        elif ratio <= 1.0:
            return 70
        elif ratio <= 1.15:
            return 60
        elif ratio <= 1.3:
            return 50
        elif ratio <= 1.5:
            return 40
        else:
            return 30
    
    def _calculate_heat_score(self, sales: int, stats: Dict[str, float]) -> float:
        if sales <= 0 or stats['avg'] == 0:
            return 50
        
        ratio = sales / stats['avg']
        
        if ratio >= 10:
            return 100
        elif ratio >= 5:
            return 90
        elif ratio >= 2:
            return 80
        elif ratio >= 1:
            return 70
        elif ratio >= 0.5:
            return 60
        elif ratio >= 0.2:
            return 50
        else:
            return 40
    
    def _calculate_credit_score(self, shop_score: float) -> float:
        if shop_score <= 0:
            return 50
        return shop_score * 20
    
    def _calculate_value_index(self, product: Product) -> float:
        perf_weight = 0.4
        price_weight = 0.3
        heat_weight = 0.2
        credit_weight = 0.1
        
        performance_score = getattr(product, 'performance_score', 50)
        price_score = getattr(product, 'price_score', 50)
        heat_score = getattr(product, 'heat_score', 50)
        credit_score = getattr(product, 'credit_score', 50)
        
        value_index = (
            performance_score * perf_weight +
            price_score * price_weight +
            heat_score * heat_weight +
            credit_score * credit_weight
        )
        
        return round(value_index, 2)
    
    def sort_products(self, products: List[Product], 
                     sort_by: str = 'price', 
                     order: str = 'asc') -> List[Product]:
        """排序商品"""
        sort_key_map = {
            'price': lambda p: p.price,
            'sales': lambda p: p.sales_count,
            'score': lambda p: p.value_index if hasattr(p, 'value_index') else 0,
            'shop_score': lambda p: p.shop_score,
            'name': lambda p: p.name,
        }
        
        sort_key = sort_key_map.get(sort_by, sort_key_map['price'])
        
        reverse = order.lower() == 'desc'
        
        return sorted(products, key=sort_key, reverse=reverse)
    
    def get_top_recommendations(self, products: List[Product], 
                               top_n: int = 5) -> List[Product]:
        """获取最佳推荐"""
        analyzed = self.analyze(products)
        sorted_products = self.sort_products(analyzed, 'score', 'desc')
        return sorted_products[:top_n]
    
    def compare_products(self, products: List[Product]) -> ComparisonResult:
        """生成对比结果"""
        if not products:
            return ComparisonResult([], [], {}, {}, {})
        
        analyzed = self.analyze(products)
        
        recommendations = self._generate_recommendations(analyzed)
        
        price_chart_data = self._generate_price_chart(analyzed)
        
        radar_data = self._generate_radar_data(analyzed)
        
        statistics = self._generate_statistics(analyzed)
        
        return ComparisonResult(
            products=analyzed,
            recommendations=recommendations,
            price_chart_data=price_chart_data,
            radar_data=radar_data,
            statistics=statistics
        )
    
    def _generate_recommendations(self, products: List[Product]) -> List[str]:
        recommendations = []
        
        if not products:
            return recommendations
        
        best_value = max(products, key=lambda p: p.value_index if hasattr(p, 'value_index') else 0)
        recommendations.append(
            f"性价比之选: {best_value.name} "
            f"(性价比指数: {getattr(best_value, 'value_index', 0):.1f})"
        )
        
        lowest_price = min(products, key=lambda p: p.price)
        if lowest_price != best_value:
            recommendations.append(
                f"最低价格: {lowest_price.name} "
                f"(价格: {lowest_price.price:,.0f})"
            )
        
        highest_sales = max(products, key=lambda p: p.sales_count)
        if highest_sales.sales_count > 0:
            recommendations.append(
                f"最受欢迎: {highest_sales.name} "
                f"(销量: {highest_sales.sales_count:,})"
            )
        
        highest_perf = max(products, key=lambda p: getattr(p, 'performance_score', 0))
        if highest_perf and getattr(highest_perf, 'performance_score', 0) > 50:
            recommendations.append(
                f"性能最强: {highest_perf.name} "
                f"(性能分: {getattr(highest_perf, 'performance_score', 0):.0f})"
            )
        
        return recommendations
    
    def _generate_price_chart(self, products: List[Product]) -> Dict[str, Any]:
        sorted_by_price = sorted(products, key=lambda p: p.price)
        
        categories = [p.name[:15] + '...' if len(p.name) > 15 else p.name for p in sorted_by_price]
        prices = [p.price for p in sorted_by_price]
        
        return {
            'categories': categories,
            'series': [{
                'name': '价格',
                'data': prices,
                'platforms': [p.platform for p in sorted_by_price]
            }],
            'y_axis_label': '价格 (元)'
        }
    
    def _generate_radar_data(self, products: List[Product]) -> Dict[str, Any]:
        indicators = [
            {'name': '性能', 'max': 200},
            {'name': '价格优势', 'max': 100},
            {'name': '热度', 'max': 100},
            {'name': '店铺信誉', 'max': 100},
        ]
        
        series = []
        colors = ['#5470C6', '#EE6666', '#73C0DE', '#FAC858', '#91CC75']
        
        for i, product in enumerate(products[:5]):
            perf_score = getattr(product, 'performance_score', 50)
            price_score = getattr(product, 'price_score', 50)
            heat_score = getattr(product, 'heat_score', 50)
            credit_score = getattr(product, 'credit_score', 50)
            
            series.append({
                'name': product.name[:10] + '...' if len(product.name) > 10 else product.name,
                'value': [perf_score, price_score, heat_score, credit_score],
                'color': colors[i % len(colors)]
            })
        
        return {
            'indicators': indicators,
            'series': series
        }
    
    def _generate_statistics(self, products: List[Product]) -> Dict[str, Any]:
        if not products:
            return {}
        
        prices = [p.price for p in products]
        sales = [p.sales_count for p in products]
        scores = [p.shop_score for p in products if p.shop_score > 0]
        
        return {
            'total_count': len(products),
            'price_range': {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices),
            },
            'total_sales': sum(sales),
            'avg_shop_score': sum(scores) / len(scores) if scores else 0,
            'platform_count': len(set(p.platform for p in products)),
        }
    
    def generate_mock_trends(self, products: List[Product], 
                            days: int = 30) -> TrendSummary:
        """生成模拟价格趋势数据"""
        trends = []
        
        for product in products[:5]:
            trend = PriceTrend(
                product_id=product.id,
                product_name=product.name,
                platform=product.platform
            )
            
            base_price = product.price
            current_date = datetime.now()
            
            for i in range(days):
                date = current_date - timedelta(days=days - i - 1)
                variation = random.uniform(-0.1, 0.1)
                price = base_price * (1 + variation)
                
                if i > 0 and random.random() < 0.3:
                    price = price * random.uniform(0.95, 1.05)
                
                trend.add_record(round(price, 2), date)
            
            trends.append(trend)
        
        return TrendSummary(
            keyword="GPU",
            trends=trends,
            generated_at=datetime.now()
        )
