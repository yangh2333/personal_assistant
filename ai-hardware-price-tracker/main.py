#!/usr/bin/env python3
"""
PriceScout - AI硬件价格采集与对比工具

Usage:
    python main.py web      - 启动Web服务
    python main.py cli      - 启动命令行工具
    python main.py example  - 显示示例数据
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "web":
        from web.app import run_web
        print("🚀 启动 PriceScout Web 服务...")
        print("📍 访问地址: http://localhost:5000")
        run_web()
    
    elif command == "cli":
        from cli.main import cli
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        cli()
    
    elif command == "example":
        from core import get_example_data
        import json
        data = get_example_data()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
