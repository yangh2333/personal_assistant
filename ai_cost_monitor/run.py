#!/usr/bin/env python3
"""
AI集群成本监控系统 - 应用启动入口
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, init_database

def main():
    """主入口函数"""
    # 创建Flask应用
    app = create_app()
    
    # 初始化数据库
    init_database(app)
    
    # 获取端口配置
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           AI集群成本监控系统 v1.0                         ║
╠═══════════════════════════════════════════════════════════╣
║  访问地址: http://0.0.0.0:{port}                          ║
║  API文档:   http://0.0.0.0:{port}/api                      ║
╠═══════════════════════════════════════════════════════════╣
║  集群规模选项:                                            ║
║    - 千卡集群 (1024 GPU)                                  ║
║    - 万卡集群 (10240 GPU)                                 ║
║    - 十万卡集群 (102400 GPU)                              ║
╠═══════════════════════════════════════════════════════════╣
║  预置成本项:                                              ║
║    - 硬件: NVIDIA H200/B200 GPU, DGX服务器, 网络设备      ║
║    - 软件: NVIDIA AI Enterprise, Kubernetes, 监控系统      ║
║    - 运维: 电力, 人力, 带宽成本                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 启动应用
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    main()
