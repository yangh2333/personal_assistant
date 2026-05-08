import re
import sys
from pathlib import Path
from typing import List, Dict, Set
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.product import Product


class Deduplicator:
    """数据去重处理器"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.seen_ids: Set[str] = set()
        self.seen_urls: Set[str] = set()
        self.seen_names: Set[str] = set()
    
    def deduplicate(self, products: List[Product]) -> List[Product]:
        """去重处理"""
        self.seen_ids.clear()
        self.seen_urls.clear()
        self.seen_names.clear()
        
        unique_products = []
        
        for product in products:
            if self._is_duplicate(product):
                continue
            
            self.seen_ids.add(product.id)
            self.seen_urls.add(self._normalize_url(product.url))
            self.seen_names.add(self._normalize_name(product.name))
            unique_products.append(product)
        
        return unique_products
    
    def _is_duplicate(self, product: Product) -> bool:
        normalized_url = self._normalize_url(product.url)
        if normalized_url in self.seen_urls:
            return True
        
        normalized_name = self._normalize_name(product.name)
        if normalized_name in self.seen_names:
            return True
        
        for seen_name in self.seen_names:
            similarity = self._calculate_similarity(normalized_name, seen_name)
            if similarity >= self.similarity_threshold:
                if self._same_price_range(product.price, seen_name):
                    return True
        
        return False
    
    def _normalize_url(self, url: str) -> str:
        if not url:
            return ""
        
        url = url.strip()
        url = re.sub(r'\?.*$', '', url)
        url = re.sub(r'/+$', '', url)
        
        return url.lower()
    
    def _normalize_name(self, name: str) -> str:
        name = name.lower()
        name = re.sub(r'[^\w\u4e00-\u9fff]', '', name)
        name = re.sub(r'\d+', 'N', name)
        
        keywords = ['rtx', 'gtx', 'rx', 'a100', 'h100', 'ssd', 'nvme']
        for kw in keywords:
            name = name.replace(kw, '')
        
        return name.strip()
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _same_price_range(self, price: float, name: str) -> bool:
        if 'N' in name:
            return True
        return False
    
    def merge_duplicates(self, products: List[Product]) -> List[Product]:
        """合并重复商品，保留最优数据"""
        grouped: Dict[str, List[Product]] = {}
        
        for product in products:
            key = self._get_merge_key(product)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(product)
        
        merged = []
        for products_list in grouped.values():
            if len(products_list) == 1:
                merged.extend(products_list)
            else:
                merged.append(self._select_best(products_list))
        
        return merged
    
    def _get_merge_key(self, product: Product) -> str:
        model = product.model or ''
        brand = product.brand or ''
        return f"{brand}:{model}".lower()
    
    def _select_best(self, products: List[Product]) -> Product:
        return max(products, key=lambda p: (
            p.shop_score if p.shop_score else 0,
            p.sales_count,
            -p.price
        ))
