#!/usr/bin/env python3
"""
PriceScout AI - AI基础设施硬件价格采集与对比工具
命令行主程序
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from tabulate import tabulate

from models import Product
from scrapers import MockScraper, JDScraper, TBScraper, PDDSpider
from processors import DataCleaner, Deduplicator, Analyzer
from storage import Database, PriceDatabase


class PriceScoutCLI:
    """价格采集CLI工具"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.cleaner = DataCleaner()
        self.deduplicator = Deduplicator()
        self.analyzer = Analyzer()
        self.db = Database()
        self.price_db = PriceDatabase()
        self.scrapers = {}
    
    def _init_scrapers(self, platforms: List[str]):
        platform_map = {
            'jd': JDScraper,
            'jd.com': JDScraper,
            '京东': JDScraper,
            'taobao': TBScraper,
            'tb': TBScraper,
            'taobao': TBScraper,
            '淘宝': TBScraper,
            '天猫': TBScraper,
            'pdd': PDDSpider,
            'pinduoduo': PDDSpider,
            '拼多多': PDDSpider,
            'mock': MockScraper,
        }
        
        for platform in platforms:
            platform_lower = platform.lower()
            if platform_lower in platform_map:
                if platform_lower not in self.scrapers:
                    self.scrapers[platform_lower] = platform_map[platform_lower]()
    
    async def search(self, keyword: str, platforms: List[str] = None,
                    pages: int = 1, sort: str = 'price',
                    order: str = 'asc', limit: int = 50) -> dict:
        """搜索商品"""
        start_time = datetime.now()
        
        if platforms is None or not platforms:
            platforms = ['mock']
        
        self._init_scrapers(platforms)
        
        all_raw_products = []
        
        for platform_name, scraper in self.scrapers.items():
            try:
                async with scraper:
                    products = await scraper.search(keyword, page=1)
                    all_raw_products.extend(products)
                    if self.verbose:
                        click.echo(f"[{platform_name}] 采集到 {len(products)} 个商品")
            except Exception as e:
                if self.verbose:
                    click.echo(f"[{platform_name}] 采集失败: {e}")
        
        if self.verbose:
            click.echo(f"总计原始数据: {len(all_raw_products)} 条")
        
        cleaned_products = self.cleaner.clean(all_raw_products)
        if self.verbose:
            click.echo(f"清洗后数据: {len(cleaned_products)} 条")
        
        unique_products = self.deduplicator.deduplicate(cleaned_products)
        if self.verbose:
            click.echo(f"去重后数据: {len(unique_products)} 条")
        
        analyzed_products = self.analyzer.analyze(unique_products)
        
        sorted_products = self.analyzer.sort_products(analyzed_products, sort, order)
        
        result_products = sorted_products[:limit]
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'keyword': keyword,
            'platforms': list(self.scrapers.keys()),
            'products': result_products,
            'total_count': len(result_products),
            'search_time': search_time,
            'statistics': self.cleaner.get_statistics(result_products)
        }
    
    def compare(self, products: List[Product]) -> dict:
        """对比商品"""
        if len(products) < 2:
            click.echo("对比功能需要至少2个商品")
            return {}
        
        comparison = self.analyzer.compare_products(products)
        
        return comparison.to_dict()
    
    async def trend(self, keyword: str, days: int = 30) -> dict:
        """获取价格趋势"""
        search_result = await self.search(keyword, platforms=['mock'], limit=10)
        
        products = search_result.get('products', [])
        
        if not products:
            return {}
        
        trend_summary = self.analyzer.generate_mock_trends(products, days)
        
        self.price_db.save_trends(trend_summary)
        
        return trend_summary.to_dict()


def format_products_table(products: List[Product], limit: int = 20) -> str:
    """格式化商品表格"""
    if not products:
        return "没有找到商品"
    
    headers = ["序号", "商品名称", "价格", "销量", "评分", "店铺", "平台"]
    rows = []
    
    for i, p in enumerate(products[:limit], 1):
        name = p.name[:25] + '...' if len(p.name) > 25 else p.name
        price = f"¥{p.price:,.0f}"
        sales = f"{p.sales_count:,}" if p.sales_count else "N/A"
        score = f"{p.shop_score:.1f}" if p.shop_score else "N/A"
        shop = p.shop_name[:10] + '...' if len(p.shop_name) > 10 else p.shop_name
        platform = p.platform
        
        rows.append([i, name, price, sales, score, shop, platform])
    
    return tabulate(rows, headers=headers, tablefmt='grid')


def format_statistics(stats: dict) -> str:
    """格式化统计信息"""
    if not stats:
        return ""
    
    lines = []
    lines.append("\n📊 数据统计:")
    
    if 'total_count' in stats:
        lines.append(f"   总数量: {stats['total_count']} 个商品")
    
    if 'price_range' in stats:
        pr = stats['price_range']
        lines.append(f"   价格区间: ¥{pr['min']:,.0f} - ¥{pr['max']:,.0f}")
        lines.append(f"   平均价格: ¥{pr['avg']:,.0f}")
    
    if 'total_sales' in stats:
        lines.append(f"   总销量: {stats['total_sales']:,}")
    
    if 'avg_score' in stats and stats['avg_score'] > 0:
        lines.append(f"   平均评分: {stats['avg_score']:.2f}")
    
    if 'platform_distribution' in stats:
        lines.append("   平台分布:")
        for platform, count in stats['platform_distribution'].items():
            lines.append(f"     - {platform}: {count}")
    
    if 'brand_distribution' in stats:
        lines.append("   品牌分布:")
        for brand, count in stats['brand_distribution'].items():
            lines.append(f"     - {brand}: {count}")
    
    return '\n'.join(lines)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='显示详细日志')
@click.option('--config', type=click.Path(exists=True), help='配置文件路径')
@click.pass_context
def cli(ctx, verbose, config):
    """PriceScout AI - AI基础设施硬件价格采集与对比工具"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    ctx.obj['scout'] = PriceScoutCLI(verbose=verbose)


@cli.command()
@click.argument('keyword')
@click.option('--platforms', '-p', multiple=True, 
              type=click.Choice(['jd', 'taobao', 'pdd', 'mock']),
              help='指定采集平台')
@click.option('--pages', type=int, default=1, help='采集页数')
@click.option('--sort', '-s', type=click.Choice(['price', 'sales', 'score', 'shop_score']),
              default='price', help='排序方式')
@click.option('--order', '-o', type=click.Choice(['asc', 'desc']),
              default='asc', help='排序顺序')
@click.option('--limit', '-l', type=int, default=50, help='结果数量限制')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
@click.option('--format', '-f', type=click.Choice(['table', 'csv', 'json']),
              default='table', help='输出格式')
@click.pass_context
def search(ctx, keyword, platforms, pages, sort, order, limit, output, format):
    """搜索商品
    
    示例:
    
    \b
    $ pricescout search "RTX 4090"
    $ pricescout search "A100" --platforms jd taobao --sort price --order asc
    $ pricescout search "SSD" --limit 20 --output results.csv
    """
    scout: PriceScoutCLI = ctx.obj['scout']
    
    click.echo(f"\n🔍 正在搜索: {keyword}")
    if platforms:
        click.echo(f"   平台: {', '.join(platforms)}")
    click.echo(f"   排序: {sort} ({order})")
    click.echo("")
    
    platform_list = list(platforms) if platforms else ['mock']
    
    result = asyncio.run(scout.search(
        keyword=keyword,
        platforms=platform_list,
        pages=pages,
        sort=sort,
        order=order,
        limit=limit
    ))
    
    products = result.get('products', [])
    
    if format == 'table':
        click.echo(format_products_table(products, limit))
    elif format == 'json':
        output_data = {
            'keyword': keyword,
            'total_count': result['total_count'],
            'search_time': result['search_time'],
            'statistics': result['statistics'],
            'products': [p.to_dict() for p in products]
        }
        click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))
    elif format == 'csv':
        db = Database()
        csv_path = output or f"{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        saved_path = db.save_products(products, csv_path)
        click.echo(f"已保存到: {saved_path}")
    
    click.echo(format_statistics(result.get('statistics', {})))
    
    click.echo(f"\n⏱️  搜索完成, 耗时: {result['search_time']:.2f}秒")


@cli.command()
@click.argument('products_file', type=click.Path(exists=True))
@click.option('--limit', '-l', type=int, default=10, help='对比商品数量')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
@click.option('--chart', is_flag=True, help='生成对比图表数据')
@click.pass_context
def compare(ctx, products_file, limit, output, chart):
    """对比商品
    
    示例:
    
    \b
    $ pricescout compare results.csv --limit 5
    $ pricescout compare results.csv --chart --output comparison.json
    """
    scout: PriceScoutCLI = ctx.obj['scout']
    
    db = Database()
    products = db.load_products(products_file)
    
    if not products:
        click.echo("没有找到可对比的商品")
        return
    
    click.echo(f"\n📊 开始对比 {len(products)} 个商品...")
    
    comparison = scout.analyzer.compare_products(products[:limit])
    
    click.echo("\n" + "="*60)
    click.echo("📈 性价比推荐")
    click.echo("="*60)
    for rec in comparison.recommendations:
        click.echo(f"  {rec}")
    
    click.echo("\n" + "="*60)
    click.echo("📋 竞品对比表")
    click.echo("="*60)
    
    headers = ["商品名称", "价格", "销量", "店铺评分", "性价比指数"]
    rows = []
    for p in comparison.products:
        name = p.name[:20] + '...' if len(p.name) > 20 else p.name
        price = f"¥{p.price:,.0f}"
        sales = f"{p.sales_count:,}" if p.sales_count else "N/A"
        score = f"{p.shop_score:.1f}" if p.shop_score else "N/A"
        value_idx = f"{p.value_index:.1f}" if hasattr(p, 'value_index') else "N/A"
        rows.append([name, price, sales, score, value_idx])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    
    if chart:
        chart_data = {
            'price_chart': comparison.price_chart_data,
            'radar_chart': comparison.radar_data
        }
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(chart_data, f, ensure_ascii=False, indent=2)
            click.echo(f"\n图表数据已保存到: {output}")
        else:
            click.echo("\n图表数据:")
            click.echo(json.dumps(chart_data, ensure_ascii=False, indent=2))


@cli.command()
@click.argument('keyword')
@click.option('--days', '-d', type=int, default=30, help='历史天数')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
@click.pass_context
def trend(ctx, keyword, days, output):
    """查看价格趋势
    
    示例:
    
    \b
    $ pricescout trend "RTX 4090" --days 30
    $ pricescout trend "A100" --output trend_data.json
    """
    scout: PriceScoutCLI = ctx.obj['scout']
    
    click.echo(f"\n📈 正在获取 {keyword} 价格趋势 (最近 {days} 天)...")
    
    trend_data = asyncio.run(scout.trend(keyword, days))
    
    if not trend_data or not trend_data.get('trends'):
        click.echo("没有找到趋势数据")
        return
    
    click.echo("\n" + "="*60)
    click.echo(f"📊 {keyword} 价格走势")
    click.echo("="*60)
    
    for trend_item in trend_data['trends']:
        click.echo(f"\n🔹 {trend_item['product_name']} ({trend_item['platform']})")
        
        records = trend_item.get('records', [])
        if records:
            prices = [r['price'] for r in records]
            dates = [r['recorded_at'][:10] for r in records]
            
            click.echo(f"   价格区间: ¥{min(prices):,.0f} - ¥{max(prices):,.0f}")
            click.echo(f"   最新价格: ¥{prices[-1]:,.0f}")
            click.echo(f"   趋势变化: {((prices[-1] - prices[0]) / prices[0] * 100):+.1f}%")
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(trend_data, f, ensure_ascii=False, indent=2)
        click.echo(f"\n趋势数据已保存到: {output}")


@cli.command()
@click.argument('keyword')
@click.option('--platforms', '-p', multiple=True,
              type=click.Choice(['jd', 'taobao', 'pdd', 'mock']),
              help='指定采集平台')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
@click.option('--format', '-f', type=click.Choice(['csv', 'json']),
              default='json', help='导出格式')
@click.pass_context
def export(ctx, keyword, platforms, output, format):
    """导出商品数据
    
    示例:
    
    \b
    $ pricescout export "GPU" --output gpu_data.csv --format csv
    $ pricescout export "SSD" --format json
    """
    scout: PriceScoutCLI = ctx.obj['scout']
    
    click.echo(f"\n📦 正在导出 {keyword} 数据...")
    
    platform_list = list(platforms) if platforms else ['mock']
    
    result = asyncio.run(scout.search(
        keyword=keyword,
        platforms=platform_list,
        limit=100
    ))
    
    products = result.get('products', [])
    
    if not products:
        click.echo("没有找到可导出的数据")
        return
    
    export_path = output or f"{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
    
    db = Database()
    saved_path = db.save_products(products, export_path)
    
    click.echo(f"✅ 已导出 {len(products)} 个商品到: {saved_path}")


@cli.command()
@click.pass_context
def version(ctx):
    """显示版本信息"""
    click.echo("PriceScout AI v1.0.0")
    click.echo("AI基础设施硬件价格采集与对比工具")
    click.echo("")
    click.echo("支持的平台: 京东, 淘宝, 拼多多")


def main():
    """主入口"""
    cli(obj={})


if __name__ == '__main__':
    main()
