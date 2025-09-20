from flask import Flask, request, jsonify, Response
import requests

app = Flask(__name__)

@app.route('/proxy', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_request():
    try:
        # Get the target URL from the 'site' query parameter.
        target_url = request.args.get('site')
        if not target_url:
            return jsonify({'error': 'Missing site parameter'}), 400

        # Ensure the URL has a protocol
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url

        # Prepare headers to forward.
        headers = {key: value for key, value in request.headers if key.lower() not in ['host', 'origin', 'referer', 'x-forwarded-for', 'x-real-ip']}
        headers['X-Forwarded-For'] = request.remote_addr

        # Make the request to the target site based on the HTTP method.
        if request.method == 'GET':
            response = requests.get(target_url, headers=headers, params=request.args, stream=True)
        elif request.method == 'POST':
            response = requests.post(target_url, headers=headers, data=request.get_data(), stream=True)
        else:
            response = requests.request(request.method, target_url, headers=headers, data=request.get_data(), stream=True)

        # Create a Flask response from the fetched response.
        proxy_response = Response(response.iter_content(chunk_size=1024), status=response.status_code)
        
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        for key, value in response.headers.items():
            if key.lower() not in excluded_headers:
                proxy_response.headers[key] = value

        return proxy_response

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Proxy request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/')
def home():
    return '''
    Proxy API
    Use: /proxy?site=https://example.com
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
