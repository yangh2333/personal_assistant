"""
数据处理器
数据清洗、去重、排序、分析
"""

import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class PriceStats:
    """价格统计"""
    min: float
    max: float
    avg: float
    median: float
    q1: float
    q3: float


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.platform_map = {
            "jd": "京东",
            "tb": "淘宝", 
            "pdd": "拼多多",
            "demo": "示例"
        }
    
    def process(self, data: List[dict]) -> Dict[str, Any]:
        """完整数据处理流程"""
        cleaned = self.clean(data)
        deduplicated = self.deduplicate(cleaned)
        analyzed = self.analyze(deduplicated)
        return {
            "data": analyzed["data"],
            "stats": analyzed["stats"],
            "summary": self._generate_summary(analyzed["stats"])
        }
    
    def clean(self, data: List[dict]) -> List[dict]:
        """数据清洗"""
        cleaned = []
        for item in data:
            if not self._is_valid(item):
                continue
            
            cleaned_item = self._normalize(item)
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _is_valid(self, item: dict) -> bool:
        """验证数据有效性"""
        if not item:
            return False
        
        name = item.get("name", "")
        if not name or len(name) < 3:
            return False
        
        price = item.get("price", 0)
        if not isinstance(price, (int, float)) or price <= 0:
            return False
        
        return True
    
    def _normalize(self, item: dict) -> dict:
        """标准化数据格式"""
        return {
            "id": item.get("id", ""),
            "name": self._normalize_name(item.get("name", "")),
            "price": round(float(item.get("price", 0)), 2),
            "sales": int(item.get("sales", 0)),
            "shop_name": item.get("shop_name", "未知店铺"),
            "shop_score": round(float(item.get("shop_score", 0)), 1),
            "platform": item.get("platform", "unknown"),
            "platform_icon": item.get("platform_icon", "📦"),
            "platform_name": item.get("platform_name", self.platform_map.get(item.get("platform", ""), "未知")),
            "url": item.get("url", ""),
            "image": item.get("image", ""),
            "crawl_time": item.get("crawl_time", datetime.now().isoformat()),
            "tags": item.get("tags", [])
        }
    
    def _normalize_name(self, name: str) -> str:
        """标准化商品名称"""
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'[🔥💰⭐🎉✨📢]', '', name)
        name = name.strip()
        return name
    
    def deduplicate(self, data: List[dict]) -> List[dict]:
        """去重处理"""
        seen = set()
        result = []
        
        for item in data:
            key = self._generate_key(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result
    
    def _generate_key(self, item: dict) -> str:
        """生成去重键"""
        name = self._normalize_name(item.get("name", ""))
        price = round(float(item.get("price", 0)), 0)
        return f"{name}_{price}"
    
    def sort(self, data: List[dict], 
             sort_by: str = "price", 
             order: str = "asc") -> List[dict]:
        """排序"""
        if not data:
            return []
        
        valid_sort_keys = ["price", "sales", "shop_score", "name"]
        if sort_by not in valid_sort_keys:
            sort_by = "price"
        
        reverse = order == "desc"
        
        return sorted(data, 
                     key=lambda x: (x.get(sort_by, 0), x.get("name", "")),
                     reverse=reverse)
    
    def analyze(self, data: List[dict]) -> Dict[str, Any]:
        """数据分析"""
        if not data:
            return {
                "data": [],
                "stats": self._empty_stats()
            }
        
        analyzed_data = self._add_value_score(data)
        stats = self._calc_stats(analyzed_data)
        
        return {
            "data": analyzed_data,
            "stats": stats
        }
    
    def _add_value_score(self, data: List[dict]) -> List[dict]:
        """计算性价比评分并添加标签"""
        prices = [item["price"] for item in data]
        max_price = max(prices) if prices else 1
        min_price = min(prices) if prices else 1
        
        for item in data:
            price_normalized = (item["price"] - min_price) / (max_price - min_price + 0.001)
            
            sales = item.get("sales", 0)
            sales_normalized = min(sales / 10000, 1)
            
            score = item.get("shop_score", 0) / 5.0
            
            value_score = (1 - price_normalized) * 0.5 + sales_normalized * 0.3 + score * 0.2
            
            item["value_score"] = round(value_score, 3)
            
            if value_score >= 0.75 and item["price"] < (max_price + min_price) / 2:
                if "💰 性价比之选" not in item["tags"]:
                    item["tags"].append("💰 性价比之选")
            
            if item.get("sales", 0) >= 5000:
                if "🔥 热销爆款" not in item["tags"]:
                    item["tags"].append("🔥 热销爆款")
            
            if item.get("shop_score", 0) >= 4.9:
                if "⭐ 金牌店铺" not in item["tags"]:
                    item["tags"].append("⭐ 金牌店铺")
            
            if item["price"] <= min_price * 1.05:
                if "📍 价格最低" not in item["tags"]:
                    item["tags"].append("📍 价格最低")
        
        return data
    
    def _calc_stats(self, data: List[dict]) -> Dict[str, Any]:
        """计算统计数据"""
        if not data:
            return self._empty_stats()
        
        prices = sorted([item["price"] for item in data])
        sales = [item.get("sales", 0) for item in data]
        
        n = len(prices)
        price_stats = self._calc_price_stats(prices)
        
        platform_counts = {}
        for item in data:
            platform = item.get("platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        top_sales = sorted(data, key=lambda x: x.get("sales", 0), reverse=True)[:10]
        top_value = sorted(data, key=lambda x: x.get("value_score", 0), reverse=True)[:5]
        
        return {
            "total_count": n,
            "price_stats": {
                "min": price_stats.min,
                "max": price_stats.max,
                "avg": price_stats.avg,
                "median": price_stats.median,
                "q1": price_stats.q1,
                "q3": price_stats.q3
            },
            "sales_stats": {
                "total": sum(sales),
                "avg": sum(sales) / n if n > 0 else 0,
                "max": max(sales) if sales else 0
            },
            "platform_counts": platform_counts,
            "top_sales": top_sales,
            "top_value": top_value
        }
    
    def _calc_price_stats(self, prices: List[float]) -> PriceStats:
        """计算价格统计"""
        if not prices:
            return PriceStats(min=0, max=0, avg=0, median=0, q1=0, q3=0)
        
        n = len(prices)
        sorted_prices = sorted(prices)
        
        def percentile(data, p):
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if f < len(data) - 1 else f
            return data[f] + (k - f) * (data[c] - data[f])
        
        return PriceStats(
            min=sorted_prices[0],
            max=sorted_prices[-1],
            avg=sum(sorted_prices) / n,
            median=percentile(sorted_prices, 50),
            q1=percentile(sorted_prices, 25),
            q3=percentile(sorted_prices, 75)
        )
    
    def _empty_stats(self) -> Dict[str, Any]:
        """空统计数据"""
        return {
            "total_count": 0,
            "price_stats": {"min": 0, "max": 0, "avg": 0, "median": 0, "q1": 0, "q3": 0},
            "sales_stats": {"total": 0, "avg": 0, "max": 0},
            "platform_counts": {},
            "top_sales": [],
            "top_value": []
        }
    
    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        """生成摘要文本"""
        if stats.get("total_count", 0) == 0:
            return "暂无数据"
        
        price_stats = stats.get("price_stats", {})
        platform_counts = stats.get("platform_counts", {})
        
        summary = f"共采集 {stats['total_count']} 件商品，"
        summary += f"价格区间 ¥{price_stats.get('min', 0):.0f}-{price_stats.get('max', 0):.0f}，"
        summary += f"均价 ¥{price_stats.get('avg', 0):.0f}"
        
        if platform_counts:
            summary += f"，涉及 {len(platform_counts)} 个平台"
        
        return summary
    
    def export_json(self, data: List[dict]) -> str:
        """导出为JSON格式"""
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_csv(self, data: List[dict]) -> str:
        """导出为CSV格式"""
        if not data:
            return ""
        
        headers = ["名称", "价格", "销量", "店铺", "评分", "平台", "链接", "标签"]
        rows = []
        
        for item in data:
            rows.append([
                item.get("name", ""),
                str(item.get("price", "")),
                str(item.get("sales", "")),
                item.get("shop_name", ""),
                str(item.get("shop_score", "")),
                item.get("platform_name", ""),
                item.get("url", ""),
                "|".join(item.get("tags", []))
            ])
        
        csv_lines = [",".join(f'"{h}"' for h in headers)]
        for row in rows:
            csv_lines.append(",".join(f'"{cell}"' for cell in row))
        
        return "\n".join(csv_lines)
