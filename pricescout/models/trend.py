from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random


@dataclass
class PriceTrend:
    product_id: str
    product_name: str
    platform: str
    records: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_record(self, price: float, recorded_at: Optional[datetime] = None):
        if recorded_at is None:
            recorded_at = datetime.now()
        self.records.append({
            'price': price,
            'recorded_at': recorded_at.isoformat()
        })
    
    def get_chart_data(self) -> Dict[str, Any]:
        dates = [r['recorded_at'][:10] for r in self.records]
        prices = [r['price'] for r in self.records]
        return {
            'dates': dates,
            'prices': prices,
            'name': self.product_name,
            'platform': self.platform
        }
    
    def calculate_stats(self) -> Dict[str, Any]:
        if not self.records:
            return {}
        
        prices = [r['price'] for r in self.records]
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': sum(prices) / len(prices),
            'current_price': prices[-1] if prices else 0,
            'price_change': prices[-1] - prices[0] if len(prices) > 1 else 0,
            'price_change_pct': ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'platform': self.platform,
            'records': self.records
        }


@dataclass  
class TrendSummary:
    keyword: str
    trends: List[PriceTrend]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def get_all_platforms(self) -> List[str]:
        return list(set(t.platform for t in self.trends))
    
    def get_best_deals(self, top_n: int = 5) -> List[Dict[str, Any]]:
        latest_prices = []
        for trend in self.trends:
            if trend.records:
                latest = trend.records[-1]
                stats = trend.calculate_stats()
                latest_prices.append({
                    'product_id': trend.product_id,
                    'product_name': trend.product_name,
                    'platform': trend.platform,
                    'current_price': latest['price'],
                    'min_price': stats.get('min_price', latest['price']),
                    'max_price': stats.get('max_price', latest['price']),
                    'avg_price': stats.get('avg_price', latest['price']),
                    'price_change_pct': stats.get('price_change_pct', 0)
                })
        
        latest_prices.sort(key=lambda x: x['current_price'])
        return latest_prices[:top_n]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'keyword': self.keyword,
            'trends': [t.to_dict() for t in self.trends],
            'generated_at': self.generated_at.isoformat()
        }
