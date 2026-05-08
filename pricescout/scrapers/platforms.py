from .base import BaseScraper, ScraperConfig, RawProduct
import urllib.parse


class JDScraper(BaseScraper):
    """京东商城采集器"""
    
    def __init__(self):
        super().__init__(ScraperConfig(
            platform_name='京东',
            base_url='https://www.jd.com',
            search_url='https://search.jd.com/Search',
            rate_limit=2.0,
            headers={
                'Referer': 'https://www.jd.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        ))
    
    def _build_search_url(self, keyword: str, page: int = 1, **kwargs) -> str:
        params = {
            'keyword': keyword,
            'enc': 'utf-8',
            'wq': keyword,
            'page': page,
            'click': '0',
        }
        return f"{self.config.search_url}?{urllib.parse.urlencode(params)}"
    
    def _parse_search_results(self, html: str) -> list:
        products = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.select('.gl-item')
            for item in items:
                try:
                    name_elem = item.select_one('.p-name em') or item.select_one('.p-name a')
                    price_elem = item.select_one('.p-price i') or item.select_one('.p-price strong i')
                    sales_elem = item.select_one('.p-commit a') or item.select_one('.p-commit strong')
                    shop_elem = item.select_one('.p-shop a') or item.select_one('.p-shop')
                    link_elem = item.select_one('.p-name a')
                    
                    if name_elem and price_elem:
                        name = name_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True)
                        
                        sales = '0'
                        if sales_elem:
                            sales_text = sales_elem.get_text(strip=True)
                            import re
                            sales_match = re.search(r'(\d+)', sales_text)
                            if sales_match:
                                sales = sales_match.group(1)
                        
                        shop = ''
                        if shop_elem:
                            shop = shop_elem.get_text(strip=True)
                        
                        url = ''
                        if link_elem:
                            href = link_elem.get('href', '')
                            url = href if href.startswith('http') else f'https:{href}'
                        
                        products.append(RawProduct(
                            raw_name=name,
                            raw_price=price_text,
                            raw_sales=sales,
                            raw_score='0',
                            shop_name=shop,
                            url=url,
                            platform='京东'
                        ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return products


class TBScraper(BaseScraper):
    """淘宝/天猫采集器"""
    
    def __init__(self):
        super().__init__(ScraperConfig(
            platform_name='淘宝',
            base_url='https://www.taobao.com',
            search_url='https://s.taobao.com/search',
            rate_limit=2.5,
            headers={
                'Referer': 'https://www.taobao.com/',
            }
        ))
    
    def _build_search_url(self, keyword: str, page: int = 1, **kwargs) -> str:
        params = {
            'q': keyword,
            'sort': kwargs.get('sort', 'sale-desc'),
            'pageSize': 44,
        }
        return f"{self.config.search_url}?{urllib.parse.urlencode(params)}"
    
    def _parse_search_results(self, html: str) -> list:
        products = []
        
        try:
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.select('.item')
            for item in items:
                try:
                    name_elem = item.select_one('.title') or item.select_one('a')
                    price_elem = item.select_one('.price')
                    sales_elem = item.select_one('.deal-cnt') or item.select_one('.sales')
                    shop_elem = item.select_one('.shop')
                    link_elem = item.select_one('a')
                    
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        name = re.sub(r'\s+', ' ', name)
                        
                        price = '0'
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'(\d+\.?\d*)', price_text)
                            if price_match:
                                price = price_match.group(1)
                        
                        sales = '0'
                        if sales_elem:
                            sales_text = sales_elem.get_text(strip=True)
                            sales_match = re.search(r'(\d+)', sales_text)
                            if sales_match:
                                sales = sales_match.group(1)
                        
                        shop = ''
                        if shop_elem:
                            shop = shop_elem.get_text(strip=True)
                        
                        url = ''
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href.startswith('//'):
                                url = f'https:{href}'
                            elif href.startswith('/'):
                                url = f'https://www.taobao.com{href}'
                            else:
                                url = href
                        
                        products.append(RawProduct(
                            raw_name=name,
                            raw_price=price,
                            raw_sales=sales,
                            raw_score='0',
                            shop_name=shop,
                            url=url,
                            platform='淘宝'
                        ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return products


class PDDSpider(BaseScraper):
    """拼多多采集器"""
    
    def __init__(self):
        super().__init__(ScraperConfig(
            platform_name='拼多多',
            base_url='https://www.pinduoduo.com',
            search_url='https://mobile.pinduoduo.com/search.html',
            rate_limit=1.5,
            headers={
                'Referer': 'https://www.pinduoduo.com/',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.0 NetType/WIFI Language/zh_CN',
            }
        ))
    
    def _build_search_url(self, keyword: str, page: int = 1, **kwargs) -> str:
        params = {
            'keyword': keyword,
            'page': page,
        }
        return f"{self.config.search_url}?{urllib.parse.urlencode(params)}"
    
    def _parse_search_results(self, html: str) -> list:
        products = []
        
        try:
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.select('.goods-item') or soup.select('.list-item')
            for item in items:
                try:
                    name_elem = item.select_one('.goods-name') or item.select_one('.title')
                    price_elem = item.select_one('.price') or item.select_one('.sale-price')
                    sales_elem = item.select_one('.sales') or item.select_one('.sales-count')
                    shop_elem = item.select_one('.mall-name') or item.select_one('.shop')
                    link_elem = item.select_one('a')
                    
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        
                        price = '0'
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'(\d+\.?\d*)', price_text)
                            if price_match:
                                price = price_match.group(1)
                        
                        sales = '0'
                        if sales_elem:
                            sales_text = sales_elem.get_text(strip=True)
                            sales_match = re.search(r'(\d+)', sales_text)
                            if sales_match:
                                sales = sales_match.group(1)
                        
                        shop = ''
                        if shop_elem:
                            shop = shop_elem.get_text(strip=True)
                        
                        url = ''
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href.startswith('/'):
                                url = f'https://mobile.pinduoduo.com{href}'
                            else:
                                url = href
                        
                        products.append(RawProduct(
                            raw_name=name,
                            raw_price=price,
                            raw_sales=sales,
                            raw_score='0',
                            shop_name=shop,
                            url=url,
                            platform='拼多多'
                        ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return products
