# AI集群成本监控系统

## 项目简介

AI集群成本监控系统是一款面向AI基础设施建设的成本计算与监控工具，能够覆盖千卡、万卡、十万卡三种规模集群的全生命周期成本计算。

## 核心功能

- ✅ 多规模支持：千卡(1024卡)、万卡(10240卡)、十万卡(102400卡)
- ✅ 全组件成本：硬件、软件、运维三大类成本全覆盖
- ✅ 实时仪表盘：总成本、分项占比、趋势图表
- ✅ Excel导出：专业格式报表，包含多个工作表
- ✅ 集群配置：灵活配置GPU型号、部署方式、电价等参数

## 技术架构

- **后端**：Python Flask + SQLAlchemy + SQLite
- **前端**：Vue.js 3 + Element Plus + ECharts
- **部署**：支持单机部署和Docker部署

## 快速开始

### 环境要求

- Python 3.9+
- Ubuntu 20.04+ / CentOS 7+ / Debian 11+

### 安装依赖

```bash
cd ai_cost_monitor
pip install -r requirements.txt --break-system-packages
```

### 初始化数据库

```bash
python -c "from app import create_app, init_database; app = create_app(); init_database(app)"
```

### 启动服务

```bash
python run.py
```

访问 `http://localhost:5000` 查看应用。

## API接口

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/clusters | 获取集群配置列表 |
| POST | /api/calculate | 执行成本计算 |
| GET | /api/costs/summary | 获取成本汇总 |
| GET | /api/costs/breakdown | 获取成本分项 |
| GET | /api/costs/trend | 获取成本趋势 |
| GET | /api/cost-items | 获取成本项列表 |
| PUT | /api/cost-items/<id> | 更新成本项 |
| GET | /api/export/excel | 导出Excel |
| GET | /api/export/logs | 获取导出日志 |

## 成本计算模型

### 硬件成本

```
硬件成本 = Σ(单价 × 数量 × 年维保系数 × 分摊年数)
年维保系数 = 1 + (年维保费率 × 分摊年数)
```

### 电力成本

```
年电力成本 = 总功耗(KW) × 24 × 365 × 电价 × PUE
```

### 运维成本

```
总运维成本 = (人力成本 + 维保成本 + 网络成本) × 运营年数
```

## 预置成本项

### 硬件类

| 成本项 | 单价(元) | 维保率 |
|--------|----------|--------|
| NVIDIA H200 GPU | 220,000/张 | 10% |
| NVIDIA B200 GPU | 350,000/张 | 10% |
| DGX H200服务器 | 1,800,000/台 | 8% |
| InfiniBand交换机 | 150,000/台 | 10% |
| 全闪存存储阵列 | 2,000,000/套 | 8% |
| 液冷CDU系统 | 500,000/套 | 5% |
| UPS不间断电源 | 300,000/套 | 5% |

### 软件类

| 成本项 | 单价(元/年) |
|--------|-------------|
| NVIDIA AI Enterprise | 80,000/GPU |
| Kubernetes企业版 | 50,000/节点 |
| 监控告警系统 | 30,000/套 |
| 操作系统许可 | 5,000/节点 |

## 部署指南

### Systemd服务

创建 `/etc/systemd/system/ai-cost-monitor.service`:

```ini
[Unit]
Description=AI Cost Monitor Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai_cost_monitor
ExecStart=/opt/ai_cost_monitor/venv/bin/python run.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 许可证

MIT License
