"""
CareerLens AI — WSGI entry point for gunicorn / IBM Cloud deployment.
"""
from app import app

if __name__ == "__main__":
    app.run()
