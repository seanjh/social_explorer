#!flask/bin/python
import os
from server.explorer import app

if os.getenv('FLASK_ENV', None) == 'PRODUCTION':
    app.run(debug=False)
else:
    app.run(port=5000, debug=True)