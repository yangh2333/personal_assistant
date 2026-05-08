"""
采集器基类
定义统一的数据采集接口
"""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Any
import random


class BaseCrawler(ABC):
    """采集器抽象基类"""
    
    PLATFORM_NAME: str = ""
    PLATFORM_ICON: str = ""
    
    def __init__(self):
        self.session = None
        self._rate_limit_delay = 1.0
    
    @abstractmethod
    async def search(self, keyword: str, limit: int = 50) -> List[dict]:
        """搜索商品 - 子类必须实现"""
        pass
    
    def _create_product(self, item: Dict[str, Any]) -> dict:
        """创建标准化商品对象"""
        return {
            "id": item.get("id", self._generate_id(item)),
            "name": item.get("name", item.get("title", "")),
            "price": float(item.get("price", 0)),
            "sales": self._parse_sales(item.get("sales", item.get("sales_count", 0))),
            "shop_name": item.get("shop_name", item.get("shop", "")),
            "shop_score": float(item.get("shop_score", item.get("shop_rating", 0))),
            "platform": self.PLATFORM_NAME,
            "platform_icon": self.PLATFORM_ICON,
            "url": item.get("url", item.get("link", "")),
            "image": item.get("image", item.get("img", "")),
            "crawl_time": datetime.now().isoformat(),
            "tags": item.get("tags", [])
        }
    
    def _generate_id(self, item: Dict[str, Any]) -> str:
        """生成唯一ID"""
        unique_str = f"{self.PLATFORM_NAME}_{item.get('name', '')}_{item.get('price', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    
    def _parse_sales(self, sales: Any) -> int:
        """解析销量数据"""
        if isinstance(sales, int):
            return sales
        if isinstance(sales, str):
            sales = sales.strip()
            if "万" in sales:
                try:
                    return int(float(sales.replace("万", "")) * 10000)
                except:
                    return 0
            if "+" in sales:
                sales = sales.replace("+", "")
            try:
                return int(sales)
            except:
                return 0
        return 0
    
    async def _rate_limit(self):
        """限速控制"""
        await asyncio.sleep(self._rate_limit_delay)
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com"
        }


class MockCrawler(BaseCrawler):
    """模拟数据采集器 - 用于演示和测试"""
    
    PLATFORM_NAME = "demo"
    PLATFORM_ICON = "🔬"
    
    PRODUCT_TEMPLATES = [
        {"name": "NVIDIA RTX 4090 24G 显卡", "price_range": (12000, 18000), "category": "显卡"},
        {"name": "NVIDIA RTX 4080 SUPER 16G 显卡", "price_range": (8000, 12000), "category": "显卡"},
        {"name": "NVIDIA RTX 4070 Ti SUPER 16G 显卡", "price_range": (5500, 7500), "category": "显卡"},
        {"name": "NVIDIA RTX 4070 12G 显卡", "price_range": (3800, 5000), "category": "显卡"},
        {"name": "AMD RX 7900 XTX 24G 显卡", "price_range": (7000, 10000), "category": "显卡"},
        {"name": "AMD RX 7800 XT 16G 显卡", "price_range": (3500, 4800), "category": "显卡"},
        {"name": "NVIDIA A100 80GB PCIe 计算卡", "price_range": (80000, 120000), "category": "计算卡"},
        {"name": "NVIDIA H100 80GB HBM3 计算卡", "price_range": (200000, 300000), "category": "计算卡"},
        {"name": "NVIDIA L40 48G Ada生成式GPU", "price_range": (60000, 90000), "category": "计算卡"},
        {"name": "Intel Xeon Gold 6248R 处理器", "price_range": (18000, 25000), "category": "CPU"},
        {"name": "AMD EPYC 9654 96核处理器", "price_range": (60000, 90000), "category": "CPU"},
        {"name": "Intel i9-14900K 处理器", "price_range": (3500, 4500), "category": "CPU"},
        {"name": "AMD Ryzen 9 7950X3D 处理器", "price_range": (3800, 5000), "category": "CPU"},
        {"name": "三星 64GB DDR5 4800 服务器内存", "price_range": (2000, 3500), "category": "内存"},
        {"name": "三星 32GB DDR5 5600 内存条", "price_range": (600, 900), "category": "内存"},
        {"name": "长江存储 2TB NVMe SSD", "price_range": (800, 1200), "category": "存储"},
        {"name": "三星 2TB 990 Pro NVMe SSD", "price_range": (1200, 1800), "category": "存储"},
        {"name": "华硕 Z790 主板", "price_range": (2500, 4000), "category": "主板"},
        {"name": "海盗船 1000W 80+金牌电源", "price_range": (800, 1200), "category": "电源"},
        {"name": "NVIDIA Jetson AGX Orin 开发套件", "price_range": (8000, 12000), "category": "开发板"},
    ]
    
    SHOPS = [
        {"name": "NVIDIA官方旗舰店", "score": 4.9},
        {"name": "京东自营旗舰店", "score": 4.8},
        {"name": "华硕ROG旗舰店", "score": 4.9},
        {"name": "AMD官方旗舰店", "score": 4.8},
        {"name": "电脑配件专营店", "score": 4.5},
        {"name": "数码科技专营店", "score": 4.6},
        {"name": "正品保障旗舰店", "score": 4.7},
        {"name": "金牌卖家店铺", "score": 4.8},
        {"name": "七天无理由退换", "score": 4.6},
        {"name": "厂家直销店", "score": 4.4},
    ]
    
    async def search(self, keyword: str, limit: int = 50) -> List[dict]:
        """生成模拟数据"""
        await asyncio.sleep(0.5)
        
        matched_products = []
        keyword_lower = keyword.lower()
        
        for template in self.PRODUCT_TEMPLATES:
            if keyword_lower in template["name"].lower() or keyword_lower in template["category"].lower():
                for shop in random.sample(self.SHOPS, min(3, len(self.SHOPS))):
                    base_price = random.uniform(template["price_range"][0], template["price_range"][1])
                    sales = random.randint(100, 10000)
                    
                    item = {
                        "name": f"{template['name']} {random.choice(['『热卖中』', '『新品上架』', ''])}",
                        "price": round(base_price * random.uniform(0.9, 1.1), 2),
                        "sales": sales,
                        "shop_name": shop["name"],
                        "shop_score": shop["score"],
                        "url": f"https://demo.example.com/product/{hashlib.md5(template['name'].encode()).hexdigest()[:8]}",
                        "image": f"https://via.placeholder.com/200x200?text={template['category']}",
                        "tags": []
                    }
                    
                    if sales > 5000:
                        item["tags"].append("🔥 销量爆款")
                    if base_price < template["price_range"][0] * 1.05:
                        item["tags"].append("💰 限时特惠")
                    if shop["score"] >= 4.9:
                        item["tags"].append("⭐ 金牌店铺")
                    
                    matched_products.append(self._create_product(item))
        
        if not matched_products:
            for i in range(min(limit, 20)):
                template = random.choice(self.PRODUCT_TEMPLATES)
                base_price = random.uniform(template["price_range"][0], template["price_range"][1])
                item = {
                    "name": f"{template['name']} #{i+1}",
                    "price": round(base_price, 2),
                    "sales": random.randint(50, 5000),
                    "shop_name": random.choice(self.SHOPS)["name"],
                    "shop_score": round(random.uniform(4.0, 5.0), 1),
                    "url": f"https://demo.example.com/product/{i}",
                    "image": "",
                    "tags": []
                }
                matched_products.append(self._create_product(item))
        
        return matched_products[:limit]
