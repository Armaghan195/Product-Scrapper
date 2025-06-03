import streamlit as st
import pandas as pd
from datetime import datetime
import time
import traceback
import re
from scraper import ProductScraper

# Optional plotly import with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly not installed. Analytics charts will be limited. Install with: pip install plotly")

# Configure page
st.set_page_config(
    page_title="SmartScrape Pro Enhanced",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .search-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #dee2e6;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .price-tag {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2e7d32;
        background: #e8f5e8;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        display: inline-block;
    }
    
    .location-tag {
        color: #1976d2;
        font-style: italic;
        background: #e3f2fd;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    
    .rating-tag {
        color: #f57c00;
        background: #fff3e0;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    
    .status-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .region-selector {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #b3d9ff;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scraper' not in st.session_state:
    st.session_state.scraper = ProductScraper()
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Enhanced categories
categories = {
    "🏠 Household": {
        "description": "Home appliances, kitchen items, cleaning supplies, furniture",
        "examples": ["Vacuum cleaner", "Coffee maker", "Air purifier", "Blender", "Microwave", "Dishwasher"]
    },
    "💻 Technology": {
        "description": "Electronics, gadgets, computers, phones, gaming",
        "examples": ["iPhone 15", "MacBook Pro", "Gaming laptop", "Wireless headphones", "Smart TV", "PlayStation 5"]
    },
    "📚 Books": {
        "description": "Books, e-books, audiobooks, educational materials",
        "examples": ["Python programming book", "Fiction novel", "Self-help book", "Textbook", "Biography", "Cookbook"]
    },
    "🚗 Automotive": {
        "description": "Cars, motorcycles, parts, accessories, tools",
        "examples": ["Honda City", "Toyota Camry", "BMW X5", "Car battery", "Brake pads", "Motor oil"]
    },
    "👕 Fashion": {
        "description": "Clothing, shoes, accessories, jewelry",
        "examples": ["Nike shoes", "Levi's jeans", "Designer handbag", "Watch", "Sunglasses", "T-shirt"]
    },
    "🏃 Sports": {
        "description": "Sports equipment, fitness gear, outdoor activities",
        "examples": ["Treadmill", "Yoga mat", "Basketball", "Tennis racket", "Dumbbells", "Bicycle"]
    }
}

# Region mapping for better user experience
REGION_MAPPING = {
    "🇺🇸 United States": "us-en",
    "🇬🇧 United Kingdom": "uk-en", 
    "🇨🇦 Canada": "ca-en",
    "🇦🇺 Australia": "au-en",
    "🇩🇪 Germany": "de-de",
    "🇫🇷 France": "fr-fr",
    "🇪🇸 Spain": "es-es",
    "🇮🇹 Italy": "it-it",
    "🇳🇱 Netherlands": "nl-nl",
    "🇮🇳 India": "in-en",
    "🇯🇵 Japan": "jp-jp",
    "🇰🇷 South Korea": "kr-kr",
    "🇧🇷 Brazil": "br-pt",
    "🌍 Global (All Regions)": "global"
}

# Sidebar navigation
st.sidebar.markdown("## 🔍 SmartScrape Pro Enhanced")
st.sidebar.markdown("*Global Product Search Engine*")
st.sidebar.markdown("---")

if st.sidebar.button("🏠 Home", use_container_width=True):
    st.session_state.current_page = 'home'
    st.rerun()

if st.sidebar.button("📊 View Results", use_container_width=True, disabled=len(st.session_state.scraped_data) == 0):
    st.session_state.current_page = 'results'
    st.rerun()

if st.sidebar.button("🔧 Direct Search", use_container_width=True):
    st.session_state.current_page = 'direct_search'
    st.rerun()

if PLOTLY_AVAILABLE and st.sidebar.button("📈 Analytics", use_container_width=True, disabled=len(st.session_state.scraped_data) == 0):
    st.session_state.current_page = 'analytics'
    st.rerun()

# Display current results and search history in sidebar
if st.session_state.scraped_data:
    st.sidebar.markdown("---")
    st.sidebar.metric("Current Results", len(st.session_state.scraped_data))

if st.session_state.search_history:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Recent Searches:**")
    for search in st.session_state.search_history[-3:]:
        st.sidebar.markdown(f"• {search}")

# Main content
if st.session_state.current_page == 'home':
    st.markdown('<h1 class="main-header">🔍 SmartScrape Pro Enhanced</h1>', unsafe_allow_html=True)
    st.markdown("### Find the best deals across the web with intelligent global product scraping")
    
    # Features showcase
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🌍 Global Search**")
        st.markdown("Search across 13+ countries and regions")
    with col2:
        st.markdown("**⚡ Fast Scraping**")
        st.markdown("Parallel processing for faster results")
    with col3:
        st.markdown("**📊 Smart Analytics**")
        st.markdown("Price analysis and market insights")
    
    st.markdown("---")
    st.markdown("## 🎯 Choose a Category to Start")
    
    # Display categories in a grid
    cols = st.columns(2)
    for i, (category, info) in enumerate(categories.items()):
        with cols[i % 2]:
            with st.container():
                if st.button(f"{category}", use_container_width=True, key=f"cat_{category}"):
                    st.session_state.selected_category = category
                    st.session_state.current_page = 'category_search'
                    st.rerun()
                
                st.markdown(f"**{info['description']}**")
                st.markdown(f"*Examples: {', '.join(info['examples'][:3])}...*")
            st.markdown("---")

elif st.session_state.current_page == 'category_search':
    category = st.session_state.selected_category
    category_info = categories[category]
    
    st.markdown(f"## {category}")
    st.markdown(f"*{category_info['description']}*")
    
    st.markdown("---")
    
    # Enhanced search form with region selection
    with st.container():
        st.markdown('<div class="search-box">', unsafe_allow_html=True)
        st.markdown("### 🔍 What product are you looking for?")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Enter specific product name:",
                placeholder=f"e.g., {category_info['examples'][0]}",
                key="category_search_input"
            )
        
        with col2:
            max_results = st.selectbox("Max results:", [10, 25, 50, 100, 500], index=2)
        
        # Region selection section
        st.markdown('<div class="region-selector">', unsafe_allow_html=True)
        st.markdown("**🌍 Search Region Selection:**")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_regions = st.multiselect(
                "Choose specific regions (leave empty for global search):",
                list(REGION_MAPPING.keys()),
                default=[],
                help="Select specific regions to focus your search. Global search covers all regions."
            )
        with col2:
            include_ratings = st.checkbox("Include product ratings", value=True)
            parallel_workers = st.slider("Search speed (workers):", 1, 8, 4, 
                                       help="Higher = faster but less polite to websites")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Example suggestions
        st.markdown("**💡 Popular searches in this category:**")
        cols = st.columns(min(len(category_info['examples']), 4))
        
        for i, example in enumerate(category_info['examples'][:4]):
            with cols[i]:
                if st.button(example, key=f"example_{i}"):
                    st.session_state.search_query = example
                    st.session_state.search_category = category.split()[1].lower()
                    st.session_state.max_results = max_results
                    st.session_state.selected_regions = [REGION_MAPPING[r] for r in selected_regions] if selected_regions else ['global']
                    st.session_state.parallel_workers = parallel_workers
                    st.session_state.current_page = 'scraping'
                    st.rerun()
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Search Products", use_container_width=True, disabled=not search_query):
                # Add to search history
                if search_query not in st.session_state.search_history:
                    st.session_state.search_history.append(search_query)
                
                st.session_state.search_query = search_query
                st.session_state.search_category = category.split()[1].lower()
                st.session_state.max_results = max_results
                st.session_state.selected_regions = [REGION_MAPPING[r] for r in selected_regions] if selected_regions else ['global']
                st.session_state.parallel_workers = parallel_workers
                st.session_state.current_page = 'scraping'
                st.rerun()
        
        with col2:
            if st.button("← Back to Categories", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'direct_search':
    st.markdown("## 🔧 Direct Product Search")
    st.markdown("Search for any product across all categories globally")
    
    with st.container():
        st.markdown('<div class="search-box">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Enter product name:",
                placeholder="e.g., Honda City, iPhone 15 Pro Max, Nike Air Jordan",
                key="direct_search_input"
            )
        
        with col2:
            max_results = st.selectbox("Max results:", [10, 25, 50, 100, 500], index=2)
        
        # Enhanced region selection
        st.markdown('<div class="region-selector">', unsafe_allow_html=True)
        st.markdown("**🌍 Advanced Search Options:**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            category_options = ["General"] + [cat.split()[1] for cat in categories.keys()]
            selected_category = st.selectbox(
                "Category (helps improve results):",
                category_options
            )
        with col2:
            selected_regions = st.multiselect(
                "Target regions:",
                list(REGION_MAPPING.keys()),
                default=["🌍 Global (All Regions)"],
                help="Select specific regions or keep Global for worldwide search"
            )
        with col3:
            parallel_workers = st.slider("Parallel workers:", 1, 10, 5,
                                       help="Higher = faster but less polite")
        st.markdown('</div>', unsafe_allow_html=True)
        
        direct_url = st.text_input(
            "🌐 Or enter a direct product URL:",
            placeholder="https://amazon.com/product-page"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Search Internet", use_container_width=True, disabled=not search_query):
                # Add to search history
                if search_query not in st.session_state.search_history:
                    st.session_state.search_history.append(search_query)
                
                st.session_state.search_query = search_query
                st.session_state.search_category = selected_category.lower()
                st.session_state.max_results = max_results
                st.session_state.selected_regions = [REGION_MAPPING[r] for r in selected_regions] if selected_regions else ['global']
                st.session_state.parallel_workers = parallel_workers
                st.session_state.current_page = 'scraping'
                st.rerun()
        
        with col2:
            if st.button("🌐 Scrape URL", use_container_width=True, disabled=not direct_url):
                st.session_state.direct_url = direct_url
                st.session_state.current_page = 'scraping'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'scraping':
    st.markdown("## 🔄 Searching the Global Internet...")
    
    # Create containers for real-time updates
    status_container = st.container()
    progress_container = st.container()
    
    with status_container:
        status_text = st.empty()
    
    with progress_container:
        progress_bar = st.progress(0)
    
    try:
        if hasattr(st.session_state, 'search_query'):
            # Enhanced internet search mode
            query = st.session_state.search_query
            category = getattr(st.session_state, 'search_category', 'general')
            max_results = getattr(st.session_state, 'max_results', 50)
            selected_regions = getattr(st.session_state, 'selected_regions', ['global'])
            parallel_workers = getattr(st.session_state, 'parallel_workers', 5)
            
            # Display search info
            regions_text = "Global" if 'global' in selected_regions else f"{len(selected_regions)} regions"
            status_text.markdown(f'<div class="status-box">🌍 Searching {regions_text} for: <strong>{query}</strong><br>Target: {max_results} results | Workers: {parallel_workers}</div>', unsafe_allow_html=True)
            progress_bar.progress(10)
            
            # Update scraper settings
            st.session_state.scraper.max_workers = parallel_workers
            
            # Perform the enhanced search and scraping with region filtering
            if 'global' not in selected_regions:
                # Update scraper regions for specific region search
                st.session_state.scraper.search_regions = selected_regions
            
            products = st.session_state.scraper.search_and_scrape_enhanced(
                query=query,
                category=category,
                max_results=max_results
            )
            
            progress_bar.progress(100)
            status_text.markdown('<div class="status-box">✅ Global search completed!</div>', unsafe_allow_html=True)
            
            # Clean up session state
            for attr in ['search_query', 'search_category', 'max_results', 'selected_regions', 'parallel_workers']:
                if hasattr(st.session_state, attr):
                    delattr(st.session_state, attr)
        
        elif hasattr(st.session_state, 'direct_url'):
            # Direct URL mode
            url = st.session_state.direct_url
            status_text.markdown(f'<div class="status-box">🌐 Scraping: <strong>{url}</strong></div>', unsafe_allow_html=True)
            progress_bar.progress(50)
            
            product = st.session_state.scraper.scrape_product_page_enhanced(url)
            products = [product] if product else []
            
            progress_bar.progress(100)
            status_text.markdown('<div class="status-box">✅ Scraping completed!</div>', unsafe_allow_html=True)
            
            # Clean up session state
            if hasattr(st.session_state, 'direct_url'):
                delattr(st.session_state, 'direct_url')
        
        # Store results
        st.session_state.scraped_data = products
        
        time.sleep(2)  # Show completion message briefly
        st.session_state.current_page = 'results'
        st.rerun()
    
    except Exception as e:
        st.error(f"An error occurred during scraping: {str(e)}")
        st.code(traceback.format_exc())
        if st.button("Return to Home"):
            st.session_state.current_page = 'home'
            st.rerun()

elif st.session_state.current_page == 'results':
    st.markdown("## 📊 Global Search Results")
    
    if not st.session_state.scraped_data:
        st.warning("No products found. This could be due to:")
        st.markdown("""
        - **Search engines blocking requests** - Try a different search term
        - **Network issues** - Check your internet connection
        - **Website protection** - Some sites block automated scraping
        - **Search term too specific** - Try broader terms
        - **Regional restrictions** - Product might not be available in selected regions
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Another Search"):
                st.session_state.current_page = 'direct_search'
                st.rerun()
        with col2:
            if st.button("🏠 Back to Home"):
                st.session_state.current_page = 'home'
                st.rerun()
    else:
        # Enhanced summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Products", len(st.session_state.scraped_data))
        with col2:
            valid_prices = [p for p in st.session_state.scraped_data if p['price'] != "Price not found"]
            st.metric("With Prices", len(valid_prices))
        with col3:
            in_stock = [p for p in st.session_state.scraped_data if p.get('availability') == "In Stock"]
            st.metric("In Stock", len(in_stock))
        with col4:
            unique_sites = len(set(p['product_url'].split('/')[2] for p in st.session_state.scraped_data))
            st.metric("Different Sites", unique_sites)
        with col5:
            unique_regions = len(set(p.get('search_region', 'unknown') for p in st.session_state.scraped_data))
            st.metric("Regions", unique_regions)
        
        # Enhanced filters
        st.markdown("### 🔍 Filter & Sort Results")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            price_filter = st.selectbox("Price:", ["All", "With Price Only", "No Price"])
        with col2:
            availability_filter = st.selectbox("Availability:", ["All", "In Stock", "Out of Stock", "Limited Stock", "Unknown"])
        with col3:
            region_filter = st.selectbox("Region:", ["All"] + list(set(p.get('search_region', 'unknown') for p in st.session_state.scraped_data)))
        with col4:
            sort_by = st.selectbox("Sort by:", ["Relevance", "Price (Low to High)", "Price (High to Low)", "Rating (High to Low)"])
        
        # Apply filters
        filtered_data = st.session_state.scraped_data.copy()
        
        if price_filter == "With Price Only":
            filtered_data = [p for p in filtered_data if p['price'] != "Price not found"]
        elif price_filter == "No Price":
            filtered_data = [p for p in filtered_data if p['price'] == "Price not found"]
        
        if availability_filter != "All":
            filtered_data = [p for p in filtered_data if p.get('availability') == availability_filter]
        
        if region_filter != "All":
            filtered_data = [p for p in filtered_data if p.get('search_region') == region_filter]
        
        # Sort results
        if sort_by.startswith("Price") and filtered_data:
            def extract_price_value(product):
                price_str = product['price']
                if price_str == "Price not found":
                    return float('inf') if "Low to High" in sort_by else 0
                
                numbers = re.findall(r'[\d,]+\.?\d*', price_str.replace(',', ''))
                if numbers:
                    try:
                        return float(numbers[0])
                    except:
                        return float('inf') if "Low to High" in sort_by else 0
                return float('inf') if "Low to High" in sort_by else 0
            
            filtered_data.sort(key=extract_price_value, reverse="High to Low" in sort_by)
        
        elif sort_by == "Rating (High to Low)":
            def extract_rating_value(product):
                rating_str = product.get('rating', 'No rating')
                if rating_str == "No rating":
                    return 0
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_str)
                return float(rating_match.group(1)) if rating_match else 0
            
            filtered_data.sort(key=extract_rating_value, reverse=True)
        
        # Display products with enhanced cards
        st.markdown(f"### Showing {len(filtered_data)} products")
        
        for i, product in enumerate(filtered_data):
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{product['name']}**")
                    if product.get('search_snippet'):
                        st.markdown(f"*{product['search_snippet'][:150]}...*")
                    
                    # Enhanced tags
                    tag_col1, tag_col2, tag_col3 = st.columns(3)
                    with tag_col1:
                        st.markdown(f'<span class="price-tag">{product["price"]}</span>', unsafe_allow_html=True)
                    with tag_col2:
                        st.markdown(f'<span class="location-tag">📍 {product["location"]}</span>', unsafe_allow_html=True)
                    with tag_col3:
                        if product.get('rating') and product['rating'] != "No rating":
                            st.markdown(f'<span class="rating-tag">⭐ {product["rating"]}</span>', unsafe_allow_html=True)
                    
                    if product.get('availability'):
                        availability_color = "green" if product['availability'] == "In Stock" else "red"
                        st.markdown(f'<span style="color: {availability_color}">📦 {product["availability"]}</span>', unsafe_allow_html=True)
                    
                    if product.get('description') and product['description'] != "No description available":
                        st.markdown(f"**Description:** {product['description']}")
                
                with col2:
                    if product.get('image_url'):
                        try:
                            st.image(product['image_url'], width=150)
                        except:
                            st.markdown("🖼️ Image not available")
                    else:
                        st.markdown("🖼️ No image")
                
                with col3:
                    if st.button("🔗 View Product", key=f"view_{i}"):
                        st.markdown(f"[Open in new tab]({product['product_url']})")
                    
                    # Show domain and region
                    domain = product['product_url'].split('/')[2] if '/' in product['product_url'] else "Unknown"
                    st.markdown(f"*{domain}*")
                    if product.get('search_region'):
                        st.markdown(f"*Region: {product['search_region']}*")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Enhanced export and action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Export to CSV", use_container_width=True):
                df = pd.DataFrame(filtered_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"scraped_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if PLOTLY_AVAILABLE and st.button("📊 View Analytics", use_container_width=True):
                st.session_state.current_page = 'analytics'
                st.rerun()
        
        with col3:
            if st.button("🔄 New Search", use_container_width=True):
                st.session_state.current_page = 'direct_search'
                st.rerun()
        
        with col4:
            if st.button("🗑️ Clear Results", use_container_width=True):
                st.session_state.scraped_data = []
                st.session_state.current_page = 'home'
                st.rerun()

elif st.session_state.current_page == 'analytics' and PLOTLY_AVAILABLE:
    st.markdown("## 📈 Product Analytics Dashboard")
    
    if not st.session_state.scraped_data:
        st.warning("No data available for analytics. Please search for products first.")
        if st.button("🔍 Start Searching"):
            st.session_state.current_page = 'direct_search'
            st.rerun()
    else:
        data = st.session_state.scraped_data
        
        # Price analysis
        valid_prices = []
        for product in data:
            if product['price'] != "Price not found":
                price_match = re.search(r'[\d,]+\.?\d*', product['price'].replace(',', ''))
                if price_match:
                    try:
                        valid_prices.append(float(price_match.group()))
                    except:
                        continue
        
        if valid_prices:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 💰 Price Distribution")
                fig = px.histogram(x=valid_prices, nbins=20, title="Price Distribution")
                fig.update_layout(xaxis_title="Price", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📊 Price Statistics")
                st.metric("Average Price", f"${sum(valid_prices)/len(valid_prices):.2f}")
                st.metric("Median Price", f"${sorted(valid_prices)[len(valid_prices)//2]:.2f}")
                st.metric("Price Range", f"${min(valid_prices):.2f} - ${max(valid_prices):.2f}")
        
        # Regional analysis
        regions = [p.get('search_region', 'unknown') for p in data]
        region_counts = {region: regions.count(region) for region in set(regions)}
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌍 Regional Distribution")
            fig = px.pie(values=list(region_counts.values()), names=list(region_counts.keys()), 
                        title="Products by Region")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🏪 Site Distribution")
            sites = [p['product_url'].split('/')[2] for p in data]
            site_counts = {site: sites.count(site) for site in set(sites)}
            top_sites = dict(sorted(site_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            
            fig = px.bar(x=list(top_sites.values()), y=list(top_sites.keys()), 
                        orientation='h', title="Top 10 Sites")
            st.plotly_chart(fig, use_container_width=True)
        
        # Availability analysis
        availability = [p.get('availability', 'Unknown') for p in data]
        availability_counts = {status: availability.count(status) for status in set(availability)}
        
        st.markdown("### 📦 Availability Analysis")
        fig = px.bar(x=list(availability_counts.keys()), y=list(availability_counts.values()),
                    title="Product Availability Status")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    pass