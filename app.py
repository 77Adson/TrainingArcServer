from flask import Flask, jsonify, request
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'message': 'Hello from Local Flask Server!',
        'status': 'OK',
        'timestamp': datetime.datetime.now().isoformat(),
        'environment': 'local'
    })

@app.route('/status')
def status():
    return jsonify({
        'status': 'running',
        'server_time': datetime.datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': 'local'
    })

@app.route('/hello/<name>')
def hello_name(name):
    return jsonify({
        'message': f'Hello {name}!',
        'greeting_time': datetime.datetime.now().isoformat(),
        'environment': 'local'
    })

@app.route('/test', methods=['POST', 'GET'])
def test():
    if request.method == 'POST':
        return jsonify({
            'message': 'POST request received successfully!',
            'method': 'POST',
            'received_at': datetime.datetime.now().isoformat(),
            'environment': 'local'
        })
    else:
        return jsonify({
            'message': 'GET request received!',
            'method': 'GET',
            'received_at': datetime.datetime.now().isoformat(),
            'environment': 'local'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)