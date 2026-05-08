import re
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.product import Product
from scrapers.base import RawProduct


class DataCleaner:
    """数据清洗处理器"""
    
    def __init__(self):
        self.brand_patterns = {
            'NVIDIA': [r'(NVIDIA|英伟达|Nvidia)', r'(RTX\s*\d{3,4}|GTX\s*\d{3,4}|A\s*100|H\s*100|L\s*40)'],
            'AMD': [r'(AMD| Radeon)', r'(RX\s*\d{4}|RX\s*\d{3})'],
            'Intel': [r'(Intel|英特尔)', r'(i\d-\d{4,5}|至强|E5|i9|i7|i5)'],
            '三星': [r'(三星|Samsung)', r'(9[89]\d|PRO|970|980|990)'],
            '西部数据': [r'(西部数据|WD|Western)', r'(SN\d{3}|WD\d|Black|Blue|Red)'],
            '希捷': [r'(希捷|Seagate)', r'(酷鱼|酷狼|银河|Exos|Ironwolf)'],
            '华硕': [r'(华硕|ASUS|ROG|TUF)', r'(RTX|GTX|RX|HD)'],
            '微星': [r'(微星|MSI)', r'(RTX|GTX|RX)'],
            '技嘉': [r'(技嘉|GIGABYTE|AORUS)', r'(RTX|GTX|RX)'],
            '七彩虹': [r'(七彩虹|Colorful|iGame)', r'(RTX|GTX)'],
            '影驰': [r'(影驰|GALAX)', r'(RTX|GTX|GeForce)'],
        }
        
        self.blacklist_shops = [
            '二手', '租赁', '测试', '样机', '清仓特卖'
        ]
        
        self.blacklist_keywords = [
            '二手', '翻新', '维修', '租', '押金', '样品', '清仓'
        ]
    
    def clean(self, raw_products: List[RawProduct]) -> List[Product]:
        """清洗原始数据"""
        cleaned = []
        
        for raw in raw_products:
            try:
                product = self._clean_single(raw)
                if product and self._is_valid(product):
                    cleaned.append(product)
            except Exception:
                continue
        
        return cleaned
    
    def _clean_single(self, raw: RawProduct) -> Product:
        product = Product()
        
        product.raw_name = raw.raw_name
        product.name = self._clean_name(raw.raw_name)
        product.brand, product.model = self._extract_brand_model(product.name)
        product.price = self._clean_price(raw.raw_price)
        product.original_price = self._extract_original_price(raw.raw_price)
        product.discount = self._calculate_discount(product.price, product.original_price)
        product.sales_count = self._clean_sales(raw.raw_sales)
        product.shop_score = self._clean_score(raw.raw_score)
        product.shop_name = self._clean_shop_name(raw.shop_name)
        product.platform = raw.platform
        product.url = raw.url
        product.image_url = raw.image_url
        product.collected_at = raw.collected_at
        
        self._extract_specs(product)
        
        return product
    
    def _clean_name(self, name: str) -> str:
        name = re.sub(r'\[.*?\]', '', name)
        name = re.sub(r'【.*?】', '', name)
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'<.*?>', '', name)
        name = re.sub(r'[^\w\s\-\u4e00-\u9fff%]', ' ', name)
        name = ' '.join(name.split())
        return name.strip()
    
    def _extract_brand_model(self, name: str) -> tuple:
        brand = '其他'
        model = ''
        
        for brand_name, patterns in self.brand_patterns.items():
            if any(re.search(p, name, re.IGNORECASE) for p in patterns[:1]):
                brand = brand_name
                
                for pattern in patterns[1:]:
                    match = re.search(pattern, name, re.IGNORECASE)
                    if match:
                        model = match.group(0).replace(' ', '')
                        break
                break
        
        return brand, model
    
    def _clean_price(self, price_str: str) -> float:
        if not price_str:
            return 0.0
        
        price_str = str(price_str).replace(',', '').replace(' ', '')
        
        patterns = [
            r'¥?\s*(\d+\.?\d*)',
            r'￥\s*(\d+\.?\d*)',
            r'RMB\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price_str)
            if match:
                return float(match.group(1))
        
        return 0.0
    
    def _extract_original_price(self, price_str: str) -> float:
        patterns = [
            r'原价[：:]?\s*¥?\s*(\d+\.?\d*)',
            r'原价\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*元起',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price_str)
            if match:
                return float(match.group(1))
        
        return 0.0
    
    def _calculate_discount(self, current: float, original: float) -> float:
        if original > 0 and current > 0:
            return round((original - current) / original * 10, 1)
        return 0.0
    
    def _clean_sales(self, sales_str: str) -> int:
        if not sales_str:
            return 0
        
        sales_str = str(sales_str).replace(',', '').replace(' ', '')
        sales_str = sales_str.replace('万', '0000').replace('+', '')
        
        patterns = [
            r'(\d+\.?\d*)\s*[万千]?\+?',
            r'(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sales_str)
            if match:
                value = float(match.group(1))
                if '万' in sales_str:
                    value *= 10000
                elif '千' in sales_str:
                    value *= 1000
                return int(value)
        
        return 0
    
    def _clean_score(self, score_str: str) -> float:
        if not score_str or score_str == '0':
            return 0.0
        
        match = re.search(r'(\d+\.?\d*)', str(score_str))
        if match:
            score = float(match.group(1))
            if 0 <= score <= 5:
                return score
            elif score > 5:
                return score / 20
        return 0.0
    
    def _clean_shop_name(self, shop_name: str) -> str:
        if not shop_name:
            return '未知店铺'
        
        shop_name = shop_name.strip()
        shop_name = re.sub(r'\s+', ' ', shop_name)
        
        for keyword in self.blacklist_shops:
            if keyword in shop_name:
                return shop_name
        
        return shop_name
    
    def _extract_specs(self, product: Product):
        """提取规格参数"""
        specs = {}
        
        vram_match = re.search(r'(\d+)\s*[Gg]?\s*(显存|VGA内存)', product.name)
        if vram_match:
            specs['vram'] = f"{vram_match.group(1)}GB"
        
        core_match = re.search(r'(\d+)\s*[Cc]ore|[Cc]UDA\s*(\d+)', product.name, re.IGNORECASE)
        if core_match:
            cores = core_match.group(1) or core_match.group(2)
            specs['cores'] = cores
        
        pcie_match = re.search(r'(PCIE\s*[234]\.0|PCI-E\s*[234]\.0)', product.name, re.IGNORECASE)
        if pcie_match:
            specs['pcie'] = pcie_match.group(1).upper()
        
        power_match = re.search(r'(\d+)\s*W(?:\s*电源|功耗)', product.name, re.IGNORECASE)
        if power_match:
            specs['tdp'] = f"{power_match.group(1)}W"
        
        product.specs = specs
    
    def _is_valid(self, product: Product) -> bool:
        if not product.name or len(product.name) < 5:
            return False
        
        if product.price <= 0:
            return False
        
        for keyword in self.blacklist_keywords:
            if keyword in product.name:
                return False
        
        if any(keyword in product.shop_name for keyword in self.blacklist_shops):
            return False
        
        return True
    
    def get_statistics(self, products: List[Product]) -> Dict[str, Any]:
        """获取数据统计信息"""
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
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'platform_distribution': self._count_by_platform(products),
            'brand_distribution': self._count_by_brand(products),
        }
    
    def _count_by_platform(self, products: List[Product]) -> Dict[str, int]:
        counts = {}
        for p in products:
            counts[p.platform] = counts.get(p.platform, 0) + 1
        return counts
    
    def _count_by_brand(self, products: List[Product]) -> Dict[str, int]:
        counts = {}
        for p in products:
            counts[p.brand] = counts.get(p.brand, 0) + 1
        return counts
