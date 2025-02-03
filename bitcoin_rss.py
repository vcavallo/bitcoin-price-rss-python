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

def create_or_update_rss(price, data_dir='data'):
    """Generate RSS feed with current Bitcoin price"""
    if price is None:
        return False
        
    try:
        base_url = 'http://localhost:8000'  # Default to localhost, can be changed
        
        fg = FeedGenerator()
        fg.id(f'{base_url}/bitcoin-price-feed')
        fg.title('Bitcoin Price Feed')
        fg.subtitle('Live Bitcoin price updates every 30 minutes')
        fg.link(href=base_url)
        fg.language('en')
        
        timestamp = int(time.time())
        current_time = datetime.now(timezone.utc)
        
        fe = fg.add_entry()
        fe.id(f'{base_url}/price/{timestamp}')
        fe.title(f'Bitcoin Price: ${price:,.2f}')
        fe.link(href=base_url)
        fe.description(f'The current price of Bitcoin is ${price:,.2f} USD as of {current_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')
        fe.published(current_time)
        
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

def run_http_server(port=8000, directory='data'):
    """Run a simple HTTP server to serve the RSS feed"""
    os.chdir(directory)
    handler = SimpleHTTPRequestHandlerWithCORS
    with socketserver.TCPServer(("", port), handler) as httpd:
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
        time.sleep(1800)

if __name__ == "__main__":
    main()
