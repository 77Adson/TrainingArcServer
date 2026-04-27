from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) # Run the Flask app on all available interfaces and port 5000