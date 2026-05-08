from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import asyncio
import httpx
import random
import time
from bs4 import BeautifulSoup
import json


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


@dataclass
class ScraperConfig:
    platform_name: str
    base_url: str
    search_url: str
    rate_limit: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    headers: Dict[str, str] = field(default_factory=lambda: {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    })
    proxy: Optional[str] = None


@dataclass
class RawProduct:
    raw_name: str
    raw_price: str
    raw_sales: str
    raw_score: str
    shop_name: str
    url: str
    platform: str
    source: str = ""
    image_url: str = ""
    collected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'raw_name': self.raw_name,
            'raw_price': self.raw_price,
            'raw_sales': self.raw_sales,
            'raw_score': self.raw_score,
            'shop_name': self.shop_name,
            'url': self.url,
            'platform': self.platform,
            'source': self.source,
            'image_url': self.image_url,
            'collected_at': self.collected_at.isoformat()
        }


class BaseScraper(ABC):
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session: Optional[httpx.AsyncClient] = None
        self._request_count = 0
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        headers = self.config.headers.copy()
        headers['User-Agent'] = random.choice(USER_AGENTS)
        return headers
    
    async def _request(self, url: str, method: str = 'GET', **kwargs) -> Optional[str]:
        self._request_count += 1
        headers = self._get_headers()
        
        for attempt in range(self.config.max_retries):
            try:
                if method.upper() == 'GET':
                    response = await self.session.get(url, headers=headers, **kwargs)
                else:
                    response = await self.session.post(url, headers=headers, **kwargs)
                
                if response.status_code == 200:
                    await self._rate_limit()
                    return response.text
                elif response.status_code == 403:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                else:
                    await asyncio.sleep(random.uniform(1, 3))
                    continue
                    
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
                    continue
                else:
                    return None
        
        return None
    
    async def _rate_limit(self):
        delay = random.uniform(
            self.config.rate_limit * 0.5,
            self.config.rate_limit * 1.5
        )
        await asyncio.sleep(delay)
    
    async def search(self, keyword: str, page: int = 1, **kwargs) -> List[RawProduct]:
        url = self._build_search_url(keyword, page, **kwargs)
        html = await self._request(url)
        if html:
            return self._parse_search_results(html)
        return []
    
    @abstractmethod
    def _build_search_url(self, keyword: str, page: int, **kwargs) -> str:
        pass
    
    @abstractmethod
    def _parse_search_results(self, html: str) -> List[RawProduct]:
        pass
    
    async def batch_search(self, keywords: List[str], pages: int = 1) -> List[RawProduct]:
        all_products = []
        semaphore = asyncio.Semaphore(3)
        
        async def search_with_semaphore(keyword: str):
            async with semaphore:
                products = []
                for page in range(1, pages + 1):
                    page_products = await self.search(keyword, page)
                    products.extend(page_products)
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                return products
        
        tasks = [search_with_semaphore(kw) for kw in keywords]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
        
        return all_products


class MockScraper(BaseScraper):
    """模拟采集器 - 用于演示和测试"""
    
    def __init__(self):
        super().__init__(ScraperConfig(
            platform_name='mock',
            base_url='https://mock.example.com',
            search_url='https://mock.example.com/search'
        ))
        self._mock_data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            'RTX 4090': [
                {'name': 'NVIDIA RTX 4090 公版 24G显存 游戏显卡', 'price': 15999, 'sales': 2580, 'score': 4.9, 'shop': 'NVIDIA官方旗舰店', 'url': 'https://example.com/4090-1'},
                {'name': '华硕 ROG STRIX RTX 4090 24G 游戏显卡', 'price': 18999, 'sales': 1890, 'score': 4.8, 'shop': '华硕官方旗舰店', 'url': 'https://example.com/4090-2'},
                {'name': '七彩虹 iGame RTX 4090 Neptune 24G 水冷显卡', 'price': 17499, 'sales': 956, 'score': 4.9, 'shop': '七彩虹旗舰店', 'url': 'https://example.com/4090-3'},
                {'name': '影驰 RTX 4090 金属大师 24G OC 显卡', 'price': 16499, 'sales': 1230, 'score': 4.7, 'shop': '影驰官方旗舰店', 'url': 'https://example.com/4090-4'},
                {'name': '技嘉 AORUS RTX 4090 24G 超级雕 显卡', 'price': 17999, 'sales': 780, 'score': 4.8, 'shop': '技嘉官方旗舰店', 'url': 'https://example.com/4090-5'},
            ],
            'RTX 4080': [
                {'name': 'NVIDIA RTX 4080 公版 16G显存 性能显卡', 'price': 9499, 'sales': 3560, 'score': 4.9, 'shop': 'NVIDIA官方旗舰店', 'url': 'https://example.com/4080-1'},
                {'name': '华硕 TUF RTX 4080 16G 游戏显卡', 'price': 10599, 'sales': 2150, 'score': 4.8, 'shop': '华硕官方旗舰店', 'url': 'https://example.com/4080-2'},
                {'name': '微星 RTX 4080 16G SUPRIM X 超龙 显卡', 'price': 10999, 'sales': 1680, 'score': 4.9, 'shop': '微星官方旗舰店', 'url': 'https://example.com/4080-3'},
                {'name': '七彩虹 iGame RTX 4080 Ultra W 16G', 'price': 9999, 'sales': 2340, 'score': 4.7, 'shop': '七彩虹旗舰店', 'url': 'https://example.com/4080-4'},
            ],
            'A100': [
                {'name': 'NVIDIA A100 40G SXM 深度学习计算卡', 'price': 89999, 'sales': 156, 'score': 4.9, 'shop': 'NVIDIA官方旗舰店', 'url': 'https://example.com/a100-1'},
                {'name': 'NVIDIA A100 80G SXM 数据中心计算卡', 'price': 149999, 'sales': 89, 'score': 4.9, 'shop': '服务器专营店', 'url': 'https://example.com/a100-2'},
                {'name': 'A100 40G PCIE 计算加速卡 服务器用', 'price': 85999, 'sales': 234, 'score': 4.8, 'shop': '企业级硬件商城', 'url': 'https://example.com/a100-3'},
            ],
            'H100': [
                {'name': 'NVIDIA H100 80G SXM5 顶级计算卡', 'price': 299999, 'sales': 45, 'score': 5.0, 'shop': '官方旗舰店', 'url': 'https://example.com/h100-1'},
                {'name': 'H100 80G PCIE 计算加速服务器', 'price': 319999, 'sales': 28, 'score': 4.9, 'shop': '数据中心专营', 'url': 'https://example.com/h100-2'},
            ],
            '服务器': [
                {'name': '戴尔 PowerEdge R750 服务器 2U机架式', 'price': 45999, 'sales': 89, 'score': 4.8, 'shop': '戴尔官方旗舰店', 'url': 'https://example.com/server-1'},
                {'name': '华为 FusionServer Pro 2288H V5 服务器', 'price': 38999, 'sales': 156, 'score': 4.7, 'shop': '华为企业业务店', 'url': 'https://example.com/server-2'},
                {'name': '浪潮 NF5280M6 服务器 2U双路', 'price': 32999, 'sales': 234, 'score': 4.6, 'shop': '浪潮官方旗舰店', 'url': 'https://example.com/server-3'},
            ],
            'SSD': [
                {'name': '三星 990 PRO 2TB NVMe SSD 固态硬盘', 'price': 1599, 'sales': 8950, 'score': 4.9, 'shop': '三星存储旗舰店', 'url': 'https://example.com/ssd-1'},
                {'name': '西部数据 WD_BLACK SN850X 2TB SSD', 'price': 1399, 'sales': 6780, 'score': 4.8, 'shop': '西部数据官方店', 'url': 'https://example.com/ssd-2'},
                {'name': '致态 TiPro7000 2TB PCIE4.0 SSD', 'price': 999, 'sales': 4560, 'score': 4.7, 'shop': '致态官方旗舰店', 'url': 'https://example.com/ssd-3'},
            ],
        }
    
    def _match_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        keyword_lower = keyword.lower()
        results = []
        
        for kw, products in self._mock_data.items():
            if keyword_lower in kw.lower():
                results.extend(products)
        
        if not results:
            for products in self._mock_data.values():
                results.extend(products)
            results = results[:20]
        
        return results
    
    async def search(self, keyword: str, page: int = 1, **kwargs) -> List[RawProduct]:
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        matched = self._match_keyword(keyword)
        
        return [
            RawProduct(
                raw_name=p['name'],
                raw_price=str(p['price']),
                raw_sales=str(p['sales']),
                raw_score=str(p['score']),
                shop_name=p['shop'],
                url=p['url'],
                platform='模拟平台',
                source='mock'
            )
            for p in matched
        ]
    
    def _build_search_url(self, keyword: str, page: int, **kwargs) -> str:
        return f"https://mock.example.com/search?q={keyword}&page={page}"
    
    def _parse_search_results(self, html: str) -> List[RawProduct]:
        return []
