from flask import Flask, request, jsonify, Response
import requests
from urllib.parse import urljoin, unquote

app = Flask(__name__)

# Base URL of the proxy itself
PROXY_BASE_URL = "http://127.0.0.1:5000"

@app.route('/<path:proxy_url>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(proxy_url):
    try:
        # Prepend 'http://' if missing for requests.
        if not proxy_url.startswith(('http://', 'https://')):
            proxy_url = 'https://' + proxy_url

        # Check for original URL in headers. This is a common practice for proxies.
        original_url = request.headers.get('X-Original-URL', proxy_url)
        
        # Determine the target URL
        target_url = urljoin(original_url, request.full_path)
        
        # Prepare headers to forward. This is crucial for handling sessions.
        headers = {key: value for key, value in request.headers if key.lower() not in ['host', 'origin', 'referer', 'x-forwarded-for', 'x-real-ip']}
        headers['X-Forwarded-For'] = request.remote_addr
        
        # Make the request to the target site.
        if request.method == 'GET':
            response = requests.get(target_url, headers=headers, params=request.args, stream=True)
        elif request.method == 'POST':
            response = requests.post(target_url, headers=headers, data=request.get_data(), stream=True)
        else:
            # Handle other methods.
            response = requests.request(request.method, target_url, headers=headers, data=request.get_data(), stream=True)

        # Create a Flask response from the fetched response.
        # This streams the content to the client, which is memory-efficient.
        # It also copies all headers and the status code.
        proxy_response = Response(response.iter_content(chunk_size=1024), status=response.status_code)
        
        # Copy headers from the target response to the proxy response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        for key, value in response.headers.items():
            if key.lower() not in excluded_headers:
                proxy_response.headers[key] = value

        return proxy_response
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Proxy request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
