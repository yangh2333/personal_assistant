from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import hashlib
import json


@dataclass
class Product:
    id: str = ""
    name: str = ""
    brand: str = ""
    model: str = ""
    price: float = 0.0
    currency: str = "CNY"
    original_price: float = 0.0
    discount: float = 0.0
    sales_count: int = 0
    sales_unit: str = "月销"
    shop_score: float = 0.0
    shop_name: str = ""
    platform: str = ""
    url: str = ""
    specs: Dict[str, Any] = field(default_factory=dict)
    image_url: str = ""
    collected_at: datetime = field(default_factory=datetime.now)
    category: str = ""
    
    def __post_init__(self):
        if not self.id and self.name:
            self.id = self.generate_id()
    
    def generate_id(self) -> str:
        content = f"{self.platform}:{self.name}:{self.url}".encode('utf-8')
        return hashlib.md5(content).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['collected_at'] = self.collected_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        if isinstance(data.get('collected_at'), str):
            data['collected_at'] = datetime.fromisoformat(data['collected_at'])
        return cls(**data)
    
    def standardize_name(self) -> str:
        import re
        name = self.name
        name = re.sub(r'\[.*?\]', '', name)
        name = re.sub(r'【.*?】', '', name)
        name = re.sub(r'[^\w\s\-\u4e00-\u9fff]', ' ', name)
        name = ' '.join(name.split())
        self.name = name
        return name
    
    def extract_brand_model(self) -> tuple:
        import re
        brand_patterns = [
            r'(NVIDIA|nvidia|英伟达)',
            r'(AMD|amd)',
            r'(Intel|intel|英特尔)',
            r'(七彩虹|影驰|华硕|微星|技嘉)',
            r'(三星|西部数据|希捷)',
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, self.name, re.IGNORECASE)
            if match:
                self.brand = match.group(1)
                break
        
        model_match = re.search(r'(RTX\s*\d{3,4}|GTX\s*\d{3,4}|A\s*100|H\s*100|L\s*40)', 
                                 self.name, re.IGNORECASE)
        if model_match:
            self.model = model_match.group(1).replace(' ', '')
        
        return self.brand, self.model


@dataclass
class PriceRecord:
    product_id: str
    product_name: str
    platform: str
    price: float
    recorded_at: datetime = field(default_factory=datetime.now)
    source_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'platform': self.platform,
            'price': self.price,
            'recorded_at': self.recorded_at.isoformat(),
            'source_url': self.source_url
        }


@dataclass
class ComparisonResult:
    products: List[Product]
    recommendations: List[str]
    price_chart_data: Dict[str, Any] = field(default_factory=dict)
    radar_data: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'products': [p.to_dict() for p in self.products],
            'recommendations': self.recommendations,
            'price_chart_data': self.price_chart_data,
            'radar_data': self.radar_data,
            'statistics': self.statistics
        }


@dataclass
class SearchResult:
    keyword: str
    platforms: List[str]
    total_count: int
    products: List[Product]
    search_time: float
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'keyword': self.keyword,
            'platforms': self.platforms,
            'total_count': self.total_count,
            'products': [p.to_dict() for p in self.products],
            'search_time': self.search_time,
            'errors': self.errors
        }
