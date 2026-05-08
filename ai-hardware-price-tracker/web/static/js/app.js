/**
 * PriceScout Frontend Application
 * AI硬件价格采集与对比工具
 */

class PriceScoutApp {
    constructor() {
        this.currentData = [];
        this.currentStats = null;
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadExampleData();
        this.initCharts();
    }
    
    bindEvents() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        document.getElementById('search-btn').addEventListener('click', () => this.handleSearch());
        
        document.getElementById('keyword-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSearch();
        });
        
        document.getElementById('sort-select').addEventListener('change', (e) => {
            this.handleSort(e.target.value);
        });
        
        document.getElementById('export-btn').addEventListener('click', () => this.handleExport());
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.toggle('active', tab.id === `${tabName}-tab`);
        });
        
        if (tabName === 'charts' && this.currentData.length > 0) {
            this.updateCharts();
        }
    }
    
    async loadExampleData() {
        try {
            this.showLoading();
            const response = await fetch('/api/example');
            const result = await response.json();
            
            if (result.success) {
                this.currentData = result.data;
                this.currentStats = result.stats;
                this.renderProducts();
                this.updateStats();
                this.updateCharts();
            }
        } catch (error) {
            console.error('加载示例数据失败:', error);
            this.showToast('加载示例数据失败', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async handleSearch() {
        const keyword = document.getElementById('keyword-input').value.trim();
        if (!keyword) {
            this.showToast('请输入搜索关键词', 'error');
            return;
        }
        
        const platforms = Array.from(document.querySelectorAll('.platform-select input:checked'))
            .map(cb => cb.value);
        
        if (platforms.length === 0) {
            this.showToast('请至少选择一个平台', 'error');
            return;
        }
        
        const limit = parseInt(document.getElementById('limit-select').value);
        
        this.showProgress('正在准备采集...');
        
        try {
            const response = await fetch('/api/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword, platforms, limit })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentData = result.data;
                this.currentStats = result.stats;
                this.renderProducts();
                this.updateStats();
                this.updateCharts();
                this.hideProgress();
                this.showToast(`成功获取 ${result.data.length} 条数据`, 'success');
                
                this.switchTab('search');
            } else {
                this.hideProgress();
                this.showToast(result.error || '采集失败', 'error');
            }
        } catch (error) {
            this.hideProgress();
            console.error('采集失败:', error);
            this.showToast('采集失败，请重试', 'error');
        }
    }
    
    renderProducts() {
        const grid = document.getElementById('products-grid');
        grid.innerHTML = '';
        
        if (this.currentData.length === 0) {
            grid.innerHTML = '<div class="loading-indicator"><span>暂无数据</span></div>';
            return;
        }
        
        this.currentData.forEach((product, index) => {
            const card = this.createProductCard(product, index);
            grid.appendChild(card);
        });
    }
    
    createProductCard(product, index) {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.style.animationDelay = `${index * 50}ms`;
        
        const platformIcon = this.getPlatformIcon(product.platform);
        
        const tagsHtml = product.tags.map(tag => {
            let className = '';
            if (tag.includes('性价比')) className = 'recommend';
            else if (tag.includes('热销')) className = 'hot';
            else if (tag.includes('金牌')) className = 'top';
            return `<span class="product-tag ${className}">${tag}</span>`;
        }).join('');
        
        card.innerHTML = `
            <div class="product-header">
                <div class="product-platform">
                    <span>${platformIcon}</span>
                    <span>${product.platform_name || product.platform}</span>
                </div>
                ${tagsHtml ? `<div class="product-tags">${tagsHtml}</div>` : ''}
            </div>
            <div class="product-name">${this.escapeHtml(product.name)}</div>
            <div class="product-info">
                <div class="product-info-item">
                    <span>📦</span>
                    <span>销量 ${product.sales.toLocaleString()}</span>
                </div>
                <div class="product-info-item">
                    <span>⭐</span>
                    <span>${product.shop_score}</span>
                </div>
            </div>
            <div class="product-price">¥${product.price.toLocaleString()}</div>
            <div class="product-shop">
                <span class="product-shop-name">${this.escapeHtml(product.shop_name)}</span>
                ${product.shop_score >= 4.8 ? '<span class="product-score"> ⭐金牌店铺</span>' : ''}
            </div>
            ${product.url ? `
                <a href="${product.url}" target="_blank" class="product-link">
                    <span>🔗</span> 查看详情
                </a>
            ` : ''}
        `;
        
        return card;
    }
    
    getPlatformIcon(platform) {
        const icons = { jd: '🟠', tb: '🟡', pdd: '🟢', demo: '🔬' };
        return icons[platform] || '📦';
    }
    
    updateStats() {
        if (!this.currentStats) return;
        
        document.getElementById('results-count').textContent = this.currentStats.total_count;
        
        const priceStats = this.currentStats.price_stats || {};
        document.getElementById('price-range').textContent = 
            `¥${(priceStats.min || 0).toLocaleString()} - ¥${(priceStats.max || 0).toLocaleString()}`;
    }
    
    handleSort(sortValue) {
        if (this.currentData.length === 0) return;
        
        const [sortBy, order] = sortValue.split('-');
        
        const sorted = [...this.currentData].sort((a, b) => {
            let aVal = a[sortBy] || 0;
            let bVal = b[sortBy] || 0;
            
            if (order === 'desc') {
                return bVal - aVal;
            }
            return aVal - bVal;
        });
        
        this.currentData = sorted;
        this.renderProducts();
    }
    
    async handleExport() {
        if (this.currentData.length === 0) {
            this.showToast('没有可导出的数据', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: this.currentData, format: 'json' })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const blob = new Blob([result.content], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `pricescout_export_${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
                this.showToast('导出成功', 'success');
            }
        } catch (error) {
            console.error('导出失败:', error);
            this.showToast('导出失败', 'error');
        }
    }
    
    initCharts() {
        this.charts = {
            priceDistribution: echarts.init(document.getElementById('price-distribution-chart')),
            salesRanking: echarts.init(document.getElementById('sales-ranking-chart')),
            platformDistribution: echarts.init(document.getElementById('platform-distribution-chart')),
            priceSales: echarts.init(document.getElementById('price-sales-chart'))
        };
        
        window.addEventListener('resize', () => {
            Object.values(this.charts).forEach(chart => chart.resize());
        });
    }
    
    updateCharts() {
        if (!this.currentData || this.currentData.length === 0) return;
        
        this.renderPriceDistributionChart();
        this.renderSalesRankingChart();
        this.renderPlatformDistributionChart();
        this.renderPriceSalesChart();
    }
    
    renderPriceDistributionChart() {
        const prices = this.currentData.map(p => p.price).sort((a, b) => a - b);
        
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(26, 35, 50, 0.95)',
                borderColor: '#334155',
                textStyle: { color: '#f8fafc' }
            },
            xAxis: {
                type: 'category',
                data: prices.map((_, i) => `#${i + 1}`),
                axisLine: { lineStyle: { color: '#334155' } },
                axisLabel: { color: '#64748b' }
            },
            yAxis: {
                type: 'value',
                name: '价格 (¥)',
                axisLine: { lineStyle: { color: '#334155' } },
                axisLabel: { color: '#64748b', formatter: v => `¥${(v/1000).toFixed(0)}k` },
                splitLine: { lineStyle: { color: '#1a2332' } }
            },
            series: [{
                type: 'bar',
                data: prices,
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#00d4ff' },
                        { offset: 1, color: '#7c3aed' }
                    ])
                },
                barWidth: '60%'
            }],
            grid: { left: '10%', right: '5%', bottom: '15%', top: '10%' }
        };
        
        this.charts.priceDistribution.setOption(option);
    }
    
    renderSalesRankingChart() {
        const topSales = [...this.currentData]
            .sort((a, b) => b.sales - a.sales)
            .slice(0, 10);
        
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(26, 35, 50, 0.95)',
                borderColor: '#334155',
                textStyle: { color: '#f8fafc' }
            },
            grid: { left: '3%', right: '5%', bottom: '3%', top: '3%', containLabel: true },
            xAxis: {
                type: 'value',
                axisLine: { lineStyle: { color: '#334155' } },
                axisLabel: { color: '#64748b' },
                splitLine: { lineStyle: { color: '#1a2332' } }
            },
            yAxis: {
                type: 'category',
                data: topSales.map(p => p.name.substring(0, 15) + '...'),
                axisLine: { lineStyle: { color: '#334155' } },
                axisLabel: { color: '#64748b', fontSize: 10 }
            },
            series: [{
                type: 'bar',
                data: topSales.map(p => p.sales),
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                        { offset: 0, color: '#f472b6' },
                        { offset: 1, color: '#00d4ff' }
                    ])
                },
                barWidth: '50%'
            }]
        };
        
        this.charts.salesRanking.setOption(option);
    }
    
    renderPlatformDistributionChart() {
        const counts = {};
        this.currentData.forEach(p => {
            const platform = p.platform_name || p.platform;
            counts[platform] = (counts[platform] || 0) + 1;
        });
        
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'item',
                backgroundColor: 'rgba(26, 35, 50, 0.95)',
                borderColor: '#334155',
                textStyle: { color: '#f8fafc' }
            },
            legend: {
                orient: 'vertical',
                right: '5%',
                top: 'center',
                textStyle: { color: '#94a3b8' }
            },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['40%', '50%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 8,
                    borderColor: '#1a2332',
                    borderWidth: 2
                },
                label: { show: false },
                emphasis: {
                    label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#f8fafc' }
                },
                data: Object.entries(counts).map(([name, value], i) => ({
                    value,
                    name,
                    itemStyle: {
                        color: ['#00d4ff', '#7c3aed', '#f472b6', '#10b981'][i % 4]
                    }
                }))
            }]
        };
        
        this.charts.platformDistribution.setOption(option);
    }
    
    renderPriceSalesChart() {
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'item',
                backgroundColor: 'rgba(26, 35, 50, 0.95)',
                borderColor: '#334155',
                textStyle: { color: '#f8fafc' },
                formatter: params => `${params.data.name}<br/>价格: ¥${params.data.price.toLocaleString()}<br/>销量: ${params.data.sales.toLocaleString()}`
            },
            xAxis: {
                type: 'value',
                name: '价格 (¥)',
                axisLine: { lineStyle: { color: '#334155' } },
                axisLabel: { color: '#64748b', formatter: v => `¥${(v/1000).toFixed(0)}k` },
                splitLine: { lineStyle: { color: '#1a2332' } }
            },
            yAxis: {
                type: 'value',
                name: '销量',
                axisLine: { lineStyle: { color: '#334155' } },
                axisLabel: { color: '#64748b', formatter: v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v },
                splitLine: { lineStyle: { color: '#1a2332' } }
            },
            series: [{
                type: 'scatter',
                symbolSize: data => Math.max(10, Math.min(40, Math.sqrt(data.sales) / 3)),
                data: this.currentData.map(p => ({
                    name: p.name.substring(0, 20),
                    value: [p.price, p.sales],
                    price: p.price,
                    sales: p.sales
                })),
                itemStyle: {
                    color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.5, [
                        { offset: 0, color: '#00d4ff' },
                        { offset: 1, color: '#7c3aed' }
                    ])
                }
            }],
            grid: { left: '10%', right: '5%', bottom: '10%', top: '10%' }
        };
        
        this.charts.priceSales.setOption(option);
    }
    
    showLoading() {
        document.getElementById('loading-indicator').classList.remove('hidden');
    }
    
    hideLoading() {
        document.getElementById('loading-indicator').classList.add('hidden');
    }
    
    showProgress(message) {
        const area = document.getElementById('progress-area');
        area.classList.remove('hidden');
        document.getElementById('progress-text').textContent = message;
        document.getElementById('progress-fill').style.width = '30%';
    }
    
    hideProgress() {
        document.getElementById('progress-area').classList.add('hidden');
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new PriceScoutApp();
});
