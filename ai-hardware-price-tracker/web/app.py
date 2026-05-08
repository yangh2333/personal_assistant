"""
PriceScout Web - Flask Web应用
"""

import asyncio
import json
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import CrawlerEngine, DataProcessor, get_example_data, get_example_stats

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["JSON_SORT_KEYS"] = False

processor = DataProcessor()


@app.route("/")
def index():
    """主页"""
    return render_template("index.html")


@app.route("/api/example")
def api_example():
    """获取示例数据"""
    data = get_example_data()
    result = processor.process(data)
    sorted_data = processor.sort(result["data"], "price", "asc")
    
    return jsonify({
        "success": True,
        "data": sorted_data,
        "stats": result["stats"],
        "summary": result["summary"]
    })


@app.route("/api/crawl", methods=["POST"])
def api_crawl():
    """采集数据API"""
    try:
        req_data = request.get_json()
        keyword = req_data.get("keyword", "RTX 4090")
        platforms = req_data.get("platforms", ["demo"])
        limit = req_data.get("limit", 20)
        
        if isinstance(platforms, str):
            platforms = [platforms]
        
        engine = CrawlerEngine(platforms)
        raw_data = asyncio.run(engine.crawl(keyword, limit))
        
        if not raw_data:
            return jsonify({
                "success": False,
                "error": "未获取到数据"
            })
        
        result = processor.process(raw_data)
        sorted_data = processor.sort(result["data"], "price", "asc")
        
        return jsonify({
            "success": True,
            "data": sorted_data,
            "stats": result["stats"],
            "summary": result["summary"]
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route("/api/sort", methods=["POST"])
def api_sort():
    """排序数据API"""
    try:
        req_data = request.get_json()
        data = req_data.get("data", [])
        sort_by = req_data.get("sort_by", "price")
        order = req_data.get("order", "asc")
        
        sorted_data = processor.sort(data, sort_by, order)
        
        return jsonify({
            "success": True,
            "data": sorted_data
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route("/api/export", methods=["POST"])
def api_export():
    """导出数据API"""
    try:
        req_data = request.get_json()
        data = req_data.get("data", [])
        export_format = req_data.get("format", "json")
        
        if export_format == "csv":
            content = processor.export_csv(data)
        else:
            content = processor.export_json(data)
        
        return jsonify({
            "success": True,
            "content": content,
            "format": export_format
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


def run_web(host="0.0.0.0", port=5000, debug=True):
    """运行Web服务"""
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web()
