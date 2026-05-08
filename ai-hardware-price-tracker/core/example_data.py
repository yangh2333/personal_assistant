"""
示例数据
用于演示和默认展示
"""

from typing import List, Dict, Any
from datetime import datetime


def get_example_data() -> List[Dict[str, Any]]:
    """获取示例数据"""
    return [
        {
            "id": "demo_001",
            "name": "NVIDIA RTX 4090 24G 公版 显卡",
            "price": 12999.00,
            "sales": 8500,
            "shop_name": "NVIDIA官方旗舰店",
            "shop_score": 4.9,
            "platform": "jd",
            "platform_icon": "🟠",
            "platform_name": "京东",
            "url": "https://item.jd.com/100038046894.html",
            "image": "https://via.placeholder.com/200x200?text=RTX+4090",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["💰 性价比之选", "🔥 热销爆款", "⭐ 金牌店铺"],
            "value_score": 0.85
        },
        {
            "id": "demo_002",
            "name": "华硕 ROG STRIX RTX 4090 24G 电竞显卡",
            "price": 16999.00,
            "sales": 5200,
            "shop_name": "华硕ROG旗舰店",
            "shop_score": 4.9,
            "platform": "tb",
            "platform_icon": "🟡",
            "platform_name": "淘宝",
            "url": "https://item.taobao.com/item.htm?id=123456789",
            "image": "https://via.placeholder.com/200x200?text=ROG+4090",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["⭐ 金牌店铺"],
            "value_score": 0.65
        },
        {
            "id": "demo_003",
            "name": "NVIDIA RTX 4080 SUPER 16G 显卡",
            "price": 7999.00,
            "sales": 6200,
            "shop_name": "电脑配件专营店",
            "shop_score": 4.6,
            "platform": "pdd",
            "platform_icon": "🟢",
            "platform_name": "拼多多",
            "url": "https://youhui.pinduoduo.com/goods/12345",
            "image": "https://via.placeholder.com/200x200?text=RTX+4080S",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["💰 性价比之选", "🔥 热销爆款"],
            "value_score": 0.82
        },
        {
            "id": "demo_004",
            "name": "AMD RX 7900 XTX 24G 显卡",
            "price": 7899.00,
            "sales": 3800,
            "shop_name": "AMD官方旗舰店",
            "shop_score": 4.8,
            "platform": "jd",
            "platform_icon": "🟠",
            "platform_name": "京东",
            "url": "https://item.jd.com/100045678901.html",
            "image": "https://via.placeholder.com/200x200?text=RX+7900XTX",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["💰 性价比之选", "⭐ 金牌店铺"],
            "value_score": 0.88
        },
        {
            "id": "demo_005",
            "name": "NVIDIA RTX 4070 Ti SUPER 16G 显卡",
            "price": 5999.00,
            "sales": 9800,
            "shop_name": "京东自营旗舰店",
            "shop_score": 4.8,
            "platform": "jd",
            "platform_icon": "🟠",
            "platform_name": "京东",
            "url": "https://item.jd.com/100055555555.html",
            "image": "https://via.placeholder.com/200x200?text=RTX+4070TiS",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["🔥 热销爆款", "📍 价格最低"],
            "value_score": 0.91
        },
        {
            "id": "demo_006",
            "name": "NVIDIA A100 80GB PCIe 计算卡 AI加速器",
            "price": 89999.00,
            "sales": 450,
            "shop_name": "NVIDIA官方旗舰店",
            "shop_score": 4.9,
            "platform": "tb",
            "platform_icon": "🟡",
            "platform_name": "淘宝",
            "url": "https://item.taobao.com/item.htm?id=987654321",
            "image": "https://via.placeholder.com/200x200?text=A100",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["⭐ 金牌店铺"],
            "value_score": 0.55
        },
        {
            "id": "demo_007",
            "name": "Intel i9-14900K 24核 处理器",
            "price": 3899.00,
            "sales": 4200,
            "shop_name": "数码科技专营店",
            "shop_score": 4.7,
            "platform": "jd",
            "platform_icon": "🟠",
            "platform_name": "京东",
            "url": "https://item.jd.com/100066666666.html",
            "image": "https://via.placeholder.com/200x200?text=i9-14900K",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["💰 性价比之选"],
            "value_score": 0.78
        },
        {
            "id": "demo_008",
            "name": "AMD Ryzen 9 7950X3D 处理器",
            "price": 4199.00,
            "sales": 3100,
            "shop_name": "AMD官方旗舰店",
            "shop_score": 4.8,
            "platform": "pdd",
            "platform_icon": "🟢",
            "platform_name": "拼多多",
            "url": "https://youhui.pinduoduo.com/goods/67890",
            "image": "https://via.placeholder.com/200x200?text=R9-7950X3D",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["⭐ 金牌店铺"],
            "value_score": 0.72
        },
        {
            "id": "demo_009",
            "name": "三星 64GB DDR5 4800 服务器内存",
            "price": 2599.00,
            "sales": 1800,
            "shop_name": "正品保障旗舰店",
            "shop_score": 4.7,
            "platform": "jd",
            "platform_icon": "🟠",
            "platform_name": "京东",
            "url": "https://item.jd.com/100077777777.html",
            "image": "https://via.placeholder.com/200x200?text=DDR5+64G",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": [],
            "value_score": 0.68
        },
        {
            "id": "demo_010",
            "name": "长江存储 2TB NVMe SSD 固态硬盘",
            "price": 899.00,
            "sales": 12000,
            "shop_name": "厂家直销店",
            "shop_score": 4.5,
            "platform": "tb",
            "platform_icon": "🟡",
            "platform_name": "淘宝",
            "url": "https://item.taobao.com/item.htm?id=111222333",
            "image": "https://via.placeholder.com/200x200?text=NVMe+2TB",
            "crawl_time": "2024-01-15T10:30:00",
            "tags": ["🔥 热销爆款", "📍 价格最低", "💰 性价比之选"],
            "value_score": 0.95
        }
    ]


def generate_sample_data(keyword: str = "RTX 4090", count: int = 10) -> List[Dict[str, Any]]:
    """生成样例数据"""
    base_products = [
        {
            "name": "NVIDIA RTX 4090 24G 显卡",
            "price_range": (12000, 18000),
            "sales_range": (500, 10000)
        },
        {
            "name": "NVIDIA RTX 4080 SUPER 16G 显卡",
            "price_range": (7000, 11000),
            "sales_range": (300, 8000)
        },
        {
            "name": "AMD RX 7900 XTX 24G 显卡",
            "price_range": (7000, 10000),
            "sales_range": (200, 6000)
        }
    ]
    
    import random
    platforms = [
        {"platform": "jd", "icon": "🟠", "name": "京东"},
        {"platform": "tb", "icon": "🟡", "name": "淘宝"},
        {"platform": "pdd", "icon": "🟢", "name": "拼多多"}
    ]
    
    shops = [
        {"name": "官方旗舰店", "score": 4.9},
        {"name": "自营旗舰店", "score": 4.8},
        {"name": "授权专卖店", "score": 4.6},
        {"name": "科技专营店", "score": 4.5}
    ]
    
    result = []
    for i in range(min(count, len(base_products) * 3)):
        product = base_products[i % len(base_products)]
        platform = random.choice(platforms)
        shop = random.choice(shops)
        
        price = round(random.uniform(*product["price_range"]), 2)
        sales = random.randint(*product["sales_range"])
        
        item = {
            "id": f"sample_{i+1:03d}",
            "name": f"{product['name']} #{i+1}",
            "price": price,
            "sales": sales,
            "shop_name": f"{shop['name']}",
            "shop_score": shop["score"],
            "platform": platform["platform"],
            "platform_icon": platform["icon"],
            "platform_name": platform["name"],
            "url": f"https://example.com/product/{i+1}",
            "image": "",
            "crawl_time": datetime.now().isoformat(),
            "tags": [],
            "value_score": 0.0
        }
        
        if sales > 5000:
            item["tags"].append("🔥 热销爆款")
        if price < product["price_range"][0] * 1.1:
            item["tags"].append("💰 性价比之选")
        if shop["score"] >= 4.8:
            item["tags"].append("⭐ 金牌店铺")
        
        result.append(item)
    
    return result


def get_example_stats() -> Dict[str, Any]:
    """获取示例统计信息"""
    return {
        "total_count": 10,
        "price_stats": {
            "min": 899.00,
            "max": 89999.00,
            "avg": 18628.90,
            "median": 6949.00,
            "q1": 3899.00,
            "q3": 12999.00
        },
        "sales_stats": {
            "total": 53750,
            "avg": 5375,
            "max": 12000
        },
        "platform_counts": {
            "jd": 5,
            "tb": 3,
            "pdd": 2
        },
        "summary": "共采集 10 件商品，价格区间 ¥899-¥89999，均价 ¥18629，涉及 3 个平台"
    }
