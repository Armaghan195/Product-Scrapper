import streamlit as st
import pandas as pd
from datetime import datetime
import time
import traceback
import re
from scraper import ProductScraper

# Configure page
st.set_page_config(
    page_title="SmartScrape Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (removed the white bar styling)
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
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
    }
    
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .price-tag {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2e7d32;
    }
    
    .location-tag {
        color: #1976d2;
        font-style: italic;
    }
    
    .status-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
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

# Categories with better descriptions
categories = {
    "🏠 Household": {
        "description": "Home appliances, kitchen items, cleaning supplies",
        "examples": ["Vacuum cleaner", "Coffee maker", "Air purifier", "Blender"]
    },
    "💻 Technology": {
        "description": "Electronics, gadgets, computers, phones",
        "examples": ["iPhone 15", "MacBook Pro", "Gaming laptop", "Wireless headphones"]
    },
    "📚 Books": {
        "description": "Books, e-books, audiobooks, educational materials",
        "examples": ["Python programming book", "Fiction novel", "Self-help book"]
    },
    "🚗 Automotive": {
        "description": "Car parts, accessories, tools, automotive supplies",
        "examples": ["Car battery", "Brake pads", "Motor oil", "Car charger"]
    }
}

# Sidebar navigation
st.sidebar.markdown("## 🔍 SmartScrape Pro")
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

# Display current results count in sidebar
if st.session_state.scraped_data:
    st.sidebar.markdown("---")
    st.sidebar.metric("Current Results", len(st.session_state.scraped_data))

# Main content
if st.session_state.current_page == 'home':
    st.markdown('<h1 class="main-header">🔍 SmartScrape Pro</h1>', unsafe_allow_html=True)
    st.markdown("### Find the best deals across the web with intelligent product scraping")
    
    st.markdown("---")
    st.markdown("## 🎯 Choose a Category to Start")
    
    for category, info in categories.items():
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button(category, use_container_width=True, key=f"cat_{category}"):
                    st.session_state.selected_category = category
                    st.session_state.current_page = 'category_search'
                    st.rerun()
            
            with col2:
                st.markdown(f"**{info['description']}**")
                st.markdown(f"*Examples: {', '.join(info['examples'][:3])}...*")
        
        st.markdown("---")

elif st.session_state.current_page == 'category_search':
    category = st.session_state.selected_category
    category_info = categories[category]
    
    st.markdown(f"## {category}")
    st.markdown(f"*{category_info['description']}*")
    
    st.markdown("---")
    
    # Search form
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
            max_results = st.selectbox("Max results:", [5, 10, 15, 20], index=1)
        
        # Example suggestions
        st.markdown("**💡 Popular searches in this category:**")
        cols = st.columns(len(category_info['examples']))
        
        for i, example in enumerate(category_info['examples']):
            with cols[i]:
                if st.button(example, key=f"example_{i}"):
                    st.session_state.search_query = example
                    st.session_state.search_category = category.split()[1].lower()
                    st.session_state.max_results = max_results
                    st.session_state.current_page = 'scraping'
                    st.rerun()
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Search Products", use_container_width=True, disabled=not search_query):
                st.session_state.search_query = search_query
                st.session_state.search_category = category.split()[1].lower()
                st.session_state.max_results = max_results
                st.session_state.current_page = 'scraping'
                st.rerun()
        
        with col2:
            if st.button("← Back to Categories", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'direct_search':
    st.markdown("## 🔧 Direct Product Search")
    st.markdown("Search for any product across all categories")
    
    with st.container():
        st.markdown('<div class="search-box">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Enter product name:",
                placeholder="e.g., iPhone 15 Pro Max, Nike Air Jordan, Samsung TV",
                key="direct_search_input"
            )
        
        with col2:
            max_results = st.selectbox("Max results:", [5, 10, 15, 20], index=1)
        
        # Category selection for better results
        category_options = ["General"] + [cat.split()[1] for cat in categories.keys()]
        selected_category = st.selectbox(
            "Category (optional - helps improve results):",
            category_options
        )
        
        direct_url = st.text_input(
            "🌐 Or enter a direct product URL:",
            placeholder="https://amazon.com/product-page"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Search Internet", use_container_width=True, disabled=not search_query):
                st.session_state.search_query = search_query
                st.session_state.search_category = selected_category.lower()
                st.session_state.max_results = max_results
                st.session_state.current_page = 'scraping'
                st.rerun()
        
        with col2:
            if st.button("🌐 Scrape URL", use_container_width=True, disabled=not direct_url):
                st.session_state.direct_url = direct_url
                st.session_state.current_page = 'scraping'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'scraping':
    st.markdown("## 🔄 Searching the Internet...")
    
    # Create a container for real-time updates
    status_container = st.container()
    progress_container = st.container()
    
    with status_container:
        status_text = st.empty()
    
    with progress_container:
        progress_bar = st.progress(0)
    
    try:
        if hasattr(st.session_state, 'search_query'):
            # Internet search mode
            query = st.session_state.search_query
            category = getattr(st.session_state, 'search_category', 'general')
            max_results = getattr(st.session_state, 'max_results', 10)
            
            status_text.markdown(f'<div class="status-box">🔍 Searching the internet for: <strong>{query}</strong></div>', unsafe_allow_html=True)
            progress_bar.progress(10)
            
            # Perform the search and scraping
            products = st.session_state.scraper.search_and_scrape(
                query=query,
                category=category,
                max_results=max_results
            )
            
            progress_bar.progress(100)
            status_text.markdown('<div class="status-box">✅ Search completed!</div>', unsafe_allow_html=True)
            
            # Clean up session state
            for attr in ['search_query', 'search_category', 'max_results']:
                if hasattr(st.session_state, attr):
                    delattr(st.session_state, attr)
        
        elif hasattr(st.session_state, 'direct_url'):
            # Direct URL mode
            url = st.session_state.direct_url
            status_text.markdown(f'<div class="status-box">🌐 Scraping: <strong>{url}</strong></div>', unsafe_allow_html=True)
            progress_bar.progress(50)
            
            product = st.session_state.scraper.scrape_product_page(url)
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
    st.markdown("## 📊 Search Results")
    
    if not st.session_state.scraped_data:
        st.warning("No products found. This could be due to:")
        st.markdown("""
        - **Search engines blocking requests** - Try a different search term
        - **Network issues** - Check your internet connection
        - **Website protection** - Some sites block automated scraping
        - **Search term too specific** - Try broader terms
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
        # Summary metrics - FIXED INDENTATION
        col1, col2, col3, col4 = st.columns(4)
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
        
        # Filters
        st.markdown("### 🔍 Filter Results")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            price_filter = st.selectbox("Price:", ["All", "With Price Only", "No Price"])
        with col2:
            availability_filter = st.selectbox("Availability:", ["All", "In Stock", "Out of Stock", "Unknown"])
        with col3:
            sort_by = st.selectbox("Sort by:", ["Relevance", "Price (Low to High)", "Price (High to Low)"])
        
        # Apply filters
        filtered_data = st.session_state.scraped_data.copy()
        
        if price_filter == "With Price Only":
            filtered_data = [p for p in filtered_data if p['price'] != "Price not found"]
        elif price_filter == "No Price":
            filtered_data = [p for p in filtered_data if p['price'] == "Price not found"]
        
        if availability_filter != "All":
            filtered_data = [p for p in filtered_data if p.get('availability') == availability_filter]
        
        # Sort results
        if sort_by.startswith("Price") and filtered_data:
            def extract_price_value(product):
                price_str = product['price']
                if price_str == "Price not found":
                    return float('inf') if "Low to High" in sort_by else 0
                
                # Extract numeric value from price string
                numbers = re.findall(r'[\d,]+\.?\d*', price_str.replace(',', ''))
                if numbers:
                    try:
                        return float(numbers[0])
                    except:
                        return float('inf') if "Low to High" in sort_by else 0
                return float('inf') if "Low to High" in sort_by else 0
            
            filtered_data.sort(key=extract_price_value, reverse="High to Low" in sort_by)
        
        # Display products
        st.markdown(f"### Showing {len(filtered_data)} products")
        
        for i, product in enumerate(filtered_data):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{product['name']}**")
                    if product.get('search_snippet'):
                        st.markdown(f"*{product['search_snippet'][:100]}...*")
                    
                    st.markdown(f'<span class="price-tag">{product["price"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="location-tag">📍 {product["location"]}</span>', unsafe_allow_html=True)
                    
                    if product.get('availability'):
                        availability_color = "green" if product['availability'] == "In Stock" else "red"
                        st.markdown(f'<span style="color: {availability_color}">📦 {product["availability"]}</span>', unsafe_allow_html=True)
                
                with col2:
                    if product.get('image_url'):
                        try:
                            st.image(product['image_url'], width=120)
                        except:
                            st.markdown("🖼️ Image not available")
                    else:
                        st.markdown("🖼️ No image")
                
                with col3:
                    if st.button("🔗 View Product", key=f"view_{i}"):
                        st.markdown(f"[Open in new tab]({product['product_url']})")
                    
                    # Show domain
                    domain = product['product_url'].split('/')[2] if '/' in product['product_url'] else "Unknown"
                    st.markdown(f"*{domain}*")
            
            st.markdown("---")
        
        # Export and action buttons
        col1, col2, col3 = st.columns(3)
        
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
            if st.button("🔄 New Search", use_container_width=True):
                st.session_state.current_page = 'direct_search'
                st.rerun()
        
        with col3:
            if st.button("🗑️ Clear Results", use_container_width=True):
                st.session_state.scraped_data = []
                st.session_state.current_page = 'home'
                st.rerun()

if __name__ == "__main__":
    pass