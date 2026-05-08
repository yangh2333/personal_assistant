"""
PriceScout - AI硬件价格采集与对比工具
核心模块
"""

from .engine import CrawlerEngine
from .processor import DataProcessor
from .example_data import get_example_data, get_example_stats, generate_sample_data

__all__ = [
    "CrawlerEngine",
    "DataProcessor",
    "get_example_data",
    "get_example_stats",
    "generate_sample_data"
]
