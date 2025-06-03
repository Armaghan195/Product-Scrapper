import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin, urlparse
from duckduckgo_search import DDGS
import concurrent.futures
import threading
from typing import List, Dict, Optional
import json

class ProductScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8,fr;q=0.7,de;q=0.6,it;q=0.5,pt;q=0.4,ru;q=0.3,ja;q=0.2,ko;q=0.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Global e-commerce sites and marketplaces
        self.global_ecommerce_domains = [
            # US & International
            'amazon.com', 'amazon.co.uk', 'amazon.ca', 'amazon.de', 'amazon.fr', 'amazon.it', 'amazon.es', 'amazon.in', 'amazon.com.au', 'amazon.co.jp',
            'ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.fr', 'ebay.it', 'ebay.es', 'ebay.ca', 'ebay.com.au',
            'walmart.com', 'target.com', 'bestbuy.com', 'newegg.com', 'costco.com', 'homedepot.com', 'lowes.com',
            
            # European
            'zalando.com', 'otto.de', 'cdiscount.com', 'fnac.com', 'mediamarkt.de', 'saturn.de', 'currys.co.uk', 'argos.co.uk',
            'bol.com', 'coolblue.nl', 'elgiganten.dk', 'elkjop.no', 'gigantti.fi', 'emag.ro', 'allegro.pl',
            
            # Asian
            'alibaba.com', 'aliexpress.com', 'taobao.com', 'tmall.com', 'jd.com', 'rakuten.com', 'rakuten.co.jp',
            'flipkart.com', 'myntra.com', 'snapdeal.com', 'paytmmall.com', 'shopee.com', 'lazada.com',
            'qoo10.com', 'gmarket.co.kr', '11st.co.kr', 'coupang.com',
            
            # Others
            'mercadolibre.com', 'mercadolivre.com.br', 'olx.com', 'jumia.com', 'konga.com', 'takealot.com',
            'etsy.com', 'overstock.com', 'wayfair.com', 'wish.com', 'banggood.com', 'gearbest.com',
            
            # Automotive specific
            'autotrader.com', 'cars.com', 'cargurus.com', 'carmax.com', 'vroom.com', 'carvana.com',
            'autotrader.co.uk', 'motors.co.uk', 'pistonheads.com', 'mobile.de', 'autoscout24.com',
            'leboncoin.fr', 'subito.it', 'marktplaats.nl', 'blocket.se', 'finn.no',
            'cardekho.com', 'carwale.com', 'zigwheels.com', 'pakwheels.com', 'carmudi.com'
        ]
        
        # Regional search terms for better global coverage
        self.regional_terms = {
            'automotive': ['car', 'auto', 'vehicle', 'motor', 'voiture', 'coche', 'automobile', 'wagen', 'bil'],
            'technology': ['tech', 'electronic', 'gadget', 'device', 'digital', 'smart'],
            'household': ['home', 'house', 'kitchen', 'appliance', 'domestic', 'ménage', 'casa', 'haus'],
            'books': ['book', 'livre', 'libro', 'buch', 'bok', 'kitab']
        }
        
        # Country-specific search regions
        self.search_regions = ['us-en', 'uk-en', 'ca-en', 'au-en', 'de-de', 'fr-fr', 'es-es', 'it-it', 'nl-nl', 'in-en', 'jp-jp', 'kr-kr', 'br-pt']
        
        self.max_workers = 5  # For parallel processing
        self.request_delay = (0.5, 2.0)  # Random delay range
    
    def search_products_multi_region(self, query: str, category: str = 'general', max_results: int = 50) -> List[Dict]:
        """Search for products across multiple regions"""
        all_results = []
        
        # Enhance query with regional terms
        enhanced_queries = self._enhance_query_with_regional_terms(query, category)
        
        # Search across multiple regions
        for region in self.search_regions[:6]:  # Limit to 6 regions to avoid rate limiting
            try:
                print(f"Searching in region: {region}")
                
                for enhanced_query in enhanced_queries[:2]:  # Use top 2 enhanced queries
                    results = self._search_single_region(enhanced_query, region, max_results // len(self.search_regions))
                    all_results.extend(results)
                    
                    if len(all_results) >= max_results:
                        break
                
                if len(all_results) >= max_results:
                    break
                    
                # Small delay between regions
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Error searching region {region}: {e}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        print(f"Found {len(unique_results)} unique results across regions")
        return unique_results[:max_results]
    
    def _enhance_query_with_regional_terms(self, query: str, category: str) -> List[str]:
        """Enhance query with regional and category-specific terms"""
        enhanced_queries = [query]
        
        # Add category-specific terms
        if category.lower() in self.regional_terms:
            for term in self.regional_terms[category.lower()][:3]:
                enhanced_queries.append(f"{query} {term}")
        
        # Add commerce-related terms
        commerce_terms = ['buy', 'price', 'shop', 'store', 'market', 'sale', 'deal']
        for term in commerce_terms[:2]:
            enhanced_queries.append(f"{query} {term}")
        
        return enhanced_queries
    
    def _search_single_region(self, query: str, region: str, max_results: int) -> List[Dict]:
        """Search in a single region using DuckDuckGo"""
        try:
            ddgs = DDGS()
            results = []
            
            # Search with region specification
            search_results = ddgs.text(query, region=region, max_results=max_results * 2)
            
            for result in search_results:
                url = result.get('href', '')
                title = result.get('title', '')
                snippet = result.get('body', '')
                
                # Filter for e-commerce sites or relevant content
                if self._is_relevant_result(url, title, snippet):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'region': region
                    })
                    
                    if len(results) >= max_results:
                        break
            
            return results
            
        except Exception as e:
            print(f"Error searching in region {region}: {e}")
            return []
    
    def _is_relevant_result(self, url: str, title: str, snippet: str) -> bool:
        """Check if result is relevant for product search"""
        url_lower = url.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        # Check for e-commerce domains
        if any(domain in url_lower for domain in self.global_ecommerce_domains):
            return True
        
        # Check for commerce-related keywords
        commerce_keywords = ['buy', 'price', 'shop', 'store', 'market', 'sale', 'deal', 'product', 'item']
        if any(keyword in title_lower or keyword in snippet_lower for keyword in commerce_keywords):
            return True
        
        # Check for currency symbols
        currency_pattern = r'[\$€£¥₹₽¢]|\bUSD\b|\bEUR\b|\bGBP\b|\bINR\b'
        if re.search(currency_pattern, title + ' ' + snippet):
            return True
        
        return False
    
    def extract_price(self, text: str) -> str:
        """Enhanced price extraction with multiple currencies"""
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            # US Dollar
            r'\$\s*[\d,]+(?:\.\d{1,2})?',
            r'USD\s*[\d,]+(?:\.\d{1,2})?',
            r'[\d,]+(?:\.\d{1,2})?\s*USD',
            
            # Euro
            r'€\s*[\d,]+(?:\.\d{1,2})?',
            r'EUR\s*[\d,]+(?:\.\d{1,2})?',
            r'[\d,]+(?:\.\d{1,2})?\s*EUR',
            
            # British Pound
            r'£\s*[\d,]+(?:\.\d{1,2})?',
            r'GBP\s*[\d,]+(?:\.\d{1,2})?',
            
            # Indian Rupee
            r'₹\s*[\d,]+(?:\.\d{1,2})?',
            r'INR\s*[\d,]+(?:\.\d{1,2})?',
            r'Rs\.?\s*[\d,]+',
            
            # Japanese Yen
            r'¥\s*[\d,]+',
            r'JPY\s*[\d,]+',
            
            # Other currencies
            r'₽\s*[\d,]+',  # Russian Ruble
            r'R\$\s*[\d,]+(?:\.\d{1,2})?',  # Brazilian Real
            r'₩\s*[\d,]+',  # Korean Won
            
            # Generic price patterns
            r'Price[:\s]*[\$€£¥₹₽]\s*[\d,]+(?:\.\d{1,2})?',
            r'[\d,]+(?:\.\d{1,2})?\s*(?:dollars|euros|pounds|rupees|yen)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return "Price not found"
    
    def scrape_product_page_enhanced(self, url: str) -> Optional[Dict]:
        """Enhanced product page scraping with better selectors"""
        try:
            time.sleep(random.uniform(*self.request_delay))
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product = {
                'name': self._extract_product_name(soup),
                'price': self._extract_product_price(soup),
                'location': self._extract_location(url, soup),
                'product_url': url,
                'image_url': self._extract_image_url(soup, url),
                'availability': self._extract_availability(soup),
                'rating': self._extract_rating(soup),
                'description': self._extract_description(soup)
            }
            
            return product
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name with enhanced selectors"""
        selectors = [
            'h1[id*="title"]', 'h1[class*="title"]', 'h1[class*="name"]',
            '.product-title h1', '.product-name h1', '.item-title h1',
            'h1', '.title', '.product-title', '.product-name', '.item-title',
            '[data-testid="product-title"]', '[data-testid="product-name"]',
            '.pdp-product-name', '.product-detail-title', '.listing-title'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text().strip()
                if 5 < len(name) < 200 and not re.match(r'^[\d\s\W]+$', name):
                    return name
        
        return "Product name not found"
    
    def _extract_product_price(self, soup: BeautifulSoup) -> str:
        """Extract price with enhanced selectors"""
        # First try specific price selectors
        price_selectors = [
            '.a-price-whole', '.a-price', '.price-current', '.price-now',
            '.product-price', '.current-price', '.sale-price', '.price',
            '[data-testid="price"]', '.notranslate', '.price-display',
            '.listing-price', '.item-price', '.cost', '.amount'
        ]
        
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text()
                extracted_price = self.extract_price(price_text)
                if extracted_price != "Price not found":
                    return extracted_price
        
        # Fallback to full page text
        page_text = soup.get_text()
        return self.extract_price(page_text)
    
    def _extract_location(self, url: str, soup: BeautifulSoup) -> str:
        """Extract location with enhanced detection"""
        domain = urlparse(url).netloc.lower()
        
        # Domain-based location mapping
        domain_locations = {
            'amazon.com': 'United States', 'amazon.co.uk': 'United Kingdom',
            'amazon.ca': 'Canada', 'amazon.de': 'Germany', 'amazon.fr': 'France',
            'amazon.it': 'Italy', 'amazon.es': 'Spain', 'amazon.in': 'India',
            'amazon.com.au': 'Australia', 'amazon.co.jp': 'Japan',
            'ebay.co.uk': 'United Kingdom', 'ebay.de': 'Germany', 'ebay.fr': 'France',
            'flipkart.com': 'India', 'myntra.com': 'India', 'snapdeal.com': 'India',
            'rakuten.co.jp': 'Japan', 'mercadolibre.com': 'Latin America',
            'allegro.pl': 'Poland', 'bol.com': 'Netherlands', 'cdiscount.com': 'France'
        }
        
        for domain_key, location in domain_locations.items():
            if domain_key in domain:
                return location
        
        # Try to extract from page content
        page_text = soup.get_text().lower()
        location_patterns = [
            r'ships from[\s:]+([A-Za-z\s,]+)',
            r'sold by[\s:]+([A-Za-z\s,]+)',
            r'location[\s:]+([A-Za-z\s,]+)',
            r'country[\s:]+([A-Za-z\s,]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, page_text)
            if match:
                location = match.group(1).strip()
                if 2 < len(location) < 50:
                    return location.title()
        
        return "International"
    
    def _extract_image_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract product image URL"""
        img_selectors = [
            '#landingImage', '.product-image img', '.main-image img',
            'img[data-testid="product-image"]', '.product-photo img',
            '.item-image img', '.gallery-image img', '.primary-image img'
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                src = img['src']
                if not src.startswith('data:') and 'placeholder' not in src.lower():
                    return urljoin(base_url, src)
        
        return ""
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability status"""
        page_text = soup.get_text().lower()
        
        if any(term in page_text for term in ['in stock', 'available', 'ready to ship']):
            return "In Stock"
        elif any(term in page_text for term in ['out of stock', 'unavailable', 'sold out']):
            return "Out of Stock"
        elif any(term in page_text for term in ['limited', 'few left', 'low stock']):
            return "Limited Stock"
        
        return "Unknown"
    
    def _extract_rating(self, soup: BeautifulSoup) -> str:
        """Extract product rating"""
        rating_selectors = [
            '.a-icon-alt', '.rating', '.stars', '.review-score',
            '[data-testid="rating"]', '.product-rating', '.star-rating'
        ]
        
        for selector in rating_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text() or elem.get('alt', '') or elem.get('title', '')
                rating_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:out of|/|\s)\s*(\d+)', text)
                if rating_match:
                    return f"{rating_match.group(1)}/{rating_match.group(2)}"
        
        return "No rating"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        desc_selectors = [
            '.product-description', '.description', '.product-details',
            '.item-description', '.product-summary', '.overview'
        ]
        
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                desc = elem.get_text().strip()
                if 10 < len(desc) < 500:
                    return desc[:200] + "..." if len(desc) > 200 else desc
        
        return "No description available"
    
    def scrape_products_parallel(self, search_results: List[Dict], max_workers: int = None) -> List[Dict]:
        """Scrape products in parallel for better performance"""
        if max_workers is None:
            max_workers = min(self.max_workers, len(search_results))
        
        products = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_result = {
                executor.submit(self.scrape_product_page_enhanced, result['url']): result 
                for result in search_results
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_result):
                search_result = future_to_result[future]
                try:
                    product = future.result()
                    if product:
                        # Add search metadata
                        product['search_title'] = search_result['title']
                        product['search_snippet'] = search_result['snippet']
                        product['search_region'] = search_result.get('region', 'unknown')
                        products.append(product)
                        print(f"✓ Scraped: {product['name'][:50]}...")
                    else:
                        print(f"✗ Failed to scrape: {search_result['url']}")
                except Exception as e:
                    print(f"✗ Error scraping {search_result['url']}: {e}")
        
        return products
    
    def search_and_scrape_enhanced(self, query: str, category: str = 'general', max_results: int = 50) -> List[Dict]:
        """Main enhanced search and scrape function"""
        print(f"Starting enhanced search for: '{query}' in category: {category}")
        print(f"Target results: {max_results}")
        
        # Search across multiple regions
        search_results = self.search_products_multi_region(query, category, max_results)
        
        if not search_results:
            print("No search results found")
            return []
        
        print(f"Found {len(search_results)} search results, starting parallel scraping...")
        
        # Scrape products in parallel
        products = self.scrape_products_parallel(search_results)
        
        print(f"Successfully scraped {len(products)} products out of {len(search_results)} results")
        return products