import os
from server.explorer import app

if __name__ == '__main__':
    if os.getenv('FLASK_ENV', None) == 'PRODUCTION':
        app.run('0.0.0.0')
        print 'Running production app'
    else:
        app.run(debug=True)
        print 'Running app on localhost:5000'