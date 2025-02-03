# Standalone Bitcoin RSS Feed

A simple Python service that fetches the current Bitcoin price every 30 minutes and serves it as an RSS feed.

## Features

- Fetches Bitcoin price from CoinGecko API
- Updates RSS feed every 30 minutes
- Serves feed via built-in HTTP server
- Simple web interface to view the current price and RSS feed

## Requirements

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone this repository or download the files
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the service:
   ```bash
   python bitcoin_rss.py
   ```

2. Access the web interface at: http://localhost:8000

The service will:
- Start a web server on port 8000
- Create a `data` directory to store the RSS feed
- Update the Bitcoin price every 30 minutes
- Serve both an RSS feed and a simple web page

## Customization

- To change the port, modify the `port` parameter in the `run_http_server` function call
- To change the update frequency, modify the sleep duration in the main loop (default is 1800 seconds / 30 minutes)
- To serve on a different domain, update the `base_url` variable in `create_or_update_rss`

## Hosting

You could run this on a server and set up nginx or apache to point to the right places idk I'm doing it in a big Docker setup with Traefik but I haven't thought about how to host just this one service, do your own research :)

## License

MIT License
