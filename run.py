from app import create_app
from livereload import Server
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv(override=True)

# Detect environment
environment = os.getenv("ENV", "production")

# Create the Flask app
app = create_app()

if __name__ == "__main__":
    if environment == "development":
        server = Server(app.wsgi_app)
        server.watch("app/**/*.py")
        server.watch("app/templates/**/*.html")
        server.watch("app/static/**/*.css")
        print("Running in development mode with LiveReload at http://127.0.0.1:5000")
        server.serve(port=5000)
    else:
        print("Running in production mode at http://127.0.0.1:5000")
        app.run(port=5000)
