import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # FIX #6: debug and port were hardcoded — now read from config/env
    port = int(os.getenv('PORT', 5000))
    app.run(debug=app.config.get('DEBUG', False), port=port)
