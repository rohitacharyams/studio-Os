#!/bin/bash
# Azure App Service startup script
cd /home/site/wwwroot/backend
pip install -r requirements-prod.txt
gunicorn --bind=0.0.0.0:8000 --timeout 600 wsgi:app
