import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin, urlparse
from duckduckgo_search import DDGS
import concurrent.futures
import threading
from typing import List, Dict, Optional, Set, Tuple
import json
import logging
from io import BytesIO
from PIL import Image
import csv
import os
import io

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8,fr;q=0.7,de;q=0.6,it;q=0.5,pt;q=0.4,ru;q=0.3,ja;q=0.2,ko;q=0.1,ar;q=0.1,hi;q=0.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        
        # Base global e-commerce sites and marketplaces
        self.global_ecommerce_domains = [
            # Major global platforms
            'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr', 'amazon.it', 'amazon.es', 
            'amazon.in', 'amazon.co.jp', 'amazon.com.au', 'amazon.ca', 'amazon.com.mx', 
            'amazon.com.br', 'amazon.ae', 'amazon.sa', 'amazon.sg', 'amazon.nl',
            'ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.fr', 'ebay.it', 'ebay.es', 
            'ebay.com.au', 'ebay.ca', 'ebay.in',
            'walmart.com', 'target.com', 'bestbuy.com', 'newegg.com', 'homedepot.com', 
            'lowes.com', 'costco.com', 'macys.com', 'kohls.com', 'wayfair.com',
            
            # European platforms
            'zalando.com', 'otto.de', 'cdiscount.com', 'fnac.com', 'mediamarkt.de', 
            'saturn.de', 'currys.co.uk', 'argos.co.uk', 'bol.com', 'coolblue.nl', 
            'allegro.pl', 'asos.com', 'next.co.uk', 'johnlewis.com', 'very.co.uk', 'tesco.com',
            
            # Asian platforms
            'flipkart.com', 'myntra.com', 'snapdeal.com', 'paytmmall.com', 'tatacliq.com',
            'ajio.com', 'nykaa.com', 'meesho.com', 'shopclues.com', 'croma.com',
            'rakuten.co.jp', 'yahoo.co.jp', 'taobao.com', 'tmall.com', 'jd.com',
            'alibaba.com', 'aliexpress.com', 'gmarket.co.kr', 'coupang.com', '11st.co.kr',
            'qoo10.com', 'lazada.com', 'shopee.com', 'tokopedia.com', 'bukalapak.com',
            
            # Middle East & Africa
            'noon.com', 'namshi.com', 'souq.com', 'wadi.com', 'jumia.com.ng', 'jumia.co.ke',
            'jumia.com.gh', 'jumia.co.za', 'takealot.com', 'konga.com',
            
            # Pakistani sites
            'pakwheels.com', 'olx.com.pk', 'daraz.pk', 'homeshopping.pk', 'telemart.pk',
            'ishopping.pk', 'mega.pk', 'symbios.pk', 'shophive.com', 'myshop.pk',
            
            # Latin America
            'mercadolibre.com', 'mercadolivre.com.br', 'americanas.com.br', 'casasbahia.com.br',
            'magazineluiza.com.br', 'liverpool.com.mx', 'falabella.com', 'ripley.com',
            
            # Other popular sites
            'etsy.com', 'overstock.com', 'wish.com', 'banggood.com', 'gearbest.com',
            'temu.com', 'shein.com', 'ikea.com', 'apple.com', 'samsung.com'
        ]
        
        # Load additional domains from CSV - this will be the main source
        self.csv_domains = []
        self._load_domains_from_csv()
        
        # Enhanced domain to region mapping
        self.domain_region_mapping = {
            # North America
            'amazon.com': 'us-en', 'walmart.com': 'us-en', 'target.com': 'us-en',
            'bestbuy.com': 'us-en', 'ebay.com': 'us-en', 'amazon.ca': 'ca-en',
            
            # Europe
            'amazon.co.uk': 'uk-en', 'ebay.co.uk': 'uk-en', 'amazon.de': 'de-de',
            'amazon.fr': 'fr-fr', 'amazon.it': 'it-it', 'amazon.es': 'es-es',
            'zalando.com': 'de-de', 'otto.de': 'de-de', 'allegro.pl': 'pl-pl',
            
            # South Asia
            'amazon.in': 'in-en', 'flipkart.com': 'in-en', 'myntra.com': 'in-en',
            'snapdeal.com': 'in-en', 'paytmmall.com': 'in-en', 'tatacliq.com': 'in-en',
            'pakwheels.com': 'pk-en', 'olx.com.pk': 'pk-en', 'daraz.pk': 'pk-en',
            
            # East Asia
            'amazon.co.jp': 'jp-jp', 'rakuten.co.jp': 'jp-jp', 'taobao.com': 'cn-zh',
            'tmall.com': 'cn-zh', 'jd.com': 'cn-zh', 'gmarket.co.kr': 'kr-kr',
            'coupang.com': 'kr-kr', 'lazada.com': 'sg-en', 'shopee.com': 'sg-en',
            
            # Middle East
            'amazon.ae': 'ae-en', 'noon.com': 'ae-en', 'namshi.com': 'ae-en',
            'souq.com': 'ae-en', 'dubizzle.com': 'ae-en',
            
            # Australia/Oceania
            'amazon.com.au': 'au-en', 'ebay.com.au': 'au-en', 'kogan.com': 'au-en',
            
            # Latin America
            'mercadolibre.com': 'mx-es', 'mercadolivre.com.br': 'br-pt',
            'amazon.com.mx': 'mx-es', 'amazon.com.br': 'br-pt'
        }
        
        # Simplified search regions for better performance
        self.search_regions = [
            'us-en', 'uk-en', 'de-de', 'fr-fr', 'es-es', 'it-it', 'nl-nl', 'ca-en',
            'in-en', 'pk-en', 'jp-jp', 'kr-kr', 'cn-zh', 'sg-en', 'au-en',
            'ae-en', 'sa-ar', 'br-pt', 'mx-es', 'ar-es'
        ]
        
        # Default settings - optimized for maximum results
        self.max_workers = 8  # Increased for more aggressive searching
        self.request_delay = (0.3, 0.8)  # Reduced delay for faster processing
        self.max_retries = 2
        self.timeout = 8
        self.search_timeout = 6
        self.image_fetch_timeout = 8
        self.max_image_size = (600, 600)
        self.image_quality = 80
        
        # Cache and progress tracking
        self.url_cache = set()
        self.progress_lock = threading.Lock()
        self.progress = {
            'search_completed': 0,
            'search_total': 0,
            'scrape_completed': 0,
            'scrape_total': 0,
            'status': 'idle',
            'message': '',
            'error': None
        }
        
        # Enhanced search methods - more aggressive approach
        self.search_methods = [
            self._search_with_ddgs_aggressive,
            self._search_with_csv_domains_comprehensive,
            self._search_with_major_sites_extensive,
            self._search_with_category_specific_sites,
            self._search_with_regional_variations,
            self._search_with_fallback_terms_extensive
        ]
        
    def _load_domains_from_csv(self):
        """Load additional domains from the provided CSV file"""
        try:
            csv_url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/global_ecommerce_domains_extended-tkAgUrtheYUbHJAxoo6imNFJsbmvKA.csv"
            response = requests.get(csv_url, timeout=15)
            if response.status_code == 200:
                csv_data = response.content.decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(csv_data))
                
                for row in csv_reader:
                    domain = row.get('Domain', '').strip()
                    if domain and domain not in self.global_ecommerce_domains:
                        self.csv_domains.append(domain)
                        self.global_ecommerce_domains.append(domain)
                        
                        # Add to region mapping if region info is available
                        region = row.get('Region', '').strip()
                        language_code = row.get('Language Code', '').strip()
                        if region and language_code and domain not in self.domain_region_mapping:
                            # Map region names to language codes
                            region_mapping = {
                                'North America': 'us-en',
                                'Europe': 'uk-en',
                                'South Asia': 'in-en',
                                'East Asia': 'jp-jp',
                                'Middle East': 'ae-en',
                                'Latin America': 'br-pt',
                                'Africa': 'za-en',
                                'Oceania': 'au-en'
                            }
                            mapped_region = region_mapping.get(region, language_code.lower())
                            self.domain_region_mapping[domain] = mapped_region
                
                logger.info(f"Loaded {len(self.csv_domains)} additional domains from CSV (Total: {len(self.global_ecommerce_domains)})")
                
        except Exception as e:
            logger.warning(f"Could not load additional domains from CSV: {e}")
    
    def get_progress(self):
        """Get current progress information"""
        with self.progress_lock:
            return self.progress.copy()
    
    def update_progress(self, **kwargs):
        """Update progress information"""
        with self.progress_lock:
            for key, value in kwargs.items():
                if key in self.progress:
                    self.progress[key] = value
    
    def search_products_multi_region(self, query: str, category: str = 'general', max_results: int = 100, 
                                     regions: List[str] = None, progress_callback=None) -> List[Dict]:
        """Enhanced search with multiple aggressive methods to reach max_results"""
        logger.info(f"Starting aggressive search for: '{query}' with target: {max_results} results")
        
        self.update_progress(
            status='searching',
            message=f"Searching for '{query}' - Target: {max_results} results",
            search_total=max_results,
            search_completed=0
        )
        
        all_results = []
        seen_urls = set()
        
        # Calculate results needed per method
        results_per_method = max(50, max_results // len(self.search_methods))
        
        # Try all search methods aggressively
        for method_index, search_method in enumerate(self.search_methods):
            if len(all_results) >= max_results:
                break
                
            try:
                self.update_progress(
                    message=f"Method {method_index + 1}/{len(self.search_methods)}: {search_method.__name__}..."
                )
                
                needed_results = max_results - len(all_results)
                method_results = search_method(query, category, min(results_per_method, needed_results))
                
                # Add only unique results
                new_results = 0
                for result in method_results:
                    if result['url'] not in seen_urls:
                        seen_urls.add(result['url'])
                        all_results.append(result)
                        new_results += 1
                
                logger.info(f"Method {method_index + 1} ({search_method.__name__}) found {new_results} new results (Total: {len(all_results)})")
                
                self.update_progress(
                    search_completed=len(all_results),
                    message=f"Found {len(all_results)}/{max_results} results..."
                )
                
                if progress_callback:
                    progress_callback(self.get_progress())
                
                # Small delay between methods
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in search method {method_index + 1}: {e}")
                continue
        
        # If still not enough results, try intensive variations
        if len(all_results) < max_results * 0.8:  # If less than 80% of target
            logger.info(f"Only found {len(all_results)}/{max_results} results. Trying intensive search...")
            self.update_progress(
                message=f"Intensive search: {len(all_results)}/{max_results} found, trying more variations..."
            )
            
            intensive_results = self._intensive_search_variations(query, category, max_results - len(all_results), seen_urls)
            all_results.extend(intensive_results)
        
        self.update_progress(
            status='search_complete',
            message=f"Search complete. Found {len(all_results)} results."
        )
        
        logger.info(f"Final search results: {len(all_results)} products found")
        return all_results[:max_results]
    
    def _search_with_ddgs_aggressive(self, query: str, category: str, max_results: int) -> List[Dict]:
        """Aggressive DuckDuckGo search with many variations"""
        results = []
        
        # More comprehensive query variations
        query_variations = [
            query,
            f"{query} buy online",
            f"{query} shop",
            f"{query} price",
            f"{query} store",
            f"{query} market",
            f"{query} sale",
            f"buy {query}",
            f"shop {query}",
            f"{query} deals",
            f"{query} offers",
            f"best {query}",
            f"{query} review",
            f"{query} amazon",
            f"{query} walmart",
            f"{query} ebay",
            f"{query} online",
            f"{query} cheap",
            f"{query} discount",
            f"{query} compare",
            f"{query} best price",
            f'"{query}" buy',
            f'"{query}" shop',
            f'"{query}" price',
            f"{query} for sale",
            f"{query} marketplace",
            f"{query} shopping",
            f"{query} purchase",
            f"{query} order online"
        ]
        
        # Use more variations based on max_results
        variations_to_use = min(len(query_variations), max(8, max_results // 20))
        
        for variation in query_variations[:variations_to_use]:
            if len(results) >= max_results:
                break
                
            try:
                logger.info(f"DuckDuckGo search: '{variation}'")
                
                ddgs = DDGS()
                # Increase results per query
                results_per_query = min(30, max_results - len(results))
                search_results = ddgs.text(
                    variation,
                    max_results=results_per_query,
                    timeout=4
                )
                
                for result in search_results:
                    url = result.get('href', '')
                    title = result.get('title', '')
                    snippet = result.get('body', '')
                    
                    if self._is_relevant_result(url, title, snippet):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'region': 'global',
                            'source': 'ddgs'
                        })
                        
                        if len(results) >= max_results:
                            break
                
                # Shorter delay for more aggressive searching
                time.sleep(0.3)
                
            except Exception as e:
                logger.warning(f"DuckDuckGo search failed for '{variation}': {e}")
                continue
        
        return results
    
    def _search_with_csv_domains_comprehensive(self, query: str, category: str, max_results: int) -> List[Dict]:
        """Comprehensive search using all CSV domains"""
        results = []
        
        # Use a large subset of CSV domains
        domains_to_use = self.csv_domains[:min(200, max_results)]  # Use up to 200 domains
        
        # Common search URL patterns
        search_patterns = [
            'https://www.{}/search?q={}',
            'https://www.{}/s?k={}',
            'https://www.{}/search?query={}',
            'https://www.{}/search?term={}',
            'https://www.{}/search?keyword={}',
            'https://www.{}/products/search?q={}',
            'https://www.{}/shop/search?q={}',
            'https://www.{}/catalog/search?q={}',
            'https://{}/search?q={}',
            'https://{}/s?k={}',
            'https://{}/search?query={}',
        ]
        
        clean_query = re.sub(r'[^\w\s-]', '', query).replace(' ', '+')
        
        for domain in domains_to_use:
            if len(results) >= max_results:
                break
                
            try:
                # Try multiple search patterns for each domain
                for pattern in search_patterns[:3]:  # Use first 3 patterns
                    if len(results) >= max_results:
                        break
                        
                    try:
                        url = pattern.format(domain, clean_query)
                        
                        results.append({
                            'title': f"{query} - {domain}",
                            'url': url,
                            'snippet': f"Search results for {query} on {domain}",
                            'region': self.domain_region_mapping.get(domain, 'international'),
                            'source': 'csv_domains'
                        })
                        
                    except Exception:
                        continue
                        
            except Exception as e:
                continue
        
        return results
    
    def _search_with_major_sites_extensive(self, query: str, category: str, max_results: int) -> List[Dict]:
        """Extensive search on major e-commerce sites with multiple patterns"""
        results = []
        
        # Expanded major sites with their search patterns
        major_sites = {
            'amazon.com': [
                'https://www.amazon.com/s?k={}',
                'https://www.amazon.com/s?field-keywords={}',
                'https://www.amazon.com/gp/search?keywords={}'
            ],
            'ebay.com': [
                'https://www.ebay.com/sch/i.html?_nkw={}',
                'https://www.ebay.com/sch/{}',
                'https://www.ebay.com/itm/{}'
            ],
            'walmart.com': [
                'https://www.walmart.com/search?q={}',
                'https://www.walmart.com/search/?query={}',
                'https://www.walmart.com/browse/{}?cat_id=0'
            ],
            'target.com': [
                'https://www.target.com/s?searchTerm={}',
                'https://www.target.com/s/{}',
                'https://www.target.com/c/{}'
            ],
            'bestbuy.com': [
                'https://www.bestbuy.com/site/searchpage.jsp?st={}',
                'https://www.bestbuy.com/site/search?st={}',
                'https://www.bestbuy.com/site/shop/{}'
            ],
            'flipkart.com': [
                'https://www.flipkart.com/search?q={}',
                'https://www.flipkart.com/search?query={}',
                'https://www.flipkart.com/{}/pr'
            ],
            'amazon.in': [
                'https://www.amazon.in/s?k={}',
                'https://www.amazon.in/s?field-keywords={}',
                'https://www.amazon.in/gp/search?keywords={}'
            ],
            'amazon.co.uk': [
                'https://www.amazon.co.uk/s?k={}',
                'https://www.amazon.co.uk/s?field-keywords={}',
                'https://www.amazon.co.uk/gp/search?keywords={}'
            ],
            'amazon.de': [
                'https://www.amazon.de/s?k={}',
                'https://www.amazon.de/s?field-keywords={}',
                'https://www.amazon.de/gp/search?keywords={}'
            ],
            'noon.com': [
                'https://www.noon.com/uae-en/search?q={}',
                'https://www.noon.com/uae-en/search/?q={}',
                'https://www.noon.com/egypt-en/search?q={}'
            ],
            'pakwheels.com': [
                'https://www.pakwheels.com/used-cars/search/-/mk_{}/',
                'https://www.pakwheels.com/new-cars/{}/',
                'https://www.pakwheels.com/bikes/search/-/mk_{}/'
            ],
            'daraz.pk': [
                'https://www.daraz.pk/catalog/?q={}',
                'https://www.daraz.pk/products/{}/',
                'https://www.daraz.pk/search/?q={}'
            ],
            'aliexpress.com': [
                'https://www.aliexpress.com/wholesale?SearchText={}',
                'https://www.aliexpress.com/af/{}.html',
                'https://www.aliexpress.com/category/0/search?SearchText={}'
            ],
            'shopee.com': [
                'https://shopee.com/search?keyword={}',
                'https://shopee.sg/search?keyword={}',
                'https://shopee.ph/search?keyword={}'
            ],
            'lazada.com': [
                'https://www.lazada.com/catalog/?q={}',
                'https://www.lazada.sg/catalog/?q={}',
                'https://www.lazada.com.my/catalog/?q={}'
            ]
        }
        
        clean_query = re.sub(r'[^\w\s-]', '', query).replace(' ', '+')
        
        for site, patterns in major_sites.items():
            if len(results) >= max_results:
                break
                
            for pattern in patterns:
                if len(results) >= max_results:
                    break
                    
                try:
                    url = pattern.format(clean_query)
                    
                    results.append({
                        'title': f"{query} - {site}",
                        'url': url,
                        'snippet': f"Search results for {query} on {site}",
                        'region': self.domain_region_mapping.get(site, 'global'),
                        'source': 'major_sites'
                    })
                    
                except Exception:
                    continue
        
        return results
    
    def _search_with_category_specific_sites(self, query: str, category: str, max_results: int) -> List[Dict]:
        """Search category-specific sites"""
        results = []
        
        # Category-specific sites
        category_sites = {
            'automotive': [
                'autotrader.com', 'cars.com', 'cargurus.com', 'carmax.com', 'vroom.com',
                'autotrader.co.uk', 'motors.co.uk', 'mobile.de', 'autoscout24.com',
                'cardekho.com', 'carwale.com', 'zigwheels.com', 'pakwheels.com',
                'dubizzle.com', 'yallamotor.com', 'hatla2ee.com'
            ],
            'technology': [
                'newegg.com', 'bestbuy.com', 'bhphotovideo.com', 'adorama.com',
                'currys.co.uk', 'mediamarkt.de', 'saturn.de', 'croma.com',
                'vijaysales.com', 'reliancedigital.in'
            ],
            'fashion': [
                'zara.com', 'hm.com', 'uniqlo.com', 'gap.com', 'adidas.com', 'nike.com',
                'asos.com', 'zalando.com', 'myntra.com', 'ajio.com', 'nykaa.com'
            ],
            'books': [
                'amazon.com', 'barnesandnoble.com', 'bookdepository.com', 'waterstones.com',
                'flipkart.com', 'amazon.in', 'crossword.in'
            ],
            'household': [
                'ikea.com', 'wayfair.com', 'homedepot.com', 'lowes.com', 'bedbathandbeyond.com',
                'pepperfry.com', 'urbanladder.com', 'fabindia.com'
            ],
            'sports': [
                'nike.com', 'adidas.com', 'decathlon.com', 'dickssportinggoods.com',
                'sportsauthority.com', 'decathlon.in'
            ]
        }
        
        sites = category_sites.get(category.lower(), category_sites.get('general', []))
        if not sites:
            # Use general e-commerce sites
            sites = ['amazon.com', 'ebay.com', 'walmart.com', 'flipkart.com', 'noon.com']
        
        clean_query = re.sub(r'[^\w\s-]', '', query).replace(' ', '+')
        
        search_patterns = [
            'https://www.{}/search?q={}',
            'https://www.{}/s?k={}',
            'https://{}/search?q={}',
            'https://{}/s?k={}'
        ]
        
        for site in sites:
            if len(results) >= max_results:
                break
                
            for pattern in search_patterns:
                if len(results) >= max_results:
                    break
                    
                try:
                    url = pattern.format(site, clean_query)
                    
                    results.append({
                        'title': f"{query} - {site}",
                        'url': url,
                        'snippet': f"Category-specific search for {query} on {site}",
                        'region': self.domain_region_mapping.get(site, 'global'),
                        'source': 'category_sites'
                    })
                    
                except Exception:
                    continue
        
        return results
    
    def _search_with_regional_variations(self, query: str, category: str, max_results: int) -> List[Dict]:
        """Search with regional domain variations"""
        results = []
        
        # Regional variations of major sites
        regional_sites = [
            'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr', 'amazon.it', 'amazon.es',
            'amazon.in', 'amazon.co.jp', 'amazon.com.au', 'amazon.ca', 'amazon.com.mx',
            'amazon.com.br', 'amazon.ae', 'amazon.sa', 'amazon.sg', 'amazon.nl',
            'ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.fr', 'ebay.it', 'ebay.es',
            'ebay.com.au', 'ebay.ca', 'ebay.in'
        ]
        
        clean_query = re.sub(r'[^\w\s-]', '', query).replace(' ', '+')
        
        for site in regional_sites:
            if len(results) >= max_results:
                break
                
            try:
                url = f"https://www.{site}/s?k={clean_query}"
                
                results.append({
                    'title': f"{query} - {site}",
                    'url': url,
                    'snippet': f"Regional search for {query} on {site}",
                    'region': self.domain_region_mapping.get(site, 'international'),
                    'source': 'regional'
                })
                
            except Exception:
                continue
        
        return results
    
    def _search_with_fallback_terms_extensive(self, query: str, category: str, max_results: int) -> List[Dict]:
        """Extensive fallback search with many term combinations"""
        results = []
        
        # Extensive fallback terms
        fallback_terms = [
            'buy', 'shop', 'store', 'market', 'sale', 'deal', 'offer', 'price', 'cheap',
            'discount', 'online', 'purchase', 'order', 'shopping', 'marketplace',
            'retail', 'vendor', 'supplier', 'seller', 'merchant', 'outlet', 'bazaar'
        ]
        
        # Create many combinations
        enhanced_queries = []
        for term in fallback_terms[:15]:  # Use more terms
            enhanced_queries.extend([
                f"{query} {term}",
                f"{term} {query}",
                f"{query} {term} online",
                f"best {query} {term}",
                f"{query} {term} price"
            ])
        
        # Add site-specific searches
        major_sites = ['amazon', 'ebay', 'walmart', 'flipkart', 'noon', 'daraz']
        for site in major_sites:
            enhanced_queries.extend([
                f"{query} site:{site}.com",
                f"{query} {site}",
                f"buy {query} {site}"
            ])
        
        # Limit queries based on max_results
        queries_to_use = enhanced_queries[:min(len(enhanced_queries), max_results // 5)]
        
        for enhanced_query in queries_to_use:
            if len(results) >= max_results:
                break
                
            # Create mock results for popular sites
            popular_sites = ['amazon.com', 'ebay.com', 'walmart.com', 'flipkart.com', 'noon.com', 'daraz.pk']
            
            for site in popular_sites:
                if len(results) >= max_results:
                    break
                    
                search_url = f"https://www.{site}/search?q={enhanced_query.replace(' ', '+')}"
                
                results.append({
                    'title': f"{enhanced_query} - {site}",
                    'url': search_url,
                    'snippet': f"Fallback search for {enhanced_query} on {site}",
                    'region': self.domain_region_mapping.get(site, 'global'),
                    'source': 'fallback'
                })
        
        return results
    
    def _intensive_search_variations(self, query: str, category: str, needed_results: int, seen_urls: set) -> List[Dict]:
        """Intensive search with many more variations when not enough results"""
        results = []
        
        # More intensive query variations
        intensive_variations = [
            f'"{query}"', f"'{query}'", f"{query} product", f"{query} item",
            f"{query} brand", f"{query} model", f"{query} type", f"{query} style",
            f"{query} new", f"{query} used", f"{query} refurbished", f"{query} original",
            f"{query} genuine", f"{query} authentic", f"{query} official", f"{query} certified",
            f"{query} wholesale", f"{query} retail", f"{query} bulk", f"{query} single",
            f"{query} pack", f"{query} set", f"{query} kit", f"{query} bundle",
            f"{query} collection", f"{query} series", f"{query} edition", f"{query} version"
        ]
        
        # Add more sites from CSV
        additional_sites = self.csv_domains[200:500] if len(self.csv_domains) > 200 else self.csv_domains
        
        for variation in intensive_variations:
            if len(results) >= needed_results:
                break
                
            clean_variation = re.sub(r'[^\w\s-]', '', variation).replace(' ', '+')
            
            for site in additional_sites[:50]:  # Use 50 more sites
                if len(results) >= needed_results:
                    break
                    
                try:
                    url = f"https://www.{site}/search?q={clean_variation}"
                    
                    if url not in seen_urls:
                        results.append({
                            'title': f"{variation} - {site}",
                            'url': url,
                            'snippet': f"Intensive search for {variation} on {site}",
                            'region': self.domain_region_mapping.get(site, 'international'),
                            'source': 'intensive'
                        })
                        seen_urls.add(url)
                        
                except Exception:
                    continue
        
        return results
    
    def _is_relevant_result(self, url: str, title: str, snippet: str) -> bool:
        """Enhanced relevance checking"""
        url_lower = url.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        # Check for e-commerce domains
        if any(domain in url_lower for domain in self.global_ecommerce_domains):
            return True
        
        # Check for commerce-related keywords
        commerce_keywords = [
            'buy', 'price', 'shop', 'store', 'market', 'sale', 'deal', 'product', 'item',
            'purchase', 'order', 'shipping', 'delivery', 'discount', 'offer', 'review',
            'compare', 'best', 'cheap', 'affordable', 'quality', 'brand', 'online'
        ]
        
        text_to_check = f"{title_lower} {snippet_lower} {url_lower}"
        
        # Count commerce keywords
        keyword_count = sum(1 for keyword in commerce_keywords if keyword in text_to_check)
        
        # More lenient for getting more results
        return keyword_count >= 1
    
    def scrape_products_parallel(self, search_results: List[Dict], max_workers: int = None, progress_callback=None) -> List[Dict]:
        """Enhanced parallel scraping with better error handling"""
        if not search_results:
            return []
            
        if max_workers is None:
            max_workers = min(self.max_workers, len(search_results))
        
        products = []
        successful = 0
        failed = 0
        
        self.update_progress(
            status='scraping',
            scrape_total=len(search_results),
            scrape_completed=0,
            message=f"Starting to scrape {len(search_results)} products..."
        )
        
        logger.info(f"Starting parallel scraping of {len(search_results)} products with {max_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping tasks
            future_to_result = {
                executor.submit(self._scrape_with_timeout, result['url']): result 
                for result in search_results
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_result):
                search_result = future_to_result[future]
                try:
                    product = future.result(timeout=self.timeout)
                    if product:
                        # Add search metadata
                        product['search_title'] = search_result['title']
                        product['search_snippet'] = search_result['snippet']
                        product['search_region'] = search_result.get('region', 'unknown')
                        product['search_source'] = search_result.get('source', 'unknown')
                        products.append(product)
                        successful += 1
                        
                        self.update_progress(
                            scrape_completed=successful + failed,
                            message=f"Scraped {successful} products successfully..."
                        )
                        
                        if progress_callback:
                            progress_callback(self.get_progress())
                            
                        logger.info(f"✓ Successfully scraped: {product['name'][:50]}... ({successful}/{len(search_results)})")
                    else:
                        failed += 1
                        self.update_progress(scrape_completed=successful + failed)
                        
                except Exception as e:
                    failed += 1
                    self.update_progress(scrape_completed=successful + failed)
                    logger.warning(f"✗ Failed to scrape: {search_result['url'][:50]}... ({failed} failures)")
        
        self.update_progress(
            status='scraping_complete',
            message=f"Scraping complete: {successful} successful, {failed} failed"
        )
        
        logger.info(f"Parallel scraping completed: {successful} successful, {failed} failed")
        return products
    
    def _scrape_with_timeout(self, url: str) -> Optional[Dict]:
        """Scrape a single URL with timeout protection"""
        try:
            return self.scrape_product_page_enhanced(url)
        except Exception as e:
            logger.warning(f"Scraping failed for {url}: {e}")
            return None
    
    def scrape_product_page_enhanced(self, url: str) -> Optional[Dict]:
        """Enhanced product page scraping with better error handling"""
        if url in self.url_cache:
            return None
            
        self.url_cache.add(url)
        
        for attempt in range(self.max_retries):
            try:
                # Add delay to be respectful
                time.sleep(random.uniform(*self.request_delay))
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                domain = urlparse(url).netloc.lower()
                region = self._detect_region_from_domain(domain)
                
                product = {
                    'name': self._extract_product_name(soup),
                    'price': self._extract_product_price(soup),
                    'location': self._extract_location(url, soup),
                    'product_url': url,
                    'image_url': self._extract_image_url(soup, url),
                    'image_data': None,
                    'availability': self._extract_availability(soup),
                    'rating': self._extract_rating(soup),
                    'description': self._extract_description(soup),
                    'domain': domain,
                    'region': region
                }
                
                # Try to fetch image (with timeout)
                if product['image_url']:
                    try:
                        product['image_data'] = self._fetch_and_process_image(product['image_url'])
                    except:
                        pass  # Ignore image fetch errors
                
                return product
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    logger.warning(f"Failed to scrape {url} after {self.max_retries} attempts")
                    return None
                time.sleep(1 * (attempt + 1))
                
            except Exception as e:
                logger.warning(f"Error scraping {url}: {e}")
                return None
    
    def _detect_region_from_domain(self, domain: str) -> str:
        """Detect region from domain"""
        # Try direct domain match
        for domain_key, region in self.domain_region_mapping.items():
            if domain_key in domain:
                return region
        
        # TLD-based detection
        tld_mapping = {
            '.uk': 'uk-en', '.de': 'de-de', '.fr': 'fr-fr', '.it': 'it-it', '.es': 'es-es',
            '.jp': 'jp-jp', '.in': 'in-en', '.au': 'au-en', '.ca': 'ca-en', '.br': 'br-pt',
            '.mx': 'mx-es', '.ae': 'ae-en', '.sa': 'sa-ar', '.pk': 'pk-en', '.kr': 'kr-kr',
            '.cn': 'cn-zh', '.sg': 'sg-en'
        }
        
        for tld, region in tld_mapping.items():
            if domain.endswith(tld):
                return region
        
        return 'us-en' if domain.endswith('.com') else 'international'
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name with enhanced selectors"""
        selectors = [
            'h1[id*="title"]', 'h1[class*="title"]', 'h1[class*="name"]',
            '.product-title h1', '.product-name h1', '.item-title h1',
            'h1', '.title', '.product-title', '.product-name',
            '[data-testid="product-title"]', '[itemprop="name"]'
        ]
        
        for selector in selectors:
            elems = soup.select(selector)
            for elem in elems:
                name = elem.get_text().strip()
                if 5 < len(name) < 200 and not re.match(r'^[\d\s\W]+$', name):
                    return name
        
        return "Product name not found"
    
    def _extract_product_price(self, soup: BeautifulSoup) -> str:
        """Extract price with enhanced selectors"""
        price_selectors = [
            '.a-price-whole', '.a-price', '.price-current', '.price-now',
            '.product-price', '.current-price', '.sale-price', '.price',
            '[data-testid="price"]', '.notranslate', '[class*="price"]',
            '[itemprop="price"]', '.price-box', '.pricing'
        ]
        
        for selector in price_selectors:
            elems = soup.select(selector)
            for elem in elems:
                price_text = elem.get_text()
                extracted_price = self.extract_price(price_text)
                if extracted_price != "Price not found":
                    return extracted_price
        
        # Fallback to full page text
        page_text = soup.get_text()
        return self.extract_price(page_text)
    
    def extract_price(self, text: str) -> str:
        """Enhanced price extraction"""
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            r'\$\s*[\d,]+(?:\.\d{1,2})?',
            r'€\s*[\d,]+(?:\.\d{1,2})?',
            r'£\s*[\d,]+(?:\.\d{1,2})?',
            r'₹\s*[\d,]+(?:\.\d{1,2})?',
            r'PKR\s*[\d,]+(?:\.\d{1,2})?',
            r'¥\s*[\d,]+',
            r'AED\s*[\d,]+(?:\.\d{1,2})?',
            r'SAR\s*[\d,]+(?:\.\d{1,2})?',
            r'[\d,]+(?:\.\d{1,2})?\s*(?:USD|EUR|GBP|INR|PKR|JPY|AED|SAR)',
            r'Rs\.?\s*[\d,]+(?:\.\d{1,2})?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return "Price not found"
    
    def _extract_location(self, url: str, soup: BeautifulSoup) -> str:
        """Extract location with enhanced detection"""
        domain = urlparse(url).netloc.lower()
        
        # Domain-based location mapping
        domain_locations = {
            'amazon.com': 'United States', 'amazon.co.uk': 'United Kingdom',
            'amazon.de': 'Germany', 'amazon.fr': 'France', 'amazon.in': 'India',
            'flipkart.com': 'India', 'pakwheels.com': 'Pakistan', 'daraz.pk': 'Pakistan',
            'noon.com': 'United Arab Emirates', 'walmart.com': 'United States',
            'ebay.com': 'United States', 'ebay.co.uk': 'United Kingdom'
        }
        
        for domain_key, location in domain_locations.items():
            if domain_key in domain:
                return location
        
        # TLD-based detection
        tld_mapping = {
            '.uk': 'United Kingdom', '.de': 'Germany', '.fr': 'France',
            '.in': 'India', '.pk': 'Pakistan', '.ae': 'United Arab Emirates',
            '.jp': 'Japan', '.au': 'Australia', '.ca': 'Canada'
        }
        
        for tld, location in tld_mapping.items():
            if domain.endswith(tld):
                return location
        
        return "International"
    
    def _extract_image_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract product image URL"""
        img_selectors = [
            '#landingImage', '#imgBlkFront', '.product-image img',
            '.main-image img', 'meta[property="og:image"]',
            'img[itemprop="image"]', '.gallery-image img'
        ]
        
        # Check meta tags first
        meta = soup.select_one('meta[property="og:image"]')
        if meta and meta.get('content'):
            return urljoin(base_url, meta.get('content'))
        
        # Check image tags
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                src = img.get('src') or img.get('data-src')
                if src and not src.startswith('data:'):
                    return urljoin(base_url, src)
        
        return ""
    
    def _fetch_and_process_image(self, image_url: str) -> Optional[bytes]:
        """Fetch and process image data with timeout"""
        try:
            response = self.session.get(image_url, timeout=self.image_fetch_timeout, stream=True)
            response.raise_for_status()
            
            # Process image
            img = Image.open(BytesIO(response.content))
            if img.width > self.max_image_size[0] or img.height > self.max_image_size[1]:
                img.thumbnail(self.max_image_size, Image.LANCZOS)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=self.image_quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Error fetching image {image_url}: {e}")
            return None
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability status"""
        availability_selectors = [
            '#availability', '.availability', '.stock', '[id*="stock"]'
        ]
        
        for selector in availability_selectors:
            elems = soup.select(selector)
            for elem in elems:
                text = elem.get_text().lower()
                if 'in stock' in text or 'available' in text:
                    return "In Stock"
                elif 'out of stock' in text or 'unavailable' in text:
                    return "Out of Stock"
        
        return "Unknown"
    
    def _extract_rating(self, soup: BeautifulSoup) -> str:
        """Extract product rating"""
        rating_selectors = [
            '.a-icon-alt', '.rating', '.stars', '[itemprop="ratingValue"]'
        ]
        
        for selector in rating_selectors:
            elems = soup.select(selector)
            for elem in elems:
                text = elem.get_text() or elem.get('content', '')
                rating_match = re.search(r'(\d+(?:\.\d+)?)', text)
                if rating_match:
                    return f"{rating_match.group(1)}/5"
        
        return "No rating"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        desc_selectors = [
            '#productDescription', '.product-description', '.description',
            '[itemprop="description"]', '.product-details'
        ]
        
        for selector in desc_selectors:
            elems = soup.select(selector)
            for elem in elems:
                desc = elem.get_text().strip()
                if 10 < len(desc) < 1000:
                    desc = re.sub(r'\s+', ' ', desc)
                    return desc[:300] + "..." if len(desc) > 300 else desc
        
        return "No description available"
    
    def search_and_scrape_enhanced(self, query: str, category: str = 'general', max_results: int = 100,
                                  regions: List[str] = None, progress_callback=None) -> List[Dict]:
        """Main enhanced search and scrape function with aggressive result targeting"""
        logger.info(f"Starting aggressive search for: '{query}' with target: {max_results} results")
        
        # Search for products with aggressive targeting
        search_results = self.search_products_multi_region(
            query=query,
            category=category,
            max_results=max_results,
            regions=regions,
            progress_callback=progress_callback
        )
        
        if not search_results:
            logger.warning("No search results found")
            return []
        
        logger.info(f"Found {len(search_results)} search results, starting scraping...")
        
        # Scrape products
        products = self.scrape_products_parallel(
            search_results, 
            max_workers=self.max_workers,
            progress_callback=progress_callback
        )
        
        logger.info(f"Successfully scraped {len(products)} products")
        return products
