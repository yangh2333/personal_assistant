import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from models.product import Product, SearchResult
from models.trend import PriceTrend, TrendSummary


class Database:
    """数据存储基类"""
    
    def __init__(self, db_path: str = './data'):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
    
    def save_products(self, products: List[Product], filename: str) -> str:
        """保存商品数据"""
        filepath = self.db_path / filename
        
        if filepath.suffix == '.json':
            return self._save_json(products, filepath)
        elif filepath.suffix == '.csv':
            return self._save_csv(products, filepath)
        else:
            filepath = filepath.with_suffix('.json')
            return self._save_json(products, filepath)
    
    def _save_json(self, products: List[Product], filepath: Path) -> str:
        data = [p.to_dict() for p in products]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def _save_csv(self, products: List[Product], filepath: Path) -> str:
        if not products:
            return str(filepath)
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            writer.writerow([
                'ID', '商品名称', '品牌', '型号', '价格', '原价', '折扣',
                '销量', '店铺评分', '店铺名称', '平台', '链接', '采集时间'
            ])
            
            for p in products:
                writer.writerow([
                    p.id,
                    p.name,
                    p.brand,
                    p.model,
                    p.price,
                    p.original_price,
                    p.discount,
                    p.sales_count,
                    p.shop_score,
                    p.shop_name,
                    p.platform,
                    p.url,
                    p.collected_at.isoformat() if p.collected_at else ''
                ])
        
        return str(filepath)
    
    def load_products(self, filepath: str) -> List[Product]:
        """加载商品数据"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            return []
        
        if filepath.suffix == '.json':
            return self._load_json(filepath)
        elif filepath.suffix == '.csv':
            return self._load_csv(filepath)
        
        return []
    
    def _load_json(self, filepath: Path) -> List[Product]:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [Product.from_dict(item) for item in data]
    
    def _load_csv(self, filepath: Path) -> List[Product]:
        products = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    product = Product(
                        id=row.get('ID', ''),
                        name=row.get('商品名称', ''),
                        brand=row.get('品牌', ''),
                        model=row.get('型号', ''),
                        price=float(row.get('价格', 0)),
                        original_price=float(row.get('原价', 0)),
                        discount=float(row.get('折扣', 0)),
                        sales_count=int(row.get('销量', 0)),
                        shop_score=float(row.get('店铺评分', 0)),
                        shop_name=row.get('店铺名称', ''),
                        platform=row.get('平台', ''),
                        url=row.get('链接', ''),
                    )
                    
                    if row.get('采集时间'):
                        product.collected_at = datetime.fromisoformat(row['采集时间'])
                    
                    products.append(product)
                except Exception:
                    continue
        
        return products


class PriceDatabase:
    """价格趋势数据库"""
    
    def __init__(self, db_path: str = './data/trends'):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.trends_file = self.db_path / 'trends.json'
    
    def save_trends(self, summary: TrendSummary) -> str:
        """保存价格趋势"""
        data = summary.to_dict()
        
        with open(self.trends_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(self.trends_file)
    
    def load_trends(self) -> Optional[TrendSummary]:
        """加载价格趋势"""
        if not self.trends_file.exists():
            return None
        
        with open(self.trends_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        trends = []
        for trend_data in data.get('trends', []):
            trend = PriceTrend(
                product_id=trend_data['product_id'],
                product_name=trend_data['product_name'],
                platform=trend_data['platform'],
                records=trend_data.get('records', [])
            )
            trends.append(trend)
        
        return TrendSummary(
            keyword=data.get('keyword', ''),
            trends=trends,
            generated_at=datetime.fromisoformat(data.get('generated_at', datetime.now().isoformat()))
        )
    
    def add_price_record(self, product_id: str, product_name: str, 
                        platform: str, price: float) -> None:
        """添加价格记录"""
        trends = self.load_trends() or TrendSummary(keyword='', trends=[])
        
        existing = None
        for trend in trends.trends:
            if trend.product_id == product_id:
                existing = trend
                break
        
        if existing:
            existing.add_record(price)
        else:
            new_trend = PriceTrend(
                product_id=product_id,
                product_name=product_name,
                platform=platform
            )
            new_trend.add_record(price)
            trends.trends.append(new_trend)
        
        self.save_trends(trends)
    
    def get_product_trend(self, product_id: str) -> Optional[PriceTrend]:
        """获取单个商品趋势"""
        trends = self.load_trends()
        if not trends:
            return None
        
        for trend in trends.trends:
            if trend.product_id == product_id:
                return trend
        
        return None
