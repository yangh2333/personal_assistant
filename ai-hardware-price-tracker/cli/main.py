#!/usr/bin/env python3
"""
PriceScout CLI - AI硬件价格采集与对比工具命令行界面
"""

import asyncio
import json
import sys
from typing import Optional, List
import click
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import CrawlerEngine, DataProcessor, get_example_data, generate_sample_data


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def colorize(text: str, color: str) -> str:
    """添加颜色"""
    return f"{color}{text}{Colors.RESET}"


def print_banner():
    """打印横幅"""
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   {Colors.BOLD}🔍 PriceScout{Colors.RESET} {Colors.CYAN}- AI硬件价格采集与对比工具{Colors.RESET}              ║
║                                                              ║
║   {Colors.DIM}多平台比价 | 智能推荐 | 数据可视化{Colors.RESET}                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
    """
    print(banner)


def print_progress(progress_info: dict):
    """打印进度"""
    status = progress_info.get("status", "")
    message = progress_info.get("message", "")
    
    if status == "starting":
        print(f"\n{Colors.CYAN}▶ {message}{Colors.RESET}")
    elif status == "crawling":
        print(f"{Colors.YELLOW}  ◌ {message}{Colors.RESET}")
    elif status == "platform_completed":
        print(f"{Colors.GREEN}  ✓ {message}{Colors.RESET}")
    elif status == "completed":
        print(f"\n{Colors.GREEN}✓ {message}{Colors.RESET}")
    elif status == "error":
        print(f"{Colors.RED}  ✗ {message}{Colors.RESET}")


def print_product_card(product: dict, index: int):
    """打印商品卡片"""
    name = product.get("name", "未知商品")[:40]
    price = product.get("price", 0)
    sales = product.get("sales", 0)
    shop = product.get("shop_name", "未知店铺")[:20]
    score = product.get("shop_score", 0)
    platform = product.get("platform_icon", "📦")
    tags = product.get("tags", [])
    
    price_color = Colors.GREEN if price < 5000 else Colors.YELLOW if price < 20000 else Colors.RED
    
    tags_str = " ".join(tags) if tags else ""
    
    print(f"""
{Colors.CYAN}┌{'─' * 60}┐{Colors.RESET}
{Colors.CYAN}│{Colors.RESET} {index:2d}. {name:<54s} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}│{Colors.RESET}    💰 价格: {colorize(f'¥{price:,.2f}', price_color)}  "
          f"📦 销量: {Colors.YELLOW}{sales:,}{Colors.RESET}  ⭐ 评分: {score}  "
          f"{platform}  {Colors.DIM}{shop}{Colors.RESET}
{Colors.CYAN}│{Colors.RESET}    {tags_str:<54s} {Colors.CYAN}│{Colors.RESET}
{Colors.CYAN}└{'─' * 60}┘{Colors.RESET}
    """)


def print_stats(stats: dict):
    """打印统计信息"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}📊 数据统计{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")
    
    total = stats.get("total_count", 0)
    price_stats = stats.get("price_stats", {})
    
    print(f"  商品总数: {Colors.BOLD}{total}{Colors.RESET}")
    print(f"  价格区间: {Colors.GREEN}¥{price_stats.get('min', 0):,.0f}{Colors.RESET} - "
          f"{Colors.RED}¥{price_stats.get('max', 0):,.0f}{Colors.RESET}")
    print(f"  平均价格: {Colors.YELLOW}¥{price_stats.get('avg', 0):,.2f}{Colors.RESET}")
    print(f"  中位价格: {Colors.CYAN}¥{price_stats.get('median', 0):,.2f}{Colors.RESET}")
    
    platform_counts = stats.get("platform_counts", {})
    if platform_counts:
        print(f"\n  {Colors.BOLD}📍 平台分布:{Colors.RESET}")
        for platform, count in platform_counts.items():
            platform_info = {"jd": ("🟠 京东",), "tb": ("🟡 淘宝",), 
                           "pdd": ("🟢 拼多多",), "demo": ("🔬 示例",)}
            name = platform_info.get(platform, (platform,))[0]
            print(f"    {name}: {count} 件")


def print_recommendations(top_value: list):
    """打印推荐"""
    if not top_value:
        return
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}🎯 性价比推荐 TOP 5{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")
    
    for i, item in enumerate(top_value[:5], 1):
        name = item.get("name", "")[:35]
        price = item.get("price", 0)
        score = item.get("value_score", 0)
        print(f"  {i}. {name}")
        print(f"     💰 ¥{price:,.2f}  |  性价比指数: "
              f"{colorize(f'{score:.2f}', Colors.GREEN if score > 0.7 else Colors.YELLOW)}")


@click.group()
@click.version_option(version="1.0.0", prog_name="PriceScout")
def cli():
    """PriceScout - AI硬件价格采集与对比工具"""
    pass


@cli.command()
@click.option("-k", "--keyword", "-k", prompt="请输入搜索关键词", 
              help="搜索关键词，如: RTX 4090, A100, i9")
@click.option("-p", "--platforms", multiple=True, 
              type=click.Choice(["jd", "tb", "pdd", "demo"], case_sensitive=False),
              default=["demo"], help="选择采集平台")
@click.option("-l", "--limit", default=20, help="每个平台采集数量")
@click.option("-s", "--sort", "sort_by", type=click.Choice(["price", "sales", "score"]),
              default="price", help="排序方式")
@click.option("-o", "--order", type=click.Choice(["asc", "desc"]),
              default="asc", help="排序顺序")
@click.option("-o", "--output", "output_file", type=click.Path(), 
              default=None, help="输出文件路径")
@click.option("--no-demo/--use-demo", default=True, 
              help="是否使用演示数据")
def search(keyword: str, platforms: tuple, limit: int, sort_by: str, 
          order: str, output_file: Optional[str], no_demo: bool):
    """搜索并采集商品价格信息"""
    print_banner()
    
    print(f"{Colors.DIM}🔍 关键词: {Colors.RESET}{Colors.BOLD}{keyword}{Colors.RESET}")
    print(f"{Colors.DIM}📦 平台: {Colors.RESET}{', '.join(platforms)}")
    print(f"{Colors.DIM}📊 数量: {Colors.RESET}每平台 {limit} 条\n")
    
    engine = CrawlerEngine(list(platforms))
    engine.set_progress_callback(print_progress)
    
    processor = DataProcessor()
    
    try:
        raw_data = asyncio.run(engine.crawl(keyword, limit))
        
        if not raw_data:
            click.echo(f"{Colors.RED}⚠ 未获取到任何数据{Colors.RESET}")
            return
        
        result = processor.process(raw_data)
        sorted_data = processor.sort(result["data"], sort_by, order)
        
        click.echo(f"\n{Colors.BOLD}{'─' * 60}{Colors.RESET}")
        click.echo(f"{Colors.BOLD}📋 商品列表 (按{sort_by} {'升序' if order == 'asc' else '降序'}){Colors.RESET}\n")
        
        for i, product in enumerate(sorted_data, 1):
            print_product_card(product, i)
        
        print_stats(result["stats"])
        print_recommendations(result["stats"].get("top_value", []))
        
        if output_file:
            output_path = Path(output_file)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(sorted_data, f, ensure_ascii=False, indent=2)
            click.echo(f"\n{Colors.GREEN}✓ 数据已保存至: {output_file}{Colors.RESET}")
        
        click.echo(f"\n{Colors.DIM}💡 提示: 使用 --output 参数导出JSON格式数据{Colors.RESET}")
        
    except KeyboardInterrupt:
        click.echo(f"\n{Colors.YELLOW}⚠ 用户中断操作{Colors.RESET}")
    except Exception as e:
        click.echo(f"\n{Colors.RED}✗ 错误: {str(e)}{Colors.RESET}")


@cli.command()
@click.option("-o", "--output", type=click.Path(), 
              default="example_data.json", help="输出文件路径")
def example(output: str):
    """显示示例数据"""
    print_banner()
    
    click.echo(f"{Colors.BOLD}{Colors.CYAN}📦 加载示例数据...{Colors.RESET}\n")
    
    data = get_example_data()
    processor = DataProcessor()
    result = processor.process(data)
    sorted_data = processor.sort(result["data"], "price", "asc")
    
    for i, product in enumerate(sorted_data, 1):
        print_product_card(product, i)
    
    print_stats(result["stats"])
    print_recommendations(result["stats"].get("top_value", []))
    
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    click.echo(f"\n{Colors.GREEN}✓ 示例数据已保存至: {output}{Colors.RESET}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-s", "--sort", "sort_by", type=click.Choice(["price", "sales", "score"]),
              default="price", help="排序方式")
@click.option("-o", "--order", type=click.Choice(["asc", "desc"]),
              default="asc", help="排序顺序")
def analyze(input_file: str, sort_by: str, order: str):
    """分析本地JSON数据文件"""
    print_banner()
    
    click.echo(f"{Colors.BOLD}{Colors.CYAN}📂 加载数据文件: {input_file}{Colors.RESET}\n")
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        processor = DataProcessor()
        result = processor.process(data)
        sorted_data = processor.sort(result["data"], sort_by, order)
        
        click.echo(f"{Colors.GREEN}✓ 成功加载 {len(data)} 条数据{Colors.RESET}\n")
        
        for i, product in enumerate(sorted_data, 1):
            print_product_card(product, i)
        
        print_stats(result["stats"])
        
    except json.JSONDecodeError:
        click.echo(f"{Colors.RED}✗ 文件格式错误: 不是有效的JSON文件{Colors.RESET}")
    except Exception as e:
        click.echo(f"{Colors.RED}✗ 错误: {str(e)}{Colors.RESET}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-f", "--format", "export_format", 
              type=click.Choice(["json", "csv"]), default="csv", help="导出格式")
@click.option("-o", "--output", type=click.Path(), 
              default=None, help="输出文件路径")
def export(input_file: str, export_format: str, output: Optional[str]):
    """导出数据为指定格式"""
    print_banner()
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        processor = DataProcessor()
        
        if export_format == "json":
            content = processor.export_json(data)
            ext = "json"
        else:
            content = processor.export_csv(data)
            ext = "csv"
        
        output_path = Path(output) if output else Path(f"export_{Path(input_file).stem}.{ext}")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        click.echo(f"{Colors.GREEN}✓ 已导出为 {export_format.upper()} 格式: {output_path}{Colors.RESET}")
        
    except Exception as e:
        click.echo(f"{Colors.RED}✗ 导出失败: {str(e)}{Colors.RESET}")


@cli.command()
def platforms():
    """显示支持的平台列表"""
    print_banner()
    
    click.echo(f"{Colors.BOLD}📦 支持的电商平台{Colors.RESET}\n")
    
    platforms_info = [
        ("jd", "🟠 京东", "JD.com - 中国最大的自营电商平台"),
        ("tb", "🟡 淘宝", "Taobao.com - 阿里巴巴旗下C2C平台"),
        ("pdd", "🟢 拼多多", "Pinduoduo.com - 社交电商平台"),
        ("demo", "🔬 示例", "演示数据 - 用于功能演示和测试")
    ]
    
    for code, name, desc in platforms_info:
        click.echo(f"  {Colors.CYAN}{name}{Colors.RESET}")
        click.echo(f"    {Colors.DIM}{desc}{Colors.RESET}\n")


if __name__ == "__main__":
    cli()
