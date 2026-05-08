# AI硬件价格采集与对比工具 - 技术架构文档

## 1. 系统架构设计

### 1.1 整体架构图
```
┌─────────────────────────────────────────────────────────────────┐
│                        展示层 (Presentation)                     │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │  CLI Tool       │    │  Web Interface (Flask + Vue3)       │ │
│  │  (Click CLI)    │    │  - Search Input                      │ │
│  └────────┬────────┘    │  - Results Grid                     │ │
│           │              │  - Charts Panel                     │ │
│           │              └──────────────┬──────────────────────┘ │
└───────────┼─────────────────────────────┼──────────────────────┘
            │                             │
┌───────────┴─────────────────────────────┴───────────────────────┐
│                        服务层 (Service)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  DataService                                                  ││
│  │  - crawl(keyword, platforms)     采集入口                    ││
│  │  - process_data(raw_data)         数据处理                   ││
│  │  - analyze_data(data)             数据分析                   ││
│  │  - export_data(data, format)      数据导出                   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
            │
┌───────────┴─────────────────────────────────────────────────────┐
│                        采集层 (Crawler)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ JD Crawler  │ │ TB Crawler │ │ PDD Crawler │ │ Mock Data │ │
│  │ (API模式)   │ │ (API模式)   │ │ (API模式)   │ │ (演示用)  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
            │
┌───────────┴─────────────────────────────────────────────────────┐
│                        数据层 (Data)                             │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────────────────────┐ │
│  │ JSON Storage│ │ SQLite DB   │ │ In-Memory Cache            │ │
│  └─────────────┘ └─────────────┘ └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系
```
cli.py          # Click命令行入口
    └── core.engine        # 采集引擎
          ├── core.jd      # 京东采集器
          ├── core.tb      # 淘宝采集器  
          ├── core.pdd     # 拼多多采集器
          ├── core.mock    # 模拟数据生成器
          └── core.processor # 数据处理器

web/
    └── app.py             # Flask应用
          ├── api.py       # API路由
          └── web/         # Vue前端
```

---

## 2. 核心模块详细设计

### 2.1 采集引擎 (core/engine.py)

```python
class CrawlerEngine:
    """采集引擎主控制器"""
    
    def __init__(self, platforms: List[str]):
        self.platforms = platforms
        self.crawlers = self._init_crawlers()
    
    async def crawl(self, keyword: str, limit: int = 50) -> List[dict]:
        """异步并发采集"""
        tasks = [crawler.search(keyword, limit) for crawler in self.crawlers]
        results = await asyncio.gather(*tasks)
        return self._merge_results(results)
    
    def _merge_results(self, results: List[List[dict]]) -> List[dict]:
        """合并多平台结果"""
        all_data = []
        for platform_data in results:
            all_data.extend(platform_data)
        return all_data
```

### 2.2 采集器基类 (core/base.py)

```python
class BaseCrawler(ABC):
    """采集器抽象基类"""
    
    PLATFORM_NAME: str = ""
    BASE_URL: str = ""
    
    def __init__(self):
        self.session = None
    
    @abstractmethod
    async def search(self, keyword: str, limit: int) -> List[dict]:
        """搜索商品"""
        pass
    
    def _parse_response(self, response: dict) -> List[dict]:
        """解析响应数据"""
        pass
    
    def _create_product(self, item: dict) -> dict:
        """创建标准化商品对象"""
        return {
            "id": f"{self.PLATFORM_NAME}_{item.get('id', '')}",
            "name": item.get("title", ""),
            "price": float(item.get("price", 0)),
            "sales": self._parse_sales(item.get("sales", "0")),
            "shop_name": item.get("shop", {}).get("name", ""),
            "shop_score": float(item.get("shop", {}).get("score", 0)),
            "platform": self.PLATFORM_NAME,
            "url": item.get("url", ""),
            "crawl_time": datetime.now().isoformat(),
            "tags": []
        }
```

### 2.3 数据处理器 (core/processor.py)

```python
class DataProcessor:
    """数据处理器"""
    
    def clean(self, data: List[dict]) -> List[dict]:
        """数据清洗"""
        cleaned = []
        for item in data:
            if self._is_valid(item):
                item = self._normalize(item)
                cleaned.append(item)
        return cleaned
    
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
    
    def sort(self, data: List[dict], 
             sort_by: str = "price", 
             order: str = "asc") -> List[dict]:
        """排序"""
        return sorted(data, 
                     key=lambda x: x.get(sort_by, 0),
                     reverse=(order == "desc"))
    
    def analyze(self, data: List[dict]) -> dict:
        """数据分析"""
        return {
            "total_count": len(data),
            "price_stats": self._calc_price_stats(data),
            "top_sales": self._get_top_items(data, "sales", 10),
            "recommendations": self._get_recommendations(data)
        }
    
    def _get_recommendations(self, data: List[dict]) -> List[dict]:
        """性价比推荐算法"""
        for item in data:
            score = self._calc_value_score(item)
            if score > 0.8:
                item["tags"].append("性价比推荐")
            if item.get("sales", 0) > 5000:
                item["tags"].append("销量冠军")
            if item.get("shop_score", 0) >= 4.9:
                item["tags"].append("金牌店铺")
        return data
```

---

## 3. 数据可视化方案

### 3.1 图表类型

| 图表类型 | 用途 | 技术方案 |
|---------|------|---------|
| 价格分布箱线图 | 展示价格区间分布 | ECharts Boxplot |
| 销量对比柱状图 | Top10商品销量 | ECharts Bar |
| 平台占比饼图 | 各平台商品数量 | ECharts Pie |
| 价格趋势折线图 | 价格走势 | ECharts Line |
| 散点图 | 价格-销量关系 | ECharts Scatter |

### 3.2 可视化组件设计

```javascript
// 价格分布图配置
{
  type: 'boxplot',
  title: '价格分布',
  data: priceRanges,
  colors: ['#00d4ff', '#7c3aed', '#f472b6']
}
```

---

## 4. API设计

### 4.1 采集API
```
POST /api/crawl
Request: { keyword: string, platforms: string[], limit: number }
Response: { success: boolean, data: Product[], stats: Analysis }
```

### 4.2 数据导出API
```
GET /api/export?format=json|csv|excel
Request: { data: Product[] }
Response: File download
```

---

## 5. 项目文件结构

```
ai-hardware-price-tracker/
├── core/
│   ├── __init__.py
│   ├── engine.py       # 采集引擎
│   ├── base.py         # 基类定义
│   ├── jd.py           # 京东采集器
│   ├── tb.py           # 淘宝采集器
│   ├── pdd.py          # 拼多多采集器
│   ├── mock.py         # 模拟数据生成器
│   ├── processor.py    # 数据处理器
│   └── example_data.py # 示例数据
├── cli/
│   ├── __init__.py
│   └── main.py         # 命令行入口
├── web/
│   ├── app.py          # Flask应用
│   ├── templates/
│   │   └── index.html  # Vue应用入口
│   └── static/
│       ├── css/
│       └── js/
├── requirements.txt
├── SPEC.md
└── README.md
```
