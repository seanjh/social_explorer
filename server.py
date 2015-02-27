import os
from server.explorer import app

if __name__ == '__main__':
    if os.getenv('FLASK_ENV', None) == 'PRODUCTION':
        app.run(host='0.0.0.0', port=80)
    else:
        app.run(debug=True, port=5000)