# AI Infra硬件价格采集与对比工具 - 技术架构文档

## 1. 系统架构概览

### 1.1 整体架构设计
```
┌────────────────────────────────────────────────────────────────┐
│                        用户交互层                               │
│  ┌──────────────────┐         ┌──────────────────────────────┐│
│  │   CLI命令行工具   │         │       Web演示页面             ││
│  │   pricescout     │         │   React + ECharts + Vite    ││
│  └──────────────────┘         └──────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
                               │
┌────────────────────────────────────────────────────────────────┐
│                        业务逻辑层                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐│
│  │ 数据采集   │  │ 数据清洗   │  │ 数据分析   │  │ 可视化   ││
│  │ 调度器    │  │ 去重模块   │  │ 性价比    │  │ 图表生成 ││
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘│
└────────────────────────────────────────────────────────────────┘
                               │
┌────────────────────────────────────────────────────────────────┐
│                        平台适配层                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ 京东适配器  │  │ 淘宝适配器  │  │ 拼多多适配器│               │
│  │ JDSpider   │  │ TBSpider   │  │ PDDSpider  │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└────────────────────────────────────────────────────────────────┘
                               │
┌────────────────────────────────────────────────────────────────┐
│                        数据存储层                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ 原始数据   │  │ 清洗数据   │  │ 历史趋势   │               │
│  │ storage/  │  │ storage/   │  │ storage/   │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心模块设计

### 2.1 数据采集模块 (Scraper)

#### 2.1.1 抽象基类设计
```python
class BaseScraper(ABC):
    """平台采集器抽象基类"""
    
    def __init__(self, config: ScraperConfig):
        self.platform_name: str
        self.base_url: str
        self.headers: Dict[str, str]
        self.rate_limit: float  # 请求间隔(秒)
    
    @abstractmethod
    async def search(self, keyword: str, **kwargs) -> List[RawProduct]:
        """搜索商品"""
        pass
    
    @abstractmethod
    def parse_product(self, html: str) -> RawProduct:
        """解析商品详情页"""
        pass
    
    async def batch_scrape(self, keywords: List[str]) -> List[RawProduct]:
        """批量采集"""
        pass
```

#### 2.1.2 采集策略
| 策略项 | 说明 |
|--------|------|
| 并发控制 | 单平台最大并发3个请求 |
| 请求间隔 | 平台间随机延迟1-3秒 |
| 重试机制 | 失败自动重试3次，指数退避 |
| 反爬应对 | 随机User-Agent，代理池支持 |

### 2.2 数据清洗模块 (Processor)

#### 2.2.1 清洗流程
```
原始数据 → 字段标准化 → 去重处理 → 异常检测 → 格式化输出
```

#### 2.2.2 清洗规则
| 规则 | 处理方式 |
|------|----------|
| 价格清洗 | 提取数字，转换为float，标注货币单位 |
| 名称标准化 | 去除emoji、特殊字符，提取品牌+型号 |
| 销量统一 | 转换为统一单位(万)，保留2位小数 |
| 去重策略 | 商品ID > 名称相似度 > URL匹配 |

### 2.3 数据分析模块 (Analyzer)

#### 2.3.1 性价比指数计算
```
性价比指数 = (性能分 × 0.4 + 价格分 × 0.3 + 热度分 × 0.2 + 信誉分 × 0.1) × 100
```

| 评分维度 | 计算方式 | 权重 |
|----------|----------|------|
| 性能分 | 基于配置参数计算(显存/CUDA核心数等) | 40% |
| 价格分 | 基于价格分布计算(价格越低分数越高) | 30% |
| 热度分 | 基于销量和搜索量计算 | 20% |
| 信誉分 | 基于店铺评分计算 | 10% |

### 2.4 可视化模块 (Visualizer)

#### 2.4.1 图表类型
| 图表类型 | 用途 | 使用的库 |
|----------|------|----------|
| 价格趋势折线图 | 展示历史价格走势 | ECharts Line |
| 价格分布直方图 | 展示市场价格区间 | ECharts Bar |
| 性价比雷达图 | 多维度综合对比 | ECharts Radar |
| 竞品对比表格 | 详细参数横向对比 | 自定义Table |

---

## 3. 数据模型设计

### 3.1 核心数据模型
```python
@dataclass
class Product:
    """商品数据模型"""
    id: str                      # 唯一标识
    name: str                    # 商品名称(标准化)
    brand: str                   # 品牌
    model: str                   # 型号
    price: float                 # 价格(元)
    currency: str = "CNY"        # 货币单位
    sales_count: int             # 销量
    shop_score: float            # 店铺评分(0-5)
    shop_name: str               # 店铺名称
    platform: str                # 平台名称
    url: str                     # 商品链接
    specs: Dict[str, Any]        # 规格参数
    image_url: str               # 商品图片
    collected_at: datetime       # 采集时间

@dataclass
class PriceTrend:
    """价格趋势数据"""
    product_id: str
    price: float
    recorded_at: datetime

@dataclass
class ComparisonResult:
    """对比结果"""
    products: List[Product]
    recommendations: List[str]
    price_chart_data: Dict
    radar_data: Dict
```

---

## 4. CLI工具设计

### 4.1 命令行接口
```
pricescout [OPTIONS] COMMAND [ARGS]...

选项:
  --config PATH     配置文件路径
  --verbose         显示详细日志
  --debug           调试模式

命令:
  search    搜索商品
  compare   商品对比
  trend     价格趋势
  export    导出数据
```

### 4.2 search子命令
```
pricescout search [OPTIONS] KEYWORD

选项:
  --platforms       平台列表 (jd,taobao,pdd)
  --sort            排序方式 (price, sales, score)
  --order           排序顺序 (asc, desc)
  --limit           结果数量限制
  --output          输出格式 (table, csv, json)
  --save            保存到文件
```

### 4.3 compare子命令
```
pricescout compare [OPTIONS] PRODUCTS...

选项:
  --metrics         对比指标
  --chart           生成对比图表
  --output          输出路径
```

---

## 5. Web页面设计

### 5.1 页面结构
```
┌──────────────────────────────────────────────────────────────┐
│  Header: Logo + 标题 + 导航                                    │
├──────────────────────────────────────────────────────────────┤
│  Search Bar: 关键词输入 + 平台选择 + 搜索按钮                    │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐  ┌────────────────────────────┐ │
│  │   价格趋势图表 (ECharts) │  │   性价比TOP5 (卡片列表)      │ │
│  │   - 折线图展示价格走势   │  │   - 包含推荐标签             │ │
│  │   - 支持时间范围切换     │  │   - 显示关键参数             │ │
│  └─────────────────────────┘  └────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│  商品列表 (表格/卡片视图切换)                                   │
│  - 列: 商品信息 | 价格 | 销量 | 评分 | 操作                     │
│  - 支持排序、筛选、分页                                         │
├──────────────────────────────────────────────────────────────┤
│  对比区域 (可折叠)                                              │
│  - 已选商品列表                                                 │
│  - 参数对比表格                                                 │
│  - 雷达图对比                                                   │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 示例数据
页面初始化时展示AI硬件示例数据：
- GPU系列: RTX 4090, RTX 4080, A100, H100
- 存储设备: 企业级SSD, NAS存储
- 服务器: 整机服务器、工作站

---

## 6. 技术实现要点

### 6.1 异步采集架构
```python
import asyncio
import httpx

class AsyncScraper:
    """异步采集器"""
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(3)  # 控制并发数
    
    async def fetch(self, url: str) -> str:
        async with self.semaphore:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.text
    
    async def batch_search(self, keywords: List[str]) -> List[RawProduct]:
        tasks = [self.search(keyword) for keyword in keywords]
        return await asyncio.gather(*tasks)
```

### 6.2 数据缓存策略
| 数据类型 | 缓存策略 | TTL |
|----------|----------|-----|
| 搜索结果 | Redis/内存 | 30分钟 |
| 商品详情 | 内存缓存 | 1小时 |
| 价格趋势 | 持久化 | 长期 |

### 6.3 反爬应对策略
- 随机User-Agent轮换
- 请求间隔随机化
- Cookie池管理
- 代理IP池(可选)

---

## 7. 项目文件结构
```
pricescout/
├── pricescout.py              # CLI主程序
├── config.yaml                # 配置文件
├── requirements.txt           # Python依赖
├── models/
│   ├── __init__.py
│   ├── product.py            # 商品数据模型
│   └── trend.py              # 趋势数据模型
├── scrapers/
│   ├── __init__.py
│   ├── base.py               # 采集器基类
│   ├── jd_scraper.py         # 京东采集器
│   ├── tb_scraper.py         # 淘宝采集器
│   └── pdd_scraper.py        # 拼多多采集器
├── processors/
│   ├── __init__.py
│   ├── cleaner.py            # 数据清洗
│   ├── deduplicator.py       # 去重处理
│   └── analyzer.py           # 数据分析
├── storage/
│   ├── __init__.py
│   └── database.py           # 数据存储
└── web/
    ├── index.html            # Web页面
    ├── styles.css            # 样式文件
    ├── app.js                # 前端逻辑
    └── sample_data.json      # 示例数据
```

---

## 8. 依赖清单

### 8.1 Python依赖
| 包名 | 版本 | 用途 |
|------|------|------|
| click | ^8.1.0 | CLI框架 |
| httpx | ^0.25.0 | 异步HTTP客户端 |
| beautifulsoup4 | ^4.12.0 | HTML解析 |
| pandas | ^2.0.0 | 数据处理 |
| sqlalchemy | ^2.0.0 | 数据库ORM |
| aiofiles | ^23.0.0 | 异步文件操作 |
| pyyaml | ^6.0.0 | 配置文件解析 |

### 8.2 Web依赖
| 包名 | 版本 | 用途 |
|------|------|------|
| echarts | ^5.4.0 | 图表库 |
| vue | ^3.3.0 | 前端框架 |

---

## 9. 部署方案

### 9.1 Docker部署
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "pricescout.py", "--help"]
```

### 9.2 启动方式
```bash
# CLI模式
python pricescout.py search "RTX 4090" --platforms=jd

# Web模式
python -m http.server 8080  # 静态文件服务
```
