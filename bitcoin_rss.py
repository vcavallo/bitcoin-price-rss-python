import time
import os
import sys
import http.server
import socketserver
import threading
import requests
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator

def get_bitcoin_price():
    """Fetch current Bitcoin price from CoinGecko API"""
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        response.raise_for_status()
        return response.json()['bitcoin']['usd']
    except (requests.RequestException, KeyError) as e:
        print(f"Error fetching Bitcoin price: {e}")
        return None

def create_or_update_rss(price, data_dir='data/public', base_url='http://localhost:8000', max_entries=10):
    """Generate RSS feed with current Bitcoin price"""
    if price is None:
        return False
        
    try:
        # Try to read existing feed
        feed_path = os.path.join(data_dir, 'bitcoin_price_feed.xml')
        existing_entries = []
        
        if os.path.exists(feed_path):
            try:
                # Try to use feedparser if available
                try:
                    from feedparser import parse
                    feed = parse(feed_path)
                    # Convert existing entries to (timestamp, price, datetime) tuples
                    for entry in feed.entries:
                        try:
                            entry_id = entry.id.split('/')[-1]
                            timestamp = int(entry_id)
                            price_str = entry.title.split('$')[1].replace(',', '')
                            price_val = float(price_str)
                            pub_date = datetime.fromtimestamp(timestamp, timezone.utc)
                            existing_entries.append((timestamp, price_val, pub_date))
                        except (IndexError, ValueError):
                            continue
                except ImportError:
                    # Fallback to simple XML parsing if feedparser is not available
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(feed_path)
                    root = tree.getroot()
                    for item in root.findall('.//item'):
                        try:
                            guid = item.find('guid').text
                            title = item.find('title').text
                            pubDate = item.find('pubDate').text
                            
                            entry_id = guid.split('/')[-1]
                            timestamp = int(entry_id)
                            price_str = title.split('$')[1].replace(',', '')
                            price_val = float(price_str)
                            # Parse the RFC 822 date format
                            from email.utils import parsedate_to_datetime
                            pub_date = parsedate_to_datetime(pubDate)
                            existing_entries.append((timestamp, price_val, pub_date))
                        except (AttributeError, IndexError, ValueError):
                            continue
            except Exception as e:
                print(f"Error parsing existing feed: {e}")
                # Continue with empty existing entries if parsing fails
        
        # Create new feed
        fg = FeedGenerator()
        fg.id(f'{base_url}/bitcoin-price-feed')
        fg.title('Bitcoin Price Feed')
        fg.subtitle('Live Bitcoin price updates every 30 minutes')
        fg.link(href=base_url)
        fg.language('en')
        
        # Add current price as new entry
        timestamp = int(time.time())
        current_time = datetime.now(timezone.utc)
        
        fe = fg.add_entry()
        fe.id(f'{base_url}/price/{timestamp}')
        fe.title(f'Bitcoin Price: ${price:,.2f}')
        fe.link(href=base_url)
        fe.description(f'The current price of Bitcoin is ${price:,.2f} USD as of {current_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')
        fe.published(current_time)
        
        # Add previous entries
        existing_entries.sort(reverse=True)  # Sort by timestamp descending
        for prev_timestamp, prev_price, prev_time in existing_entries[:max_entries-1]:
            fe = fg.add_entry()
            fe.id(f'{base_url}/price/{prev_timestamp}')
            fe.title(f'Bitcoin Price: ${prev_price:,.2f}')
            fe.link(href=base_url)
            fe.description(f'The price of Bitcoin was ${prev_price:,.2f} USD as of {prev_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')
            fe.published(prev_time)
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Write the feed atomically using a temporary file
        temp_path = os.path.join(data_dir, 'bitcoin_price_feed.xml.tmp')
        final_path = os.path.join(data_dir, 'bitcoin_price_feed.xml')
        
        with open(temp_path, 'wb') as f:
            content = fg.rss_str(pretty=True)
            f.write(content)
        
        os.replace(temp_path, final_path)
        
        # Create/update index.html
        index_path = os.path.join(data_dir, 'index.html')
        with open(index_path, 'w') as f:
            f.write("""
<html>
<head>
    <title>Bitcoin Price RSS Feed</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; }}
        h1 {{ color: #333; }}
        .price {{ font-size: 1.2em; margin: 1em 0; }}
        .updated {{ color: #666; }}
    </style>
</head>
<body>
    <h1>Bitcoin Price RSS Feed</h1>
    <p class="price">Current Bitcoin Price: ${:,.2f} USD</p>
    <p class="updated">Last updated: {}</p>
    <p><a href="bitcoin_price_feed.xml">View RSS Feed</a></p>
</body>
</html>
""".format(price, current_time.strftime("%Y-%m-%d %H:%M:%S UTC")))
        
        return True
    except Exception as e:
        print(f"Error creating RSS feed: {e}")
        return False

class SimpleHTTPRequestHandlerWithCORS(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

class SimpleHTTPRequestHandlerWithCORS(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='data/public', **kwargs)
        
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def run_http_server(port=8000):
    """Run a simple HTTP server to serve the RSS feed"""
    with socketserver.TCPServer(("", port), SimpleHTTPRequestHandlerWithCORS) as httpd:
        print(f"Serving at http://localhost:{port}")
        httpd.serve_forever()

def main():
    """Main loop to update the RSS feed periodically"""
    print("Starting Bitcoin Price RSS Feed Service")
    
    # Start HTTP server in a separate thread
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    
    while True:
        try:
            price = get_bitcoin_price()
            if create_or_update_rss(price):
                print(f"Successfully updated RSS feed with price: ${price:,.2f}")
            else:
                print("Failed to update RSS feed")
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
        
        # Sleep for 30 minutes
        # time.sleep(1800)
        time.sleep(100)

if __name__ == "__main__":
    main()
