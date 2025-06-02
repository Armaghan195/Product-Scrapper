import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin, urlparse
from duckduckgo_search import DDGS
import json

class ProductScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # E-commerce sites to focus on
        self.ecommerce_domains = [
            'amazon.com', 'ebay.com', 'walmart.com', 'target.com', 'bestbuy.com',
            'newegg.com', 'homedepot.com', 'lowes.com', 'costco.com', 'etsy.com',
            'overstock.com', 'wayfair.com', 'alibaba.com', 'aliexpress.com'
        ]
    
    def search_products(self, query, category='general', max_results=10):
        """Search for products using DuckDuckGo"""
        try:
            print(f"Searching DuckDuckGo for: {query}")
            
            # Create search query with e-commerce focus
            search_query = f"{query} buy price shop"
            
            # Add category-specific terms
            if category.lower() in ['technology', 'tech']:
                search_query += " electronics gadgets"
            elif category.lower() in ['household', 'home']:
                search_query += " home appliances"
            elif category.lower() in ['automotive', 'car']:
                search_query += " auto parts car"
            elif category.lower() in ['books', 'book']:
                search_query += " books literature"
            
            # Use DuckDuckGo search
            ddgs = DDGS()
            search_results = []
            
            # Get search results
            results = ddgs.text(search_query, max_results=max_results * 2)  # Get more to filter
            
            for result in results:
                url = result.get('href', '')
                title = result.get('title', '')
                snippet = result.get('body', '')
                
                # Filter for e-commerce sites
                if any(domain in url.lower() for domain in self.ecommerce_domains):
                    search_results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
                    
                    if len(search_results) >= max_results:
                        break
            
            print(f"Found {len(search_results)} e-commerce results")
            return search_results
            
        except Exception as e:
            print(f"Error searching DuckDuckGo: {e}")
            return []
    
    def extract_price(self, text):
        """Extract price from text using multiple patterns"""
        # Clean text first
        text = re.sub(r'\s+', ' ', text)
        
        patterns = [
            r'\$\s*[\d,]+(?:\.\d{1,2})?',  # $100.00, $1,000.00
            r'USD\s*[\d,]+(?:\.\d{1,2})?',  # USD 100.00
            r'[\d,]+(?:\.\d{1,2})?\s*USD',  # 100.00 USD
            r'Price[:\s]*\$\s*[\d,]+(?:\.\d{1,2})?',  # Price: $100.00
            r'₹\s*[\d,]+(?:\.\d{1,2})?',  # ₹100.00
            r'£\s*[\d,]+(?:\.\d{1,2})?',  # £100.00
            r'€\s*[\d,]+(?:\.\d{1,2})?',  # €100.00
            r'\$[\d,]+',  # Simple $100
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first match, cleaned up
                price = matches[0].strip()
                return price
        
        return "Price not found"
    
    def extract_product_info(self, soup, url):
        """Extract product information from BeautifulSoup object"""
        product = {
            'name': 'Product name not found',
            'price': 'Price not found',
            'location': 'Location not specified',
            'product_url': url,
            'image_url': '',
            'availability': 'Unknown'
        }
        
        try:
            # Extract product name
            name_selectors = [
                'h1[id*="title"]',  # Amazon
                'h1.product-title',
                'h1.pdp-product-name',
                '.product-title h1',
                'h1',
                '.title',
                '[data-testid="product-title"]',
                '.product-name',
                '.item-title'
            ]
            
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    name = elem.get_text().strip()
                    if len(name) > 5 and len(name) < 200:
                        product['name'] = name
                        break
            
            # Extract price from page text
            page_text = soup.get_text()
            product['price'] = self.extract_price(page_text)
            
            # Try specific price selectors if not found
            if product['price'] == "Price not found":
                price_selectors = [
                    '.a-price-whole',  # Amazon
                    '.price-current',
                    '.price',
                    '[data-testid="price"]',
                    '.product-price',
                    '.current-price',
                    '.sale-price',
                    '.price-now',
                    '.notranslate'
                ]
                
                for selector in price_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        price_text = elem.get_text()
                        extracted_price = self.extract_price(price_text)
                        if extracted_price != "Price not found":
                            product['price'] = extracted_price
                            break
            
            # Extract image
            img_selectors = [
                '#landingImage',  # Amazon
                '.product-image img',
                '.main-image img',
                'img[data-testid="product-image"]',
                '.product-photo img',
                '.item-image img'
            ]
            
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img and img.get('src'):
                    src = img['src']
                    if not src.startswith('data:'):
                        product['image_url'] = urljoin(url, src)
                        break
            
            # Extract availability
            availability_text = page_text.lower()
            if 'in stock' in availability_text:
                product['availability'] = "In Stock"
            elif 'out of stock' in availability_text:
                product['availability'] = "Out of Stock"
            elif 'limited' in availability_text or 'few left' in availability_text:
                product['availability'] = "Limited Stock"
            
            # Determine location based on domain
            domain = urlparse(url).netloc.lower()
            if 'amazon.com' in domain:
                product['location'] = "United States"
            elif 'amazon.co.uk' in domain:
                product['location'] = "United Kingdom"
            elif 'amazon.ca' in domain:
                product['location'] = "Canada"
            elif 'ebay.com' in domain:
                product['location'] = "United States"
            elif 'walmart.com' in domain:
                product['location'] = "United States"
            elif 'target.com' in domain:
                product['location'] = "United States"
            elif 'bestbuy.com' in domain:
                product['location'] = "United States"
            else:
                product['location'] = "International"
            
        except Exception as e:
            print(f"Error extracting product info: {e}")
        
        return product
    
    def scrape_product_page(self, url):
        """Scrape individual product page"""
        try:
            print(f"Scraping: {url}")
            
            # Add random delay to be respectful
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            product = self.extract_product_info(soup, url)
            
            return product
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def search_and_scrape(self, query, category='general', max_results=10):
        """Main function to search and scrape products"""
        print(f"Starting search for: '{query}' in category: {category}")
        
        # Search for products
        search_results = self.search_products(query, category, max_results)
        
        if not search_results:
            print("No search results found")
            return []
        
        products = []
        
        for i, result in enumerate(search_results):
            try:
                print(f"Processing {i+1}/{len(search_results)}: {result['title'][:50]}...")
                
                product = self.scrape_product_page(result['url'])
                
                if product:
                    # Add search result info
                    product['search_title'] = result['title']
                    product['search_snippet'] = result['snippet']
                    products.append(product)
                    print(f"✓ Successfully scraped: {product['name'][:50]}...")
                else:
                    print(f"✗ Failed to scrape product from {result['url']}")
                
            except Exception as e:
                print(f"Error processing search result: {e}")
                continue
        
        print(f"Successfully scraped {len(products)} products out of {len(search_results)} results")
        return products