from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from urllib.parse import unquote
import re

app = Flask(__name__)

# Configure CORS to only allow requests from homelessman's websim subdomains
CORS(app, origins=r'https://websim\.com/@homelessman.*')

@app.route('/getweb')
def get_website():
    try:
        # Additional origin check for extra security
        origin = request.headers.get('Origin') or request.headers.get('Referer', '').rstrip('/')
        if not origin:
            return jsonify({'error': 'Access denied: No origin header'}), 403
            
        # Check if origin matches the allowed pattern
        pattern = r'^https://websim\.com/@homelessman(/.*)?$'
        if not re.match(pattern, origin):
            return jsonify({'error': 'Access denied: Invalid origin'}), 403
        
        site_url = request.args.get('site')
        if not site_url:
            return jsonify({'error': 'Missing site parameter'}), 400
        
        # Decode URL if it's encoded
        site_url = unquote(site_url)
        
        # Add protocol if missing
        if not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
        
        # Fetch the website
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(site_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return {
            'url': site_url,
            'status_code': response.status_code,
            'content': response.text,
            'headers': dict(response.headers)
        }
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch website: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/')
def home():
    return '''
    Website Fetcher API
    Use: /getweb?site=https://example.com
    Access restricted to @homelessman websim domains
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
