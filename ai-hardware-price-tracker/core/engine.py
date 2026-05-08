"""
数据采集引擎
支持多平台并发采集
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from .base import MockCrawler, BaseCrawler


class CrawlerEngine:
    """采集引擎主控制器"""
    
    PLATFORMS = {
        "jd": {"name": "京东", "icon": "🟠"},
        "tb": {"name": "淘宝", "icon": "🟡"},
        "pdd": {"name": "拼多多", "icon": "🟢"},
        "demo": {"name": "示例数据", "icon": "🔬"}
    }
    
    def __init__(self, platforms: Optional[List[str]] = None):
        self.platforms = platforms or ["demo"]
        self.crawlers: Dict[str, BaseCrawler] = {}
        self._init_crawlers()
        self._progress_callback = None
    
    def _init_crawlers(self):
        """初始化采集器"""
        for platform in self.platforms:
            if platform == "demo":
                self.crawlers["demo"] = MockCrawler()
            elif platform == "jd":
                self.crawlers["jd"] = self._create_jd_crawler()
            elif platform == "tb":
                self.crawlers["tb"] = self._create_tb_crawler()
            elif platform == "pdd":
                self.crawlers["pdd"] = self._create_pdd_crawler()
    
    def _create_jd_crawler(self) -> BaseCrawler:
        """创建京东采集器"""
        return MockCrawler()
    
    def _create_tb_crawler(self) -> BaseCrawler:
        """创建淘宝采集器"""
        return MockCrawler()
    
    def _create_pdd_crawler(self) -> BaseCrawler:
        """创建拼多多采集器"""
        return MockCrawler()
    
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self._progress_callback = callback
    
    async def crawl(self, keyword: str, limit: int = 50) -> List[dict]:
        """并发采集所有平台"""
        if self._progress_callback:
            self._progress_callback({"status": "starting", "message": "开始采集..."})
        
        tasks = []
        for platform in self.platforms:
            if platform in self.crawlers:
                crawler = self.crawlers[platform]
                tasks.append(self._crawl_with_progress(platform, crawler, keyword, limit))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_data = []
        for result in results:
            if isinstance(result, list):
                all_data.extend(result)
            elif isinstance(result, Exception):
                print(f"采集错误: {result}")
        
        if self._progress_callback:
            self._progress_callback({
                "status": "completed",
                "message": f"采集完成，共获取 {len(all_data)} 条数据"
            })
        
        return all_data
    
    async def _crawl_with_progress(self, platform: str, crawler: BaseCrawler, 
                                   keyword: str, limit: int) -> List[dict]:
        """带进度报告的采集"""
        platform_info = self.PLATFORMS.get(platform, {"name": platform, "icon": "📦"})
        
        if self._progress_callback:
            self._progress_callback({
                "status": "crawling",
                "platform": platform,
                "message": f"正在采集 {platform_info['icon']} {platform_info['name']}..."
            })
        
        try:
            data = await crawler.search(keyword, limit)
            for item in data:
                item["platform"] = platform
                item["platform_icon"] = platform_info["icon"]
                item["platform_name"] = platform_info["name"]
            
            if self._progress_callback:
                self._progress_callback({
                    "status": "platform_completed",
                    "platform": platform,
                    "count": len(data),
                    "message": f"{platform_info['icon']} {platform_info['name']} 采集完成: {len(data)} 条"
                })
            
            return data
        except Exception as e:
            if self._progress_callback:
                self._progress_callback({
                    "status": "error",
                    "platform": platform,
                    "message": f"{platform_info['icon']} {platform_info['name']} 采集失败: {str(e)}"
                })
            return []
    
    def get_platform_info(self) -> Dict[str, Dict]:
        """获取平台信息"""
        return self.PLATFORMS


class CrawlerFactory:
    """采集器工厂"""
    
    @staticmethod
    def create(platform: str) -> BaseCrawler:
        """创建指定平台的采集器"""
        crawlers = {
            "jd": MockCrawler,
            "tb": MockCrawler,
            "pdd": MockCrawler,
            "demo": MockCrawler
        }
        
        crawler_class = crawlers.get(platform.lower())
        if crawler_class:
            crawler = crawler_class()
            crawler.PLATFORM_NAME = platform
            return crawler
        
        raise ValueError(f"不支持的平台: {platform}")
